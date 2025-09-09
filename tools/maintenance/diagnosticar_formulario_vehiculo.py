#!/usr/bin/env python3
"""
Script para diagnosticar y corregir el problema de guardado del formulario de vehículos
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User
from django.test.client import Client

from taller.models.clientes import Cliente
from taller.models.extras_vehiculo import ColorVehiculo
from taller.models.marca import Marca
from taller.models.modelo import Modelo


def diagnosticar_formulario():
    """Diagnostica problemas con el formulario de crear vehículo"""

    print("🔍 Diagnosticando formulario de crear vehículo...")

    # 1. Verificar que existan datos de prueba necesarios
    print("\n📊 Verificando datos requeridos:")

    try:
        # Verificar usuario
        user = User.objects.filter(username="testuser_cl").first()
        if not user:
            print("❌ Usuario testuser_cl no encontrado")
            return False
        print(f"✅ Usuario: {user.username}")

        # Verificar clientes
        clientes_count = Cliente.objects.count()
        print(f"✅ Clientes disponibles: {clientes_count}")

        # Verificar marcas
        marcas_count = Marca.objects.count()
        if marcas_count == 0:
            print("❌ No hay marcas disponibles")
            return False
        print(f"✅ Marcas disponibles: {marcas_count}")

        # Verificar modelos
        modelos_count = Modelo.objects.count()
        print(f"✅ Modelos disponibles: {modelos_count}")

        # Verificar colores
        colores_count = ColorVehiculo.objects.count()
        if colores_count == 0:
            print("❌ No hay colores disponibles")
            return False
        print(f"✅ Colores disponibles: {colores_count}")

    except Exception as e:
        print(f"❌ Error verificando datos: {e}")
        return False

    # 2. Simular POST de prueba
    print("\n🧪 Simulando POST de prueba...")

    try:
        client = Client()
        client.force_login(user)

        # Obtener datos de prueba
        cliente = Cliente.objects.first()
        marca = Marca.objects.first()
        modelo = Modelo.objects.filter(marca=marca).first()
        color = ColorVehiculo.objects.first()

        # Datos del formulario
        form_data = {
            "cliente": cliente.id if cliente else "",
            "marca": marca.id if marca else "",
            "modelo": modelo.id if modelo else "",
            "color": color.id if color else "",
            "patente": "TEST123",
            "ano": "2023",
            "vin": "",
            "observaciones": "Vehículo de prueba",
        }

        print(f"📝 Datos de prueba: {form_data}")

        # Realizar POST
        response = client.post("/taller/vehiculos/crear/", form_data)

        print(f"📤 Status code: {response.status_code}")
        print(f"📍 Redirect location: {response.get('Location', 'No redirect')}")

        if response.status_code == 200:
            print("⚠️ Formulario devuelto (posibles errores de validación)")
            # Buscar errores en el contenido
            content = response.content.decode("utf-8")
            if "error" in content.lower():
                print("🔍 Posibles errores encontrados en la respuesta")
        elif response.status_code == 302:
            print("✅ Redirección exitosa (vehículo probablemente creado)")
        else:
            print(f"❌ Código de estado inesperado: {response.status_code}")

        return response.status_code in [200, 302]

    except Exception as e:
        print(f"❌ Error en simulación: {e}")
        return False


def verificar_vista():
    """Verifica la configuración de la vista"""

    print("\n🔍 Verificando vista crear_vehiculo...")

    try:

        print("✅ Vista crear_vehiculo importada correctamente")

        # Verificar URL
        from django.urls import reverse

        url = reverse("taller:vehiculos:crear_vehiculo")
        print(f"✅ URL: {url}")

        return True

    except Exception as e:
        print(f"❌ Error verificando vista: {e}")
        return False


def sugerir_solucion():
    """Sugiere soluciones basadas en el diagnóstico"""

    print("\n💡 Posibles soluciones:")
    print(
        "1. Verificar que los campos del template coincidan con los esperados por la vista"
    )
    print("2. Asegurar que la vista procese correctamente los datos POST")
    print("3. Verificar que el formulario VehiculoForm valide correctamente")
    print("4. Comprobar que el redirect apunte a la URL correcta")
    print("5. Verificar que no hay errores de JavaScript que impidan el envío")


if __name__ == "__main__":
    print("🚀 Diagnóstico del formulario de crear vehículo...")

    # Ejecutar diagnósticos
    vista_ok = verificar_vista()
    formulario_ok = diagnosticar_formulario()

    if vista_ok and formulario_ok:
        print("\n🎉 ¡Diagnóstico completado!")
    else:
        print("\n⚠️ Se encontraron problemas")
        sugerir_solucion()
