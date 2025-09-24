#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'creditos.settings')
django.setup()

from main.models import Cliente, Credito, Pago

def verificar_registros():
    print("=== VERIFICACIÓN DE REGISTROS PARA PAGINACIÓN ===")
    
    # Clientes
    total_clientes = Cliente.objects.filter(activo=True).count()
    print(f"🔵 Clientes activos: {total_clientes} (Paginación: 20 por página)")
    if total_clientes > 20:
        print("   ✅ Debería mostrar paginación")
    else:
        print("   ❌ NO mostrará paginación (menos de 20 registros)")
    
    # Créditos  
    total_creditos = Credito.objects.count()
    print(f"🔵 Créditos totales: {total_creditos} (Paginación: 15 por página)")
    if total_creditos > 15:
        print("   ✅ Debería mostrar paginación")
    else:
        print("   ❌ NO mostrará paginación (menos de 15 registros)")
    
    # Pagos
    total_pagos = Pago.objects.count()
    print(f"🔵 Pagos totales: {total_pagos} (Paginación: 25 por página)")
    if total_pagos > 25:
        print("   ✅ Debería mostrar paginación")
    else:
        print("   ❌ NO mostrará paginación (menos de 25 registros)")

def crear_registros_prueba():
    print("\n=== CREANDO REGISTROS DE PRUEBA ===")
    
    # Crear clientes de prueba si hay pocos
    total_clientes = Cliente.objects.filter(activo=True).count()
    if total_clientes < 25:
        print(f"Creando clientes de prueba...")
        for i in range(25 - total_clientes):
            Cliente.objects.create(
                nombres=f"Cliente Prueba {i+1}",
                apellidos="Apellido Prueba", 
                cedula=f"1000000{i+1:03d}",
                celular=f"300123456{i%10}",
                direccion=f"Dirección de prueba {i+1}",
                barrio=f"Barrio {i+1}",
                activo=True
            )
        print(f"   ✅ Creados {25 - total_clientes} clientes de prueba")
    
    # Crear pagos de prueba si hay pocos
    total_pagos = Pago.objects.count()
    if total_pagos < 30:
        # Necesitamos un crédito para crear pagos
        credito = Credito.objects.first()
        if credito:
            print(f"Creando pagos de prueba...")
            from decimal import Decimal
            for i in range(30 - total_pagos):
                Pago.objects.create(
                    credito=credito,
                    monto=Decimal('50000'),
                    numero_cuota=i+1,
                    observaciones=f"Pago de prueba {i+1}"
                )
            print(f"   ✅ Creados {30 - total_pagos} pagos de prueba")
    
    print("\n=== VERIFICACIÓN POST-CREACIÓN ===")
    verificar_registros()

if __name__ == "__main__":
    verificar_registros()
    
    respuesta = input("\n¿Crear registros de prueba para testear paginación? (s/n): ")
    if respuesta.lower() == 's':
        crear_registros_prueba()
    else:
        print("No se crearon registros de prueba.")