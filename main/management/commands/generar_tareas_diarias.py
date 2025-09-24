from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import date, timedelta
from main.models import TareaCobro
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Genera tareas de cobro diarias para todos los cobradores activos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fecha',
            type=str,
            help='Fecha para generar tareas (YYYY-MM-DD). Por defecto: hoy',
        )
        
        parser.add_argument(
            '--dias-adelante',
            type=int,
            default=0,
            help='Generar tareas para X días adelante (por defecto: 0)',
        )
        
        parser.add_argument(
            '--forzar',
            action='store_true',
            help='Forzar generación incluso si ya existen tareas para la fecha',
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada del proceso',
        )

    def handle(self, *args, **options):
        try:
            # Determinar fecha
            if options['fecha']:
                try:
                    fecha = timezone.datetime.strptime(options['fecha'], '%Y-%m-%d').date()
                    self.stdout.write(f'Usando fecha especificada: {fecha}')
                except ValueError:
                    raise CommandError('Formato de fecha inválido. Use YYYY-MM-DD')
            else:
                fecha = date.today()
                if options['dias_adelante']:
                    fecha += timedelta(days=options['dias_adelante'])
                self.stdout.write(f'Usando fecha: {fecha}')
            
            # Configurar verbosidad
            verbose = options['verbose']
            
            # Verificar si ya existen tareas para la fecha
            if not options['forzar']:
                tareas_existentes = TareaCobro.objects.filter(fecha_asignacion=fecha).count()
                if tareas_existentes > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Ya existen {tareas_existentes} tareas para {fecha}. '
                            'Use --forzar para generar de todos modos.'
                        )
                    )
                    return
            
            # Generar tareas
            self.stdout.write(f'Generando tareas para {fecha}...')
            
            tareas_creadas = TareaCobro.generar_tareas_diarias(fecha, verbose=verbose)
            
            if tareas_creadas > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Se generaron {tareas_creadas} tareas para {fecha}'
                    )
                )
                
                if verbose:
                    # Mostrar resumen por cobrador
                    from main.models import Cobrador
                    cobradores = Cobrador.objects.filter(activo=True)
                    
                    self.stdout.write('\n--- Resumen por cobrador ---')
                    for cobrador in cobradores:
                        tareas_cobrador = TareaCobro.objects.filter(
                            cobrador=cobrador,
                            fecha_asignacion=fecha
                        ).count()
                        
                        if tareas_cobrador > 0:
                            rutas = ', '.join([r.nombre for r in cobrador.rutas.all()])
                            self.stdout.write(
                                f'• {cobrador.nombre_completo}: {tareas_cobrador} tareas (Rutas: {rutas})'
                            )
                    self.stdout.write('----------------------------\n')
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'No se generaron tareas para {fecha}. '
                        'Verifique que hay cobradores activos con rutas asignadas y cuotas por cobrar.'
                    )
                )
                
        except Exception as e:
            logger.error(f'Error al generar tareas: {str(e)}', exc_info=True)
            raise CommandError(f'Error al generar tareas: {str(e)}')
    
    def log_info(self, message, verbose=False):
        """Helper para logging condicional"""
        if verbose:
            self.stdout.write(f'INFO: {message}')
        logger.info(message)