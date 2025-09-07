"""
Test directo de creación de documento para taller2
"""

import os
import sys

import django

sys.path.append(".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
django.setup()

import json
from datetime import date

from django.contrib.auth.models import User

from taller.models.clientes import Cliente
from taller.models.documento import (Documento, RepuestoDocumento,
                                     ServicioDocumento)
from taller.models.empresa import Empresa
from taller.models.tecnico import Mecanico


def crear_documento_taller2_directo():
    """Crear documento directamente para taller2"""

    print("🧪 CREAR DOCUMENTO DIRECTO PARA TALLER2")
    print("=" * 50)

    # 1. Obtener usuario taller2
    try:
        user_taller2 = User.objects.get(username="taller2")
        empresa_taller2 = user_taller2.empresa_usuario
        print(f"👤 Usuario: {user_taller2.username}")
        print(f"🏢 Empresa: {empresa_taller2.nombre_taller}")
    except Exception as e:
        print(f"❌ Error obteniendo usuario/empresa: {e}")
        return

    # 2. Obtener cliente de esta empresa
    cliente = Cliente.objects.filter(empresa=empresa_taller2).first()
    if not cliente:
        print("❌ No hay clientes para esta empresa")
        return

    print(f"👤 Cliente: {cliente.nombre}")

    # 3. Obtener o crear mecánico
    mecanico, _ = Tecnico.objects.get_or_create(nombre="Mecánico Taller2")
    print(f"🔧 Mecánico: {mecanico.nombre}")

    # 4. Crear documento
    count = Documento.objects.filter(empresa=empresa_taller2).count()
    documento = Documento.objects.create(
        empresa=empresa_taller2,
        tipo_documento="Presupuesto",
        numero_documento=f"T2-{count+1:03d}",
        fecha=date.today(),
        cliente=cliente,
        mecanico=mecanico,
        kilometraje=200000,
    )

    print(f"📋 Documento creado: #{documento.id} - {documento.numero_documento}")

    # 5. Agregar repuesto
    repuesto = RepuestoDocumento.objects.create(
        documento=documento,
        codigo="T2REP001",
        nombre="Filtro Test Taller2",
        cantidad=2,
        precio=30000,
    )
    print(
        f"🔩 Repuesto agregado: {repuesto.nombre} (${repuesto.precio} x {repuesto.cantidad})"
    )

    # 6. Agregar servicio
    servicio = ServicioDocumento.objects.create(
        empresa=empresa_taller2,
        documento=documento,
        nombre="Servicio Test Taller2",
        precio=45000,
    )
    print(f"⚙️ Servicio agregado: {servicio.nombre} (${servicio.precio})")

    # 7. Verificar totales
    total_repuestos = sum(
        r.total for r in RepuestoDocumento.objects.filter(documento=documento)
    )
    total_servicios = sum(
        s.precio for s in ServicioDocumento.objects.filter(documento=documento)
    )
    total_general = total_repuestos + total_servicios

    print(f"💰 Total repuestos: ${total_repuestos}")
    print(f"💰 Total servicios: ${total_servicios}")
    print(f"💰 TOTAL GENERAL: ${total_general}")

    print(f"🔗 URL Ver: http://127.0.0.1:8000/documentos/{documento.id}/")
    print(f"🔗 URL Editar: http://127.0.0.1:8000/documentos/editar/{documento.id}/")

    return documento


def verificar_documento_taller2(documento_id):
    """Verificar que el documento creado tiene todos los datos"""

    print(f"\n🔍 VERIFICAR DOCUMENTO #{documento_id}")
    print("=" * 30)

    try:
        documento = Documento.objects.get(id=documento_id)
        print(f"📋 Documento: {documento.tipo_documento} {documento.numero_documento}")
        print(f"🏢 Empresa: {documento.empresa.nombre_taller}")
        print(f"👤 Cliente: {documento.cliente.nombre}")
        print(
            f"🔧 Mecánico: {documento.mecanico.nombre if documento.mecanico else 'Sin mecánico'}"
        )

        # Verificar repuestos
        repuestos = RepuestoDocumento.objects.filter(documento=documento)
        print(f"🔩 Repuestos ({repuestos.count()}):")
        for rep in repuestos:
            print(
                f"   - {rep.codigo}: {rep.nombre} (${rep.precio} x {rep.cantidad} = ${rep.total})"
            )

        # Verificar servicios
        servicios = ServicioDocumento.objects.filter(documento=documento)
        print(f"⚙️ Servicios ({servicios.count()}):")
        for serv in servicios:
            print(f"   - {serv.nombre}: ${serv.precio}")

        # Estado
        if repuestos.exists() or servicios.exists():
            print(f"✅ DOCUMENTO COMPLETO")
        else:
            print(f"❌ DOCUMENTO VACÍO")

    except Documento.DoesNotExist:
        print(f"❌ Documento #{documento_id} no encontrado")


def comparar_documentos_empresas():
    """Comparar documentos entre empresas"""

    print(f"\n📊 COMPARACIÓN DOCUMENTOS POR EMPRESA")
    print("=" * 50)

    empresas = Empresa.objects.all()
    for empresa in empresas:
        documentos = Documento.objects.filter(empresa=empresa)

        docs_con_datos = 0
        docs_vacios = 0

        for doc in documentos:
            repuestos = RepuestoDocumento.objects.filter(documento=doc)
            servicios = ServicioDocumento.objects.filter(documento=doc)

            if repuestos.exists() or servicios.exists():
                docs_con_datos += 1
            else:
                docs_vacios += 1

        print(f"🏢 {empresa.nombre_taller}:")
        print(f"   📄 Total docs: {documentos.count()}")
        print(f"   ✅ Con datos: {docs_con_datos}")
        print(f"   ❌ Vacíos: {docs_vacios}")

        if docs_vacios > 0:
            print(f"   ⚠️ PROBLEMA: {docs_vacios} documentos sin datos")


if __name__ == "__main__":
    # Crear documento test para taller2
    doc = crear_documento_taller2_directo()

    # Verificar que se creó correctamente
    if doc:
        verificar_documento_taller2(doc.id)

    # Comparar estado general
    comparar_documentos_empresas()
