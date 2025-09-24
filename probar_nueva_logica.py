#!/usr/bin/env python
"""
Script para probar la nueva lógica de generación de tareas centrada en HOY
"""
import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'creditos.settings')
django.setup()

from main.models import Cliente, Credito, CronogramaPago, TareaCobro, Cobrador, Ruta

def revisar_cuotas_que_vencen_hoy():
    print("🔍 CUOTAS QUE VENCEN HOY")
    print("=" * 50)
    
    hoy = date.today()
    
    # Buscar TODAS las cuotas que vencen exactamente hoy
    cuotas_hoy = CronogramaPago.objects.filter(
        fecha_vencimiento=hoy,
        estado__in=['PENDIENTE', 'PARCIAL'],
        credito__estado__in=['DESEMBOLSADO', 'VENCIDO'],
        credito__cobrador__isnull=False
    ).select_related('credito__cliente', 'credito__cobrador').order_by('credito__tipo_plazo', 'credito__cliente__nombres')
    
    print(f"📅 Fecha de hoy: {hoy}")
    print(f"📋 Cuotas que vencen HOY: {cuotas_hoy.count()}")
    print()
    
    if cuotas_hoy.exists():
        for cuota in cuotas_hoy:
            tipo_credito = cuota.credito.get_tipo_plazo_display()
            print(f"🏦 Cuota #{cuota.numero_cuota} - Crédito #{cuota.credito.id} ({tipo_credito})")
            print(f"   👤 Cliente: {cuota.credito.cliente.nombre_completo}")
            print(f"   💵 Monto cuota: ${cuota.monto_cuota}")
            print(f"   📅 Vence: {cuota.fecha_vencimiento}")
            print(f"   🚶 Cobrador: {cuota.credito.cobrador.nombre_completo}")
            
            # Verificar si ya tiene tarea para hoy
            tiene_tarea_hoy = TareaCobro.objects.filter(
                cuota=cuota, 
                fecha_asignacion=hoy
            ).exists()
            print(f"   📌 Tarea para hoy: {'✅ Sí' if tiene_tarea_hoy else '❌ No'}")
            print()
    else:
        print("❌ No hay cuotas que venzan exactamente hoy")
    
    return cuotas_hoy.count()

def probar_generacion_nueva():
    print("\n🚀 PROBANDO NUEVA LÓGICA DE GENERACIÓN")
    print("=" * 50)
    
    # Eliminar tareas existentes para hoy para hacer prueba limpia
    hoy = date.today()
    tareas_existentes = TareaCobro.objects.filter(fecha_asignacion=hoy).count()
    
    if tareas_existentes > 0:
        print(f"⚠️  Hay {tareas_existentes} tareas existentes para hoy")
        respuesta = input("¿Eliminar tareas existentes para hacer prueba limpia? (s/n): ")
        if respuesta.lower() in ['s', 'si', 'sí']:
            TareaCobro.objects.filter(fecha_asignacion=hoy).delete()
            print("✅ Tareas existentes eliminadas")
    
    # Generar tareas con nueva lógica
    print(f"\n🔄 Generando tareas para {hoy} con nueva lógica...")
    tareas_creadas = TareaCobro.generar_tareas_diarias(fecha=hoy, verbose=True)
    
    print(f"\n📊 RESULTADO:")
    print(f"   ✅ Tareas creadas: {tareas_creadas}")
    
    # Verificar que se crearon tareas para los créditos diarios
    tareas_diarias = TareaCobro.objects.filter(
        fecha_asignacion=hoy,
        cuota__credito__tipo_plazo='DIARIO'
    )
    
    print(f"   📅 Tareas para créditos DIARIOS: {tareas_diarias.count()}")
    
    if tareas_diarias.exists():
        print("\n🎯 TAREAS CREADAS PARA CRÉDITOS DIARIOS:")
        for tarea in tareas_diarias:
            print(f"   • {tarea.cliente.nombre_completo} - Cuota #{tarea.cuota.numero_cuota} - ${tarea.monto_a_cobrar}")
    
    # Verificar distribución por modalidad
    modalidades = {}
    for tarea in TareaCobro.objects.filter(fecha_asignacion=hoy):
        modalidad = tarea.cuota.credito.get_tipo_plazo_display()
        if modalidad not in modalidades:
            modalidades[modalidad] = 0
        modalidades[modalidad] += 1
    
    print(f"\n📊 DISTRIBUCIÓN POR MODALIDAD:")
    for modalidad, cantidad in modalidades.items():
        print(f"   📋 {modalidad}: {cantidad} tareas")

if __name__ == "__main__":
    try:
        cuotas_hoy = revisar_cuotas_que_vencen_hoy()
        
        if cuotas_hoy > 0:
            probar_generacion_nueva()
        else:
            print("\n❌ No hay cuotas que venzan hoy, no se puede probar la generación.")
            print("💡 Puedes crear un crédito diario para probar o ajustar fechas de cronograma existente.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()