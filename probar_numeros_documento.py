#!/usr/bin/env python
"""
Script para probar la API de generación de números de documento
"""

import os
import sys

import django
from django.conf import settings

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth import get_user_model

from taller.models.documento import Documento
from taller.models.empresa import Empresa

User = get_user_model()


def probar_generacion_numeros():
    """Prueba la generación de números de documento"""
    print("🧪 Probando generación de números de documento...")

    try:
        # Obtener una empresa de prueba
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ No hay empresas en la base de datos")
            return

        print(f"📊 Empresa de prueba: {empresa.nombre_taller}")
        print(f"🌍 País: {empresa.pais}")

        # Tipos de documento según país
        tipos = ["PRESUPUESTO", "ORDEN_TRABAJO", "FACTURA", "BOLETA"]

        print("\n📋 Probando generación de números por tipo:")
        print("-" * 50)

        for tipo in tipos:
            # Crear documento temporal
            doc_temp = Documento(tipo=tipo, empresa=empresa)

            try:
                numero = doc_temp.generar_numero_documento()
                print(f"✅ {tipo:15} → {numero}")
            except Exception as e:
                print(f"❌ {tipo:15} → Error: {e}")

        print("\n🔍 Verificando secuencias existentes:")
        print("-" * 50)

        for tipo in tipos:
            count = Documento.objects.filter(empresa=empresa, tipo=tipo).count()
            print(f"📊 {tipo:15} → {count} documentos existentes")

    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    probar_generacion_numeros()
