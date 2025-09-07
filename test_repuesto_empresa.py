#!/usr/bin/env python
"""
🧪 Script de prueba: Verificar relación Usuario->Empresa en RepuestoForm
"""
import os
import sys

import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.forms.repuesto import RepuestoForm
from taller.models.empresa import Empresa
from taller.models.tienda import Tienda


def test_user_empresa_relation():
    print("🔍 Verificando relación Usuario->Empresa...")

    # Buscar un usuario existente
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("❌ No hay usuarios en el sistema")
        return

    print(f"👤 Usuario encontrado: {user.username}")

    # Verificar si tiene empresa
    try:
        empresa = user.empresa_usuario  # related_name desde el modelo Empresa
        print(f"🏢 Empresa del usuario: {empresa}")
    except AttributeError:
        print("⚠️  Usuario sin empresa, creando una...")
        empresa, created = Empresa.objects.get_or_create(
            usuario=user, defaults={"nombre_taller": f"Taller de {user.username}"}
        )
        print(f"🏢 Empresa {'creada' if created else 'encontrada'}: {empresa}")

    # Verificar tienda
    tienda = Tienda.objects.first()
    if not tienda:
        tienda = Tienda.objects.create(nombre="Tienda de Prueba")
        print(f"🏪 Tienda creada: {tienda}")
    else:
        print(f"🏪 Tienda encontrada: {tienda}")

    # Simular datos del formulario
    form_data = {
        "tienda": tienda.pk,  # Usar .pk en lugar de .id
        "nombre_repuesto": "Filtro de Aceite FINAL",
        "part_number": "FINAL001",
        "precio_compra": "13000",
        "precio_venta": "19000",
        "stock": "50",
        "observaciones": "Prueba final",
    }

    print(f"📝 Datos del formulario: {form_data}")

    # Crear y validar formulario
    form = RepuestoForm(form_data)
    print(f"✅ Formulario válido: {form.is_valid()}")

    if not form.is_valid():
        print(f"❌ Errores: {form.errors}")
        return

    # Guardar el repuesto
    repuesto = form.save(commit=False)
    repuesto.empresa = empresa
    repuesto.save()

    print(f"🎉 Repuesto creado exitosamente!")
    print(f"   ID: {repuesto.id}")
    print(f"   Nombre: {repuesto.nombre_repuesto}")
    print(f"   Empresa: {repuesto.empresa}")
    print(f"   Tienda: {repuesto.tienda}")
    print(f"   Precio compra: ${repuesto.precio_compra:,}")
    print(f"   Precio venta: ${repuesto.precio_venta:,}")


if __name__ == "__main__":
    test_user_empresa_relation()
