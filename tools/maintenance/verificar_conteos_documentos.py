#!/usr/bin/env python3
"""
Script para verificar que los conteos de documentos están funcionando correctamente
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.db.models import Count, IntegerField, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce

from taller.documentos.models import Documento
from taller.repuestos.models import RepuestoDocumento
from taller.servicios.models import ServicioDocumento, ServicioExternoDocumento
from taller.vehiculos.models import VehiculoDocumento


def verificar_conteos():
    print("=== VERIFICACIÓN DE CONTEOS DE DOCUMENTOS ===\n")

    # Obtener documentos con anotaciones igual que en la vista
    vehiculos_subquery = VehiculoDocumento.objects.filter(documento=OuterRef("pk")).aggregate(
        total_millas=Coalesce(Sum("kilometraje"), 0, output_field=IntegerField())
    )["total_millas"]

    repuestos_subquery = RepuestoDocumento.objects.filter(documento=OuterRef("pk")).aggregate(
        total_repuestos=Coalesce(Count("id"), 0, output_field=IntegerField())
    )["total_repuestos"]

    servicios_subquery = ServicioDocumento.objects.filter(documento=OuterRef("pk")).aggregate(
        total_servicios=Coalesce(Count("id"), 0, output_field=IntegerField())
    )["total_servicios"]

    otros_subquery = ServicioExternoDocumento.objects.filter(documento=OuterRef("pk")).aggregate(
        total_otros=Coalesce(Count("id"), 0, output_field=IntegerField())
    )["total_otros"]

    documentos = Documento.objects.annotate(
        total_millas=Subquery(vehiculos_subquery, output_field=IntegerField()),
        total_repuestos=Subquery(repuestos_subquery, output_field=IntegerField()),
        total_servicios=Subquery(servicios_subquery, output_field=IntegerField()),
        total_otros=Subquery(otros_subquery, output_field=IntegerField()),
    ).order_by("-fecha_creacion")[
        :5
    ]  # Solo los últimos 5 para verificar

    print("ÚLTIMOS 5 DOCUMENTOS CON CONTEOS:")
    print("-" * 80)
    print(
        f"{'ID':<5} {'Fecha':<12} {'Millas':<8} {'#Rep':<6} {'#Serv':<7} {'#Otros':<8} {'Total $':<10}"
    )
    print("-" * 80)

    for doc in documentos:
        fecha_str = doc.fecha_creacion.strftime("%Y-%m-%d") if doc.fecha_creacion else "N/A"
        total_str = f"${doc.total_factura or 0:,.0f}"

        print(
            f"{doc.id:<5} {fecha_str:<12} {doc.total_millas or 0:<8} "
            f"{doc.total_repuestos or 0:<6} {doc.total_servicios or 0:<7} "
            f"{doc.total_otros or 0:<8} {total_str:<10}"
        )

    print("\n=== VERIFICACIÓN DETALLADA POR DOCUMENTO ===\n")

    # Verificar documento por documento
    for doc in documentos[:3]:  # Solo los primeros 3 para detalle
        print(f"DOCUMENTO #{doc.id} - {doc.fecha_creacion}")
        print("-" * 40)

        # Conteo directo sin anotaciones
        millas_directo = (
            VehiculoDocumento.objects.filter(documento=doc).aggregate(total=Sum("kilometraje"))[
                "total"
            ]
            or 0
        )

        repuestos_directo = RepuestoDocumento.objects.filter(documento=doc).count()
        servicios_directo = ServicioDocumento.objects.filter(documento=doc).count()
        otros_directo = ServicioExternoDocumento.objects.filter(documento=doc).count()

        print(f"  Millas - Anotación: {doc.total_millas or 0}, Directo: {millas_directo}")
        print(f"  Repuestos - Anotación: {doc.total_repuestos or 0}, Directo: {repuestos_directo}")
        print(f"  Servicios - Anotación: {doc.total_servicios or 0}, Directo: {servicios_directo}")
        print(f"  Otros - Anotación: {doc.total_otros or 0}, Directo: {otros_directo}")

        # Verificar si hay diferencias
        diferencias = []
        if (doc.total_millas or 0) != millas_directo:
            diferencias.append(f"MILLAS: {doc.total_millas} vs {millas_directo}")
        if (doc.total_repuestos or 0) != repuestos_directo:
            diferencias.append(f"REPUESTOS: {doc.total_repuestos} vs {repuestos_directo}")
        if (doc.total_servicios or 0) != servicios_directo:
            diferencias.append(f"SERVICIOS: {doc.total_servicios} vs {servicios_directo}")
        if (doc.total_otros or 0) != otros_directo:
            diferencias.append(f"OTROS: {doc.total_otros} vs {otros_directo}")

        if diferencias:
            print(f"  ⚠️  DIFERENCIAS ENCONTRADAS: {', '.join(diferencias)}")
        else:
            print("  ✅ CONTEOS CORRECTOS")
        print()

    # Estadísticas generales
    total_docs = Documento.objects.count()
    docs_con_vehiculos = (
        Documento.objects.filter(vehiculodocumento__isnull=False).distinct().count()
    )
    docs_con_repuestos = (
        Documento.objects.filter(repuestodocumento__isnull=False).distinct().count()
    )
    docs_con_servicios = (
        Documento.objects.filter(serviciodocumento__isnull=False).distinct().count()
    )
    docs_con_otros = (
        Documento.objects.filter(servicioexternodocumento__isnull=False).distinct().count()
    )

    print("=== ESTADÍSTICAS GENERALES ===")
    print(f"Total documentos: {total_docs}")
    print(f"Documentos con vehículos: {docs_con_vehiculos}")
    print(f"Documentos con repuestos: {docs_con_repuestos}")
    print(f"Documentos con servicios: {docs_con_servicios}")
    print(f"Documentos con otros servicios: {docs_con_otros}")

    print("\n✅ VERIFICACIÓN COMPLETADA")


if __name__ == "__main__":
    verificar_conteos()
