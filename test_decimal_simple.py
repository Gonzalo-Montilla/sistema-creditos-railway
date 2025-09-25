#!/usr/bin/env python
"""
Test simple de conversión de decimales sin Django
"""
from decimal import Decimal

def test_money_conversion():
    """Test de conversión de montos colombianos"""
    
    print("=== Test de conversión de montos en pesos colombianos ===")
    
    # El caso específico que está causando problema
    test_amounts = [
        "36470",      # El monto que debería guardarse
        "36469.76",   # Con decimales precisos
        "368.38",     # El monto alterado que se está guardando mal
    ]
    
    for amount_str in test_amounts:
        print(f"\n--- Testing: {amount_str} ---")
        
        # Conversión como string
        print(f"Original string: '{amount_str}'")
        
        # Conversión a float (esto puede perder precisión)
        try:
            float_val = float(amount_str)
            print(f"float('{amount_str}') = {float_val}")
        except Exception as e:
            print(f"Error en float: {e}")
            continue
        
        # Conversión a Decimal via string después de float (método actual en el código)
        decimal_via_str = Decimal(str(float_val))
        print(f"Decimal(str({float_val})) = {decimal_via_str}")
        
        # Conversión directa a Decimal desde string (método correcto)
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
    
    print("\n=== Caso específico: 36470 vs 368.38 ===")
    # Simular lo que podría estar pasando
    original = "36470"
    problem = "368.38"
    
    print(f"Monto original: {original}")
    print(f"Monto problemático: {problem}")
    
    # ¿Podría ser un problema de división por 100?
    division_test = float(original) / 100
    print(f"{original} / 100 = {division_test}")
    
    # ¿O multiplicación?
    multiply_test = float(problem) * 100
    print(f"{problem} * 100 = {multiply_test}")

if __name__ == "__main__":
    test_money_conversion()
    print("\n=== Fin de pruebas ===")