#!/usr/bin/env python
"""
Script para crear una sesión de usuario para acceder al documento 45
"""
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from decimal import Decimal

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.db.models import (  # Se agrega import para usar Sum en la agregación
    DecimalField, ExpressionWrapper, F, Q, Sum)
from django.db.models.functions import Coalesce
from django.shortcuts import \
    render  # Importar render para devolver respuestas HTTP
from django.test import Client

from taller.documentos.models import Documento  # <- usa SIEMPRE esta
from taller.models import ConfiguracionEmpresa
from taller.utils.empresa import get_or_create_empresa  # tu helper

MONEY = DecimalField(max_digits=14, decimal_places=2)


def main():
    print("=== ACCESO AL DOCUMENTO 45 ===")

    # El documento 45 pertenece al usuario test_diagnostic
    username = "test_diagnostic"

    try:
        user = User.objects.get(username=username)
        print(f"✓ Usuario encontrado: {user.username}")

        # Crear cliente de prueba
        client = Client()

        # Intentar login (necesitamos la contraseña)
        print("\n=== INFORMACIÓN PARA ACCESO ===")
        print(f"Para acceder al documento 45, necesitas:")
        print(f"1. Iniciar sesión como: {username}")
        print(f"2. Visitar la URL: http://127.0.0.1:8000/us/documentos/form/45/")
        print("\nSi no conoces la contraseña, puedes:")
        print("- Cambiar la contraseña del usuario")
        print("- O crear un nuevo documento para tu usuario actual")

        print("\n=== DOCUMENTOS DISPONIBLES PARA OTROS USUARIOS ===")

        empresa = get_or_create_empresa(None)  # Se asigna empresa usando el helper

        for user in User.objects.all()[:5]:
            try:
                docs_count = Documento.objects.filter(empresa=empresa).count()
                if docs_count > 0:
                    docs = list(
                        Documento.objects.filter(empresa=empresa).values_list(
                            "id", flat=True
                        )[:3]
                    )
                    print(f"- {user.username}: {docs_count} documentos {docs}")
            except Exception as e:
                continue

    except User.DoesNotExist:
        print(f"✗ Usuario {username} no existe")


# Reemplazar la función documentos(request) existente con la lógica de cálculo correcta


def documentos(request):
    empresa = get_or_create_empresa(request)

    qs = (
        Documento.objects.filter(empresa=empresa, tipo__in=["FACTURA", "BOLETA"])
        .select_related("cliente")
        .prefetch_related("lineas_repuesto", "lineas_servicio", "lineas_otro_servicio")
    )

    if any(f.name == "gran_total" for f in Documento._meta.get_fields()):
        total_facturas = (
            qs.aggregate(total=Coalesce(Sum("gran_total"), 0))["total"] or 0
        )
    else:
        rep_bruto = qs.aggregate(
            v=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("lineas_repuesto__cantidad")
                        * F("lineas_repuesto__precio_unitario")
                        - F("lineas_repuesto__descuento"),
                        output_field=MONEY,
                    )
                ),
                0,
            )
        )["v"] or Decimal("0")

        serv_bruto = qs.aggregate(
            v=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("lineas_servicio__cantidad")
                        * F("lineas_servicio__precio_unitario")
                        - F("lineas_servicio__descuento"),
                        output_field=MONEY,
                    )
                ),
                0,
            )
        )["v"] or Decimal("0")

        otros_bruto = qs.aggregate(
            v=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("lineas_otro_servicio__cantidad")
                        * F("lineas_otro_servicio__precio_cliente"),
                        output_field=MONEY,
                    )
                ),
                0,
            )
        )["v"] or Decimal("0")

        cfg = ConfiguracionEmpresa.objects.get(empresa=empresa)
        iva_factor = (
            (Decimal(cfg.tasa_impuesto or 0) / Decimal("100"))
            if (empresa.pais == "CL")
            else Decimal("0")
        )
        rep_iva = (
            rep_bruto * iva_factor
            if getattr(cfg, "aplicar_impuesto_por_defecto", True)
            else Decimal("0")
        )
        total_facturas = rep_bruto + rep_iva + serv_bruto + otros_bruto

    context = {
        "documentos": qs.order_by("-fecha_emision"),
        "total_facturas": total_facturas,
    }
    return render(request, "cl/documentos.html", context)


if __name__ == "__main__":
    main()
