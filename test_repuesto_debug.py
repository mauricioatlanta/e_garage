#!/usr/bin/env python
import os
import sys
import django

# Configurar Django con SQLite temporal
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from taller.models.repuesto import Repuesto
from taller.models.empresa import Empresa
from taller.models.tienda import Tienda
from taller.forms.repuesto import RepuestoForm

def test_crear_repuesto():
    print("=== TEST: Crear Repuesto Ficticio ===")
    
    # Usar datos existentes
    empresas = Empresa.objects.all()
    tiendas = Tienda.objects.all()
    
    print(f"📊 Empresas disponibles: {empresas.count()}")
    print(f"📊 Tiendas disponibles: {tiendas.count()}")
    
    if empresas.count() == 0:
        print("❌ No hay empresas en la BD")
        return
        
    if tiendas.count() == 0:
        print("❌ No hay tiendas en la BD")
        return
    
    empresa = empresas.first()
    tienda = tiendas.first()
    
    print(f"✓ Usando empresa: {empresa}")
    print(f"✓ Usando tienda: {tienda}")
    
    # Datos de prueba para el formulario
    data = {
        'tienda': tienda.pk,
        'nombre_repuesto': 'Filtro de Aceite Debug',
        'part_number': 'DEBUG123',
        'precio_compra': '12500',  # Sin formato, solo números
        'precio_venta': '18500',   # Sin formato, solo números
        'stock': 10,
    }
    
    print(f"\n📝 Datos del formulario: {data}")
    
    # Crear formulario
    form = RepuestoForm(data)
    
    # Verificar si el formulario es válido
    print(f"✅ Formulario válido: {form.is_valid()}")
    if not form.is_valid():
        print(f"❌ Errores del formulario: {form.errors}")
        return
    
    print(f"📊 Datos limpios del formulario: {form.cleaned_data}")
    
    try:
        # Intentar guardar
        repuesto = form.save(commit=False)
        repuesto.empresa = empresa
        repuesto.save()
        print(f"\n🎉 ¡Repuesto creado exitosamente!")
        print(f"   ID: {repuesto.id}")
        print(f"   Nombre: {repuesto.nombre_repuesto}")
        print(f"   Precio compra: {repuesto.precio_compra}")
        print(f"   Precio venta: {repuesto.precio_venta}")
        print(f"   Empresa: {repuesto.empresa}")
        
        # Contar total de repuestos
        total = Repuesto.objects.count()
        print(f"\n📊 Total de repuestos en BD: {total}")
        
    except Exception as e:
        print(f"❌ Error al crear repuesto: {str(e)}")
        import traceback
        print(f"Traceback completo: {traceback.format_exc()}")

if __name__ == "__main__":
    test_crear_repuesto()
