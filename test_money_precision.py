#!/usr/bin/env python
"""
Script temporal para probar la precisión de montos en pesos colombianos
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_creditos.settings')
django.setup()

from decimal import Decimal
from main.models import Credito, CronogramaPago, TareaCobro, Pago

def test_money_conversion():
    """Test de conversión de montos colombianos"""
    
    print("=== Test de conversión de montos en pesos colombianos ===")
    
    # Montos típicos en pesos colombianos
    test_amounts = [
        "36470",      # El monto que está causando problema
        "36469.76",   # Con decimales
        "500000",     # Medio millón
        "1000000",    # Un millón
        "50000.50",   # Con decimales
        "368.38",     # El monto alterado que se guarda mal
    ]
    
    for amount_str in test_amounts:
        print(f"\n--- Testing: {amount_str} ---")
        
        # Conversión como string
        print(f"Original string: '{amount_str}'")
        
        # Conversión a float
        try:
            float_val = float(amount_str)
            print(f"float('{amount_str}') = {float_val}")
        except Exception as e:
            print(f"Error en float: {e}")
            continue
        
        # Conversión a Decimal via string (correcto)
        decimal_via_str = Decimal(str(float_val))
        print(f"Decimal(str({float_val})) = {decimal_via_str}")
        
        # Conversión directa a Decimal desde string (más preciso)
        decimal_direct = Decimal(amount_str)
        print(f"Decimal('{amount_str}') = {decimal_direct}")
        
        # Verificar si hay diferencia
        if decimal_via_str != decimal_direct:
            print(f"🚨 DIFERENCIA detectada:")
            print(f"  Via float: {decimal_via_str}")
            print(f"  Directo:   {decimal_direct}")
            print(f"  Diferencia: {decimal_direct - decimal_via_str}")
        else:
            print("✅ Ambos métodos dan el mismo resultado")

def test_real_data():
    """Test con datos reales de la base de datos"""
    print("\n\n=== Test con datos reales ===")
    
    # Buscar créditos recientes
    creditos = Credito.objects.filter(estado__in=['DESEMBOLSADO']).order_by('-id')[:5]
    
    for credito in creditos:
        print(f"\n--- Crédito #{credito.id} ---")
        print(f"Monto: ${credito.monto}")
        print(f"Cliente: {credito.cliente.nombre_completo}")
        
        # Buscar tareas de cobro
        tareas = TareaCobro.objects.filter(cuota__credito=credito)[:3]
        for tarea in tareas:
            print(f"  Tarea #{tarea.id}: Monto a cobrar=${tarea.monto_a_cobrar}, Cobrado=${tarea.monto_cobrado or 'N/A'}")
        
        # Buscar pagos
        pagos = Pago.objects.filter(credito=credito)[:3]
        for pago in pagos:
            print(f"  Pago #{pago.id}: ${pago.monto} - {pago.fecha_pago}")

if __name__ == "__main__":
    test_money_conversion()
    test_real_data()
    print("\n=== Fin de pruebas ===")