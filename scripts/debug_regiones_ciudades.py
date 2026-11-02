#!/usr/bin/env python
"""
Script para verificar datos de regiones y ciudades de Chile
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.clientes.forms import ClienteForm
from taller.models.region_ciudad import TallerCiudad, TallerRegion
from taller.models.ubicacion import Ciudad as CiudadUSA
from taller.models.ubicacion import Estado as EstadoUSA


def main():
    print("🔍 DEBUG: Verificando datos de regiones y ciudades\n")

    # 1. Verificar regiones y ciudades de Chile
    print("1. DATOS DE CHILE:")
    print("=" * 40)
    regiones = TallerRegion.objects.all()
    print(f"Regiones de Chile: {regiones.count()}")

    if regiones.count() > 0:
        for region in regiones[:5]:  # Mostrar solo las primeras 5
            ciudades = TallerCiudad.objects.filter(region=region)
            print(f"  - {region.nombre}: {ciudades.count()} ciudades")
    else:
        print("❌ No hay regiones de Chile en la base de datos")

    # 2. Verificar estados y ciudades de USA
    print("\n2. DATOS DE USA:")
    print("=" * 40)
    estados = EstadoUSA.objects.all()
    print(f"Estados de USA: {estados.count()}")

    if estados.count() > 0:
        for estado in estados[:5]:  # Mostrar solo los primeros 5
            ciudades_usa = CiudadUSA.objects.filter(estado=estado)
            print(f"  - {estado.nombre}: {ciudades_usa.count()} ciudades")
    else:
        print("❌ No hay estados de USA en la base de datos")

    # 3. Verificar formulario para usuario de Chile
    print("\n3. FORMULARIO PARA USUARIO CHILE:")
    print("=" * 40)
    try:
        user_cl = User.objects.get(username="testuser_cl")
        empresa_cl = user_cl.empresa
        print(f"Usuario: {user_cl.username}")
        print(f"Empresa: {empresa_cl.nombre_taller}")
        print(f"País: {empresa_cl.pais}")

        # Crear formulario
        form = ClienteForm(empresa=empresa_cl)
        print(f"País del formulario: {form.pais}")

        # Verificar campos visibles
        campos_ocultos = []
        campos_visibles = []

        for field_name, field in form.fields.items():
            if hasattr(field.widget, "input_type") and field.widget.input_type == "hidden":
                campos_ocultos.append(field_name)
            elif field_name in [
                "region",
                "ciudad",
                "estado_usa",
                "ciudad_usa",
                "zipcode",
            ]:
                campos_visibles.append(field_name)

        print(f"Campos visibles de ubicación: {campos_visibles}")
        print(f"Campos ocultos: {campos_ocultos}")

        # Verificar queryset de regiones
        if "region" in form.fields:
            region_qs = form.fields["region"].queryset
            print(f"Regiones disponibles en el formulario: {region_qs.count()}")

    except User.DoesNotExist:
        print("❌ Usuario testuser_cl no encontrado")
    except Exception as e:
        print(f"❌ Error: {e}")

    # 4. Verificar formulario para usuario de USA
    print("\n4. FORMULARIO PARA USUARIO USA:")
    print("=" * 40)
    try:
        user_usa = User.objects.get(username="testuser_usa")
        empresa_usa = user_usa.empresa
        print(f"Usuario: {user_usa.username}")
        print(f"Empresa: {empresa_usa.nombre_taller}")
        print(f"País: {empresa_usa.pais}")

        # Crear formulario
        form = ClienteForm(empresa=empresa_usa)
        print(f"País del formulario: {form.pais}")

        # Verificar campos visibles
        campos_ocultos = []
        campos_visibles = []

        for field_name, field in form.fields.items():
            if hasattr(field.widget, "input_type") and field.widget.input_type == "hidden":
                campos_ocultos.append(field_name)
            elif field_name in [
                "region",
                "ciudad",
                "estado_usa",
                "ciudad_usa",
                "zipcode",
            ]:
                campos_visibles.append(field_name)

        print(f"Campos visibles de ubicación: {campos_visibles}")
        print(f"Campos ocultos: {campos_ocultos}")

        # Verificar queryset de estados
        if "estado_usa" in form.fields:
            estado_qs = form.fields["estado_usa"].queryset
            print(f"Estados disponibles en el formulario: {estado_qs.count()}")

    except User.DoesNotExist:
        print("❌ Usuario testuser_usa no encontrado")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
