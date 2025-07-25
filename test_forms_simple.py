"""
Script para probar formularios inteligentes
Ejecutar con: python manage.py shell < test_forms_simple.py
"""

print("="*60)
print("🧠 PRUEBA DE FORMULARIOS INTELIGENTES POR PAÍS")
print("="*60)

from django.contrib.auth.models import User
from taller.models.empresa import Empresa

# Buscar usuarios de diferentes países
user_chile = User.objects.filter(empresa__pais='CL').first()
user_usa = User.objects.filter(empresa__pais='US').first()

if user_chile:
    print(f"✅ Usuario Chile encontrado: {user_chile.username}")
    
    # Probar formulario de vehículo
    print("\n🚗 Formulario de Vehículo (Chile):")
    from taller.vehiculos.forms import VehiculoForm
    form_vehiculo_cl = VehiculoForm(user=user_chile)
    
    # Verificar placeholder de patente
    patente_placeholder = form_vehiculo_cl.fields['patente'].widget.attrs.get('placeholder', 'N/A')
    print(f"   • Placeholder patente: {patente_placeholder}")
    
    # Probar formulario de cliente
    print("\n👥 Formulario de Cliente (Chile):")
    from taller.forms.clientes import ClienteForm
    form_cliente_cl = ClienteForm(user=user_chile)
    
    telefono_placeholder = form_cliente_cl.fields['telefono'].widget.attrs.get('placeholder', 'N/A')
    region_label = form_cliente_cl.fields['region'].label
    print(f"   • Placeholder teléfono: {telefono_placeholder}")
    print(f"   • Label región: {region_label}")
    
    # Probar formulario de repuesto
    print("\n🔧 Formulario de Repuesto (Chile):")
    from taller.forms.repuesto import RepuestoForm
    form_repuesto_cl = RepuestoForm(user=user_chile)
    
    precio_placeholder = form_repuesto_cl.fields['precio_compra'].widget.attrs.get('placeholder', 'N/A')
    print(f"   • Placeholder precio: {precio_placeholder}")

else:
    print("❌ No se encontró usuario de Chile")

if user_usa:
    print(f"\n✅ Usuario USA encontrado: {user_usa.username}")
    
    # Probar formulario de vehículo
    print("\n🚗 Formulario de Vehículo (USA):")
    from taller.vehiculos.forms import VehiculoForm
    form_vehiculo_us = VehiculoForm(user=user_usa)
    
    patente_placeholder = form_vehiculo_us.fields['patente'].widget.attrs.get('placeholder', 'N/A')
    print(f"   • Placeholder patente: {patente_placeholder}")
    
    # Probar formulario de cliente
    print("\n👥 Formulario de Cliente (USA):")
    from taller.forms.clientes import ClienteForm
    form_cliente_us = ClienteForm(user=user_usa)
    
    telefono_placeholder = form_cliente_us.fields['telefono'].widget.attrs.get('placeholder', 'N/A')
    region_label = form_cliente_us.fields['region'].label
    print(f"   • Placeholder teléfono: {telefono_placeholder}")
    print(f"   • Label región: {region_label}")
    
    # Probar formulario de repuesto
    print("\n🔧 Formulario de Repuesto (USA):")
    from taller.forms.repuesto import RepuestoForm
    form_repuesto_us = RepuestoForm(user=user_usa)
    
    precio_placeholder = form_repuesto_us.fields['precio_compra'].widget.attrs.get('placeholder', 'N/A')
    print(f"   • Placeholder precio: {precio_placeholder}")

else:
    print("❌ No se encontró usuario de USA")

print("\n" + "="*60)
print("🎉 PRUEBA DE FORMULARIOS INTELIGENTES COMPLETADA")
print("="*60)
