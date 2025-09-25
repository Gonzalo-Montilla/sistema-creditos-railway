"""
Utilidades centralizadas para cálculos de créditos informales
Esta lógica está basada en el valorizador que ya funciona correctamente
"""

from decimal import Decimal
from datetime import datetime, timedelta
import calendar


def calcular_credito_informal(monto, tasa_mensual, cantidad_cuotas, tipo_plazo):
    """
    Calcula un crédito informal usando interés simple
    Esta es la misma lógica del valorizador validado
    
    Args:
        monto: Capital del crédito (Decimal)
        tasa_mensual: Tasa de interés mensual en porcentaje (Decimal)
        cantidad_cuotas: Número de cuotas (int)
        tipo_plazo: 'DIARIO', 'SEMANAL', 'QUINCENAL', 'MENSUAL' (str)
    
    Returns:
        dict con todos los cálculos
    """
    # Convertir inputs a Decimal para precisión
    capital = Decimal(str(monto))
    tasa_decimal = Decimal(str(tasa_mensual)) / Decimal('100')
    
    # Calcular tiempo en meses según el tipo de plazo
    if tipo_plazo == 'DIARIO':
        tiempo_meses = Decimal(str(cantidad_cuotas / 30))  # 30 días por mes
        periodo_texto = 'diarios'
    elif tipo_plazo == 'SEMANAL':
        tiempo_meses = Decimal(str(cantidad_cuotas / 4.33))  # 4.33 semanas por mes
        periodo_texto = 'semanales'
    elif tipo_plazo == 'QUINCENAL':
        tiempo_meses = Decimal(str(cantidad_cuotas / 2))  # 2 quincenas por mes
        periodo_texto = 'quincenales'
    else:  # MENSUAL
        tiempo_meses = Decimal(str(cantidad_cuotas))
        periodo_texto = 'mensuales'
    
    # CÁLCULO DE INTERÉS SIMPLE (Sistema de créditos informales)
    # Interés = Capital × Tasa × Tiempo
    interes_total = capital * tasa_decimal * tiempo_meses
    monto_total_pagar = capital + interes_total
    
    # Cuota fija = Total a pagar ÷ Número de cuotas
    valor_cuota = monto_total_pagar / Decimal(str(cantidad_cuotas))
    
    # Calcular tasa efectiva anual para referencia
    if tiempo_meses > 0:
        tasa_efectiva_anual = (interes_total / capital) * (Decimal('12') / tiempo_meses) * Decimal('100')
    else:
        tasa_efectiva_anual = Decimal('0')
    
    return {
        'parametros': {
            'monto': float(capital),
            'tasa_mensual': float(tasa_mensual),
            'cantidad_cuotas': cantidad_cuotas,
            'tipo_plazo': tipo_plazo,
            'periodo_texto': periodo_texto
        },
        'calculos': {
            'capital': float(capital),
            'tiempo_meses': float(tiempo_meses),
            'interes_total': float(interes_total),
            'monto_total': float(monto_total_pagar),
            'valor_cuota': float(valor_cuota),
            'tasa_efectiva_anual': float(tasa_efectiva_anual)
        },
        'resumen': {
            'descripcion': f"Crédito de ${capital:,.0f} al {tasa_mensual}% mensual por {tiempo_meses:.1f} meses",
            'modalidad': f"{cantidad_cuotas} cuotas {periodo_texto} de ${valor_cuota:,.0f}",
            'totales': f"Total a pagar: ${monto_total_pagar:,.0f} (Intereses: ${interes_total:,.0f})"
        }
    }


