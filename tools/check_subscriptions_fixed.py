from django.contrib.auth import get_user_model

from taller.models import Empresa, Suscripcion

User = get_user_model()

print("=== EMPRESAS CON SUSCRIPCIONES ===")
try:
    suscripciones = Suscripcion.objects.all()
    for sus in suscripciones:
        print(f"Empresa: {sus.empresa.nombre_taller}")
        print(f"  Usuario: {sus.empresa.user.username}")
        print(f"  País: {sus.empresa.pais}")
        print(f"  Plan: {sus.plan}")
        print(f"  Estado: {sus.estado}")
        print(f"  Vigente: {sus.esta_vigente()}")
        print("---")
except Exception as e:
    print(f"Error al obtener suscripciones: {e}")

print("\n=== EMPRESAS SIN SUSCRIPCIONES ===")
try:
    empresas_sin_sus = Empresa.objects.filter(suscripcion__isnull=True)
    for emp in empresas_sin_sus:
        print(f"Empresa: {emp.nombre_taller}")
        print(f"  Usuario: {emp.user.username}")
        print(f"  País: {emp.pais}")
        print("---")
except Exception as e:
    print(f"Error al obtener empresas sin suscripción: {e}")

print("\n=== CREAR SUSCRIPCIÓN PARA testuser_usa ===")
try:
    user = User.objects.get(username="testuser_usa")
    empresa = user.empresa

    # Crear suscripción de prueba
    suscripcion = Suscripcion.objects.create(
        empresa=empresa,
        plan="trial",
        estado="activa",
        fecha_inicio="2025-10-06",
        fecha_fin="2025-11-06",
    )
    print(f"Suscripción creada para {empresa.nombre_taller}")
    print(f"  Plan: {suscripcion.plan}")
    print(f"  Estado: {suscripcion.estado}")
    print(f"  Vigente: {suscripcion.esta_vigente()}")

except Exception as e:
    print(f"Error al crear suscripción: {e}")
