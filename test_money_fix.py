#!/usr/bin/env python
"""
Script de prueba para verificar el funcionamiento correcto del manejo de montos
"""
from decimal import Decimal, InvalidOperation

def test_money_cleanup():
    """Prueba la función de limpieza y conversión de montos"""
    
    print("=== Pruebas de limpieza y conversión de montos ===")
    
    # Casos de prueba
    test_cases = [
        # (input, expected_output, should_pass)
        ("36470", Decimal("36470"), True),
        ("36,470", Decimal("36470"), True),
        ("36 470", Decimal("36470"), True),
        ("  36470  ", Decimal("36470"), True),
        ("36470.50", Decimal("36470.50"), True),
        ("36,470.50", Decimal("36470.50"), True),
        ("368.38", Decimal("368.38"), True),  # Ahora permitido (era el monto problemático)
        ("49", Decimal("49"), False),  # Muy bajo
        ("50000001", Decimal("50000001"), False),  # Muy alto
        ("abc", None, False),  # No numérico
        ("", None, False),  # Vacío
        ("36470,50", None, False),  # Formato incorrecto (coma decimal)
    ]
    
    def clean_and_validate_amount(amount_str):
        """Simula la lógica de limpieza y validación implementada"""
        try:
            # Limpiar el monto
            if not amount_str or not str(amount_str).strip():
                raise ValueError("Monto vacío")
            
            # Limpiar el monto de forma inteligente
            monto_str = str(amount_str).strip()
            
            # Verificar formato europeo (coma decimal)
            if ',' in monto_str:
                parts_comma = monto_str.split(',')
                if len(parts_comma) == 2 and len(parts_comma[1]) <= 2 and '.' not in parts_comma[1]:
                    raise ValueError(f"Use punto (.) como separador decimal. Ejemplo: {monto_str.replace(',', '.')}")
            
            # Limpiar comas de miles pero conservar punto decimal
            monto_limpio = monto_str.replace(' ', '')
            if ',' in monto_limpio:
                if '.' in monto_limpio:
                    parte_entera, parte_decimal = monto_limpio.split('.', 1)
                    parte_entera = parte_entera.replace(',', '')
                    monto_limpio = f"{parte_entera}.{parte_decimal}"
                else:
                    if not monto_limpio.endswith(',') and len(monto_limpio.split(',')[-1]) >= 3:
                        monto_limpio = monto_limpio.replace(',', '')
            
            monto_decimal = Decimal(monto_limpio)
            
            # Validaciones de rango para pesos colombianos
            if monto_decimal <= Decimal('0'):
                raise ValueError("El monto debe ser mayor que cero")
            
            # Permitir desde $50 para casos excepcionales
            if monto_decimal < Decimal('50'):
                raise ValueError(f"El monto ${monto_decimal} parece muy bajo para un pago en pesos colombianos.")
            
            if monto_decimal > Decimal('50000000'):
                raise ValueError(f"El monto ${monto_decimal} parece muy alto. Verifique el valor.")
            
            return monto_decimal
            
        except (ValueError, InvalidOperation) as e:
            raise ValueError(f"Monto inválido: {amount_str}. {str(e)}")
    
    passed = 0
    total = len(test_cases)
    
    for i, (input_value, expected, should_pass) in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: '{input_value}' ---")
        
        try:
            result = clean_and_validate_amount(input_value)
            if should_pass:
                if result == expected:
                    print(f"✅ PASS - Resultado: {result}")
                    passed += 1
                else:
                    print(f"❌ FAIL - Esperado: {expected}, Obtenido: {result}")
            else:
                print(f"❌ FAIL - Debería haber fallado pero pasó con: {result}")
        except ValueError as e:
            if not should_pass:
                print(f"✅ PASS - Falló correctamente: {e}")
                passed += 1
            else:
                print(f"❌ FAIL - Debería haber pasado pero falló: {e}")
        except Exception as e:
            print(f"❌ ERROR - Error inesperado: {e}")
    
    print(f"\n=== Resumen ===")
    print(f"Pasaron: {passed}/{total}")
    print(f"Porcentaje: {(passed/total)*100:.1f}%")
    
    return passed == total

def test_decimal_precision():
    """Prueba que los Decimal mantengan precisión"""
    print("\n=== Prueba de precisión decimal ===")
    
    test_values = ["36470", "36469.76", "500000.99", "1234567.89"]
    
    for value in test_values:
        print(f"\n--- Probando: {value} ---")
        
        # Método antiguo (problemático)
        float_val = float(value)
        decimal_via_float = Decimal(str(float_val))
        
        # Método nuevo (correcto)
        decimal_direct = Decimal(value)
        
        print(f"Via float: {decimal_via_float}")
        print(f"Directo:   {decimal_direct}")
        
        if decimal_via_float == decimal_direct:
            print("✅ Sin pérdida de precisión")
        else:
            print(f"🚨 PÉRDIDA DE PRECISIÓN: {decimal_direct - decimal_via_float}")

if __name__ == "__main__":
    success = test_money_cleanup()
    test_decimal_precision()
    
    if success:
        print("\n🎉 ¡Todas las pruebas pasaron! El manejo de montos funciona correctamente.")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisar el código.")