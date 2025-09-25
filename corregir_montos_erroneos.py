#!/usr/bin/env python
"""
Script para identificar y corregir montos erróneos en la base de datos
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_creditos.settings')
django.setup()

from decimal import Decimal
from main.models import Pago, TareaCobro, CronogramaPago

def identificar_datos_problematicos():
    """Identifica registros con montos sospechosamente bajos o altos"""
    print("=== Identificando datos problemáticos ===")
    
    # 1. Buscar pagos con montos muy bajos (posibles errores)
    pagos_sospechosos = Pago.objects.filter(monto__lt=1000)  # Menos de $1,000 COP
    print(f"\n📊 Pagos con montos < $1,000: {pagos_sospechosos.count()}")
    
    for pago in pagos_sospechosos:
        print(f"  Pago #{pago.id}: ${pago.monto} - Cliente: {pago.credito.cliente.nombre_completo} - Fecha: {pago.fecha_pago}")
    
    # 2. Buscar tareas con montos cobrados muy bajos
    tareas_sospechosas = TareaCobro.objects.filter(
        estado='COBRADO',
        monto_cobrado__lt=1000,
        monto_cobrado__isnull=False
    )
    print(f"\n📊 Tareas con montos cobrados < $1,000: {tareas_sospechosas.count()}")
    
    for tarea in tareas_sospechosas:
        monto_esperado = tarea.cuota.monto_cuota
        print(f"  Tarea #{tarea.id}: Cobrado=${tarea.monto_cobrado}, Esperado=${monto_esperado} - Cliente: {tarea.cliente.nombre_completo}")
    
    # 3. Buscar cuotas con pagos parciales sospechosos
    cuotas_problematicas = CronogramaPago.objects.filter(
        estado='PARCIAL',
        monto_pagado__lt=1000,
        monto_pagado__gt=0
    )
    print(f"\n📊 Cuotas con pagos parciales < $1,000: {cuotas_problematicas.count()}")
    
    for cuota in cuotas_problematicas:
        print(f"  Cuota #{cuota.id}: Pagado=${cuota.monto_pagado}, Total=${cuota.monto_cuota} - Cliente: {cuota.credito.cliente.nombre_completo}")
    
    return pagos_sospechosos, tareas_sospechosas, cuotas_problematicas

def analizar_patron_error():
    """Analiza si hay un patrón en los errores de montos"""
    print("\n=== Análisis de patrones de error ===")
    
    # Buscar el caso específico mencionado: $368.38 en lugar de $36470
    pagos_368 = Pago.objects.filter(monto=Decimal('368.38'))
    print(f"\nPagos con exactamente $368.38: {pagos_368.count()}")
    
    for pago in pagos_368:
        print(f"  Pago #{pago.id} - Cliente: {pago.credito.cliente.nombre_completo}")
        print(f"    Fecha: {pago.fecha_pago}")
        print(f"    Monto del crédito: ${pago.credito.monto}")
        print(f"    Valor cuota esperado: ${pago.credito.valor_cuota}")
        
        # Verificar si podría ser un error de división por 100
        posible_monto_real = pago.monto * 100
        print(f"    Posible monto real (x100): ${posible_monto_real}")
        
        # O error de división por 99
        posible_monto_real_99 = pago.monto * 99
        print(f"    Posible monto real (x99): ${posible_monto_real_99}")

def generar_script_correccion():
    """Genera script SQL para corregir datos erróneos"""
    print("\n=== Generando script de corrección ===")
    
    # Identificar registros problemáticos
    pagos_sospechosos, tareas_sospechosas, cuotas_problematicas = identificar_datos_problematicos()
    
    corrections_sql = []
    
    # Para cada pago sospechoso, sugerir corrección
    for pago in pagos_sospechosos:
        if pago.monto == Decimal('368.38'):
            # Este es el caso específico mencionado
            monto_corregido = Decimal('36470')  # O 36469.76 según el caso
            corrections_sql.append(
                f"UPDATE main_pago SET monto = {monto_corregido} WHERE id = {pago.id}; -- Era ${pago.monto}, Cliente: {pago.credito.cliente.nombre_completo}"
            )
    
    if corrections_sql:
        print("\nScript SQL sugerido para correcciones:")
        print("-- IMPORTANTE: Revisar cada corrección antes de ejecutar")
        for sql in corrections_sql:
            print(sql)
        
        # Guardar en archivo
        with open('correcciones_montos.sql', 'w', encoding='utf-8') as f:
            f.write("-- Script de corrección de montos erróneos\n")
            f.write("-- IMPORTANTE: Revisar cada línea antes de ejecutar\n\n")
            for sql in corrections_sql:
                f.write(sql + '\n')
        print(f"\n✅ Script guardado en: correcciones_montos.sql")
    else:
        print("\n✅ No se encontraron patrones claros para corrección automática")

def mostrar_resumen():
    """Muestra un resumen de los datos encontrados"""
    print("\n" + "="*50)
    print("RESUMEN DE HALLAZGOS")
    print("="*50)
    
    total_pagos = Pago.objects.count()
    pagos_normales = Pago.objects.filter(monto__gte=1000).count()
    pagos_bajos = Pago.objects.filter(monto__lt=1000).count()
    
    print(f"Total de pagos: {total_pagos}")
    print(f"Pagos con montos normales (≥$1,000): {pagos_normales}")
    print(f"Pagos con montos bajos (<$1,000): {pagos_bajos}")
    print(f"Porcentaje problemático: {(pagos_bajos/total_pagos)*100:.1f}%")

if __name__ == "__main__":
    try:
        print("🔍 Iniciando análisis de datos problemáticos...")
        identificar_datos_problematicos()
        analizar_patron_error()
        generar_script_correccion()
        mostrar_resumen()
        print("\n✅ Análisis completado")
    except Exception as e:
        print(f"\n❌ Error durante el análisis: {e}")
        import traceback
        traceback.print_exc()