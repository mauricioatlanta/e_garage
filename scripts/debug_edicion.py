import os
import sys

import django

sys.path.append(".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
django.setup()

from taller.models.documento import (Documento, RepuestoDocumento,
                                     ServicioDocumento)


def debug_documento_edicion():
    """Debug específico para el problema de edición de documentos"""

    print("🔍 DEBUG: Problema de Edición de Documentos")
    print("=" * 60)

    # Obtener todos los documentos
    documentos = Documento.objects.all().order_by("-id")

    print(f"📄 Total documentos: {documentos.count()}")

    if not documentos.exists():
        print("❌ No hay documentos para debuggear")
        return

    # Analizar los documentos más recientes
    for doc in documentos[:3]:
        print(f"\n📋 DOCUMENTO #{doc.id}")
        print(f"   Tipo: {doc.tipo_documento}")
        print(f"   Número: {doc.numero_documento}")
        print(f"   Fecha: {doc.fecha}")
        print(f"   Cliente: {doc.cliente.nombre if doc.cliente else 'None'}")
        print(f"   Mecánico: {doc.mecanico.nombre if doc.mecanico else 'None'}")
        print(f"   Vehículo: {doc.vehiculo.patente if doc.vehiculo else 'None'}")
        print(f"   Observaciones: {doc.observaciones or 'None'}")
        print(f"   Kilometraje: {doc.kilometraje or 'None'}")

        # Verificar repuestos
        repuestos = RepuestoDocumento.objects.filter(documento=doc)
        print(f"   🔩 Repuestos ({repuestos.count()}):")
        for rep in repuestos:
            print(
                f"      - {rep.codigo}: {rep.nombre} (${rep.precio} x {rep.cantidad} = ${rep.total})"
            )

        # Verificar servicios
        servicios = ServicioDocumento.objects.filter(documento=doc)
        print(f"   ⚙️ Servicios ({servicios.count()}):")
        for serv in servicios:
            print(f"      - {serv.nombre}: ${serv.precio}")

        # Calcular totales
        total_repuestos = sum(r.total for r in repuestos)
        total_servicios = sum(s.precio for s in servicios)
        total_general = total_repuestos + total_servicios

        print(f"   💰 Total repuestos: ${total_repuestos}")
        print(f"   💰 Total servicios: ${total_servicios}")
        print(f"   💰 TOTAL GENERAL: ${total_general}")

        # Estado del documento
        campos_vacios = []
        if not doc.cliente:
            campos_vacios.append("cliente")
        if not doc.mecanico:
            campos_vacios.append("mecánico")
        if not doc.vehiculo:
            campos_vacios.append("vehículo")
        if not repuestos.exists() and not servicios.exists():
            campos_vacios.append("repuestos/servicios")

        if campos_vacios:
            print(f"   ⚠️ Campos faltantes: {', '.join(campos_vacios)}")
        else:
            print(f"   ✅ Documento completo")

        print(f"   🔗 URL editar: http://127.0.0.1:8000/documentos/editar/{doc.id}/")


def crear_documento_test_completo():
    """Crear un documento completo para testing"""
    print("\n🧪 CREANDO DOCUMENTO TEST COMPLETO")

    from datetime import date

    from django.contrib.auth.models import User

    from taller.models.cliente import Cliente
    from taller.models.empresa import Empresa
    from taller.models.tecnico import Mecanico
    from taller.models.vehiculos import Vehiculo

    # Obtener usuario y empresa
    user = User.objects.first()
    if not user:
        print("❌ No hay usuarios en el sistema")
        return

    try:
        empresa = user.empresa_usuario
    except:
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ No hay empresas en el sistema")
            return

    # Obtener o crear cliente
    cliente = Cliente.objects.first()
    if not cliente:
        print("❌ No hay clientes en el sistema")
        return

    # Obtener o crear mecánico
    mecanico, _ = Tecnico.objects.get_or_create(nombre="Mecánico Test Completo")

    # Obtener vehículo
    vehiculo = Vehiculo.objects.first()

    # Crear documento
    documento = Documento.objects.create(
        empresa=empresa,
        tipo_documento="Presupuesto",
        numero_documento=f"TEST-{Documento.objects.count() + 1:05d}",
        fecha=date.today(),
        cliente=cliente,
        mecanico=mecanico,
        vehiculo=vehiculo,
        kilometraje=150000,
        observaciones="Documento de prueba completo para debugging",
    )

    # Agregar repuestos
    RepuestoDocumento.objects.create(
        documento=documento,
        codigo="TEST001",
        nombre="Repuesto Test 1",
        cantidad=2,
        precio=25000,
    )

    RepuestoDocumento.objects.create(
        documento=documento,
        codigo="TEST002",
        nombre="Repuesto Test 2",
        cantidad=1,
        precio=35000,
    )

    # Agregar servicios
    ServicioDocumento.objects.create(
        empresa=empresa, documento=documento, nombre="Servicio Test 1", precio=45000
    )

    ServicioDocumento.objects.create(
        empresa=empresa, documento=documento, nombre="Servicio Test 2", precio=25000
    )

    print(f"✅ Documento test creado: #{documento.id}")
    print(f"   🔗 Ver: http://127.0.0.1:8000/documentos/{documento.id}/")
    print(f"   🔗 Editar: http://127.0.0.1:8000/documentos/editar/{documento.id}/")

    return documento


if __name__ == "__main__":
    debug_documento_edicion()
    crear_documento_test_completo()
