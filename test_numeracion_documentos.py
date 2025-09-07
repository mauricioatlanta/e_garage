#!/usr/bin/env python
"""
Test para verificar que los números de documento inician desde 1 por empresa
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "e_garage.settings")

import django
from django.conf import settings

settings.DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

django.setup()

import json

from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

from taller.documentos.views import crear_documento
from taller.models.documento import Documento
from taller.models.perfilusuario import PerfilUsuario


def test_numeracion_documentos():
    print("=== TEST NUMERACIÓN DOCUMENTOS POR EMPRESA ===\n")

    # Obtener usuarios de diferentes empresas
    users = User.objects.filter(username__in=["taller1", "taller2"])

    for user in users:
        print(f"📋 Testeando numeración para: {user.username}")

        perfil = PerfilUsuario.objects.get(user=user)
        empresa = perfil.empresa

        # Verificar documentos existentes antes del test
        docs_antes = Documento.objects.filter(empresa=empresa).count()
        print(f"   Documentos existentes antes: {docs_antes}")

        # Crear request simulado
        factory = RequestFactory()

        # Datos del formulario - usar datos válidos por empresa
        if user.username == "taller1":
            cliente_id = 1  # Ajustar según los datos reales
            vehiculo_id = 1
        else:  # taller2
            cliente_id = 5  # Ricardo Lunari
            vehiculo_id = 5  # qaqa111 - BMW X3

        form_data = {
            "tipo_documento": "Presupuesto",
            "numero_documento": "",  # Vacío para que genere automáticamente
            "fecha": "2025-07-23",
            "cliente": cliente_id,
            "vehiculo": vehiculo_id,
            "kilometraje": 50000,
            "observaciones": f"Test numeración {user.username}",
            "json_items": json.dumps(
                [
                    {
                        "tipo": "servicio",
                        "nombre": f"Servicio Test {user.username}",
                        "precio": 10000,
                    }
                ]
            ),
        }

        # Crear request POST
        request = factory.post("/documentos/crear/", form_data)
        request.user = user

        # Agregar sesión al request
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        try:
            print(f"   🚀 Creando documento para {user.username}...")
            response = crear_documento(request)

            # Verificar que se creó el documento
            docs_despues = Documento.objects.filter(empresa=empresa).count()
            print(f"   Documentos después: {docs_despues}")

            if docs_despues > docs_antes:
                # Obtener el último documento creado
                ultimo_doc = (
                    Documento.objects.filter(empresa=empresa).order_by("-fecha").first()
                )
                print(f"   ✅ Documento creado: {ultimo_doc.numero_documento}")
                print(f"   Empresa: {ultimo_doc.empresa.nombre_taller}")
            else:
                print(f"   ❌ No se creó documento nuevo")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Mostrar resumen final de numeración por empresa
    print(f"\n📊 RESUMEN FINAL DE NUMERACIÓN:")

    for user in users:
        perfil = PerfilUsuario.objects.get(user=user)
        empresa = perfil.empresa

        docs = Documento.objects.filter(empresa=empresa).order_by("fecha")
        print(f"\n🏢 {empresa.nombre_taller} ({user.username}):")

        for doc in docs:
            print(f"   - {doc.numero_documento} ({doc.tipo_documento}) - {doc.fecha}")

        # Verificar que los números sean consecutivos por tipo
        presupuestos = Documento.objects.filter(
            empresa=empresa, tipo_documento="Presupuesto"
        ).order_by("fecha")

        if presupuestos.exists():
            print(f"   📋 Presupuestos: {presupuestos.count()}")
            for i, pres in enumerate(presupuestos, 1):
                numero_esperado = f"PRE-{i:05d}"
                actual = pres.numero_documento
                status = "✅" if numero_esperado == actual else "❌"
                print(f"     {status} Esperado: {numero_esperado}, Actual: {actual}")


if __name__ == "__main__":
    test_numeracion_documentos()
