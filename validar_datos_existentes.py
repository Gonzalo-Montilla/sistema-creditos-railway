#!/usr/bin/env python
"""
Script para validar datos existentes antes de aplicar las nuevas validaciones
"""
import os
import sys
import django
from datetime import date
import re

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'creditos.settings')
django.setup()

from main.models import Cliente, Codeudor

def validar_cedula(cedula):
    """Valida formato de cédula (8-10 dígitos)"""
    if not cedula:
        return False, "Cédula vacía"
    
    if not re.match(r'^\d{8,10}$', cedula):
        return False, f"Formato inválido: '{cedula}' (debe ser 8-10 dígitos)"
    
    return True, "OK"

def validar_celular(celular):
    """Valida formato de celular (10 dígitos, empieza con 3)"""
    if not celular:
        return False, "Celular vacío"
    
    if not re.match(r'^3[0-9]{9}$', celular):
        return False, f"Formato inválido: '{celular}' (debe ser 3xxxxxxxxx)"
    
    return True, "OK"

def validar_telefono_fijo(telefono):
    """Valida formato de teléfono fijo (7-8 dígitos)"""
    if not telefono:
        return True, "OK (opcional)"
    
    if not re.match(r'^[2-8][0-9]{6,7}$', telefono):
        return False, f"Formato inválido: '{telefono}' (debe ser 7-8 dígitos)"
    
    return True, "OK"

def validar_datos_clientes():
    print("🔍 VALIDANDO DATOS DE CLIENTES")
    print("=" * 50)
    
    clientes = Cliente.objects.all()
    problemas_cedula = []
    problemas_celular = []
    problemas_telefono = []
    problemas_referencias = []
    
    for cliente in clientes:
        # Validar cédula
        valido, mensaje = validar_cedula(cliente.cedula)
        if not valido:
            problemas_cedula.append(f"Cliente {cliente.id}: {mensaje}")
        
        # Validar celular
        valido, mensaje = validar_celular(cliente.celular)
        if not valido:
            problemas_celular.append(f"Cliente {cliente.id} ({cliente.nombre_completo}): {mensaje}")
        
        # Validar teléfono fijo
        valido, mensaje = validar_telefono_fijo(cliente.telefono_fijo)
        if not valido:
            problemas_telefono.append(f"Cliente {cliente.id} ({cliente.nombre_completo}): {mensaje}")
        
        # Validar referencias
        if cliente.referencia1_telefono:
            valido, mensaje = validar_celular(cliente.referencia1_telefono)
            if not valido:
                problemas_referencias.append(f"Cliente {cliente.id} Ref1: {mensaje}")
        
        if cliente.referencia2_telefono:
            valido, mensaje = validar_celular(cliente.referencia2_telefono)
            if not valido:
                problemas_referencias.append(f"Cliente {cliente.id} Ref2: {mensaje}")
    
    # Mostrar resultados
    print(f"📊 Total clientes analizados: {clientes.count()}")
    print()
    
    if problemas_cedula:
        print("❌ PROBLEMAS EN CÉDULAS:")
        for problema in problemas_cedula:
            print(f"   • {problema}")
        print()
    else:
        print("✅ Cédulas de clientes: OK")
    
    if problemas_celular:
        print("❌ PROBLEMAS EN CELULARES:")
        for problema in problemas_celular:
            print(f"   • {problema}")
        print()
    else:
        print("✅ Celulares de clientes: OK")
    
    if problemas_telefono:
        print("❌ PROBLEMAS EN TELÉFONOS FIJOS:")
        for problema in problemas_telefono:
            print(f"   • {problema}")
        print()
    else:
        print("✅ Teléfonos fijos: OK")
    
    if problemas_referencias:
        print("❌ PROBLEMAS EN REFERENCIAS:")
        for problema in problemas_referencias:
            print(f"   • {problema}")
        print()
    else:
        print("✅ Referencias: OK")
    
    return len(problemas_cedula) + len(problemas_celular) + len(problemas_telefono) + len(problemas_referencias)

def validar_datos_codeudores():
    print("🔍 VALIDANDO DATOS DE CODEUDORES")
    print("=" * 50)
    
    codeudores = Codeudor.objects.all()
    problemas_cedula = []
    problemas_celular = []
    cedulas_duplicadas = []
    
    # Detectar duplicados
    cedulas_vistas = {}
    for codeudor in codeudores:
        if codeudor.cedula in cedulas_vistas:
            cedulas_duplicadas.append(f"Cédula '{codeudor.cedula}' duplicada: IDs {cedulas_vistas[codeudor.cedula]} y {codeudor.id}")
        else:
            cedulas_vistas[codeudor.cedula] = codeudor.id
        
        # Validar formato cédula
        valido, mensaje = validar_cedula(codeudor.cedula)
        if not valido:
            problemas_cedula.append(f"Codeudor {codeudor.id}: {mensaje}")
        
        # Validar celular
        valido, mensaje = validar_celular(codeudor.celular)
        if not valido:
            problemas_celular.append(f"Codeudor {codeudor.id} ({codeudor.nombre_completo}): {mensaje}")
    
    # Mostrar resultados
    print(f"📊 Total codeudores analizados: {codeudores.count()}")
    print()
    
    if cedulas_duplicadas:
        print("❌ CÉDULAS DUPLICADAS:")
        for duplicado in cedulas_duplicadas:
            print(f"   • {duplicado}")
        print()
    else:
        print("✅ No hay cédulas duplicadas")
    
    if problemas_cedula:
        print("❌ PROBLEMAS EN CÉDULAS:")
        for problema in problemas_cedula:
            print(f"   • {problema}")
        print()
    else:
        print("✅ Cédulas de codeudores: OK")
    
    if problemas_celular:
        print("❌ PROBLEMAS EN CELULARES:")
        for problema in problemas_celular:
            print(f"   • {problema}")
        print()
    else:
        print("✅ Celulares de codeudores: OK")
    
    return len(problemas_cedula) + len(problemas_celular) + len(cedulas_duplicadas)

def sugerir_correcciones():
    print("\n🔧 SUGERENCIAS DE CORRECCIÓN")
    print("=" * 50)
    print("Si hay problemas, puedes:")
    print("1. Corregir datos manualmente en el admin de Django")
    print("2. Ejecutar script de corrección automática")
    print("3. Aplicar migración ignorando errores (NO recomendado)")
    print()
    print("Para corregir automáticamente:")
    print("• Cédulas inválidas: rellenar con ceros a la izquierda")
    print("• Celulares inválidos: reemplazar por número genérico")
    print("• Codeudores duplicados: fusionar o eliminar")

if __name__ == "__main__":
    try:
        print("🔍 VALIDACIÓN DE DATOS EXISTENTES")
        print("Antes de aplicar nuevas validaciones...")
        print("=" * 60)
        print()
        
        problemas_clientes = validar_datos_clientes()
        print()
        problemas_codeudores = validar_datos_codeudores()
        
        total_problemas = problemas_clientes + problemas_codeudores
        
        print("\n" + "=" * 60)
        print(f"📊 RESUMEN: {total_problemas} problemas encontrados")
        
        if total_problemas == 0:
            print("🎉 ¡PERFECTO! Puedes aplicar la migración sin problemas")
            print("Ejecuta: python manage.py migrate")
        else:
            print("⚠️  HAY PROBLEMAS que deben resolverse antes de la migración")
            sugerir_correcciones()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()