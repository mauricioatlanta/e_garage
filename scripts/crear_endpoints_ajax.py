#!/usr/bin/env python3
"""
Script para crear endpoints AJAX básicos para el formulario de vehículos
"""

from pathlib import Path

# Configuración
BASE_DIR = Path(r"e:\projecto\e_garage")


def create_ajax_views():
    """Crear archivo con vistas AJAX para vehículos"""

    ajax_views_content = '''from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
@require_http_methods(["GET"])
def ajax_marcas(request):
    """Endpoint AJAX para obtener marcas de vehículos"""
    try:
        # Marcas predefinidas - en el futuro se puede obtener de BD
        marcas = [
            {'id': 'Toyota', 'nombre': 'Toyota'},
            {'id': 'Ford', 'nombre': 'Ford'},
            {'id': 'Chevrolet', 'nombre': 'Chevrolet'},
            {'id': 'Hyundai', 'nombre': 'Hyundai'},
            {'id': 'Nissan', 'nombre': 'Nissan'},
            {'id': 'Volkswagen', 'nombre': 'Volkswagen'},
            {'id': 'Honda', 'nombre': 'Honda'},
            {'id': 'Mazda', 'nombre': 'Mazda'},
            {'id': 'Suzuki', 'nombre': 'Suzuki'},
            {'id': 'Renault', 'nombre': 'Renault'},
            {'id': 'Peugeot', 'nombre': 'Peugeot'},
            {'id': 'Citroën', 'nombre': 'Citroën'},
            {'id': 'BMW', 'nombre': 'BMW'},
            {'id': 'Mercedes-Benz', 'nombre': 'Mercedes-Benz'},
            {'id': 'Audi', 'nombre': 'Audi'},
            {'id': 'Kia', 'nombre': 'Kia'},
            {'id': 'Mitsubishi', 'nombre': 'Mitsubishi'},
            {'id': 'Subaru', 'nombre': 'Subaru'},
            {'id': 'Jeep', 'nombre': 'Jeep'},
            {'id': 'Land Rover', 'nombre': 'Land Rover'},
        ]

        return JsonResponse({
            'success': True,
            'marcas': marcas
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def ajax_modelos(request):
    """Endpoint AJAX para obtener modelos según marca"""
    try:
        marca_id = request.GET.get('marca_id', '')

        # Modelos predefinidos por marca
        modelos_por_marca = {
            'Toyota': [
                {'id': 'Corolla', 'nombre': 'Corolla'},
                {'id': 'Yaris', 'nombre': 'Yaris'},
                {'id': 'Hilux', 'nombre': 'Hilux'},
                {'id': 'RAV4', 'nombre': 'RAV4'},
                {'id': 'Camry', 'nombre': 'Camry'},
                {'id': 'Prius', 'nombre': 'Prius'},
                {'id': 'Land Cruiser', 'nombre': 'Land Cruiser'},
            ],
            'Ford': [
                {'id': 'Fiesta', 'nombre': 'Fiesta'},
                {'id': 'Focus', 'nombre': 'Focus'},
                {'id': 'Ranger', 'nombre': 'Ranger'},
                {'id': 'EcoSport', 'nombre': 'EcoSport'},
                {'id': 'Escape', 'nombre': 'Escape'},
                {'id': 'Mustang', 'nombre': 'Mustang'},
                {'id': 'F-150', 'nombre': 'F-150'},
            ],
            'Chevrolet': [
                {'id': 'Spark', 'nombre': 'Spark'},
                {'id': 'Sail', 'nombre': 'Sail'},
                {'id': 'Cruze', 'nombre': 'Cruze'},
                {'id': 'Captiva', 'nombre': 'Captiva'},
                {'id': 'Camaro', 'nombre': 'Camaro'},
                {'id': 'Silverado', 'nombre': 'Silverado'},
            ],
            'Hyundai': [
                {'id': 'Accent', 'nombre': 'Accent'},
                {'id': 'Elantra', 'nombre': 'Elantra'},
                {'id': 'Tucson', 'nombre': 'Tucson'},
                {'id': 'Santa Fe', 'nombre': 'Santa Fe'},
                {'id': 'i10', 'nombre': 'i10'},
                {'id': 'i30', 'nombre': 'i30'},
            ],
            'Nissan': [
                {'id': 'March', 'nombre': 'March'},
                {'id': 'Versa', 'nombre': 'Versa'},
                {'id': 'Sentra', 'nombre': 'Sentra'},
                {'id': 'X-Trail', 'nombre': 'X-Trail'},
                {'id': 'Altima', 'nombre': 'Altima'},
                {'id': 'Frontier', 'nombre': 'Frontier'},
            ],
        }

        modelos = modelos_por_marca.get(marca_id, [])

        return JsonResponse({
            'success': True,
            'modelos': modelos
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def ajax_motores(request):
    """Endpoint AJAX para obtener tipos de motor"""
    try:
        motores = [
            {'id': '1.0L', 'nombre': '1.0L'},
            {'id': '1.2L', 'nombre': '1.2L'},
            {'id': '1.4L', 'nombre': '1.4L'},
            {'id': '1.6L', 'nombre': '1.6L'},
            {'id': '1.8L', 'nombre': '1.8L'},
            {'id': '2.0L', 'nombre': '2.0L'},
            {'id': '2.4L', 'nombre': '2.4L'},
            {'id': '2.5L', 'nombre': '2.5L'},
            {'id': '3.0L V6', 'nombre': '3.0L V6'},
            {'id': '3.5L V6', 'nombre': '3.5L V6'},
            {'id': '4.0L V6', 'nombre': '4.0L V6'},
            {'id': '5.0L V8', 'nombre': '5.0L V8'},
            {'id': '1.6L Turbo', 'nombre': '1.6L Turbo'},
            {'id': '2.0L Turbo', 'nombre': '2.0L Turbo'},
            {'id': 'Híbrido', 'nombre': 'Híbrido'},
            {'id': 'Eléctrico', 'nombre': 'Eléctrico'},
            {'id': 'Diesel 2.0L', 'nombre': 'Diesel 2.0L'},
            {'id': 'Diesel 2.5L', 'nombre': 'Diesel 2.5L'},
        ]

        return JsonResponse({
            'success': True,
            'motores': motores
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def ajax_cajas(request):
    """Endpoint AJAX para obtener tipos de caja de cambios"""
    try:
        cajas = [
            {'id': 'Manual 5 velocidades', 'nombre': 'Manual 5 velocidades'},
            {'id': 'Manual 6 velocidades', 'nombre': 'Manual 6 velocidades'},
            {'id': 'Automática 4 velocidades', 'nombre': 'Automática 4 velocidades'},
            {'id': 'Automática 5 velocidades', 'nombre': 'Automática 5 velocidades'},
            {'id': 'Automática 6 velocidades', 'nombre': 'Automática 6 velocidades'},
            {'id': 'Automática 8 velocidades', 'nombre': 'Automática 8 velocidades'},
            {'id': 'Automática CVT', 'nombre': 'Automática CVT'},
            {'id': 'Secuencial', 'nombre': 'Secuencial'},
            {'id': 'Tiptronic', 'nombre': 'Tiptronic'},
            {'id': 'DSG', 'nombre': 'DSG'},
            {'id': 'PDK', 'nombre': 'PDK'},
        ]

        return JsonResponse({
            'success': True,
            'cajas': cajas
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
'''

    # Crear archivo
    ajax_views_file = BASE_DIR / "taller" / "ajax_views.py"
    ajax_views_file.write_text(ajax_views_content, encoding="utf-8")
    print(f"✅ Creado: {ajax_views_file}")

    return True


