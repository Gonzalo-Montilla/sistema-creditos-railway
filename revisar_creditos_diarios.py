#!/usr/bin/env python
"""
Script para revisar específicamente los créditos diarios y generar sus tareas
"""
import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'creditos.settings')
django.setup()

from main.models import Cliente, Credito, CronogramaPago, TareaCobro, Cobrador, Ruta

def revisar_creditos_diarios():
    print("🔍 REVISIÓN ESPECÍFICA DE CRÉDITOS DIARIOS")
    print("=" * 50)
    
    creditos_diarios = Credito.objects.filter(tipo_plazo='DIARIO')
    
    for credito in creditos_diarios:
        print(f"🏦 CRÉDITO DIARIO #{credito.id}:")
        print(f"   👤 Cliente: {credito.cliente.nombre_completo}")
        print(f"   💵 Monto: ${credito.monto}")
        print(f"   📊 Estado: {credito.estado}")
        print(f"   🗓️ Desembolso: {credito.fecha_desembolso}")
        print(f"   🚶 Cobrador: {credito.cobrador.nombre_completo if credito.cobrador else 'Sin cobrador'}")
        
        # Verificar cronograma
        cuotas = credito.cronograma.all().order_by('fecha_vencimiento')
        print(f"   📋 Total cuotas: {cuotas.count()}")
        
        if cuotas.exists():
            print("   📅 Primeras 10 cuotas:")
            for cuota in cuotas[:10]:
                dias_vencida = (date.today() - cuota.fecha_vencimiento).days
                estado_texto = "🔴 VENCIDA" if dias_vencida > 0 else "🟢 AL DÍA"
                
                # Verificar si tiene tarea
                tiene_tarea = TareaCobro.objects.filter(cuota=cuota).exists()
                tarea_texto = "✅ Con tarea" if tiene_tarea else "❌ Sin tarea"
                
                print(f"      Cuota #{cuota.numero_cuota}: {cuota.fecha_vencimiento} - ${cuota.monto_cuota} - {estado_texto} ({dias_vencida} días) - {tarea_texto}")
        
        print()

def generar_tareas_creditos_diarios():
    print("\n🚀 GENERANDO TAREAS PARA CRÉDITOS DIARIOS")
    print("=" * 50)
    
    hoy = date.today()
    creditos_diarios = Credito.objects.filter(
        tipo_plazo='DIARIO',
        estado='DESEMBOLSADO',
        cobrador__isnull=False
    )
    
    tareas_creadas = 0
    
    for credito in creditos_diarios:
        print(f"📋 Procesando crédito #{credito.id} de {credito.cliente.nombre_completo}")
        
        # Buscar cuotas vencidas o que vencen hoy para este crédito específico
        cuotas_por_cobrar = credito.cronograma.filter(
            fecha_vencimiento__lte=hoy,
            estado__in=['PENDIENTE', 'PARCIAL']
        ).exclude(
            # Excluir cuotas que ya tienen tarea
            id__in=TareaCobro.objects.values_list('cuota_id', flat=True)
        ).order_by('fecha_vencimiento')
        
        print(f"   ⏰ Cuotas para cobrar: {cuotas_por_cobrar.count()}")
        
        for cuota in cuotas_por_cobrar[:5]:  # Máximo 5 cuotas por crédito
            dias_vencida = (hoy - cuota.fecha_vencimiento).days
            
            # Determinar prioridad
            if dias_vencida > 3:
                prioridad = 'ALTA'
            elif dias_vencida >= 0:
                prioridad = 'MEDIA'
            else:
                prioridad = 'BAJA'
            
            try:
                tarea = TareaCobro.objects.create(
                    cobrador=credito.cobrador,
                    cuota=cuota,
                    fecha_asignacion=hoy,
                    prioridad=prioridad,
                    orden_visita=1  # Se optimizará después
                )
                
                print(f"   ✅ Tarea creada: Cuota #{cuota.numero_cuota} - ${cuota.monto_cuota} - {prioridad} - {dias_vencida} días")
                tareas_creadas += 1
                
            except Exception as e:
                print(f"   ❌ Error creando tarea para cuota #{cuota.numero_cuota}: {e}")
    
    print(f"\n✅ Total tareas creadas para créditos diarios: {tareas_creadas}")

if __name__ == "__main__":
    try:
        revisar_creditos_diarios()
        
        # Preguntar si quiere generar tareas
        respuesta = input("\n¿Quieres generar tareas específicas para los créditos diarios? (s/n): ")
        if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
            generar_tareas_creditos_diarios()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()