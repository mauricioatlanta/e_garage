#!/usr/bin/env python
"""
Script para probar el RepuestoForm con una configuración SQLite temporal
"""
import os
import sys
import django
from django.conf import settings

# Configurar Django con SQLite temporal
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'taller',
        ],
        SECRET_KEY='test-key-for-repuesto-form',
        USE_TZ=True,
    )

django.setup()

# Ahora podemos importar los modelos
from django.core.management import execute_from_command_line
from django.db import models
from taller.models.repuesto import Repuesto
from taller.models.empresa import Empresa
from taller.models.tienda import Tienda
from taller.forms.repuesto import RepuestoForm

def setup_test_data():
    """Crear las tablas y datos de prueba"""
    from django.core.management import call_command
    
    print("Creando tablas...")
    call_command('migrate', verbosity=0, interactive=False)
    
    # Crear empresa de prueba
    empresa = Empresa.objects.create(
        nombre_taller="Empresa Test",
        empresa="Empresa Test"
    )
    
    # Crear tienda de prueba
    tienda = Tienda.objects.create(nombre="Tienda Test")
    
    return empresa, tienda

def test_repuesto_form():
    """Probar el RepuestoForm con datos reales"""
    print("=== PRUEBA DEL REPUESTO FORM ===\n")
    
    try:
        empresa, tienda = setup_test_data()
        print(f"✓ Empresa creada: {empresa}")
        print(f"✓ Tienda creada: {tienda}")
        
        # Datos del formulario
        form_data = {
            'tienda': tienda.id,
            'nombre_repuesto': 'Filtro de Aceite Test',
            'part_number': 'TEST123',
            'precio_compra': '$12.500',
            'precio_venta': '$18.900',
            'stock': 5,
        }
        
        print(f"\nDatos del formulario: {form_data}")
        
        # Crear el formulario
        form = RepuestoForm(form_data)
        
        # Validar el formulario
        is_valid = form.is_valid()
        print(f"¿Formulario válido? {is_valid}")
        
        if not is_valid:
            print(f"Errores: {form.errors}")
            return
        
        print(f"Datos limpios: {form.cleaned_data}")
        
        # Intentar guardar
        repuesto = form.save(commit=False)
        repuesto.empresa = empresa
        repuesto.save()
        
        print(f"\n✅ REPUESTO CREADO EXITOSAMENTE!")
        print(f"  ID: {repuesto.id}")
        print(f"  Nombre: {repuesto.nombre_repuesto}")
        print(f"  Part Number: {repuesto.part_number}")
        print(f"  Precio Compra: {repuesto.precio_compra}")
        print(f"  Precio Venta: {repuesto.precio_venta}")
        print(f"  Stock: {repuesto.stock}")
        print(f"  Tienda: {repuesto.tienda}")
        print(f"  Empresa: {repuesto.empresa}")
        
        # Verificar que los precios se guardaron correctamente
        assert repuesto.precio_compra == 12500, f"Precio compra incorrecto: {repuesto.precio_compra}"
        assert repuesto.precio_venta == 18900, f"Precio venta incorrecto: {repuesto.precio_venta}"
        
        print(f"\n✅ TODAS LAS VALIDACIONES PASARON!")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_repuesto_form()
