from django.contrib.auth import get_user_model

User = get_user_model()

print("=== VERIFICAR CREDENCIALES DE testuser_usa ===")
try:
    user = User.objects.get(username="testuser_usa")

    print(f"Usuario: {user.username}")
    print(f"Email: {user.email}")
    print(f"Activo: {user.is_active}")
    print(f"Staff: {user.is_staff}")
    print(f"Superuser: {user.is_superuser}")

    # Verificar suscripción
    try:
        suscripcion = user.suscripcion
        print(f"Suscripción: {suscripcion.tipo}")
        print(f"Activa: {suscripcion.activa}")
        print(f"Vigente: {not suscripcion.esta_vencida()}")
    except:
        print("No tiene suscripción")

    # Verificar empresa
    try:
        empresa = user.empresa
        print(f"Empresa: {empresa.nombre_taller}")
        print(f"País: {empresa.pais}")
        print(f"Moneda: {empresa.moneda}")
    except:
        print("No tiene empresa asociada")

    print("\n=== CREDENCIALES DE ACCESO ===")
    print("Usuario: testuser_usa")
    print("Contraseña: (la que configuraste al crear el usuario)")
    print("URL: http://127.0.0.1:8000/us/accounts/login/")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
