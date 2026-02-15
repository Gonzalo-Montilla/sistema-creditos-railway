"""
Crea una sola tarea de cobro PENDIENTE para hoy, para probar el flujo
"Registrar cobro" (correo + WhatsApp) sin depender de créditos reales.

Uso:
  python manage.py crear_tarea_prueba_cobro
  python manage.py crear_tarea_prueba_cobro --sin-email   # Cliente sin correo (probar WhatsApp)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from main.models import Cliente, Credito, CronogramaPago, TareaCobro, Cobrador


class Command(BaseCommand):
    help = 'Crea una tarea de cobro PENDIENTE para hoy para probar el flujo Registrar cobro'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sin-email',
            action='store_true',
            help='Crear cliente sin correo (para probar envío por WhatsApp)',
        )
        parser.add_argument(
            '--fecha',
            type=str,
            help='Fecha de la tarea (YYYY-MM-DD). Por defecto: hoy',
        )

    def handle(self, *args, **options):
        try:
            fecha = date.today()
            if options.get('fecha'):
                fecha = timezone.datetime.strptime(options['fecha'], '%Y-%m-%d').date()
            sin_email = options.get('sin_email', False)

            # 1. Cobrador (usar el primero activo o crear uno de prueba)
            cobrador = Cobrador.objects.filter(activo=True).first()
            if not cobrador:
                cobrador = Cobrador.objects.create(
                    nombres='Cobrador',
                    apellidos='Prueba',
                    cedula='1099990001',
                    celular='3001112233',
                    direccion='Calle prueba 123',
                    barrio='Centro',
                    activo=True,
                )
                self.stdout.write(self.style.WARNING('Se creó cobrador de prueba.'))

            # 2. Cliente de prueba (único para no duplicar)
            cedula_prueba = '1099990002'
            cliente = Cliente.objects.filter(cedula=cedula_prueba, activo=True).first()
            if not cliente:
                cliente = Cliente.objects.create(
                    nombres='Cliente',
                    apellidos='Prueba Cobro',
                    cedula=cedula_prueba,
                    celular='3005556677',
                    direccion='Carrera 1 # 2-3',
                    barrio='Barrio Prueba',
                    email=None if sin_email else 'prueba-cobro@ejemplo.com',
                    activo=True,
                )
                self.stdout.write(self.style.WARNING('Se creó cliente de prueba.'))
            else:
                if sin_email:
                    cliente.email = None
                    cliente.save()
                elif not cliente.email:
                    cliente.email = 'prueba-cobro@ejemplo.com'
                    cliente.save()

            # 3. Crédito activo para ese cliente y cobrador
            credito = Credito.objects.filter(
                cliente=cliente,
                cobrador=cobrador,
                estado='DESEMBOLSADO',
            ).first()
            if not credito:
                credito = Credito.objects.create(
                    cliente=cliente,
                    cobrador=cobrador,
                    monto=Decimal('1000000'),
                    tasa_interes=Decimal('2.5'),
                    tipo_plazo='MENSUAL',
                    cantidad_cuotas=12,
                    estado='DESEMBOLSADO',
                    fecha_desembolso=timezone.now() - timedelta(days=60),
                )
                credito.save()  # dispara calcular_cronograma y valor_cuota
                if hasattr(credito, 'generar_cronograma'):
                    credito.generar_cronograma()
                self.stdout.write(self.style.WARNING('Se creó crédito de prueba.'))

            # Asegurar cronograma y al menos una cuota PENDIENTE
            if not credito.cronograma.exists() and hasattr(credito, 'generar_cronograma'):
                credito.generar_cronograma()
            cuota = credito.cronograma.filter(estado='PENDIENTE').first()
            if not cuota:
                cuota = credito.cronograma.order_by('numero_cuota').first()
                if cuota:
                    cuota.estado = 'PENDIENTE'
                    cuota.monto_pagado = Decimal('0')
                    cuota.fecha_pago = None
                    cuota.save()

            if not cuota:
                self.stdout.write(self.style.ERROR('No hay cuotas en el crédito. Cree cronograma desde la app.'))
                return

            # 4. Tarea PENDIENTE para hoy (evitar duplicado por unique cuota+fecha)
            tarea, created = TareaCobro.objects.get_or_create(
                cuota=cuota,
                fecha_asignacion=fecha,
                defaults={
                    'cobrador': cobrador,
                    'estado': 'PENDIENTE',
                    'prioridad': 'MEDIA',
                    'orden_visita': 1,
                }
            )
            if not created:
                tarea.estado = 'PENDIENTE'
                tarea.fecha_visita = None
                tarea.monto_cobrado = None
                tarea.observaciones = ''
                tarea.save()
                self.stdout.write(self.style.WARNING('Se reutilizó tarea existente y se dejó en PENDIENTE.'))

            self.stdout.write(
                self.style.SUCCESS(
                    f'\nTarea de prueba lista.\n'
                    f'  Tarea ID: {tarea.id} | Fecha: {fecha} | Cobrador: {cobrador.nombre_completo}\n'
                    f'  Cliente: {cliente.nombre_completo} | Email: {"(sin correo - probar WhatsApp)" if sin_email else cliente.email}\n\n'
                    f'  Ir a: Cobranza > Agenda > seleccionar fecha {fecha} y cobrador > Cobrar en la tarea.'
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            raise
