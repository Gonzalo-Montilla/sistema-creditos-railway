#!/usr/bin/env python
"""
Script para diagnosticar problemas con las tareas de cobro diarias
"""
import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'creditos.settings')
django.setup()

from main.models import Cliente, Credito, CronogramaPago, TareaCobro, Cobrador, Ruta

def diagnosticar_sistema():
    print("🔍 DIAGNÓSTICO DEL SISTEMA DE TAREAS DE COBRO")
    print("=" * 50)
    
    # 1. Verificar clientes
    total_clientes = Cliente.objects.filter(activo=True).count()
    print(f"👥 Clientes activos: {total_clientes}")
    
    # 2. Verificar créditos
    creditos_activos = Credito.objects.filter(estado__in=['DESEMBOLSADO', 'APROBADO']).count()
    creditos_diarios = Credito.objects.filter(tipo_plazo='DIARIO').count()
    print(f"💰 Créditos activos: {creditos_activos}")
    print(f"📅 Créditos diarios: {creditos_diarios}")
    
    # 3. Verificar cronogramas
    total_cuotas = CronogramaPago.objects.count()
    cuotas_pendientes = CronogramaPago.objects.filter(estado__in=['PENDIENTE', 'PARCIAL']).count()
    print(f"📋 Total cuotas: {total_cuotas}")
    print(f"⏳ Cuotas pendientes: {cuotas_pendientes}")
    
    # 4. Verificar cobradores
    cobradores_activos = Cobrador.objects.filter(activo=True).count()
    print(f"🚶 Cobradores activos: {cobradores_activos}")
    
    # 5. Verificar rutas
    rutas_activas = Ruta.objects.filter(activa=True).count()
    print(f"🗺️ Rutas activas: {rutas_activas}")
    
    # 6. Verificar tareas existentes
    total_tareas = TareaCobro.objects.count()
    tareas_hoy = TareaCobro.objects.filter(fecha_asignacion=date.today()).count()
    print(f"📋 Total tareas: {total_tareas}")
    print(f"🌅 Tareas para hoy: {tareas_hoy}")
    
    print("\n" + "=" * 50)
    
    # 7. Detalles de créditos diarios
    if creditos_diarios > 0:
        print("🔍 DETALLES DE CRÉDITOS DIARIOS:")
        print("-" * 30)
        creditos = Credito.objects.filter(tipo_plazo='DIARIO')[:5]  # Primeros 5
        
        for credito in creditos:
            print(f"🏦 Crédito #{credito.id}:")
            print(f"   📝 Cliente: {credito.cliente.nombre_completo}")
            print(f"   💵 Monto: ${credito.monto}")
            print(f"   📊 Estado: {credito.estado}")
            print(f"   🗓️ Desembolso: {credito.fecha_desembolso}")
            print(f"   🚶 Cobrador: {credito.cobrador if credito.cobrador else 'No asignado'}")
            
            # Verificar cronograma
            cuotas = credito.cronograma.all().count()
            cuotas_pendientes_credito = credito.cronograma.filter(estado__in=['PENDIENTE', 'PARCIAL']).count()
            print(f"   📋 Cuotas: {cuotas} (Pendientes: {cuotas_pendientes_credito})")
            
            # Verificar si tiene tareas
            tareas_credito = TareaCobro.objects.filter(cuota__credito=credito).count()
            print(f"   📌 Tareas generadas: {tareas_credito}")
            print()
    
    # 8. Verificar cobradores con rutas
    print("🔍 DETALLES DE COBRADORES:")
    print("-" * 30)
    
    for cobrador in Cobrador.objects.filter(activo=True):
        rutas_cobrador = cobrador.rutas.all().count()
        creditos_asignados = Credito.objects.filter(cobrador=cobrador).count()
        tareas_cobrador = TareaCobro.objects.filter(cobrador=cobrador).count()
        
        print(f"🚶 {cobrador.nombre_completo}:")
        print(f"   🗺️ Rutas asignadas: {rutas_cobrador}")
        print(f"   💰 Créditos asignados: {creditos_asignados}")
        print(f"   📌 Tareas generadas: {tareas_cobrador}")
        print()
    
    # 9. Verificar cuotas que deberían tener tareas
    print("🔍 CUOTAS QUE DEBERÍAN TENER TAREAS:")
    print("-" * 40)
    
    hoy = date.today()
    hace_30_dias = hoy - timedelta(days=30)
    
    cuotas_sin_tareas = CronogramaPago.objects.filter(
        fecha_vencimiento__gte=hace_30_dias,
        fecha_vencimiento__lte=hoy,
        estado__in=['PENDIENTE', 'PARCIAL'],
        credito__estado__in=['DESEMBOLSADO', 'VENCIDO'],
        credito__cobrador__isnull=False
    ).exclude(
        id__in=TareaCobro.objects.values_list('cuota_id', flat=True)
    )
    
    print(f"📊 Cuotas sin tareas asignadas: {cuotas_sin_tareas.count()}")
    
    for cuota in cuotas_sin_tareas[:5]:  # Primeros 5
        dias_vencida = (hoy - cuota.fecha_vencimiento).days
        print(f"   📋 Cuota #{cuota.numero_cuota} - Crédito #{cuota.credito.id}")
        print(f"      👤 Cliente: {cuota.credito.cliente.nombre_completo}")
        print(f"      📅 Vencimiento: {cuota.fecha_vencimiento} ({dias_vencida} días)")
        print(f"      💵 Monto: ${cuota.monto_cuota}")
        print(f"      🚶 Cobrador: {cuota.credito.cobrador.nombre_completo if cuota.credito.cobrador else 'No asignado'}")
        print()

def generar_tareas_forzado():
    print("\n🚀 GENERANDO TAREAS PARA HOY (FORZADO)...")
    print("=" * 50)
    
    try:
        tareas_creadas = TareaCobro.generar_tareas_diarias(fecha=date.today(), verbose=True)
        print(f"✅ Tareas creadas: {tareas_creadas}")
        
        if tareas_creadas == 0:
            print("❌ No se crearon tareas. Posibles causas:")
            print("   - No hay cobradores activos")
            print("   - No hay créditos con cuotas pendientes")
            print("   - No hay créditos asignados a cobradores")
            print("   - Las cuotas ya tienen tareas asignadas")
        
    except Exception as e:
        print(f"❌ Error al generar tareas: {e}")

if __name__ == "__main__":
    try:
        diagnosticar_sistema()
        
        # Preguntar si quiere generar tareas
        respuesta = input("\n¿Quieres intentar generar tareas para hoy? (s/n): ")
        if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
            generar_tareas_forzado()
            
    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")
        import traceback
        traceback.print_exc()