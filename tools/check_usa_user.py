from django.contrib.auth import get_user_model

User = get_user_model()

try:
    user = User.objects.get(username="testuser_usa")
    print(f"Usuario: {user.username}")
    print(f"Email: {user.email}")
    print(f"Activo: {user.is_active}")
    print(f"Staff: {user.is_staff}")
    print(f"Superuser: {user.is_superuser}")

    try:
        empresa = user.empresa
        print(f"Empresa: {empresa.nombre_taller}")
        print(f"País: {empresa.pais}")
        print(f"Moneda: {empresa.moneda}")
    except Exception as e:
        print(f"No tiene empresa asociada: {e}")

    # Verificar si tiene suscripción
    try:
        suscripcion = user.empresa.suscripcion
        print(f"Suscripción: {suscripcion.plan}")
        print(f"Estado: {suscripcion.estado}")
        print(f"Vigente: {suscripcion.esta_vigente()}")
    except Exception as e:
        print(f"No tiene suscripción: {e}")

except User.DoesNotExist:
    print("Usuario testuser_usa no existe")
except Exception as e:
    print(f"Error: {e}")