def create_ajax_urls():
    """Crear archivo con URLs para AJAX"""

    ajax_urls_content = """from django.urls import path
from . import ajax_views

app_name = 'vehiculos_ajax'

urlpatterns = [
    path('marcas/', ajax_views.ajax_marcas, name='ajax_marcas'),
    path('modelos/', ajax_views.ajax_modelos, name='ajax_modelos'),
    path('motores/', ajax_views.ajax_motores, name='ajax_motores'),
    path('cajas/', ajax_views.ajax_cajas, name='ajax_cajas'),
]
"""

    # Crear archivo
    ajax_urls_file = BASE_DIR / "taller" / "ajax_urls.py"
    ajax_urls_file.write_text(ajax_urls_content, encoding="utf-8")
    print(f"✅ Creado: {ajax_urls_file}")

    return True


def update_main_urls():
    """Actualizar URLs principales para incluir AJAX"""

    main_urls_file = BASE_DIR / "taller" / "urls.py"

    if not main_urls_file.exists():
        print(f"⚠️  No se encontró {main_urls_file}")
        return False

    # Leer contenido actual
    content = main_urls_file.read_text(encoding="utf-8")

    # Verificar si ya están las URLs AJAX
    if "ajax_urls" in content:
        print("✅ URLs AJAX ya están configuradas")
        return True

    # Agregar import y URL pattern
    if "from django.urls import path, include" not in content:
        content = content.replace(
            "from django.urls import path", "from django.urls import path, include"
        )

    # Buscar el final de urlpatterns y agregar antes del ]
    if "urlpatterns = [" in content:
        # Encontrar la posición del último ]
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.strip() == "]" and "urlpatterns" in "".join(lines[:i]):
                # Insertar la nueva URL antes del ]
                lines.insert(i, "    path('vehiculos/ajax/', include('taller.ajax_urls')),")
                break

        content = "\n".join(lines)
        main_urls_file.write_text(content, encoding="utf-8")
        print(f"✅ Actualizado: {main_urls_file}")
        return True

    return False


