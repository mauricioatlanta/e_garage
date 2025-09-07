import os
import sys

import django

sys.path.append(".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
django.setup()

from taller.models.documento import Documento, RepuestoDocumento
from taller.models.empresa import Empresa
from taller.models.lineas_documento import LineaServicio


def encontrar_documento_vacio_taller2():
    """Encontrar el documento vacío específico en Mecánica Express"""

    print("🔍 BUSCANDO DOCUMENTO VACÍO EN MECÁNICA EXPRESS")
    print("=" * 60)

    # Obtener empresa Mecánica Express
    try:
        empresa_taller2 = Empresa.objects.get(nombre_taller="Mecánica Express")
        print(f"🏢 Empresa: {empresa_taller2.nombre_taller}")
    except Empresa.DoesNotExist:
        print("❌ Empresa Mecánica Express no encontrada")
        return

    # Obtener todos los documentos de esta empresa
    documentos = Documento.objects.filter(empresa=empresa_taller2).order_by("id")
    print(f"📄 Total documentos: {documentos.count()}")

    # Analizar cada documento
    for doc in documentos:
        repuestos = RepuestoDocumento.objects.filter(documento=doc)
        servicios = LineaServicio.objects.filter(documento=doc)

        tiene_datos = repuestos.exists() or servicios.exists()
        estado = "✅ CON DATOS" if tiene_datos else "❌ VACÍO"

        print(f"\n📋 Doc #{doc.id}: {doc.tipo_documento} {doc.numero_documento}")
        print(f"   📅 Fecha: {doc.fecha}")
        print(f"   👤 Cliente: {doc.cliente.nombre if doc.cliente else 'Sin cliente'}")
        print(f"   🔧 Técnico: {doc.tecnico.nombre if doc.tecnico else 'Sin técnico'}")
        print(f"   🔩 Repuestos: {repuestos.count()}")
        print(f"   ⚙️ Servicios: {servicios.count()}")
        print(f"   🎯 Estado: {estado}")

        if not tiene_datos:
            print(f"   🔗 URL Ver: http://127.0.0.1:8000/documentos/{doc.id}/")
            print(
                f"   🔗 URL Editar: http://127.0.0.1:8000/documentos/editar/{doc.id}/"
            )
            print(f"   ⚠️ ESTE ES EL DOCUMENTO PROBLEMÁTICO")


if __name__ == "__main__":
    encontrar_documento_vacio_taller2()
