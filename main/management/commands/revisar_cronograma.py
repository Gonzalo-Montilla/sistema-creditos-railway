from django.core.management.base import BaseCommand
from decimal import Decimal
from main.models import Credito, CronogramaPago, Pago, TareaCobro

class Command(BaseCommand):
    help = 'Revisa el cronograma de pagos del crédito problemático'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Revisando cronograma del crédito problemático...")
        
        # Buscar el pago problemático
        pago_problema = Pago.objects.get(id=45)
        credito = pago_problema.credito
        
        self.stdout.write(f"\n=== INFORMACIÓN DEL CRÉDITO #{credito.id} ===")
        self.stdout.write(f"Cliente: {credito.cliente.nombre_completo}")
        self.stdout.write(f"Monto del crédito: ${credito.monto}")
        self.stdout.write(f"Tasa de interés: {credito.tasa_interes}%")
        self.stdout.write(f"Tipo de plazo: {credito.get_tipo_plazo_display()}")
        self.stdout.write(f"Cantidad de cuotas: {credito.cantidad_cuotas}")
        self.stdout.write(f"Valor cuota calculado: ${credito.valor_cuota}")
        self.stdout.write(f"Monto total a pagar: ${credito.monto_total}")
        
        # Revisar cronograma completo
        cronograma = CronogramaPago.objects.filter(credito=credito).order_by('numero_cuota')
        self.stdout.write(f"\n=== CRONOGRAMA DE PAGOS (Total: {cronograma.count()} cuotas) ===")
        
        for i, cuota in enumerate(cronograma):
            estado_text = f"[{cuota.estado}]"
            pagado_text = f"Pagado: ${cuota.monto_pagado}" if cuota.monto_pagado > 0 else "Sin pagos"
            
            self.stdout.write(
                f"  Cuota #{cuota.numero_cuota}: ${cuota.monto_cuota} - "
                f"{cuota.fecha_vencimiento} {estado_text} - {pagado_text}"
            )
            
            # Mostrar solo las primeras 5 y las últimas 5
            if i == 4 and cronograma.count() > 10:
                self.stdout.write(f"  ... ({cronograma.count() - 10} cuotas intermedias)")
                # Saltar a las últimas 5
                continue
            elif i >= cronograma.count() - 5:
                continue
            elif i > 4 and i < cronograma.count() - 5:
                continue
        
        # Revisar la cuota específica del pago problemático
        cuota_problema = pago_problema.cuota
        self.stdout.write(f"\n=== CUOTA ESPECÍFICA DEL PAGO PROBLEMÁTICO ===")
        self.stdout.write(f"Cuota ID: {cuota_problema.id}")
        self.stdout.write(f"Número de cuota: {cuota_problema.numero_cuota}")
        self.stdout.write(f"Monto de la cuota: ${cuota_problema.monto_cuota}")
        self.stdout.write(f"Monto pagado: ${cuota_problema.monto_pagado}")
        self.stdout.write(f"Saldo pendiente: ${cuota_problema.saldo_pendiente()}")
        self.stdout.write(f"Estado: {cuota_problema.estado}")
        self.stdout.write(f"Fecha vencimiento: {cuota_problema.fecha_vencimiento}")
        
        # Revisar todos los pagos del crédito
        pagos = Pago.objects.filter(credito=credito).order_by('fecha_pago')
        self.stdout.write(f"\n=== PAGOS DEL CRÉDITO (Total: {pagos.count()}) ===")
        
        total_pagado = Decimal('0')
        for pago in pagos:
            self.stdout.write(f"  Pago #{pago.id}: ${pago.monto} - {pago.fecha_pago} - Cuota #{pago.numero_cuota}")
            total_pagado += pago.monto
        
        self.stdout.write(f"\nTotal pagado según pagos: ${total_pagado}")
        self.stdout.write(f"Saldo pendiente según crédito: ${credito.saldo_pendiente()}")
        
        # Revisar tareas de cobro relacionadas
        tareas = TareaCobro.objects.filter(cuota__credito=credito).order_by('fecha_asignacion')
        self.stdout.write(f"\n=== TAREAS DE COBRO DEL CRÉDITO (Total: {tareas.count()}) ===")
        
        for tarea in tareas[:10]:  # Mostrar solo las primeras 10
            monto_cobrado_text = f"${tarea.monto_cobrado}" if tarea.monto_cobrado else "N/A"
            self.stdout.write(
                f"  Tarea #{tarea.id}: {tarea.estado} - "
                f"Cuota #{tarea.cuota.numero_cuota} - "
                f"Cobrado: {monto_cobrado_text} - "
                f"Esperado: ${tarea.monto_a_cobrar}"
            )
        
        # Análisis de discrepancias
        self.stdout.write(f"\n=== ANÁLISIS DE DISCREPANCIAS ===")
        
        # Verificar si el cálculo de valor_cuota es correcto
        if credito.cantidad_cuotas > 0:
            valor_cuota_simple = credito.monto / credito.cantidad_cuotas
            self.stdout.write(f"Valor cuota sin interés (simple): ${valor_cuota_simple}")
            self.stdout.write(f"Valor cuota con interés (actual): ${credito.valor_cuota}")
            
            diferencia = abs(credito.valor_cuota - valor_cuota_simple)
            self.stdout.write(f"Diferencia por interés: ${diferencia}")
        
        # Verificar consistencia entre cronograma y crédito
        if cronograma.exists():
            primera_cuota = cronograma.first()
            self.stdout.write(f"Monto primera cuota en cronograma: ${primera_cuota.monto_cuota}")
            self.stdout.write(f"Monto cuota calculado en crédito: ${credito.valor_cuota}")
            
            if primera_cuota.monto_cuota != credito.valor_cuota:
                self.stdout.write(self.style.ERROR("⚠️  INCONSISTENCIA: El valor en cronograma no coincide con el calculado"))
        
        self.stdout.write(self.style.SUCCESS("✅ Análisis completado"))