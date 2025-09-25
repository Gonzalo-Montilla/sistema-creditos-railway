from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Ejecuta todas las tareas automatizadas diarias del sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--solo-tareas',
            action='store_true',
            help='Solo generar tareas de cobro (no otras automatizaciones)',
        )
        
        parser.add_argument(
            '--fecha',
            type=str,
            help='Fecha específica para procesar (YYYY-MM-DD)',
        )
    
    def handle(self, *args, **options):
        try:
            from main.cron import (
                generar_tareas_diarias, 
                verificar_sistema_salud,
                analizar_cartera_diaria,
                limpiar_logs_antiguos
            )
            
            # Determinar fecha
            if options['fecha']:
                fecha = timezone.datetime.strptime(options['fecha'], '%Y-%m-%d').date()
                self.stdout.write(f'Procesando fecha específica: {fecha}')
            else:
                fecha = date.today()
                self.stdout.write(f'Procesando fecha actual: {fecha}')
            
            self.stdout.write("🤖 INICIANDO AUTOMATIZACIONES DIARIAS")
            self.stdout.write("=" * 50)
            
            # 1. SIEMPRE: Generar tareas de cobro
            self.stdout.write("📋 Generando tareas de cobro...")
            tareas_creadas = generar_tareas_diarias()
            
            if tareas_creadas > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {tareas_creadas} tareas generadas')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('ℹ️ No se generaron tareas (normal si no hay cuotas vencidas)')
                )
            
            # 2. Si no es solo tareas, ejecutar otras automatizaciones
            if not options['solo_tareas']:
                
                # Verificación de salud
                self.stdout.write("\n🏥 Verificando salud del sistema...")
                sistema_ok = verificar_sistema_salud()
                
                if sistema_ok:
                    self.stdout.write(self.style.SUCCESS('✅ Sistema saludable'))
                else:
                    self.stdout.write(self.style.ERROR('❌ Sistema con problemas'))
                
                # Tareas específicas por día
                dia_semana = fecha.weekday()
                
                if dia_semana == 6:  # Domingo
                    self.stdout.write("\n📊 Es domingo: Ejecutando análisis de cartera...")
                    analisis_ok = analizar_cartera_diaria()
                    
                    if analisis_ok:
                        self.stdout.write(self.style.SUCCESS('✅ Análisis de cartera completado'))
                    else:
                        self.stdout.write(self.style.ERROR('❌ Error en análisis de cartera'))
                    
                    self.stdout.write("\n🧹 Limpiando logs antiguos...")
                    logs_eliminados = limpiar_logs_antiguos()
                    self.stdout.write(f'🗑️ {logs_eliminados} archivos de log eliminados')
                
                elif dia_semana == 0:  # Lunes
                    self.stdout.write("\n📈 Es lunes: Preparando semana...")
                    # Aquí podrías agregar tareas específicas de inicio de semana
                    
                elif dia_semana == 4:  # Viernes
                    self.stdout.write("\n📋 Es viernes: Preparando reporte semanal...")
                    # Aquí podrías agregar reportes semanales
            
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(
                self.style.SUCCESS("🎉 AUTOMATIZACIONES COMPLETADAS EXITOSAMENTE")
            )
            
            # Resumen final
            self.stdout.write(f"\n📊 RESUMEN:")
            self.stdout.write(f"   • Fecha procesada: {fecha}")
            self.stdout.write(f"   • Tareas de cobro generadas: {tareas_creadas}")
            
            if not options['solo_tareas']:
                self.stdout.write(f"   • Sistema verificado: {'✅' if sistema_ok else '❌'}")
                if dia_semana == 6:
                    self.stdout.write(f"   • Logs limpiados: {logs_eliminados}")
            
        except Exception as e:
            logger.error(f'Error en automatizaciones: {str(e)}', exc_info=True)
            raise CommandError(f'Error ejecutando automatizaciones: {str(e)}')