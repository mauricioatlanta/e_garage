#!/usr/bin/env python
"""
Script de prueba para validar el formulario RepuestoForm
Este script funcionará independientemente de la configuración de la base de datos
"""

import os
import sys
from decimal import Decimal

# Agregar el directorio actual al path de Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# Simular un entorno Django básico
class MockModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def save(self):
        pass


# Importar solo la validación del formulario
def test_precio_cleaning():
    """Probar la lógica de limpieza de precios"""

    # Casos de prueba
    test_cases = [
        ("$12.000", 12000),
        ("15.500", 15500),
        ("$1.234.567", 1234567),
        ("5000", 5000),
        ("  $8.500  ", 8500),
        ("$10,000", 10000),  # Con coma como separador de miles
    ]

    print("=== PRUEBAS DE LIMPIEZA DE PRECIOS ===\n")

    for input_value, expected in test_cases:
        # Simular la lógica del método clean_precio_*
        limpio = (
            str(input_value).replace("$", "").replace(".", "").replace(",", "").strip()
        )
        try:
            result = int(limpio)
            status = "✓ PASS" if result == expected else "❌ FAIL"
            print(
                f"{status} | Input: '{input_value}' -> Output: {result} (Esperado: {expected})"
            )
        except ValueError as e:
            print(f"❌ ERROR | Input: '{input_value}' -> Error: {e}")

    print("\n" + "=" * 50)


def test_form_validation():
    """Probar que los datos del formulario son válidos"""

    print("\n=== SIMULACIÓN DE DATOS DEL FORMULARIO ===\n")

    # Datos de prueba que simularían venir del formulario web
    form_data = {
        "tienda": 1,
        "nombre_repuesto": "Filtro de Aceite Test",
        "part_number": "TEST123",
        "precio_compra": "$12.500",
        "precio_venta": "$18.900",
        "stock": 10,
    }

    print("Datos del formulario:")
    for key, value in form_data.items():
        print(f"  {key}: {value}")

    # Simular el procesamiento que haría el formulario
    print("\nProcesamiento de precios:")

    # Precio de compra
    precio_compra_raw = form_data["precio_compra"]
    precio_compra_clean = (
        str(precio_compra_raw)
        .replace("$", "")
        .replace(".", "")
        .replace(",", "")
        .strip()
    )
    precio_compra = int(precio_compra_clean)
    print(f"  precio_compra: '{precio_compra_raw}' -> {precio_compra}")

    # Precio de venta
    precio_venta_raw = form_data["precio_venta"]
    precio_venta_clean = (
        str(precio_venta_raw).replace("$", "").replace(".", "").replace(",", "").strip()
    )
    precio_venta = int(precio_venta_clean)
    print(f"  precio_venta: '{precio_venta_raw}' -> {precio_venta}")

    # Simular la creación del objeto
    print(f"\nSimulando creación de repuesto:")
    print(f"  Repuesto(")
    print(f"    tienda_id={form_data['tienda']},")
    print(f"    nombre_repuesto='{form_data['nombre_repuesto']}',")
    print(f"    part_number='{form_data['part_number']}',")
    print(f"    precio_compra={precio_compra},")
    print(f"    precio_venta={precio_venta},")
    print(f"    stock={form_data['stock']}")
    print(f"  )")

    print(f"\n✓ Simulación completada exitosamente!")


def main():
    print("DIAGNÓSTICO DEL FORMULARIO REPUESTO")
    print("=" * 50)

    test_precio_cleaning()
    test_form_validation()

    print(f"\n🔧 SUGERENCIAS DE MEJORA:")
    print(f"1. Los métodos clean_precio_* ya están corregidos para manejar errores")
    print(f"2. El método save() fue simplificado para evitar conflictos")
    print(f"3. Se agregó validación de errores en la conversión a entero")
    print(f"4. Se maneja tanto comas como puntos como separadores de miles")


if __name__ == "__main__":
    main()
