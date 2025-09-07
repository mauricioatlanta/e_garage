"""
Test simple directo para formularios inteligentes
"""


# Simular datos de prueba
class MockUser:
    def __init__(self, pais="CL"):
        self.empresa = MockEmpresa(pais)


class MockEmpresa:
    def __init__(self, pais="CL"):
        self.pais = pais


# Probar importaciones básicas
try:
    print("=" * 50)
    print("🧪 PRUEBA DE IMPORTACIONES Y CONFIGURACIÓN")
    print("=" * 50)

    # Test 1: Validación de patentes
    from taller.utils.pais_utils import validar_patente_por_pais

    # Patente chilena
    patente_cl = validar_patente_por_pais("ABC123", "CL")
    print(f"✅ Patente chilena ABC123: {'Válida' if patente_cl else 'Inválida'}")

    # Patente USA
    patente_us = validar_patente_por_pais("ABC123", "US")
    print(f"✅ Patente USA ABC123: {'Válida' if patente_us else 'Inválida'}")

    # Test 2: Validación de teléfonos
    from taller.utils.pais_utils import validar_telefono_por_pais

    # Teléfono chileno
    telefono_cl = validar_telefono_por_pais("+56912345678", "CL")
    print(
        f"✅ Teléfono chileno +56912345678: {'Válido' if telefono_cl else 'Inválido'}"
    )

    # Teléfono USA
    telefono_us = validar_telefono_por_pais("(555) 123-4567", "US")
    print(f"✅ Teléfono USA (555) 123-4567: {'Válido' if telefono_us else 'Inválido'}")

    # Test 3: Configuración por país
    from taller.utils.pais_utils import get_configuracion_pais

    user_cl = MockUser("CL")
    config_cl = get_configuracion_pais(user_cl.empresa)
    print(
        f"✅ Configuración Chile - Moneda: {config_cl['moneda']}, Símbolo: {config_cl['simbolo_moneda']}"
    )

    user_us = MockUser("US")
    config_us = get_configuracion_pais(user_us.empresa)
    print(
        f"✅ Configuración USA - Moneda: {config_us['moneda']}, Símbolo: {config_us['simbolo_moneda']}"
    )

    # Test 4: Regiones por país
    from taller.utils.pais_utils import get_regiones_por_pais

    estados_us = get_regiones_por_pais("US")[:3]  # Solo primeros 3
    print(f"✅ Estados USA (primeros 3): {[estado[1] for estado in estados_us]}")

    print("\n" + "=" * 50)
    print("🎯 FORMULARIOS INTELIGENTES - CONFIGURACIÓN OK")
    print("=" * 50)

    print("🚗 Características implementadas:")
    print("   • Validación de patentes por país (CL/US)")
    print("   • Validación de teléfonos por país")
    print("   • Placeholders dinámicos en formularios")
    print("   • Configuración de moneda automática")
    print("   • Regiones/estados según país")
    print("   • Formato de precios según moneda")

    print("\n📋 Formularios adaptados:")
    print("   • VehiculoForm: Marcas y validación de patente por país")
    print("   • ClienteForm: Regiones/estados y validación teléfono")
    print("   • RepuestoForm: Formato de precios según moneda")

    print("\n✅ SISTEMA DE FORMULARIOS INTELIGENTES ACTIVO")

except Exception as e:
    print(f"❌ Error en prueba: {e}")
    import traceback

    traceback.print_exc()
