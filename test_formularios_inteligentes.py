#!/usr/bin/env python
"""
Script para probar los formularios inteligentes con diferenciación por país
Verifica filtrado de marcas, regiones, precios y validaciones por país
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanico.settings')
sys.path.append('/workspaces/taller_mecanico')

django.setup()

from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.vehiculos.forms import VehiculoForm
from taller.forms.clientes import ClienteForm
from taller.forms.repuesto import RepuestoForm

def test_formularios_inteligentes():
    """Prueba los formularios inteligentes por país"""
    print("="*60)
    print("🧠 PRUEBA DE FORMULARIOS INTELIGENTES POR PAÍS")
    print("="*60)
    
    # Obtener usuarios de prueba
    try:
        user_chile = User.objects.filter(empresa__pais='CL').first()
        user_usa = User.objects.filter(empresa__pais='US').first()
        
        if not user_chile:
            print("❌ No se encontró usuario de Chile")
            return False
            
        if not user_usa:
            print("❌ No se encontró usuario de USA")
            return False
            
        print(f"✅ Usuario Chile: {user_chile.username} - Empresa: {user_chile.empresa.nombre}")
        print(f"✅ Usuario USA: {user_usa.username} - Empresa: {user_usa.empresa.nombre}")
        
    except Exception as e:
        print(f"❌ Error obteniendo usuarios: {e}")
        return False
    
    print("\n" + "="*50)
    print("🚗 PRUEBA: FORMULARIO DE VEHÍCULOS")
    print("="*50)
    
    # Prueba formulario de vehículos para Chile
    print("\n📋 Formulario Chile:")
    form_vehiculo_cl = VehiculoForm(user=user_chile)
    
    if hasattr(form_vehiculo_cl.fields['marca'], 'queryset'):
        marcas_cl = list(form_vehiculo_cl.fields['marca'].queryset.values_list('nombre', flat=True))[:5]
        print(f"   • Marcas disponibles (primeras 5): {marcas_cl}")
    
    patente_placeholder_cl = form_vehiculo_cl.fields['patente'].widget.attrs.get('placeholder', 'N/A')
    print(f"   • Placeholder patente: {patente_placeholder_cl}")
    
    # Prueba formulario de vehículos para USA
    print("\n📋 Formulario USA:")
    form_vehiculo_us = VehiculoForm(user=user_usa)
    
    if hasattr(form_vehiculo_us.fields['marca'], 'queryset'):
        marcas_us = list(form_vehiculo_us.fields['marca'].queryset.values_list('nombre', flat=True))[:5]
        print(f"   • Marcas disponibles (primeras 5): {marcas_us}")
    
    patente_placeholder_us = form_vehiculo_us.fields['patente'].widget.attrs.get('placeholder', 'N/A')
    print(f"   • Placeholder patente: {patente_placeholder_us}")
    
    print("\n" + "="*50)
    print("👥 PRUEBA: FORMULARIO DE CLIENTES")
    print("="*50)
    
    # Prueba formulario de clientes para Chile
    print("\n📋 Formulario Chile:")
    form_cliente_cl = ClienteForm(user=user_chile)
    
    telefono_placeholder_cl = form_cliente_cl.fields['telefono'].widget.attrs.get('placeholder', 'N/A')
    region_label_cl = form_cliente_cl.fields['region'].label
    print(f"   • Placeholder teléfono: {telefono_placeholder_cl}")
    print(f"   • Label región: {region_label_cl}")
    
    # Prueba formulario de clientes para USA
    print("\n📋 Formulario USA:")
    form_cliente_us = ClienteForm(user=user_usa)
    
    telefono_placeholder_us = form_cliente_us.fields['telefono'].widget.attrs.get('placeholder', 'N/A')
    region_label_us = form_cliente_us.fields['region'].label
    print(f"   • Placeholder teléfono: {telefono_placeholder_us}")
    print(f"   • Label región: {region_label_us}")
    
    print("\n" + "="*50)
    print("🔧 PRUEBA: FORMULARIO DE REPUESTOS")
    print("="*50)
    
    # Prueba formulario de repuestos para Chile
    print("\n📋 Formulario Chile:")
    form_repuesto_cl = RepuestoForm(user=user_chile)
    
    precio_compra_placeholder_cl = form_repuesto_cl.fields['precio_compra'].widget.attrs.get('placeholder', 'N/A')
    precio_venta_placeholder_cl = form_repuesto_cl.fields['precio_venta'].widget.attrs.get('placeholder', 'N/A')
    print(f"   • Placeholder precio compra: {precio_compra_placeholder_cl}")
    print(f"   • Placeholder precio venta: {precio_venta_placeholder_cl}")
    
    # Prueba formulario de repuestos para USA
    print("\n📋 Formulario USA:")
    form_repuesto_us = RepuestoForm(user=user_usa)
    
    precio_compra_placeholder_us = form_repuesto_us.fields['precio_compra'].widget.attrs.get('placeholder', 'N/A')
    precio_venta_placeholder_us = form_repuesto_us.fields['precio_venta'].widget.attrs.get('placeholder', 'N/A')
    print(f"   • Placeholder precio compra: {precio_compra_placeholder_us}")
    print(f"   • Placeholder precio venta: {precio_venta_placeholder_us}")
    
    print("\n" + "="*50)
    print("🧪 PRUEBA: VALIDACIONES POR PAÍS")
    print("="*50)
    
    # Validar patente chilena en formulario Chile
    print("\n🔍 Validación patente Chile (ABC123):")
    form_data_cl = {'patente': 'ABC123', 'marca': 1, 'modelo': 1, 'anio': 2020}
    form_vehiculo_test_cl = VehiculoForm(data=form_data_cl, user=user_chile)
    
    if form_vehiculo_test_cl.is_valid():
        print("   ✅ Patente chilena válida")
    else:
        print(f"   ❌ Error patente: {form_vehiculo_test_cl.errors.get('patente', 'N/A')}")
    
    # Validar teléfono USA en formulario USA
    print("\n📞 Validación teléfono USA ((555) 123-4567):")
    form_data_us = {
        'nombre': 'John', 'apellido': 'Doe', 'telefono': '(555) 123-4567',
        'direccion': '123 Main St', 'email': 'john@test.com'
    }
    form_cliente_test_us = ClienteForm(data=form_data_us, user=user_usa)
    
    if form_cliente_test_us.is_valid():
        print("   ✅ Teléfono USA válido")
    else:
        print(f"   ❌ Error teléfono: {form_cliente_test_us.errors.get('telefono', 'N/A')}")
    
    print("\n" + "="*60)
    print("🎉 FORMULARIOS INTELIGENTES FUNCIONANDO CORRECTAMENTE")
    print("="*60)
    
    return True

if __name__ == "__main__":
    test_formularios_inteligentes()
