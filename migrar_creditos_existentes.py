#!/usr/bin/env python
"""
Script para migrar créditos existentes a la nueva lógica de interés simple
Este script actualiza los cálculos de créditos existentes para usar la misma lógica del valorizador
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'creditos.settings')
django.setup()

from main.models import Credito
from main.creditos_utils import calcular_credito_informal, validar_parametros_credito, calcular_plazo_en_meses


def migrar_creditos_existentes():
    """
    Migra créditos existentes a la nueva lógica de cálculo
    """
    print("🔄 Iniciando migración de créditos existentes...")
    
    # Obtener todos los créditos
    creditos = Credito.objects.all()
    total_creditos = creditos.count()
    
    if total_creditos == 0:
        print("ℹ️  No hay créditos existentes para migrar.")
        return
    
    print(f"📊 Encontrados {total_creditos} créditos para migrar.")
    
    # Contadores
    migrados_exitosamente = 0
    errores = 0
    saltados = 0
    
    for i, credito in enumerate(creditos, 1):
        print(f"\n[{i}/{total_creditos}] Procesando crédito #{credito.id}")
        
        try:
            # Verificar que el crédito tenga los campos necesarios
            if not hasattr(credito, 'tipo_plazo') or not credito.tipo_plazo:
                print(f"  ⚠️  Asignando tipo_plazo por defecto (MENSUAL) al crédito #{credito.id}")
                credito.tipo_plazo = 'MENSUAL'
            
            if not hasattr(credito, 'cantidad_cuotas') or not credito.cantidad_cuotas:
                # Estimar cantidad de cuotas basado en el plazo en meses
                plazo_meses = getattr(credito, 'plazo_meses', 1)
                if credito.tipo_plazo == 'MENSUAL':
                    credito.cantidad_cuotas = int(plazo_meses)
                else:
                    # Para otros tipos, estimar
                    credito.cantidad_cuotas = max(1, int(plazo_meses))
                print(f"  ⚠️  Asignando cantidad_cuotas estimada ({credito.cantidad_cuotas}) al crédito #{credito.id}")
            
            # Validar parámetros
            es_valido, mensaje_error = validar_parametros_credito(
                monto=credito.monto,
                tasa_mensual=credito.tasa_interes,
                cantidad_cuotas=credito.cantidad_cuotas,
                tipo_plazo=credito.tipo_plazo
            )
            
            if not es_valido:
                print(f"  ❌ Error en validación: {mensaje_error}")
                errores += 1
                continue
            
            # Guardar valores originales para comparación
            valor_cuota_original = getattr(credito, 'valor_cuota', 0)
            monto_total_original = getattr(credito, 'monto_total', 0)
            
            # Recalcular usando la nueva lógica
            print(f"  🔢 Recalculando con: Monto=${credito.monto}, Tasa={credito.tasa_interes}%, {credito.cantidad_cuotas} {credito.get_tipo_plazo_display().lower()}s")
            
            # Usar el método del modelo que ya usa las funciones centralizadas
            credito.calcular_cronograma()
            
            # Actualizar plazo en meses usando función centralizada
            credito.plazo_meses = round(calcular_plazo_en_meses(credito.cantidad_cuotas, credito.tipo_plazo), 1)
            
            # Guardar cambios
            credito.save()
            
            print(f"  ✅ Migración exitosa:")
            print(f"     💰 Valor cuota: ${valor_cuota_original:,.0f} → ${credito.valor_cuota:,.0f}")
            print(f"     📊 Total: ${monto_total_original:,.0f} → ${credito.monto_total:,.0f}")
            print(f"     📅 Plazo: {credito.plazo_meses} meses")
            
            migrados_exitosamente += 1
            
        except Exception as e:
            print(f"  ❌ Error procesando crédito #{credito.id}: {str(e)}")
            errores += 1
    
    # Resumen final
    print(f"\n📋 RESUMEN DE MIGRACIÓN:")
    print(f"✅ Migrados exitosamente: {migrados_exitosamente}")
    print(f"❌ Errores: {errores}")
    print(f"⏭️  Saltados: {saltados}")
    print(f"📊 Total procesados: {migrados_exitosamente + errores + saltados}")
    
    if migrados_exitosamente > 0:
        print(f"\n🎉 Migración completada! {migrados_exitosamente} créditos ahora usan la nueva lógica de interés simple.")
    
    if errores > 0:
        print(f"\n⚠️  Hay {errores} créditos que requieren atención manual.")


def verificar_creditos_migrados():
    """
    Verifica que los créditos migrados tengan valores consistentes
    """
    print("\n🔍 Verificando consistencia de créditos migrados...")
    
    creditos = Credito.objects.all()
    problemas = []
    
    for credito in creditos:
        try:
            # Recalcular para verificar
            resultado = calcular_credito_informal(
                monto=credito.monto,
                tasa_mensual=credito.tasa_interes,
                cantidad_cuotas=credito.cantidad_cuotas,
                tipo_plazo=credito.tipo_plazo
            )
            
            # Comparar valores (con tolerancia para redondeo)
            valor_cuota_esperado = resultado['calculos']['valor_cuota']
            diferencia_cuota = abs(float(credito.valor_cuota) - valor_cuota_esperado)
            
            if diferencia_cuota > 1:  # Tolerancia de $1
                problemas.append(f"Crédito #{credito.id}: Valor cuota inconsistente (DB: ${credito.valor_cuota:,.0f}, Esperado: ${valor_cuota_esperado:,.0f})")
            
        except Exception as e:
            problemas.append(f"Crédito #{credito.id}: Error en verificación - {str(e)}")
    
    if problemas:
        print(f"⚠️  Encontrados {len(problemas)} problemas:")
        for problema in problemas[:5]:  # Mostrar solo los primeros 5
            print(f"   • {problema}")
        if len(problemas) > 5:
            print(f"   • ... y {len(problemas) - 5} más")
    else:
        print("✅ Todos los créditos están consistentes con la nueva lógica.")


if __name__ == '__main__':
    try:
        migrar_creditos_existentes()
        verificar_creditos_migrados()
        print("\n✨ Proceso completado exitosamente!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Proceso interrumpido por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error inesperado: {str(e)}")
        sys.exit(1)