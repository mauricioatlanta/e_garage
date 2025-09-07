#!/usr/bin/env python
import os
import sys

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

import json

from django.contrib.auth.models import User
from django.test import Client, TestCase

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.lineas_documento import LineaRepuesto, LineaServicio
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.tecnico import Tecnico
from taller.models.vehiculos import Vehiculo

print("=== TEST CREAR DOCUMENTO VÍA WEB ===")

# Crear client de Django
client = Client()

# 1. Crear/obtener usuario
user = User.objects.first()
if not user:
    user = User.objects.create_user(
        username="admin", password="admin123", email="admin@test.com"
    )

print(f"👤 Usuario: {user.username}")

# 2. Login
login_result = client.login(username=user.username, password="admin123")
print(f"🔑 Login exitoso: {login_result}")

# 3. Crear datos de prueba si no existen
empresa, _ = Empresa.objects.get_or_create(
    usuario=user, defaults={"nombre_taller": f"Taller de {user.username}"}
)

cliente, _ = Cliente.objects.get_or_create(
    empresa=empresa,
    nombre="Cliente Web Test",
    defaults={"email": "test@test.com", "telefono": "123456789"},
)

marca, _ = Marca.objects.get_or_create(nombre="Toyota")
modelo, _ = Modelo.objects.get_or_create(marca=marca, nombre="Corolla")

vehiculo, _ = Vehiculo.objects.get_or_create(
    empresa=empresa,
    cliente=cliente,
    patente="WEB123",
    defaults={"marca": marca, "modelo": modelo, "anio": 2020},
)

mecanico, _ = Tecnico.objects.get_or_create(nombre="Mecánico Web")

print(f"🏢 Empresa: {empresa.nombre_taller}")
print(f"👤 Cliente: {cliente.nombre}")
print(f"🚗 Vehículo: {vehiculo.patente}")
print(f"🔧 Mecánico: {mecanico.nombre}")

# 4. Simular POST con datos de documento
json_items = json.dumps(
    [
        {
            "tipo": "repuesto",
            "partnumber": "REP-WEB-001",
            "nombre": "Filtro aire web",
            "cantidad": 1,
            "precio": 18000,
        },
        {"tipo": "servicio", "nombre": "Lavado web", "precio": 15000},
    ]
)

post_data = {
    "tipo_documento": "Presupuesto",
    "fecha": "2025-01-15",
    "cliente": cliente.id,
    "vehiculo": vehiculo.id,
    "mecanico": mecanico.id,
    "kilometraje": "75000",
    "observaciones": "Test vía web",
    "json_items": json_items,
}

print(f"\n📝 Enviando POST data:")
print(f"   json_items: {json_items}")

# 5. Realizar POST al endpoint
response = client.post("/documentos/crear/", post_data)

print(f"\n📊 RESULTADO:")
print(f"   Status code: {response.status_code}")
print(f"   Redirect URL: {response.get('Location', 'No redirect')}")

if response.status_code == 302:
    print("   ✅ Redirección exitosa (documento creado)")

    # Verificar que se creó el documento
    ultimo_doc = Documento.objects.order_by("-id").first()
    if ultimo_doc:
        titulo = getattr(
            ultimo_doc,
            "numero_documento",
            getattr(ultimo_doc, "numero", str(ultimo_doc.pk)),
        )
        print(f"   📄 Último documento: {titulo}")

        # Verificar repuestos y servicios
        repuestos = LineaRepuesto.objects.filter(documento=ultimo_doc)
        servicios = LineaServicio.objects.filter(documento=ultimo_doc)

        print(f"   🔧 Repuestos creados: {repuestos.count()}")
        for rep in repuestos:
            precio_r = getattr(rep, "precio_unitario", getattr(rep, "precio", 0))
            print(f"      - {rep.nombre}: ${precio_r} x {rep.cantidad}")

        print(f"   ⚙️ Servicios creados: {servicios.count()}")
        for serv in servicios:
            precio_s = getattr(serv, "precio_unitario", getattr(serv, "precio", 0))
            print(f"      - {serv.nombre}: ${precio_s}")

        if repuestos.count() == 0 and servicios.count() == 0:
            print("   ❌ PROBLEMA: Documento creado VACÍO")
        else:
            print("   ✅ Documento creado CON repuestos/servicios")
    else:
        print("   ❌ No se encontró ningún documento")

elif response.status_code == 200:
    print("   ⚠️ Form renderizado (posibles errores)")
    if hasattr(response, "context") and "form" in response.context:
        form = response.context["form"]
        if form.errors:
            print(f"   Errores del form: {form.errors}")
else:
    print(f"   ❌ Error inesperado: {response.status_code}")
    print(f"   Content: {response.content[:500]}...")

print(f"\n✅ Test completado")
