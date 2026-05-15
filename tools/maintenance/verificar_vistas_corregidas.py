#!/usr/bin/env python3
"""
Script para verificar que las vistas optimizadas funcionan correctamente
después de corregir el FieldError de 'mecanico' por 'tecnico_responsable'
"""

import os
import sys

import django

# Configurar Django
sys.path.append(".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.documento import Documento


def verificar_vistas_corregidas():
    """Verificar que la consulta optimizada funciona"""
    print("🔍 VERIFICANDO VISTAS CORREGIDAS")
    print("=" * 40)

    try:
        # Probar la consulta exacta que usamos en las vistas
        documento = (
            Documento.objects.select_related("cliente", "vehiculo", "tecnico_responsable")
            .prefetch_related("lineas_repuesto", "lineas_servicio", "lineas_otro_servicio")
            .first()
        )

        if documento:
            print("✅ Consulta optimizada exitosa")
            print(f"   📄 Documento: {documento.numero_documento}")
            print(
                f"   👤 Cliente: {documento.cliente.nombre if documento.cliente else 'Sin cliente'}"
            )
            print(
                f"   🚗 Vehículo: {documento.vehiculo.patente if documento.vehiculo else 'Sin vehículo'}"
            )
            print(
                f"   🔧 Técnico: {documento.tecnico_responsable.nombre if documento.tecnico_responsable else 'Sin técnico'}"
            )
            print(f"   📦 Repuestos: {documento.lineas_repuesto.count()}")
            print(f"   🛠️  Servicios: {documento.lineas_servicio.count()}")
            print(f"   🏢 Otros servicios: {documento.lineas_otro_servicio.count()}")

            # Buscar nuestro documento de prueba específicamente
            doc_prueba = Documento.objects.filter(numero=888888).first()
            if doc_prueba:
                print("\n🧪 Documento de prueba encontrado:")
                print(f"   📄 ID: {doc_prueba.id}")
                print(f"   📄 Número: {doc_prueba.numero_documento}")
                print(f"   📦 Repuestos: {doc_prueba.lineas_repuesto.count()}")
                print(f"   🔗 URL para probar: /us/documentos/nuevo-ver/{doc_prueba.id}/")
            else:
                print("\n⚠️  No se encontró el documento de prueba 888888")

            return True
        else:
            print("❌ No hay documentos en la base de datos")
            return False

    except Exception as e:
        print(f"❌ Error en consulta: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    resultado = verificar_vistas_corregidas()
    if resultado:
        print("\n🎉 VERIFICACIÓN EXITOSA - Las vistas están corregidas")
    else:
        print("\n⚠️  VERIFICACIÓN FALLÓ")
