#!/usr/bin/env python
"""
Script para limpiar todos los datos de prueba del sistema
Este script elimina todos los datos pero mantiene la estructura de la base de datos
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'creditos.settings')
django.setup()

from main.models import (
    Cliente, Credito, Pago, Codeudor, CronogramaPago, 
    Cobrador, Ruta, TareaCobro, CarteraAnalisis
)
from django.contrib.auth.models import User
from django.db import transaction


def confirmar_eliminacion():
    """
    Solicita confirmación al usuario antes de proceder
    """
    print("🚨 ¡ATENCIÓN! 🚨")
    print("="*50)
    print("Este script eliminará TODOS los datos de prueba del sistema:")
    print("• Todos los clientes y sus documentos")
    print("• Todos los créditos y cronogramas de pago")
    print("• Todos los pagos registrados")
    print("• Todos los codeudores")
    print("• Todas las tareas de cobro")
    print("• Todos los análisis de cartera")
    print("• Todos los cobradores")
    print("• Todas las rutas")
    print()
    print("⚠️  Esta acción NO se puede deshacer.")
    print("=" * 50)
    
    # Solicitar confirmación múltiple
    confirmacion1 = input("¿Está seguro de que desea eliminar todos los datos? (escriba 'SI' para continuar): ")
    if confirmacion1.upper() != 'SI':
        print("❌ Operación cancelada.")
        return False
    
    confirmacion2 = input("¿Realmente desea proceder? Escriba 'ELIMINAR' para confirmar: ")
    if confirmacion2.upper() != 'ELIMINAR':
        print("❌ Operación cancelada.")
        return False
        
    confirmacion3 = input("Última confirmación. Escriba 'CONFIRMAR' para eliminar todos los datos: ")
    if confirmacion3.upper() != 'CONFIRMAR':
        print("❌ Operación cancelada.")
        return False
    
    return True


def mostrar_estadisticas_actuales():
    """
    Muestra las estadísticas actuales antes de eliminar
    """
    print("\n📊 DATOS ACTUALES EN EL SISTEMA:")
    print("-" * 40)
    
    try:
        clientes = Cliente.objects.count()
        creditos = Credito.objects.count()
        pagos = Pago.objects.count()
        codeudores = Codeudor.objects.count()
        cronogramas = CronogramaPago.objects.count()
        cobradores = Cobrador.objects.count()
        rutas = Ruta.objects.count()
        tareas = TareaCobro.objects.count()
        analisis = CarteraAnalisis.objects.count()
        
        print(f"• Clientes: {clientes}")
        print(f"• Créditos: {creditos}")
        print(f"• Pagos: {pagos}")
        print(f"• Codeudores: {codeudores}")
        print(f"• Cronogramas de pago: {cronogramas}")
        print(f"• Cobradores: {cobradores}")
        print(f"• Rutas: {rutas}")
        print(f"• Tareas de cobro: {tareas}")
        print(f"• Análisis de cartera: {analisis}")
        
        total = clientes + creditos + pagos + codeudores + cronogramas + cobradores + rutas + tareas + analisis
        print(f"\n📈 TOTAL DE REGISTROS: {total}")
        
        return total > 0
        
    except Exception as e:
        print(f"❌ Error al obtener estadísticas: {str(e)}")
        return False


def limpiar_datos():
    """
    Elimina todos los datos de prueba del sistema
    """
    print("\n🔄 Iniciando limpieza de datos...")
    
    eliminados = {
        'tareas_cobro': 0,
        'analisis_cartera': 0,
        'cronogramas': 0,
        'pagos': 0,
        'creditos': 0,
        'codeudores': 0,
        'clientes': 0,
        'cobradores': 0,
        'rutas': 0,
    }
    
    try:
        with transaction.atomic():
            # 1. Eliminar tareas de cobro (dependen de cronogramas)
            print("  🗑️  Eliminando tareas de cobro...")
            eliminados['tareas_cobro'] = TareaCobro.objects.all().delete()[0]
            
            # 2. Eliminar análisis de cartera
            print("  🗑️  Eliminando análisis de cartera...")
            eliminados['analisis_cartera'] = CarteraAnalisis.objects.all().delete()[0]
            
            # 3. Eliminar cronogramas de pago (dependen de créditos)
            print("  🗑️  Eliminando cronogramas de pago...")
            eliminados['cronogramas'] = CronogramaPago.objects.all().delete()[0]
            
            # 4. Eliminar pagos (dependen de créditos)
            print("  🗑️  Eliminando pagos...")
            eliminados['pagos'] = Pago.objects.all().delete()[0]
            
            # 5. Eliminar créditos (dependen de clientes)
            print("  🗑️  Eliminando créditos...")
            eliminados['creditos'] = Credito.objects.all().delete()[0]
            
            # 6. Eliminar codeudores (dependen de clientes)
            print("  🗑️  Eliminando codeudores...")
            eliminados['codeudores'] = Codeudor.objects.all().delete()[0]
            
            # 7. Eliminar clientes
            print("  🗑️  Eliminando clientes...")
            eliminados['clientes'] = Cliente.objects.all().delete()[0]
            
            # 8. Eliminar cobradores
            print("  🗑️  Eliminando cobradores...")
            eliminados['cobradores'] = Cobrador.objects.all().delete()[0]
            
            # 9. Eliminar rutas
            print("  🗑️  Eliminando rutas...")
            eliminados['rutas'] = Ruta.objects.all().delete()[0]
            
        print("\n✅ Limpieza completada exitosamente!")
        return eliminados
        
    except Exception as e:
        print(f"\n❌ Error durante la limpieza: {str(e)}")
        return None


def mostrar_resumen_limpieza(eliminados):
    """
    Muestra un resumen de los datos eliminados
    """
    if not eliminados:
        return
        
    print("\n📋 RESUMEN DE ELIMINACIÓN:")
    print("=" * 40)
    
    total_eliminados = 0
    for tipo, cantidad in eliminados.items():
        if cantidad > 0:
            nombre_tipo = tipo.replace('_', ' ').title()
            print(f"• {nombre_tipo}: {cantidad}")
            total_eliminados += cantidad
    
    print(f"\n🗑️  TOTAL ELIMINADOS: {total_eliminados} registros")
    
    if total_eliminados > 0:
        print("\n🎉 ¡Sistema limpio! Ahora puede crear datos nuevos desde cero.")
    else:
        print("\nℹ️  El sistema ya estaba limpio.")


def verificar_limpieza():
    """
    Verifica que todos los datos fueron eliminados correctamente
    """
    print("\n🔍 Verificando limpieza...")
    
    verificaciones = {
        'Clientes': Cliente.objects.count(),
        'Créditos': Credito.objects.count(),
        'Pagos': Pago.objects.count(),
        'Codeudores': Codeudor.objects.count(),
        'Cronogramas': CronogramaPago.objects.count(),
        'Cobradores': Cobrador.objects.count(),
        'Rutas': Ruta.objects.count(),
        'Tareas de cobro': TareaCobro.objects.count(),
        'Análisis de cartera': CarteraAnalisis.objects.count(),
    }
    
    problema = False
    for tabla, cantidad in verificaciones.items():
        if cantidad > 0:
            print(f"  ⚠️  {tabla}: {cantidad} registros restantes")
            problema = True
        else:
            print(f"  ✅ {tabla}: Limpia")
    
    if problema:
        print("\n⚠️  Algunos datos no fueron eliminados completamente.")
    else:
        print("\n✅ Verificación exitosa: Todos los datos fueron eliminados.")
    
    return not problema


def main():
    """
    Función principal del script
    """
    print("🧹 LIMPIADOR DE DATOS DE PRUEBA")
    print("Sistema de Créditos - Limpieza Completa")
    print("=" * 50)
    
    # Mostrar estadísticas actuales
    hay_datos = mostrar_estadisticas_actuales()
    
    if not hay_datos:
        print("\n✨ El sistema ya está limpio. No hay datos para eliminar.")
        return
    
    # Solicitar confirmación
    if not confirmar_eliminacion():
        return
    
    # Realizar limpieza
    eliminados = limpiar_datos()
    
    if eliminados:
        # Mostrar resumen
        mostrar_resumen_limpieza(eliminados)
        
        # Verificar limpieza
        verificar_limpieza()
        
        print("\n🎯 SIGUIENTE PASO:")
        print("Ahora puede crear nuevos clientes, créditos y datos desde la interfaz web.")
        print("El sistema está completamente limpio y listo para usar.")
    
    print("\n✨ Proceso completado!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Proceso interrumpido por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error inesperado: {str(e)}")
        sys.exit(1)