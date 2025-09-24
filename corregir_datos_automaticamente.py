#!/usr/bin/env python
"""
Script para corregir automáticamente los datos inválidos antes de la migración
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'creditos.settings')
django.setup()

from main.models import Cliente, Codeudor

def corregir_cedulas_clientes():
    print("🔧 CORRIGIENDO CÉDULAS DE CLIENTES")
    print("-" * 40)
    
    clientes = Cliente.objects.all()
    corregidos = 0
    
    for cliente in clientes:
        cedula_original = cliente.cedula
        
        # Si la cédula tiene menos de 8 dígitos, rellenar con ceros
        if len(cedula_original) < 8 and cedula_original.isdigit():
            cedula_corregida = cedula_original.zfill(8)  # Rellenar con ceros a la izquierda
            cliente.cedula = cedula_corregida
            cliente.save()
            print(f"   ✅ Cliente {cliente.id}: '{cedula_original}' → '{cedula_corregida}'")
            corregidos += 1
        elif len(cedula_original) > 10:
            # Si es muy larga, tomar los últimos 10 dígitos
            cedula_corregida = cedula_original[-10:]
            cliente.cedula = cedula_corregida
            cliente.save()
            print(f"   ✅ Cliente {cliente.id}: '{cedula_original}' → '{cedula_corregida}' (truncada)")
            corregidos += 1
    
    print(f"📊 Cédulas de clientes corregidas: {corregidos}")
    return corregidos

def corregir_celulares_clientes():
    print("\\n🔧 CORRIGIENDO CELULARES DE CLIENTES")
    print("-" * 40)
    
    clientes = Cliente.objects.all()
    corregidos = 0
    
    for cliente in clientes:
        celular_original = cliente.celular
        
        # Si el celular no cumple el formato, corregirlo
        if not celular_original.startswith('3') or len(celular_original) != 10:
            if len(celular_original) >= 7:
                # Intentar corregir agregando '3' al inicio si falta
                if not celular_original.startswith('3'):
                    celular_corregido = '3' + celular_original.zfill(9)
                else:
                    celular_corregido = celular_original.zfill(10)
                
                # Asegurar que tenga exactamente 10 dígitos
                if len(celular_corregido) > 10:
                    celular_corregido = celular_corregido[:10]
                elif len(celular_corregido) < 10:
                    celular_corregido = celular_corregido.zfill(10)
                    
                # Asegurar que empiece con 3
                if not celular_corregido.startswith('3'):
                    celular_corregido = '3' + celular_corregido[1:]
                    
            else:
                # Si es muy corto, generar número genérico
                celular_corregido = f"300000{cliente.id:04d}"
            
            cliente.celular = celular_corregido
            cliente.save()
            print(f"   ✅ Cliente {cliente.id}: '{celular_original}' → '{celular_corregido}'")
            corregidos += 1
    
    print(f"📊 Celulares de clientes corregidos: {corregidos}")
    return corregidos

def corregir_referencias():
    print("\\n🔧 CORRIGIENDO REFERENCIAS DE CLIENTES")
    print("-" * 40)
    
    clientes = Cliente.objects.all()
    corregidos = 0
    
    for cliente in clientes:
        # Referencia 1
        if cliente.referencia1_telefono:
            tel_original = cliente.referencia1_telefono
            if not tel_original.startswith('3') or len(tel_original) != 10:
                if len(tel_original) > 10:
                    tel_corregido = tel_original[:10]
                else:
                    tel_corregido = tel_original.zfill(10)
                
                if not tel_corregido.startswith('3'):
                    tel_corregido = '3' + tel_corregido[1:]
                
                cliente.referencia1_telefono = tel_corregido
                cliente.save()
                print(f"   ✅ Cliente {cliente.id} Ref1: '{tel_original}' → '{tel_corregido}'")
                corregidos += 1
        
        # Referencia 2
        if cliente.referencia2_telefono:
            tel_original = cliente.referencia2_telefono
            if not tel_original.startswith('3') or len(tel_original) != 10:
                if len(tel_original) > 10:
                    tel_corregido = tel_original[:10]
                else:
                    tel_corregido = tel_original.zfill(10)
                
                if not tel_corregido.startswith('3'):
                    tel_corregido = '3' + tel_corregido[1:]
                
                cliente.referencia2_telefono = tel_corregido
                cliente.save()
                print(f"   ✅ Cliente {cliente.id} Ref2: '{tel_original}' → '{tel_corregido}'")
                corregidos += 1
    
    print(f"📊 Referencias corregidas: {corregidos}")
    return corregidos

def verificar_correcciones():
    print("\\n🔍 VERIFICANDO CORRECCIONES")
    print("=" * 40)
    
    # Re-importar el script de validación
    import subprocess
    import sys
    
    result = subprocess.run([sys.executable, 'validar_datos_existentes.py'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        output_lines = result.stdout.split('\\n')
        for line in output_lines:
            if 'RESUMEN:' in line:
                print(f"📊 {line}")
                if '0 problemas encontrados' in line:
                    print("🎉 ¡PERFECTO! Todos los datos están corregidos")
                    return True
                else:
                    print("⚠️  Aún hay problemas pendientes")
                    return False
    
    print("❌ Error verificando correcciones")
    return False

if __name__ == "__main__":
    try:
        print("🔧 CORRECCIÓN AUTOMÁTICA DE DATOS")
        print("=" * 50)
        
        total_corregidos = 0
        total_corregidos += corregir_cedulas_clientes()
        total_corregidos += corregir_celulares_clientes()
        total_corregidos += corregir_referencias()
        
        print(f"\\n📊 TOTAL DE CAMPOS CORREGIDOS: {total_corregidos}")
        
        # Verificar que las correcciones funcionaron
        if verificar_correcciones():
            print("\\n✅ LISTO PARA MIGRAR")
            print("Ejecuta: python manage.py migrate")
        else:
            print("\\n❌ AÚN HAY PROBLEMAS")
            print("Ejecuta: python validar_datos_existentes.py")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()