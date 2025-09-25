#!/usr/bin/env python
"""
Script para probar la nueva validación de cédulas (5-10 dígitos)
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'creditos.settings')
django.setup()

from main.models import Cliente, Codeudor
from django.core.exceptions import ValidationError


def probar_cedulas():
    """
    Prueba diferentes casos de cédulas para validar la nueva regla
    """
    print("🧪 PROBANDO VALIDACIÓN DE CÉDULAS")
    print("=" * 50)
    
    # Casos de prueba
    casos_prueba = [
        # (cedula, descripcion, deberia_ser_valida)
        ("12345", "Cédula de 5 dígitos (mínimo)", True),
        ("123456", "Cédula de 6 dígitos", True),
        ("1234567", "Cédula de 7 dígitos", True),
        ("12345678", "Cédula de 8 dígitos", True),
        ("123456789", "Cédula de 9 dígitos", True),
        ("1234567890", "Cédula de 10 dígitos (máximo)", True),
        ("1234", "Cédula de 4 dígitos (muy corta)", False),
        ("12345678901", "Cédula de 11 dígitos (muy larga)", False),
        ("12345ABC", "Cédula con letras", False),
        ("", "Cédula vacía", False),
        ("00000", "Cédula con solo ceros", True),  # Técnicamente válida pero poco realista
    ]
    
    resultados_correctos = 0
    total_casos = len(casos_prueba)
    
    for cedula, descripcion, deberia_ser_valida in casos_prueba:
        print(f"\n📝 Probando: {descripcion}")
        print(f"   Cédula: '{cedula}'")
        print(f"   Debería ser válida: {'SÍ' if deberia_ser_valida else 'NO'}")
        
        try:
            # Crear un cliente temporal (sin guardarlo)
            cliente_temp = Cliente(
                nombres="Prueba",
                apellidos="Temporal",
                cedula=cedula,
                celular="3001234567",
                direccion="Calle Falsa 123",
                barrio="Barrio Prueba"
            )
            
            # Ejecutar validación completa
            cliente_temp.full_clean()
            
            # Si llegamos aquí, la validación fue exitosa
            if deberia_ser_valida:
                print("   ✅ CORRECTO: Cédula válida como esperado")
                resultados_correctos += 1
            else:
                print("   ❌ ERROR: Cédula debería ser inválida pero fue aceptada")
                
        except ValidationError as e:
            # Si hay error de validación
            if not deberia_ser_valida:
                print("   ✅ CORRECTO: Cédula inválida como esperado")
                print(f"   📄 Error: {e.message_dict.get('cedula', ['Error desconocido'])[0]}")
                resultados_correctos += 1
            else:
                print("   ❌ ERROR: Cédula debería ser válida pero fue rechazada")
                print(f"   📄 Error: {e.message_dict.get('cedula', ['Error desconocido'])[0]}")
        
        except Exception as e:
            print(f"   💥 ERROR INESPERADO: {str(e)}")
    
    # Resumen
    print(f"\n📊 RESUMEN DE PRUEBAS:")
    print("=" * 30)
    print(f"✅ Casos correctos: {resultados_correctos}/{total_casos}")
    print(f"❌ Casos fallidos: {total_casos - resultados_correctos}/{total_casos}")
    porcentaje = (resultados_correctos / total_casos) * 100
    print(f"📈 Porcentaje de éxito: {porcentaje:.1f}%")
    
    if resultados_correctos == total_casos:
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("La validación de cédulas de 5-10 dígitos está funcionando correctamente.")
    else:
        print(f"\n⚠️ Hay {total_casos - resultados_correctos} pruebas que fallaron.")
        print("Revisa la configuración de validación.")
    
    return resultados_correctos == total_casos


def probar_casos_reales():
    """
    Prueba casos reales típicos de Colombia
    """
    print(f"\n🇨🇴 PROBANDO CASOS REALES DE COLOMBIA")
    print("=" * 40)
    
    casos_colombia = [
        ("16789", "Cédula antigua de 5 dígitos"),
        ("234567", "Cédula de 6 dígitos"),
        ("1234567", "Cédula de 7 dígitos típica"),
        ("12345678", "Cédula de 8 dígitos común"),
        ("123456789", "Cédula de 9 dígitos moderna"),
        ("1020345678", "Cédula de 10 dígitos nueva"),
    ]
    
    print("Estos son ejemplos típicos de cédulas colombianas:")
    for cedula, descripcion in casos_colombia:
        try:
            cliente_temp = Cliente(
                nombres="Prueba",
                apellidos="Colombia",
                cedula=cedula,
                celular="3001234567",
                direccion="Calle Real 456",
                barrio="Barrio Colombia"
            )
            cliente_temp.full_clean()
            print(f"   ✅ {descripcion}: {cedula} - VÁLIDA")
        except ValidationError as e:
            print(f"   ❌ {descripcion}: {cedula} - INVÁLIDA")
            error_msg = e.message_dict.get('cedula', ['Error desconocido'])[0]
            print(f"      Error: {error_msg}")


if __name__ == '__main__':
    try:
        exito = probar_cedulas()
        probar_casos_reales()
        
        if exito:
            print(f"\n✨ CONCLUSIÓN:")
            print("El sistema ahora acepta cédulas colombianas desde 5 dígitos.")
            print("¡Listo para usar en producción!")
        
    except Exception as e:
        print(f"\n💥 Error ejecutando pruebas: {str(e)}")
        sys.exit(1)