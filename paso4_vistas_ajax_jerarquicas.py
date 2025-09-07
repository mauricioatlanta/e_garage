#!/usr/bin/env python3
"""
🎯 PASO 4B: Implementar vistas AJAX para dependencia jerárquica
Marca → Modelo → Motor/Caja

Este script crea las vistas AJAX necesarias para el formulario jerárquico de vehículos.
"""

import os
import sys

import django

# Configurar Django
sys.path.append("c:/projecto/projecto_1/e_garage")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taller.settings")

try:
    django.setup()
except Exception as e:
    print(f"Error configurando Django: {e}")
    sys.exit(1)





def crear_vista_ajax_modelos():
    """Crear vista AJAX para cargar modelos por marca"""
    vista_content = '''
@require_GET
def load_modelos(request):
    """
    Vista AJAX para cargar modelos filtrados por marca
    """
    marca_id = request.GET.get('marca_id')
    
    if not marca_id:
        return JsonResponse({'modelos': []})
    
    try:
        marca = get_object_or_404(Marca, id=marca_id)
        modelos = Modelo.objects.filter(marca=marca).order_by('nombre')
        
        modelos_data = [
            {
                'id': modelo.id,
                'nombre': modelo.nombre,
                'pais': modelo.pais
            }
            for modelo in modelos
        ]
        
        return JsonResponse({
            'modelos': modelos_data,
            'marca': marca.nombre
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'modelos': []
        }, status=400)
'''
    return vista_content


def crear_vista_ajax_motores():
    """Crear vista AJAX para cargar motores por modelo"""
    vista_content = '''
@require_GET  
def load_motores(request):
    """
    Vista AJAX para cargar motores filtrados por modelo
    """
    modelo_id = request.GET.get('modelo_id')
    
    if not modelo_id:
        return JsonResponse({'motores': []})
    
    try:
        modelo = get_object_or_404(Modelo, id=modelo_id)
        motores = MotorVehiculo.objects.filter(modelo=modelo).order_by('cilindrada', 'nombre')
        
        motores_data = [
            {
                'id': motor.id,
                'nombre': motor.nombre,
                'cilindrada': motor.cilindrada,
                'tipo': motor.tipo,
                'display': f"{motor.cilindrada} {motor.tipo} - {motor.nombre}"
            }
            for motor in motores
        ]
        
        return JsonResponse({
            'motores': motores_data,
            'modelo': modelo.nombre,
            'marca': modelo.marca.nombre
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'motores': []
        }, status=400)
'''
    return vista_content


def crear_vista_ajax_cajas():
    """Crear vista AJAX para cargar cajas por modelo"""
    vista_content = '''
@require_GET
def load_cajas(request):
    """
    Vista AJAX para cargar cajas filtradas por modelo
    """
    modelo_id = request.GET.get('modelo_id')
    
    if not modelo_id:
        return JsonResponse({'cajas': []})
    
    try:
        modelo = get_object_or_404(Modelo, id=modelo_id)
        cajas = CajaVehiculo.objects.filter(modelo=modelo).order_by('tipo', 'velocidades')
        
        cajas_data = [
            {
                'id': caja.id,
                'nombre': caja.nombre,
                'tipo': caja.tipo,
                'velocidades': caja.velocidades,
                'display': f"{caja.tipo} {caja.velocidades}vel - {caja.nombre}"
            }
            for caja in cajas
        ]
        
        return JsonResponse({
            'cajas': cajas_data,
            'modelo': modelo.nombre,
            'marca': modelo.marca.nombre
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'cajas': []
        }, status=400)
'''
    return vista_content


