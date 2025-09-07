#!/usr/bin/env python
"""
Script simple para crear un repuesto ficticio usando SQLite
"""
import os
import sys

import django

# Configurar Django con SQLite
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
django.setup()


def main():
    print("🚀 CREANDO REPUESTO FICTICIO")
    print("=" * 50)

    from taller.forms.repuesto import RepuestoForm
    from taller.models.empresa import Empresa
    from taller.models.repuesto import Repuesto
    from taller.models.tienda import Tienda

    # Mostrar datos existentes
    print(f"📊 Empresas: {Empresa.objects.count()}")
    print(f"📊 Tiendas: {Tienda.objects.count()}")
    print(f"📊 Repuestos: {Repuesto.objects.count()}")

    if Empresa.objects.count() == 0:
        print("❌ No hay empresas. Creando una empresa de prueba...")
        empresa = Empresa.objects.create(
            nombre_taller="Taller de Prueba", empresa="Empresa de Prueba"
        )
        print(f"✅ Empresa creada: {empresa}")
    else:
        empresa = Empresa.objects.first()
        print(f"✅ Usando empresa existente: {empresa}")

    if Tienda.objects.count() == 0:
        print("❌ No hay tiendas. Creando una tienda de prueba...")
        tienda = Tienda.objects.create(nombre="Tienda de Prueba")
        print(f"✅ Tienda creada: {tienda}")
    else:
        tienda = Tienda.objects.first()
        print(f"✅ Usando tienda existente: {tienda}")

    # Datos para el repuesto ficticio
    datos = {
        "tienda": tienda.pk,
        "nombre_repuesto": "Filtro de Aceite Ficticio",
        "part_number": "FICT-2025",
        "precio_compra": "$15.000",
        "precio_venta": "$22.500",
        "stock": 8,
    }

    print(f"\n📝 Creando repuesto con datos:")
    for key, value in datos.items():
        print(f"   {key}: {value}")

    # Validar formulario
    form = RepuestoForm(datos)
    if form.is_valid():
        print("\n✅ Formulario válido!")
        print(f"📊 Datos limpios: {form.cleaned_data}")

        # Guardar repuesto
        repuesto = form.save(commit=False)
        repuesto.empresa = empresa
        repuesto.save()

        print(f"\n🎉 ¡REPUESTO FICTICIO CREADO!")
        print(f"   🆔 ID: {repuesto.id}")
        print(f"   📦 Nombre: {repuesto.nombre_repuesto}")
        print(f"   🔢 Part Number: {repuesto.part_number}")
        print(f"   💰 Precio Compra: ${repuesto.precio_compra:,}")
        print(f"   🏷️  Precio Venta: ${repuesto.precio_venta:,}")
        print(f"   📦 Stock: {repuesto.stock}")
        print(f"   🏪 Tienda: {repuesto.tienda}")
        print(f"   🏢 Empresa: {repuesto.empresa}")

        # Mostrar totales actualizados
        total_repuestos = Repuesto.objects.count()
        print(f"\n📊 Total de repuestos en BD: {total_repuestos}")

    else:
        print("❌ Errores en el formulario:")
        for field, errors in form.errors.items():
            print(f"   {field}: {list(errors)}")


if __name__ == "__main__":
    main()
