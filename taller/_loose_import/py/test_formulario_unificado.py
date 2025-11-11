#!/usr/bin/env python
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings.dev")
django.setup()

from django.contrib.auth.models import User

from taller.forms.documento_form import DocumentoForm, get_autocomplete_url
from taller.models.clientes import Cliente
from taller.models.empresa import Empresa
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.tecnico import Tecnico
from taller.models.vehiculos import Vehiculo


def test_formulario_unificado():
    print("🧪 Test del formulario unificado DocumentoForm")

    # Crear datos de prueba
    user = User.objects.create_user(
        username="testuser_form", email="test@example.com", password="testpass123"
    )

    empresa_cl = Empresa.objects.create(nombre_taller="Taller Chile Test", pais="CL", user=user)

    cliente = Cliente.objects.create(
        nombre="Juan Pérez Test", email="juan@example.com", empresa=empresa_cl
    )

    marca = Marca.objects.create(nombre="Toyota Test", country="CL")
    modelo = Modelo.objects.create(nombre="Corolla Test", marca=marca, country="CL")

    vehiculo = Vehiculo.objects.create(
        marca=marca, modelo=modelo, anio=2020, cliente=cliente, empresa=empresa_cl
    )

    tecnico = Tecnico.objects.create(nombre="Carlos Técnico Test", empresa=empresa_cl)

    print("✅ Objetos de prueba creados")

    # Test 1: Helper de URLs
    print("\n🔧 Test helper get_autocomplete_url:")
    url_cl = get_autocomplete_url("CL", "cliente")
    url_us = get_autocomplete_url("US", "cliente")
    print(f"   - URL Chile: {url_cl}")
    print(f"   - URL USA: {url_us}")
    assert url_cl == "cl:autocomplete:cliente"
    assert url_us == "usa:autocomplete:cliente"
    print("   ✅ URLs generadas correctamente")

    # Test 2: Formulario Chile
    print("\n🇨🇱 Test formulario Chile:")
    form_cl = DocumentoForm(user=user, empresa=empresa_cl, country="CL")

    # Verificar labels
    assert form_cl.fields["cliente"].label == "Cliente"
    assert form_cl.fields["vehiculo"].label == "Vehículo"
    assert form_cl.fields["tipo"].label == "Tipo de Documento"
    print("   ✅ Labels en español correctos")

    # Verificar URLs de autocompletado
    assert form_cl.fields["cliente"].widget.url == "cl:autocomplete:cliente"
    assert form_cl.fields["vehiculo"].widget.url == "cl:autocomplete:vehiculo"
    print("   ✅ URLs de autocompletado correctas")

    # Verificar IDs de widgets
    assert form_cl.fields["tipo"].widget.attrs.get("id") == "id_tipo"
    assert form_cl.fields["cliente"].widget.attrs.get("id") == "id_cliente"
    print("   ✅ IDs de widgets correctos")

    # Test 3: Formulario USA
    print("\n🇺🇸 Test formulario USA:")
    empresa_us = Empresa.objects.create(nombre_taller="Taller USA Test", pais="US", user=user)

    form_us = DocumentoForm(user=user, empresa=empresa_us, country="US")

    # Verificar labels
    assert form_us.fields["cliente"].label == "Customer"
    assert form_us.fields["vehiculo"].label == "Vehicle"
    assert form_us.fields["tipo"].label == "Document Type"
    print("   ✅ Labels en inglés correctos")

    # Verificar URLs de autocompletado
    assert form_us.fields["cliente"].widget.url == "usa:autocomplete:cliente"
    assert form_us.fields["vehiculo"].widget.url == "usa:autocomplete:vehiculo"
    print("   ✅ URLs de autocompletado correctas")

    # Test 4: Campos explícitos
    print("\n📋 Test campos explícitos:")
    expected_fields = [
        "tipo",
        "numero",
        "fecha_emision",
        "cliente",
        "vehiculo",
        "tecnico_responsable",
        "kilometraje",
        "millas",
        "observaciones",
        "pagado",
        "metodo_pago",
        "ult4",
        "monto_pagado",
        "saldo_pendiente",
        "fecha_pago",
        "nota_pago",
        "descuento",
    ]

    form_fields = list(form_cl.fields.keys())
    for field in expected_fields:
        assert field in form_fields, f"Campo {field} no encontrado"

    print(f"   ✅ Todos los {len(expected_fields)} campos esperados están presentes")

    print("\n✅ Test del formulario unificado completado exitosamente!")


if __name__ == "__main__":
    test_formulario_unificado()
