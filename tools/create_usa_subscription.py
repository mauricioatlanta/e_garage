from datetime import datetime, timedelta

from django.contrib.auth import get_user_model

from taller.models.suscripcion import Suscripcion

User = get_user_model()

print("=== CREAR SUSCRIPCIÓN PARA testuser_usa ===")
try:
    user = User.objects.get(username="testuser_usa")
    empresa = user.empresa

    # Verificar si ya tiene suscripción
    try:
        suscripcion_existente = empresa.suscripcion
        print(f"Ya tiene suscripción: {suscripcion_existente.plan}")
        print(f"Estado: {suscripcion_existente.estado}")
        print(f"Vigente: {suscripcion_existente.esta_vigente()}")
    except:
        # Crear suscripción de prueba
        fecha_inicio = datetime.now().date()
        fecha_fin = fecha_inicio + timedelta(days=30)  # 30 días de prueba

        suscripcion = Suscripcion.objects.create(
            empresa=empresa,
            plan="trial",
            estado="activa",
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        print(f"Suscripción creada para {empresa.nombre_taller}")
        print(f"  Plan: {suscripcion.plan}")
        print(f"  Estado: {suscripcion.estado}")
        print(f"  Fecha inicio: {suscripcion.fecha_inicio}")
        print(f"  Fecha fin: {suscripcion.fecha_fin}")
        print(f"  Vigente: {suscripcion.esta_vigente()}")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
