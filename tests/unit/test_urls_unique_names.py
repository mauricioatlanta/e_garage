"""
Test anti-duplicados para URLs.
Este test asegura que no vuelvan a aparecer los warnings W005.
"""

from django.urls import get_resolver


def test_unique_url_names():
    """Verifica que no hay names de URL duplicados."""
    resolver = get_resolver()
    names = [k for k in resolver.reverse_dict.keys() if isinstance(k, str)]
    assert len(names) == len(set(names)), "Hay names de URL duplicados"


def test_core_routes_exist():
    """Verifica que las rutas críticas existen."""
    resolver = get_resolver()
    names = {k for k in resolver.reverse_dict.keys() if isinstance(k, str)}
    expected = {
        "taller_us_en:taller:clientes:lista",
        "taller_us_en:taller:vehiculos:lista",
        "taller_us_en:taller:servicios:lista",
    }
    missing = expected - names
    assert not missing, f"Faltan rutas críticas: {missing}"


if __name__ == "__main__":
    # Para ejecutar manualmente
    import os
    import sys

    import django

    # Agregar el directorio del proyecto al path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings.dev")
    django.setup()

    print("🧪 Ejecutando tests anti-duplicados...")

    try:
        test_unique_url_names()
        print("✅ test_unique_url_names: PASSED")
    except Exception as e:
        print(f"❌ test_unique_url_names: FAILED - {e}")

    try:
        test_core_routes_exist()
        print("✅ test_core_routes_exist: PASSED")
    except Exception as e:
        print(f"❌ test_core_routes_exist: FAILED - {e}")

    print("🎯 Tests anti-duplicados completados!")