def generate_report():
    """Generar reporte de endpoints creados"""
    print("\n" + "=" * 70)
    print("📊 REPORTE - ENDPOINTS AJAX PARA VEHÍCULOS")
    print("=" * 70)

    endpoints = [
        "🚗 /taller/vehiculos/ajax/marcas/ - Lista de marcas",
        "🔄 /taller/vehiculos/ajax/modelos/ - Modelos por marca",
        "⚙️  /taller/vehiculos/ajax/motores/ - Tipos de motor",
        "🔧 /taller/vehiculos/ajax/cajas/ - Tipos de caja",
    ]

    print("✨ ENDPOINTS CREADOS:")
    for endpoint in endpoints:
        print(f"   {endpoint}")

    files_created = [
        "📄 taller/ajax_views.py - Vistas AJAX",
        "🔗 taller/ajax_urls.py - URLs AJAX",
    ]

    print("\n📁 ARCHIVOS CREADOS:")
    for file_info in files_created:
        print(f"   {file_info}")

    print("\n🧪 DATOS DE PRUEBA INCLUIDOS:")
    print("   - 20 marcas populares")
    print("   - 6-7 modelos por marca principal")
    print("   - 18 tipos de motor (incluyendo híbridos)")
    print("   - 11 tipos de caja de cambios")

    print("\n🚀 USO EN JAVASCRIPT:")
    print("   fetch('/taller/vehiculos/ajax/marcas/')")
    print("   fetch('/taller/vehiculos/ajax/modelos/?marca_id=Toyota')")
    print("   fetch('/taller/vehiculos/ajax/motores/')")
    print("   fetch('/taller/vehiculos/ajax/cajas/')")

    print("=" * 70)


def main():
    """Función principal"""
    print("🚀 Creando endpoints AJAX para formulario de vehículos...")
    print("-" * 60)

    success_count = 0

    # Crear vistas AJAX
    if create_ajax_views():
        success_count += 1

    # Crear URLs AJAX
    if create_ajax_urls():
        success_count += 1

    # Actualizar URLs principales
    if update_main_urls():
        success_count += 1

    # Generar reporte
    generate_report()

    if success_count >= 2:
        print("\n🎉 ¡Endpoints AJAX creados exitosamente!")
        print("💡 Reinicia el servidor Django para aplicar los cambios")
        return True
    else:
        print("\n⚠️  Creación parcial de endpoints")
        return False


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Error: {str(e)}")
        import traceback

        traceback.print_exc()
        exit(1)
