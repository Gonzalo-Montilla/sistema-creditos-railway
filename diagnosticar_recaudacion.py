#!/usr/bin/env python
"""
Script para diagnosticar problemas con los cálculos de recaudación
"""
import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'creditos.settings')
django.setup()

from main.models import Cliente, Credito, Pago, TareaCobro, Cobrador
from django.db.models import Sum

def diagnosticar_recaudacion_sofia():
    print("🔍 DIAGNÓSTICO DE RECAUDACIÓN - SOFIA VERGARA")
    print("=" * 60)
    
    # Buscar a Sofia Vergara
    try:
        sofia = Cobrador.objects.get(nombres__icontains="SOFIA", apellidos__icontains="VERGARA")
        print(f"👤 Cobrador encontrado: {sofia.nombre_completo}")
        print(f"    ID: {sofia.id}")
    except Cobrador.DoesNotExist:
        print("❌ No se encontró a SOFIA VERGARA")
        return
    
    hoy = date.today()
    print(f"📅 Fecha de análisis: {hoy}")
    print()
    
    # 1. VERIFICAR TAREAS DE COBRO
    print("📋 TAREAS DE COBRO:")
    print("-" * 30)
    tareas_sofia = TareaCobro.objects.filter(cobrador=sofia, fecha_asignacion=hoy)
    
    for tarea in tareas_sofia:
        print(f"🎯 Tarea #{tarea.id}:")
        print(f"    Cliente: {tarea.cliente.nombre_completo}")
        print(f"    Estado: {tarea.estado}")
        print(f"    Monto a cobrar: ${tarea.monto_a_cobrar}")
        if tarea.monto_cobrado:
            print(f"    Monto cobrado: ${tarea.monto_cobrado}")
        if tarea.fecha_visita:
            print(f"    Fecha visita: {tarea.fecha_visita}")
        print()
    
    # 2. VERIFICAR PAGOS REGISTRADOS HOY
    print("💰 PAGOS REGISTRADOS HOY:")
    print("-" * 30)
    pagos_sofia_hoy = Pago.objects.filter(
        credito__cobrador=sofia,
        fecha_pago__date=hoy
    ).order_by('-fecha_pago')
    
    total_pagos_real = 0
    for pago in pagos_sofia_hoy:
        print(f"💵 Pago #{pago.id}:")
        print(f"    Cliente: {pago.credito.cliente.nombre_completo}")
        print(f"    Monto: ${pago.monto}")
        print(f"    Fecha: {pago.fecha_pago}")
        print(f"    Crédito: #{pago.credito.id}")
        if pago.observaciones:
            print(f"    Observaciones: {pago.observaciones}")
        total_pagos_real += float(pago.monto)
        print()
    
    print(f"📊 TOTAL REAL PAGOS HOY: ${total_pagos_real}")
    print()
    
    # 3. VERIFICAR CÁLCULOS DEL SISTEMA
    print("🧮 CÁLCULOS DEL SISTEMA:")
    print("-" * 30)
    
    # Cálculo usando Sum()
    total_sum = Pago.objects.filter(
        credito__cobrador=sofia,
        fecha_pago__date=hoy
    ).aggregate(total=Sum('monto'))['total'] or 0
    
    print(f"Sum() del sistema: ${total_sum}")
    print(f"Suma manual: ${total_pagos_real}")
    print(f"Diferencia: ${float(total_sum) - total_pagos_real}")
    print()
    
    # 4. VERIFICAR TAREAS MARCADAS COMO COBRADAS
    print("✅ TAREAS MARCADAS COMO COBRADAS:")
    print("-" * 30)
    
    tareas_cobradas = TareaCobro.objects.filter(
        cobrador=sofia,
        fecha_asignacion=hoy,
        estado='COBRADO'
    )
    
    total_tareas_cobrado = 0
    for tarea in tareas_cobradas:
        print(f"✅ Tarea #{tarea.id}:")
        print(f"    Cliente: {tarea.cliente.nombre_completo}")
        print(f"    Monto cobrado: ${tarea.monto_cobrado}")
        if tarea.monto_cobrado:
            total_tareas_cobrado += float(tarea.monto_cobrado)
        print()
    
    print(f"📊 TOTAL DESDE TAREAS: ${total_tareas_cobrado}")
    print()
    
    # 5. RESUMEN Y DIAGNÓSTICO
    print("🎯 DIAGNÓSTICO:")
    print("-" * 30)
    print(f"Total desde Pagos (Sum): ${total_sum}")
    print(f"Total desde Pagos (manual): ${total_pagos_real}")
    print(f"Total desde Tareas: ${total_tareas_cobrado}")
    
    if total_pagos_real != float(total_sum):
        print("❌ PROBLEMA: Diferencia entre Sum() y suma manual")
    
    if total_pagos_real != total_tareas_cobrado:
        print("❌ PROBLEMA: Diferencia entre Pagos y Tareas")
        print("    Posible causa: Pagos registrados fuera del sistema de tareas")
    
    if total_sum == 368 and total_pagos_real > 30000:
        print("❌ PROBLEMA CRÍTICO: Probable error de formato/tipo de datos")
        print("    El sistema muestra $368 pero los datos reales suman más de $30,000")
    
    print()
    return {
        'total_sum': total_sum,
        'total_manual': total_pagos_real,
        'total_tareas': total_tareas_cobrado
    }

def revisar_vista_recaudacion():
    print("🔍 REVISANDO VISTA DE RECAUDACIÓN")
    print("=" * 40)
    
    # Simular lo que hace la vista de recaudación
    from datetime import date
    from django.db.models import Sum, Count
    
    hoy = date.today()
    fecha_desde = hoy.strftime('%Y-%m-%d')
    fecha_hasta = hoy.strftime('%Y-%m-%d')
    
    print(f"Filtros: desde {fecha_desde} hasta {fecha_hasta}")
    
    cobradores = Cobrador.objects.filter(activo=True).order_by('nombres', 'apellidos')
    
    for cobrador in cobradores:
        if "SOFIA" in cobrador.nombres.upper():
            print(f"\n👤 Analizando: {cobrador.nombre_completo}")
            
            # Replicar la lógica exacta de la vista
            pagos_cobrador = Pago.objects.filter(
                credito__cobrador=cobrador,
                fecha_pago__date__gte=fecha_desde,
                fecha_pago__date__lte=fecha_hasta
            )
            
            print(f"Pagos encontrados: {pagos_cobrador.count()}")
            
            for pago in pagos_cobrador:
                print(f"  - Pago #{pago.id}: ${pago.monto} ({type(pago.monto)})")
            
            # Usar el mismo aggregate que la vista
            total_recaudado = pagos_cobrador.aggregate(Sum('monto'))['monto__sum'] or 0
            print(f"Aggregate result: {total_recaudado} ({type(total_recaudado)})")
            
            # Suma manual para comparar
            suma_manual = sum([pago.monto for pago in pagos_cobrador])
            print(f"Suma manual: {suma_manual} ({type(suma_manual)})")
            
            break

if __name__ == "__main__":
    try:
        resultado = diagnosticar_recaudacion_sofia()
        print("\n" + "=" * 60)
        revisar_vista_recaudacion()
        
        print("\n" + "=" * 60)
        print("💡 RECOMENDACIONES:")
        print("1. Verificar tipos de datos en modelo Pago.monto")
        print("2. Revisar si hay conversiones erróneas en las vistas")
        print("3. Verificar formato de números en templates")
        print("4. Revisar si hay filtros incorrectos en las consultas")
        
    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")
        import traceback
        traceback.print_exc()