def crear_vista_ajax_combinado():
    """Crear vista AJAX combinada para motores y cajas"""
    vista_content = '''
@require_GET
def load_motores_cajas(request):
    """
    Vista AJAX combinada para cargar motores y cajas por modelo
    """
    modelo_id = request.GET.get('modelo_id')
    
    if not modelo_id:
        return JsonResponse({
            'motores': [],
            'cajas': []
        })
    
    try:
        modelo = get_object_or_404(Modelo, id=modelo_id)
        
        # Cargar motores
        motores = MotorVehiculo.objects.filter(modelo=modelo).order_by('cilindrada', 'nombre')
        motores_data = [
            {
                'id': motor.id,
                'nombre': motor.nombre,
                'cilindrada': motor.cilindrada,
                'tipo': motor.tipo,
                'display': f"{motor.cilindrada} {motor.tipo} - {motor.nombre}"
            }
            for motor in motores
        ]
        
        # Cargar cajas
        cajas = CajaVehiculo.objects.filter(modelo=modelo).order_by('tipo', 'velocidades')
        cajas_data = [
            {
                'id': caja.id,
                'nombre': caja.nombre,
                'tipo': caja.tipo,
                'velocidades': caja.velocidades,
                'display': f"{caja.tipo} {caja.velocidades}vel - {caja.nombre}"
            }
            for caja in cajas
        ]
        
        return JsonResponse({
            'motores': motores_data,
            'cajas': cajas_data,
            'modelo': modelo.nombre,
            'marca': modelo.marca.nombre,
            'pais': modelo.pais
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'motores': [],
            'cajas': []
        }, status=400)
'''
    return vista_content


