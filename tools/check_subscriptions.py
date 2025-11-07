from django.contrib.auth import get_user_model
from taller.models import Empresa
from suscripciones.models import Suscripcion

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
