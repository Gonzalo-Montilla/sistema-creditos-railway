from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from datetime import datetime, timedelta
import json

@login_required
def valorizador(request):
    """Vista principal del valorizador de créditos"""
    return render(request, 'valorizador/valorizador.html')

@login_required
def calcular_credito(request):
    """API para calcular diferentes modalidades de crédito"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Obtener parámetros
        monto = Decimal(str(data.get('monto', 0)))
        tasa_mensual = Decimal(str(data.get('tasa_mensual', 20)))  # % mensual
        cantidad_cuotas = int(data.get('cantidad_cuotas', 30))
        tipo_plazo = data.get('tipo_plazo', 'DIARIO')
        
        # Validaciones
        if monto <= 0:
            return JsonResponse({'error': 'El monto debe ser mayor a cero'})
        
        if tasa_mensual < 0:
            return JsonResponse({'error': 'La tasa no puede ser negativa'})
        
        if cantidad_cuotas <= 0:
            return JsonResponse({'error': 'Las cuotas deben ser mayor a cero'})
        
        # Usar función centralizada para cálculos
        from .creditos_utils import calcular_credito_informal, generar_cronograma_fechas
        
        # Calcular usando función centralizada
        resultado = calcular_credito_informal(
            monto=monto,
            tasa_mensual=tasa_mensual,
            cantidad_cuotas=cantidad_cuotas,
            tipo_plazo=tipo_plazo
        )
        
        # Generar cronograma usando función centralizada
        cronograma = generar_cronograma_fechas(cantidad_cuotas, tipo_plazo)
        resultado['cronograma'] = cronograma
        
        return JsonResponse({'success': True, 'resultado': resultado})
        
    except Exception as e:
        return JsonResponse({'error': f'Error en el cálculo: {str(e)}'}, status=400)

@login_required
def comparar_modalidades(request):
    """API para comparar diferentes modalidades con los mismos parámetros"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        monto = Decimal(str(data.get('monto', 0)))
        tasa_mensual = Decimal(str(data.get('tasa_mensual', 20)))
        
        # Validaciones
        if monto <= 0:
            return JsonResponse({'error': 'El monto debe ser mayor a cero'})
        
        modalidades = [
            {'tipo': 'DIARIO', 'cuotas': 30, 'nombre': '30 días'},
            {'tipo': 'SEMANAL', 'cuotas': 8, 'nombre': '8 semanas'},
            {'tipo': 'QUINCENAL', 'cuotas': 4, 'nombre': '4 quincenas'},
            {'tipo': 'MENSUAL', 'cuotas': 2, 'nombre': '2 meses'},
        ]
        
        comparaciones = []
        
        for modalidad in modalidades:
            # Calcular para esta modalidad
            cantidad_cuotas = modalidad['cuotas']
            tipo_plazo = modalidad['tipo']
            
            # Calcular tiempo en meses
            if tipo_plazo == 'DIARIO':
                tiempo_meses = Decimal(str(cantidad_cuotas / 30))
            elif tipo_plazo == 'SEMANAL':
                tiempo_meses = Decimal(str(cantidad_cuotas / 4.33))
            elif tipo_plazo == 'QUINCENAL':
                tiempo_meses = Decimal(str(cantidad_cuotas / 2))
            else:  # MENSUAL
                tiempo_meses = Decimal(str(cantidad_cuotas))
            
            # Cálculo
            tasa_decimal = tasa_mensual / 100
            interes_total = monto * tasa_decimal * tiempo_meses
            monto_total = monto + interes_total
            valor_cuota = monto_total / cantidad_cuotas
            
            comparaciones.append({
                'modalidad': modalidad['nombre'],
                'tipo': tipo_plazo,
                'cuotas': cantidad_cuotas,
                'tiempo_meses': float(tiempo_meses),
                'valor_cuota': float(valor_cuota),
                'total_pagar': float(monto_total),
                'total_intereses': float(interes_total)
            })
        
        return JsonResponse({
            'success': True,
            'parametros': {
                'monto': float(monto),
                'tasa_mensual': float(tasa_mensual)
            },
            'comparaciones': comparaciones
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Error en la comparación: {str(e)}'}, status=400)

# La función generar_cronograma_fechas ahora está centralizada en creditos_utils.py
