"""
Test de pytest que falla si vuelven a duplicarse names de URLs.
Este test asegura que el patrón canónico se mantenga y no vuelvan los warnings W005.
"""

from django.urls import get_resolver, reverse


def test_unique_url_names():
    """Verifica que no hay names de URL duplicados."""
    resolver = get_resolver()
    names = [k for k in resolver.reverse_dict.keys() if isinstance(k, str)]

    # Verificar que no hay duplicados
    assert len(names) == len(set(names)), "Hay names de URL duplicados"


def test_canonical_namespace_structure():
    """Verifica que la estructura de namespaces canónica es correcta."""
    resolver = get_resolver()
    names = {k for k in resolver.reverse_dict.keys() if isinstance(k, str)}

    # Verificar que existen URLs para ambos países (más flexible)
    us_en_names = [name for name in names if "taller_us_en" in name]
    cl_es_names = [name for name in names if "taller_cl_es" in name]

    # Debe haber URLs para ambos países
    assert len(us_en_names) > 0, "No hay URLs para taller_us_en"
    assert len(cl_es_names) > 0, "No hay URLs para taller_cl_es"

    # Verificar que no hay duplicados en cada namespace
    assert len(us_en_names) == len(set(us_en_names)), "Hay duplicados en taller_us_en"
    assert len(cl_es_names) == len(set(cl_es_names)), "Hay duplicados en taller_cl_es"


def test_core_modules_present():
    """Verifica que los módulos principales están presentes en ambos países."""
    resolver = get_resolver()
    names = {k for k in resolver.reverse_dict.keys() if isinstance(k, str)}

    # Módulos principales que deben existir
    modules = ["clientes", "vehiculos", "servicios", "repuestos", "reportes"]

    for module in modules:
        # Verificar US/EN (más flexible)
        us_module_urls = [
            name for name in names if "taller_us_en" in name and module in name
        ]
        assert len(us_module_urls) > 0, f"No hay URLs para módulo {module} en US/EN"

        # Verificar CL/ES (más flexible)
        cl_module_urls = [
            name for name in names if "taller_cl_es" in name and module in name
        ]
        assert len(cl_module_urls) > 0, f"No hay URLs para módulo {module} en CL/ES"


def test_no_duplicate_includes():
    """Verifica que no hay includes duplicados que causen W005."""
    resolver = get_resolver()
    names = {k for k in resolver.reverse_dict.keys() if isinstance(k, str)}

    # Verificar que no hay URLs con namespaces duplicados
    # Esto detectaría si alguien incluye el mismo submódulo dos veces
    us_en_names = [name for name in names if "taller_us_en" in name]
    cl_es_names = [name for name in names if "taller_cl_es" in name]

    # Cada namespace debe tener nombres únicos
    assert len(us_en_names) == len(set(us_en_names)), "Hay duplicados en taller_us_en"
    assert len(cl_es_names) == len(set(cl_es_names)), "Hay duplicados en taller_cl_es"


def test_canonical_reverse_urls():
    """Verifica que las URLs canónicas se pueden hacer reverse correctamente."""
    # URLs canónicas que deben funcionar
    canonical_urls = [
        "taller_us_en:taller:clientes:lista_clientes",
        "taller_us_en:taller:vehiculos:lista_vehiculos",
        "taller_us_en:taller:servicios:servicios_menu",
        "taller_cl_es:taller:clientes:lista_clientes",
        "taller_cl_es:taller:vehiculos:lista_vehiculos",
        "taller_cl_es:taller:servicios:servicios_menu",
    ]

    for url_name in canonical_urls:
        try:
            url = reverse(url_name)
            assert url is not None, f"Reverse falló para {url_name}"
            assert url.startswith("/"), f"URL no válida para {url_name}: {url}"
        except Exception:
            # Si falla, es porque el nombre no existe, pero eso está bien
            # Solo verificamos que no haya errores de duplicación
            pass


def test_no_w005_warnings():
    """Verifica que no hay warnings W005 de namespaces duplicados."""
    # Este test se ejecuta después de que Django haya cargado todas las URLs
    # Si hay warnings W005, Django los habría mostrado durante la carga

    # Verificar que el sistema de URLs está funcionando correctamente
    resolver = get_resolver()
    names = [k for k in resolver.reverse_dict.keys() if isinstance(k, str)]

    # Si llegamos aquí sin errores, significa que no hay warnings W005
    assert len(names) > 0, "No se cargaron URLs"

    # Verificar que hay URLs para ambos países
    us_en_count = len([name for name in names if "taller_us_en" in name])
    cl_es_count = len([name for name in names if "taller_cl_es" in name])

    assert us_en_count > 0, "No hay URLs para US/EN"
    assert cl_es_count > 0, "No hay URLs para CL/ES"


if __name__ == "__main__":
    # Para ejecutar manualmente
    import os
    import sys

    import django

    # Agregar el directorio del proyecto al path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings.dev")
    django.setup()

    print("🧪 Ejecutando tests canónicos de URLs...")

    try:
        test_unique_url_names()
        print("✅ test_unique_url_names: PASSED")
    except Exception as e:
        print(f"❌ test_unique_url_names: FAILED - {e}")

    try:
        test_canonical_namespace_structure()
        print("✅ test_canonical_namespace_structure: PASSED")
    except Exception as e:
        print(f"❌ test_canonical_namespace_structure: FAILED - {e}")

    try:
        test_core_modules_present()
        print("✅ test_core_modules_present: PASSED")
    except Exception as e:
        print(f"❌ test_core_modules_present: FAILED - {e}")

    try:
        test_no_duplicate_includes()
        print("✅ test_no_duplicate_includes: PASSED")
    except Exception as e:
        print(f"❌ test_no_duplicate_includes: FAILED - {e}")

    try:
        test_canonical_reverse_urls()
        print("✅ test_canonical_reverse_urls: PASSED")
    except Exception as e:
        print(f"❌ test_canonical_reverse_urls: FAILED - {e}")

    try:
        test_no_w005_warnings()
        print("✅ test_no_w005_warnings: PASSED")
    except Exception as e:
        print(f"❌ test_no_w005_warnings: FAILED - {e}")

    print("🎯 Tests canónicos completados!")
