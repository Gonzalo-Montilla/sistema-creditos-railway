"""
Funciones automatizadas para ejecutar mediante cron jobs
Estas funciones se ejecutan automáticamente en producción
"""
import os
import logging
from datetime import date, timedelta
from django.conf import settings

# Configurar logging
logger = logging.getLogger(__name__)

def generar_tareas_diarias():
    """
    Genera tareas de cobro diarias automáticamente
    Se ejecuta todos los días laborales a las 6:00 AM
    """
    try:
        from main.models import TareaCobro
        
        fecha_hoy = date.today()
        tareas_creadas = TareaCobro.generar_tareas_diarias(fecha=fecha_hoy, verbose=True)
        
        logger.info(f"[CRON] Tareas generadas automáticamente: {tareas_creadas} para {fecha_hoy}")
        
        if tareas_creadas > 0:
            # Opcional: Enviar notificación (email, Slack, etc.)
            logger.info(f"✅ Generación automática exitosa: {tareas_creadas} tareas creadas")
        else:
            logger.info("ℹ️ No se crearon tareas nuevas (normal si no hay cuotas vencidas)")
            
        return tareas_creadas
        
    except Exception as e:
        logger.error(f"❌ Error en generación automática de tareas: {e}", exc_info=True)
        # Opcional: Enviar alerta de error
        return 0

def analizar_cartera_diaria():
    """
    Realiza análisis automático de cartera diariamente
    Se ejecuta todos los días a las 11:59 PM
    """
    try:
        from main.models import CarteraAnalisis
        
        fecha_hoy = date.today()
        analisis = CarteraAnalisis.generar_analisis_diario(fecha=fecha_hoy)
        
        logger.info(f"[CRON] Análisis de cartera completado para {fecha_hoy}")
        logger.info(f"   - Cartera total: ${analisis.cartera_total}")
        logger.info(f"   - Cartera vencida: ${analisis.cartera_vencida}")
        logger.info(f"   - Porcentaje mora: {analisis.porcentaje_cartera_vencida}%")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en análisis automático de cartera: {e}", exc_info=True)
        return False

def limpiar_logs_antiguos():
    """
    Limpia logs antiguos (más de 30 días)
    Se ejecuta los domingos a las 2:00 AM
    """
    try:
        import glob
        
        # Directorio de logs
        logs_dir = os.path.join(settings.BASE_DIR, 'logs')
        if not os.path.exists(logs_dir):
            logger.info("No hay directorio de logs para limpiar")
            return
        
        # Fecha límite (30 días atrás)
        fecha_limite = date.today() - timedelta(days=30)
        archivos_eliminados = 0
        
        # Buscar archivos de log antiguos
        patron_logs = os.path.join(logs_dir, '*.log')
        for archivo_log in glob.glob(patron_logs):
            fecha_archivo = date.fromtimestamp(os.path.getmtime(archivo_log))
            
            if fecha_archivo < fecha_limite:
                os.remove(archivo_log)
                archivos_eliminados += 1
                logger.info(f"Eliminado log antiguo: {archivo_log}")
        
        logger.info(f"[CRON] Limpieza de logs completada: {archivos_eliminados} archivos eliminados")
        return archivos_eliminados
        
    except Exception as e:
        logger.error(f"❌ Error en limpieza de logs: {e}", exc_info=True)
        return 0

def verificar_sistema_salud():
    """
    Verificación de salud del sistema
    Se puede ejecutar cada hora o según necesidades
    """
    try:
        from main.models import Cliente, Credito, TareaCobro, Cobrador
        
        # Verificaciones básicas
        clientes_activos = Cliente.objects.filter(activo=True).count()
        creditos_activos = Credito.objects.filter(estado__in=['DESEMBOLSADO', 'VENCIDO']).count()
        cobradores_activos = Cobrador.objects.filter(activo=True).count()
        tareas_hoy = TareaCobro.objects.filter(fecha_asignacion=date.today()).count()
        
        logger.info(f"[HEALTH CHECK] Sistema saludable:")
        logger.info(f"   - Clientes activos: {clientes_activos}")
        logger.info(f"   - Créditos activos: {creditos_activos}")
        logger.info(f"   - Cobradores activos: {cobradores_activos}")
        logger.info(f"   - Tareas hoy: {tareas_hoy}")
        
        # Alertas si algo está mal
        if cobradores_activos == 0:
            logger.warning("⚠️ ALERTA: No hay cobradores activos")
        
        if creditos_activos > 0 and tareas_hoy == 0:
            logger.warning("⚠️ ALERTA: Hay créditos activos pero no hay tareas para hoy")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en verificación de salud: {e}", exc_info=True)
        return False

# Funciones auxiliares para Railway o servicios cloud
def railway_daily_task():
    """
    Función principal para ejecutar en Railway mediante cron
    Combina todas las tareas diarias necesarias
    """
    logger.info("=== INICIO DE TAREAS AUTOMATIZADAS DIARIAS ===")
    
    # 1. Generar tareas de cobro
    tareas_creadas = generar_tareas_diarias()
    
    # 2. Verificar salud del sistema
    sistema_ok = verificar_sistema_salud()
    
    # 3. Solo en días específicos: análisis de cartera
    if date.today().weekday() == 6:  # Domingo
        analizar_cartera_diaria()
        limpiar_logs_antiguos()
    
    logger.info("=== FIN DE TAREAS AUTOMATIZADAS DIARIAS ===")
    
    return {
        'tareas_creadas': tareas_creadas,
        'sistema_ok': sistema_ok
    }