def main():
    print("🎯 PASO 4B: Creando vistas AJAX para dependencia jerárquica")
    print("=" * 60)

    # Crear archivo de vistas AJAX
    vistas_file = "taller/ajax_views.py"

    # Importaciones y decoradores
    content = '''from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404
from taller.models import Marca, Modelo, MotorVehiculo, CajaVehiculo

"""
🎯 Vistas AJAX para formularios jerárquicos
Marca → Modelo → Motor/Caja
"""

'''

    # Agregar las vistas
    content += crear_vista_ajax_modelos()
    content += "\n\n"
    content += crear_vista_ajax_motores()
    content += "\n\n"
    content += crear_vista_ajax_cajas()
    content += "\n\n"
    content += crear_vista_ajax_combinado()

    # Escribir archivo
    with open(vistas_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Archivo creado: {vistas_file}")

    # URLs para las vistas AJAX
    urls_content = """
# URLs para vistas AJAX jerárquicas
from django.urls import path
from taller import ajax_views

ajax_urlpatterns = [
    path('ajax/load-modelos/', ajax_views.load_modelos, name='ajax_load_modelos'),
    path('ajax/load-motores/', ajax_views.load_motores, name='ajax_load_motores'),
    path('ajax/load-cajas/', ajax_views.load_cajas, name='ajax_load_cajas'),
    path('ajax/load-motores-cajas/', ajax_views.load_motores_cajas, name='ajax_load_motores_cajas'),
]

# Agregar estas URLs a tu urlpatterns principal:
# urlpatterns += ajax_urlpatterns
"""

    urls_file = "paso4_urls_ajax.py"
    with open(urls_file, "w", encoding="utf-8") as f:
        f.write(urls_content)

    print(f"✅ Archivo creado: {urls_file}")

    # JavaScript para el frontend
    js_content = """
/**
 * 🎯 JavaScript para formularios jerárquicos
 * Marca → Modelo → Motor/Caja
 */

$(document).ready(function() {
    // Configuración CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    const csrftoken = getCookie('csrftoken');
    
    // Función para limpiar y deshabilitar select
    function clearAndDisableSelect(selectId, placeholder = 'Seleccione...') {
        const $select = $(selectId);
        $select.empty().append(`<option value="">${placeholder}</option>`);
        $select.prop('disabled', true);
    }
    
    // Función para habilitar y llenar select
    function populateSelect(selectId, data, valueField = 'id', textField = 'nombre') {
        const $select = $(selectId);
        $select.empty().append('<option value="">Seleccione...</option>');
        
        if (data && data.length > 0) {
            data.forEach(item => {
                const value = item[valueField];
                const text = item.display || item[textField];
                $select.append(`<option value="${value}">${text}</option>`);
            });
            $select.prop('disabled', false);
        } else {
            $select.prop('disabled', true);
        }
    }
    
    // Evento: Cambio de Marca
    $('#id_marca').change(function() {
        const marcaId = $(this).val();
        
        // Limpiar campos dependientes
        clearAndDisableSelect('#id_modelo', 'Seleccione marca primero');
        clearAndDisableSelect('#id_motor', 'Seleccione modelo primero');
        clearAndDisableSelect('#id_caja', 'Seleccione modelo primero');
        
        if (!marcaId) return;
        
        // Cargar modelos via AJAX
        $.get('/ajax/load-modelos/', {marca_id: marcaId})
            .done(function(data) {
                if (data.error) {
                    alert('Error: ' + data.error);
                    return;
                }
                
                populateSelect('#id_modelo', data.modelos);
                
                if (data.modelos.length === 0) {
                    $('#id_modelo').append('<option value="">No hay modelos disponibles</option>');
                }
            })
            .fail(function() {
                alert('Error al cargar modelos');
            });
    });
    
    // Evento: Cambio de Modelo
    $('#id_modelo').change(function() {
        const modeloId = $(this).val();
        
        // Limpiar campos dependientes
        clearAndDisableSelect('#id_motor', 'Seleccione modelo primero');
        clearAndDisableSelect('#id_caja', 'Seleccione modelo primero');
        
        if (!modeloId) return;
        
        // Cargar motores y cajas via AJAX combinado
        $.get('/ajax/load-motores-cajas/', {modelo_id: modeloId})
            .done(function(data) {
                if (data.error) {
                    alert('Error: ' + data.error);
                    return;
                }
                
                // Poblar motores
                populateSelect('#id_motor', data.motores);
                if (data.motores.length === 0) {
                    $('#id_motor').append('<option value="">No hay motores disponibles</option>');
                }
                
                // Poblar cajas
                populateSelect('#id_caja', data.cajas);
                if (data.cajas.length === 0) {
                    $('#id_caja').append('<option value="">No hay cajas disponibles</option>');
                }
                
                // Opcional: Mostrar información del modelo
                console.log(`Cargado: ${data.marca} ${data.modelo} (${data.pais})`);
            })
            .fail(function() {
                alert('Error al cargar motores y cajas');
            });
    });
    
    // Inicialización: Deshabilitar campos dependientes
    clearAndDisableSelect('#id_modelo', 'Seleccione marca primero');
    clearAndDisableSelect('#id_motor', 'Seleccione modelo primero');
    clearAndDisableSelect('#id_caja', 'Seleccione modelo primero');
});

/**
 * Función auxiliar para debugging
 */
function debugFormularioJerarquico() {
    console.log('Marca:', $('#id_marca').val());
    console.log('Modelo:', $('#id_modelo').val());
    console.log('Motor:', $('#id_motor').val());
    console.log('Caja:', $('#id_caja').val());
}
"""

    js_file = "paso4_formulario_jerarquico.js"
    with open(js_file, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"✅ Archivo creado: {js_file}")

    print("\n🎯 **PRÓXIMOS PASOS:**")
    print("1. Agregar las URLs AJAX a tu urls.py:")
    print("   from taller.ajax_views import ajax_urlpatterns")
    print("   urlpatterns += ajax_urlpatterns")
    print("\n2. Incluir el JavaScript en tu template:")
    print("   <script src='paso4_formulario_jerarquico.js'></script>")
    print("\n3. Asegurar que jQuery esté cargado antes del script")
    print("\n4. Verificar que los nombres de campos coincidan:")
    print("   - id_marca, id_modelo, id_motor, id_caja")

    print("\n✅ **VISTAS AJAX CREADAS EXITOSAMENTE**")
    print("🔄 Sistema listo para dependencia jerárquica Marca → Modelo → Motor/Caja")


if __name__ == "__main__":
    main()
