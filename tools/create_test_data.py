from django.contrib.auth import get_user_model

from taller.models import Cliente, Tecnico, Vehiculo
from taller.models.vehiculos import Marca, Modelo

User = get_user_model()

print("=== CREANDO DATOS DE PRUEBA ===")

# Crear datos para Chile
print("\n1. Creando datos para Chile")
try:
    user_cl = User.objects.get(username="test_chile")
    empresa_cl = user_cl.empresa

    # Crear cliente si no existe
    if not empresa_cl.cliente_set.exists():
        Cliente.objects.create(empresa=empresa_cl, nombre="Cliente Test Chile")
        print("OK: Cliente CL creado")

    # Crear tecnico si no existe
    if not empresa_cl.tecnicos.exists():
        Tecnico.objects.create(empresa=empresa_cl, nombre="Tecnico Test Chile")
        print("OK: Tecnico CL creado")

    # Crear marca si no existe
    marca_cl, created = Marca.objects.get_or_create(
        nombre="Toyota", country="CL", defaults={}
    )
    if created:
        print("OK: Marca CL creada")

    # Crear vehiculo si no existe
    if not empresa_cl.vehiculo_set.exists():
        cliente_cl = empresa_cl.cliente_set.first()
        modelo_cl, created = Modelo.objects.get_or_create(
            nombre="Corolla", marca=marca_cl, defaults={}
        )
        Vehiculo.objects.create(
            empresa=empresa_cl,
            cliente=cliente_cl,
            patente="CL1234",
            marca=marca_cl,
            modelo=modelo_cl,
            anio=2020,
        )
        print("OK: Vehiculo CL creado")

    print("OK: Datos CL completos")

except Exception as e:
    print(f"ERROR CL: {e}")

# Crear datos para USA
print("\n2. Creando datos para USA")
try:
    user_us = User.objects.get(username="testuser_usa")
    empresa_us = user_us.empresa

    # Crear cliente si no existe
    if not empresa_us.cliente_set.exists():
        Cliente.objects.create(empresa=empresa_us, nombre="Customer Test USA")
        print("OK: Cliente US creado")

    # Crear tecnico si no existe
    if not empresa_us.tecnicos.exists():
        Tecnico.objects.create(empresa=empresa_us, nombre="Technician Test USA")
        print("OK: Tecnico US creado")

    # Crear marca si no existe
    marca_us, created = Marca.objects.get_or_create(
        nombre="Ford", country="US", defaults={}
    )
    if created:
        print("OK: Marca US creada")

    # Crear vehiculo si no existe
    if not empresa_us.vehiculo_set.exists():
        cliente_us = empresa_us.cliente_set.first()
        modelo_us, created = Modelo.objects.get_or_create(
            nombre="Focus", marca=marca_us, defaults={}
        )
        Vehiculo.objects.create(
            empresa=empresa_us,
            cliente=cliente_us,
            patente="US5678",
            marca=marca_us,
            modelo=modelo_us,
            anio=2020,
        )
        print("OK: Vehiculo US creado")

    print("OK: Datos US completos")

except Exception as e:
    print(f"ERROR US: {e}")

print("\n=== DATOS DE PRUEBA COMPLETADOS ===")