def generar_cronograma_fechas(cantidad_cuotas, tipo_plazo, fecha_inicio=None):
    """
    Genera un cronograma con fechas reales de vencimiento
    Esta es la misma lógica del valorizador validado
    
    Args:
        cantidad_cuotas: Número de cuotas (int)
        tipo_plazo: 'DIARIO', 'SEMANAL', 'QUINCENAL', 'MENSUAL' (str)
        fecha_inicio: Fecha de inicio (datetime.date), por defecto hoy
    
    Returns:
        list de dict con información de cada cuota
    """
    if not fecha_inicio:
        fecha_inicio = datetime.now().date()
    
    fechas = []
    
    for i in range(1, cantidad_cuotas + 1):
        if tipo_plazo == 'DIARIO':
            fecha_vencimiento = fecha_inicio + timedelta(days=i)
        elif tipo_plazo == 'SEMANAL':
            fecha_vencimiento = fecha_inicio + timedelta(weeks=i)
        elif tipo_plazo == 'QUINCENAL':
            fecha_vencimiento = fecha_inicio + timedelta(days=i*15)
        else:  # MENSUAL
            # Para mensual, agregar meses de forma más precisa
            año = fecha_inicio.year
            mes = fecha_inicio.month + i
            dia = fecha_inicio.day
            
            # Ajustar año si el mes excede 12
            while mes > 12:
                mes -= 12
                año += 1
            
            try:
                fecha_vencimiento = fecha_inicio.replace(year=año, month=mes, day=dia)
            except ValueError:
                # Si el día no existe en ese mes (ej: 31 en febrero)
                ultimo_dia_mes = calendar.monthrange(año, mes)[1]
                fecha_vencimiento = fecha_inicio.replace(year=año, month=mes, day=min(dia, ultimo_dia_mes))
        
        # Detectar si cae en fin de semana
        es_fin_semana = fecha_vencimiento.weekday() >= 5  # 5=sábado, 6=domingo
        dia_semana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'][fecha_vencimiento.weekday()]
        
        fechas.append({
            'numero_cuota': i,
            'fecha_vencimiento': fecha_vencimiento.strftime('%Y-%m-%d'),
            'fecha_formateada': fecha_vencimiento.strftime('%d/%m/%Y'),
            'dia_semana': dia_semana,
            'es_fin_semana': es_fin_semana,
            'fecha_objeto': fecha_vencimiento  # Para uso interno
        })
    
    return fechas


def calcular_plazo_en_meses(cantidad_cuotas, tipo_plazo):
    """
    Calcula el tiempo equivalente en meses
    
    Args:
        cantidad_cuotas: Número de cuotas (int)
        tipo_plazo: 'DIARIO', 'SEMANAL', 'QUINCENAL', 'MENSUAL' (str)
    
    Returns:
        float: Tiempo en meses
    """
    if tipo_plazo == 'DIARIO':
        return cantidad_cuotas / 30
    elif tipo_plazo == 'SEMANAL':
        return cantidad_cuotas / 4.33
    elif tipo_plazo == 'QUINCENAL':
        return cantidad_cuotas / 2
    else:  # MENSUAL
        return cantidad_cuotas


def validar_parametros_credito(monto, tasa_mensual, cantidad_cuotas, tipo_plazo):
    """
    Valida los parámetros de un crédito
    
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    try:
        monto_decimal = Decimal(str(monto))
        tasa_decimal = Decimal(str(tasa_mensual))
        
        if monto_decimal <= 0:
            return False, 'El monto debe ser mayor a cero'
        
        if tasa_decimal < 0:
            return False, 'La tasa no puede ser negativa'
        
        if not isinstance(cantidad_cuotas, int) or cantidad_cuotas <= 0:
            return False, 'Las cuotas deben ser un número entero mayor a cero'
        
        if tipo_plazo not in ['DIARIO', 'SEMANAL', 'QUINCENAL', 'MENSUAL']:
            return False, 'Tipo de plazo inválido'
        
        return True, 'Parámetros válidos'
        
    except (ValueError, TypeError):
        return False, 'Error en los parámetros numéricos'


def obtener_descripcion_plazo(tipo_plazo):
    """
    Obtiene la descripción textual del tipo de plazo
    
    Returns:
        tuple: (singular, plural)
    """
    descripciones = {
        'DIARIO': ('diario', 'diarios'),
        'SEMANAL': ('semanal', 'semanales'),
        'QUINCENAL': ('quincenal', 'quincenales'),
        'MENSUAL': ('mensual', 'mensuales')
    }
    return descripciones.get(tipo_plazo, ('', ''))


def generar_descripcion_credito(resultado_calculo):
    """
    Genera descripción completa del crédito basada en los cálculos
    
    Args:
        resultado_calculo: dict resultado de calcular_credito_informal()
    
    Returns:
        str: Descripción formateada del crédito
    """
    parametros = resultado_calculo['parametros']
    calculos = resultado_calculo['calculos']
    
    return (
        f"Crédito informal de ${calculos['capital']:,.0f} al {parametros['tasa_mensual']}% mensual "
        f"por {calculos['tiempo_meses']:.1f} meses. "
        f"{parametros['cantidad_cuotas']} cuotas {parametros['periodo_texto']} de ${calculos['valor_cuota']:,.0f}. "
        f"Total: ${calculos['monto_total']:,.0f} (Intereses: ${calculos['interes_total']:,.0f})"
    )