# Recordatorios de cuotas por correo (ejecutar diario, ej: 7:00 AM)
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from datetime import date
from collections import defaultdict

from main.models import CronogramaPago


class Command(BaseCommand):
    help = 'Envía por correo recordatorios automáticos de pago (cuotas del día).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fecha',
            type=str,
            help='Fecha a considerar (YYYY-MM-DD). Por defecto hoy.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo mostrar a quién se enviaría, sin enviar.',
        )

    def handle(self, *args, **options):
        if options['fecha']:
            try:
                dia = timezone.datetime.strptime(options['fecha'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(self.style.ERROR('Fecha inválida. Use YYYY-MM-DD.'))
                return
        else:
            dia = date.today()

        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write('Modo dry-run: no se enviarán correos.')

        # Cuotas que vencen ese día y están pendientes/parciales
        cuotas = CronogramaPago.objects.filter(
            fecha_vencimiento=dia,
            estado__in=['PENDIENTE', 'PARCIAL'],
        ).select_related('credito', 'credito__cliente').order_by('credito_id', 'numero_cuota')

        # Agrupar por crédito (un correo por crédito con todas las cuotas del día)
        por_credito = defaultdict(list)
        for c in cuotas:
            por_credito[c.credito_id].append(c)

        enviados = 0
        sin_email = 0
        errores = 0

        for credito_id, lista_cuotas in por_credito.items():
            credito = lista_cuotas[0].credito
            cliente = credito.cliente
            email_destino = (cliente.email or '').strip()
            if not email_destino:
                sin_email += 1
                continue

            lineas = []
            total_dia = 0
            for cuota in lista_cuotas:
                if cuota.estado == 'PARCIAL':
                    valor = cuota.saldo_pendiente()
                    lineas.append(f"  • Cuota #{cuota.numero_cuota} (saldo pendiente): ${valor:,.0f}")
                else:
                    valor = cuota.monto_cuota
                    lineas.append(f"  • Cuota #{cuota.numero_cuota}: ${valor:,.0f}")
                total_dia += float(valor)
            texto_cuotas = '\n'.join(lineas)

            asunto = f'Recordatorio de pago CREDIFLOW - Crédito #{credito.id} ({dia.strftime("%d/%m/%Y")})'
            cuerpo = (
                f'Estimado(a) {cliente.nombre_completo},\n\n'
                f'Recuerde que hoy ({dia.strftime("%d/%m/%Y")}) corresponde el pago de su cuota del crédito con CREDIFLOW.\n\n'
                f'Crédito: #{credito.id}\n'
                f'Valor a pagar hoy: ${total_dia:,.0f}\n\n'
                f'Detalle:\n'
                f'{texto_cuotas}\n\n'
                f'Su puntualidad es la mejor referencia para próximos créditos.\n\n'
                f'Atentamente,\n'
                f'Equipo CREDIFLOW'
            )

            if dry_run:
                self.stdout.write(f'  Enviaría a {email_destino} (Crédito #{credito.id}, {len(lista_cuotas)} cuota(s))')
                enviados += 1
                continue

            try:
                EmailMessage(
                    asunto,
                    cuerpo,
                    getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@creditos.local'),
                    [email_destino],
                ).send(fail_silently=True)
                enviados += 1
            except Exception:
                errores += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Recordatorios: {enviados} enviados, {sin_email} sin email, {errores} errores.'
            )
        )
