from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from main.models import Cliente, Credito, CronogramaPago, TareaCobro, Cobrador, Ruta
import random

class Command(BaseCommand):
    help = 'Crea datos de prueba para el sistema de tareas de cobro'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fecha',
            type=str,
            help='Fecha para crear tareas (YYYY-MM-DD). Por defecto: hoy',
        )
        
        parser.add_argument(
            '--cantidad',
            type=int,
            default=10,
            help='Cantidad de tareas a crear por cobrador (por defecto: 10)',
        )

    def handle(self, *args, **options):
        try:
            # Determinar fecha
            if options['fecha']:
                fecha = timezone.datetime.strptime(options['fecha'], '%Y-%m-%d').date()
            else:
                fecha = date.today()
            
            cantidad = options['cantidad']
            
            # Obtener cobradores activos
            cobradores = Cobrador.objects.filter(activo=True)
            if not cobradores.exists():
                self.stdout.write(
                    self.style.ERROR('No hay cobradores activos. Cree cobradores primero.')
                )
                return
            
            # Limpiar tareas existentes para la fecha
            tareas_existentes = TareaCobro.objects.filter(fecha_asignacion=fecha).count()
            if tareas_existentes > 0:
                self.stdout.write(
                    self.style.WARNING(f'Eliminando {tareas_existentes} tareas existentes para {fecha}')
                )
                TareaCobro.objects.filter(fecha_asignacion=fecha).delete()
            
            tareas_creadas = 0
            
            for cobrador in cobradores:
                self.stdout.write(f'Creando tareas para {cobrador.nombre_completo}...')
                
                # Crear clientes de prueba si no existen suficientes
                clientes_cobrador = Cliente.objects.filter(
                    credito__cobrador=cobrador,
                    activo=True
                ).distinct()
                
                if clientes_cobrador.count() < cantidad:
                    # Crear clientes y créditos de prueba
                    for i in range(cantidad - clientes_cobrador.count()):
                        # Crear cliente
                        cliente = Cliente.objects.create(
                            nombres=f'Cliente_{i+1}',
                            apellidos=f'Prueba_C{cobrador.id}',
                            cedula=f'{cobrador.id}00{i+1:03d}',
                            celular=f'300{cobrador.id}{i+1:03d}',
                            direccion=f'Dirección de prueba {i+1}',
                            barrio=f'Barrio {i+1}'
                        )
                        
                        # Crear crédito
                        monto = Decimal(random.choice([500000, 800000, 1000000, 1500000]))
                        credito = Credito.objects.create(
                            cliente=cliente,
                            cobrador=cobrador,
                            monto=monto,
                            tasa_interes=Decimal('2.5'),
                            tipo_plazo='MENSUAL',
                            cantidad_cuotas=12,
                            estado='DESEMBOLSADO',
                            fecha_desembolso=timezone.now() - timedelta(days=random.randint(30, 180))
                        )
                        
                        # Crear cuotas
                        valor_cuota = monto / 12
                        for cuota_num in range(1, 13):
                            fecha_vencimiento = fecha - timedelta(
                                days=random.randint(0, 30)  # Algunas vencidas, otras por vencer
                            )
                            
                            cuota = CronogramaPago.objects.create(
                                credito=credito,
                                numero_cuota=cuota_num,
                                fecha_vencimiento=fecha_vencimiento,
                                monto_cuota=valor_cuota,
                                estado='PENDIENTE'
                            )
                
                # Obtener cuotas pendientes para este cobrador
                cuotas_pendientes = CronogramaPago.objects.filter(
                    credito__cobrador=cobrador,
                    estado='PENDIENTE',
                    fecha_vencimiento__lte=fecha
                ).order_by('fecha_vencimiento')[:cantidad]
                
                # Crear tareas
                for i, cuota in enumerate(cuotas_pendientes):
                    dias_mora = (fecha - cuota.fecha_vencimiento).days
                    
                    # Determinar prioridad
                    if dias_mora > 15:
                        prioridad = 'ALTA'
                    elif dias_mora > 5:
                        prioridad = 'MEDIA'
                    else:
                        prioridad = 'BAJA'
                    
                    # Estado aleatorio para simular progreso
                    estados_posibles = ['PENDIENTE', 'COBRADO', 'NO_ENCONTRADO', 'REPROGRAMADO']
                    estado = random.choices(
                        estados_posibles, 
                        weights=[40, 35, 15, 10]  # 35% cobradas, 40% pendientes, etc.
                    )[0]
                    
                    tarea = TareaCobro.objects.create(
                        cobrador=cobrador,
                        cuota=cuota,
                        fecha_asignacion=fecha,
                        prioridad=prioridad,
                        orden_visita=i + 1,
                        estado=estado
                    )
                    
                    # Si está cobrada, simular datos de cobro
                    if estado == 'COBRADO':
                        tarea.fecha_visita = timezone.now().replace(
                            hour=random.randint(8, 17),
                            minute=random.randint(0, 59)
                        )
                        tarea.monto_cobrado = cuota.monto_cuota
                        tarea.observaciones = 'Cobro realizado exitosamente (datos de prueba)'
                        tarea.save()
                        
                        # Marcar cuota como pagada
                        cuota.monto_pagado = cuota.monto_cuota
                        cuota.estado = 'PAGADA'
                        cuota.fecha_pago = fecha
                        cuota.save()
                    
                    elif estado in ['NO_ENCONTRADO', 'REPROGRAMADO']:
                        tarea.fecha_visita = timezone.now().replace(
                            hour=random.randint(8, 17),
                            minute=random.randint(0, 59)
                        )
                        tarea.observaciones = f'Estado: {tarea.get_estado_display()} (datos de prueba)'
                        if estado == 'REPROGRAMADO':
                            tarea.fecha_reprogramacion = fecha + timedelta(days=1)
                        tarea.save()
                    
                    tareas_creadas += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ {len(cuotas_pendientes)} tareas creadas para {cobrador.nombre_completo}')
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Se crearon {tareas_creadas} tareas de prueba para {fecha}\n'
                    f'Ahora puedes ver el Panel Supervisor con datos reales.'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al crear datos de prueba: {str(e)}')
            )