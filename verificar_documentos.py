#!/usr/bin/env python3
"""
Script simple para verificar documentos existentes y su estado
"""
import os
import sys

import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
django.setup()

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto as RepuestoDocumento
from taller.models.lineas_documento import LineaServicio


def verificar_documentos():
    print("🔍 === VERIFICACIÓN DE DOCUMENTOS EXISTENTES ===")

    documentos = Documento.objects.all().order_by("-id")[:10]
    print(f"Total documentos en BD: {Documento.objects.count()}")
    print(f"Mostrando últimos 10 documentos:")
    print("-" * 80)

    for doc in documentos:
        repuestos = RepuestoDocumento.objects.filter(documento=doc)
        servicios = LineaServicio.objects.filter(documento=doc)

        print(f"📋 ID: {doc.id} | {doc.tipo_documento} #{doc.numero_documento}")
        print(f"   Cliente: {doc.cliente}")
        print(f"   Fecha: {doc.fecha}")
        print(f"   Empresa: {doc.empresa.nombre_taller}")
        print(f"   Repuestos: {repuestos.count()}")

        for r in repuestos:
            precio_r = getattr(r, "precio_unitario", getattr(r, "precio", 0))
            print(f"     - {r.codigo} | {r.nombre} | ${precio_r} x {r.cantidad}")

        print(f"   Servicios: {servicios.count()}")
        for s in servicios:
            precio_s = getattr(s, "precio_unitario", getattr(s, "precio", 0))
            print(f"     - {s.nombre} | ${precio_s}")

        if repuestos.count() == 0 and servicios.count() == 0:
            print(f"   ❌ DOCUMENTO VACÍO")
        else:
            print(f"   ✅ DOCUMENTO CON ITEMS")
        print("-" * 40)


if __name__ == "__main__":
    verificar_documentos()
