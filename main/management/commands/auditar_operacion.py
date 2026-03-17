from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from main.models import Credito, CronogramaPago, Pago, TareaCobro


class Command(BaseCommand):
    help = "Audita integridad operativa (pagos, cuotas, tareas, cartera)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Aplica correcciones seguras (normalizacion de estados y cierre de tareas huerfanas).",
        )

    def handle(self, *args, **options):
        apply_fix = bool(options.get("fix"))
        self.stdout.write("Iniciando auditoria operativa...\n")

        resumen = {
            "cronograma_pagado_legacy": 0,
            "tareas_huerfanas_abiertas": 0,
            "tareas_abiertas_duplicadas": 0,
            "pagos_sin_cuota": 0,
            "creditos_cerrables_por_saldo": 0,
            "fixes_aplicados": 0,
        }

        # 1) Estados legacy en cronograma
        legacy_qs = CronogramaPago.objects.filter(estado="PAGADO")
        resumen["cronograma_pagado_legacy"] = legacy_qs.count()

        # 2) Tareas abiertas de cuotas ya pagadas
        estados_abiertos = [
            "PENDIENTE",
            "EN_PROCESO",
            "NO_ENCONTRADO",
            "NO_ESTABA",
            "NO_PUDO_PAGAR",
            "REPROGRAMADO",
        ]
        tareas_huerfanas = TareaCobro.objects.filter(
            estado__in=estados_abiertos,
            cuota__estado__in=["PAGADA", "PAGADO"],
        )
        resumen["tareas_huerfanas_abiertas"] = tareas_huerfanas.count()

        # 3) Duplicados operativos de tareas abiertas por cuota + fecha
        duplicadas = (
            TareaCobro.objects.filter(estado__in=estados_abiertos)
            .values("cuota_id", "fecha_asignacion")
            .annotate(c=Count("id"))
            .filter(c__gt=1)
        )
        resumen["tareas_abiertas_duplicadas"] = duplicadas.count()

        # 4) Pagos sin cuota asociada
        pagos_sin_cuota = Pago.objects.filter(cuota__isnull=True)
        resumen["pagos_sin_cuota"] = pagos_sin_cuota.count()

        # 5) Creditos con saldo practicamente cero pero no cerrados
        creditos_cerrables = []
        for credito in Credito.objects.filter(estado__in=["APROBADO", "DESEMBOLSADO", "VENCIDO"]):
            if credito.saldo_pendiente() < 1:
                creditos_cerrables.append(credito.id)
        resumen["creditos_cerrables_por_saldo"] = len(creditos_cerrables)

        # Correcciones seguras
        if apply_fix:
            with transaction.atomic():
                # A) Normalizar estado legacy PAGADO -> PAGADA
                updated_legacy = legacy_qs.update(estado="PAGADA")
                resumen["fixes_aplicados"] += updated_legacy

                # B) Cerrar tareas huerfanas de cuotas pagadas
                cuota_ids = set(tareas_huerfanas.values_list("cuota_id", flat=True))
                for cuota_id in cuota_ids:
                    closed = TareaCobro.objects.filter(
                        cuota_id=cuota_id,
                        estado__in=estados_abiertos,
                    ).update(
                        estado="CANCELADO",
                        fecha_reprogramacion=None,
                        observaciones="Cancelada automaticamente en auditoria: cuota pagada.",
                    )
                    resumen["fixes_aplicados"] += closed

                # C) Vincular pagos sin cuota cuando numero_cuota > 0 y coincide credito+cuota
                vinculados = 0
                for pago in pagos_sin_cuota.select_related("credito"):
                    if not pago.numero_cuota or pago.numero_cuota <= 0:
                        continue
                    cuota = CronogramaPago.objects.filter(
                        credito_id=pago.credito_id,
                        numero_cuota=pago.numero_cuota,
                    ).first()
                    if cuota:
                        pago.cuota = cuota
                        pago.save(update_fields=["cuota"])
                        vinculados += 1
                resumen["fixes_aplicados"] += vinculados

        # Reporte
        self.stdout.write("RESULTADO AUDITORIA")
        self.stdout.write(f"- cronograma_pagado_legacy: {resumen['cronograma_pagado_legacy']}")
        self.stdout.write(f"- tareas_huerfanas_abiertas: {resumen['tareas_huerfanas_abiertas']}")
        self.stdout.write(f"- tareas_abiertas_duplicadas: {resumen['tareas_abiertas_duplicadas']}")
        self.stdout.write(f"- pagos_sin_cuota: {resumen['pagos_sin_cuota']}")
        self.stdout.write(f"- creditos_cerrables_por_saldo: {resumen['creditos_cerrables_por_saldo']}")
        if apply_fix:
            self.stdout.write(f"- fixes_aplicados: {resumen['fixes_aplicados']}")
        self.stdout.write("")

        # Hallazgos en detalle para accion manual
        if resumen["pagos_sin_cuota"] > 0:
            self.stdout.write("Pagos sin cuota (detalle breve):")
            for p in pagos_sin_cuota.values("id", "credito_id", "numero_cuota", "monto")[:10]:
                self.stdout.write(
                    f"  Pago #{p['id']} | credito={p['credito_id']} | numero_cuota={p['numero_cuota']} | monto={p['monto']}"
                )
            self.stdout.write("")

        if resumen["creditos_cerrables_por_saldo"] > 0:
            self.stdout.write(
                "Creditos con saldo < 1 y estado activo (revisar cierre): "
                + ", ".join(str(cid) for cid in creditos_cerrables[:20])
            )
            self.stdout.write("")

        hay_bloqueantes = any(
            [
                resumen["cronograma_pagado_legacy"] > 0,
                resumen["tareas_huerfanas_abiertas"] > 0,
                resumen["tareas_abiertas_duplicadas"] > 0,
            ]
        )

        if hay_bloqueantes and not apply_fix:
            self.stdout.write(
                self.style.WARNING("Estado: ATENCION - hay hallazgos. Ejecuta con --fix para correcciones seguras.")
            )
        else:
            self.stdout.write(self.style.SUCCESS("Estado: OK operativo para demo."))
