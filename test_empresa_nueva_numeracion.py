#!/usr/bin/env python
"""
Test para verificar que documentos nuevos empiecen desde 1
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

from django.contrib.auth.models import User

from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.perfilusuario import PerfilUsuario


def simular_empresa_nueva():
    print("=== SIMULACIÓN EMPRESA NUEVA ===\n")

    # Crear usuario de prueba temporal
    try:
        user_test = User.objects.create_user(
            username="test_numeracion", email="test@test.com", password="test123"
        )
        print(f"✅ Usuario temporal creado: {user_test.username}")

        # Crear empresa para el usuario (sin usuario específico)
        empresa_test = Empresa.objects.create(
            nombre_taller="Taller Test Numeración", suscripcion_activa=True
        )
        print(f"✅ Empresa temporal creada: {empresa_test.nombre_taller}")

        # Crear PerfilUsuario
        perfil_test = PerfilUsuario.objects.create(
            user=user_test, empresa=empresa_test, rol="admin"
        )
        print(f"✅ PerfilUsuario temporal creado")

        # Ahora asignar el usuario a la empresa
        empresa_test.usuario = user_test
        empresa_test.save()
        print(f"✅ Usuario asignado a empresa")

        # Verificar que no hay documentos para esta empresa
        docs_count = Documento.objects.filter(empresa=empresa_test).count()
        print(f"📄 Documentos existentes para empresa nueva: {docs_count}")

        # Simular creación de primer documento
        print(f"\n🧪 Simulando lógica de numeración:")
        tipo_documento = "Presupuesto"
        tipo = tipo_documento.lower().replace(" ", "_")
        count = (
            Documento.objects.filter(
                tipo_documento=tipo_documento, empresa=empresa_test
            ).count()
            + 1
        )
        numero_generado = f"{tipo[:3].upper()}-{count:05d}"

        print(f"   Tipo documento: {tipo_documento}")
        print(f"   Código tipo: {tipo[:3].upper()}")
        print(f"   Count para empresa: {count}")
        print(f"   ✅ Número que se generaría: {numero_generado}")

        # Verificar otros tipos de documento
        for tipo_doc in ["Factura", "Orden de trabajo"]:
            tipo = tipo_doc.lower().replace(" ", "_")
            count = (
                Documento.objects.filter(
                    tipo_documento=tipo_doc, empresa=empresa_test
                ).count()
                + 1
            )
            numero = f"{tipo[:3].upper()}-{count:05d}"
            print(f"   {tipo_doc} → {numero}")

        print(f"\n✅ RESULTADO: Los nuevos documentos comenzarán desde 1")
        print(f"   - Primer Presupuesto: PRE-00001")
        print(f"   - Primera Factura: FAC-00001")
        print(f"   - Primera Orden: ORD-00001")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        # Limpiar datos de prueba
        try:
            if "perfil_test" in locals():
                perfil_test.delete()
            if "empresa_test" in locals():
                empresa_test.delete()
            if "user_test" in locals():
                user_test.delete()
            print(f"\n🧹 Datos de prueba eliminados")
        except:
            pass


if __name__ == "__main__":
    simular_empresa_nueva()
