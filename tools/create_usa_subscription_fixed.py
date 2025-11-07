from django.contrib.auth import get_user_model
from taller.models.suscripcion import Suscripcion
from datetime import datetime, timedelta

User = get_user_model()

print("=== CREAR SUSCRIPCIÓN PARA testuser_usa ===")
try:
    user = User.objects.get(username='testuser_usa')
    
    # Verificar si ya tiene suscripción
    try:
        suscripcion_existente = user.suscripcion
        print(f"Ya tiene suscripción: {suscripcion_existente.tipo}")
        print(f"Activa: {suscripcion_existente.activa}")
        print(f"Fecha inicio: {suscripcion_existente.fecha_inicio}")
        print(f"Fecha fin: {suscripcion_existente.fecha_fin}")
        print(f"Vencida: {suscripcion_existente.esta_vencida()}")
    except:
        # Crear suscripción de prueba
        suscripcion = Suscripcion.objects.create(
            user=user,
            tipo='trial',
            activa=True
        )
        
        # Activar la suscripción (esto establece las fechas)
        suscripcion.activar()
        
        print(f"Suscripción creada para {user.username}")
        print(f"  Tipo: {suscripcion.tipo}")
        print(f"  Activa: {suscripcion.activa}")
        print(f"  Fecha inicio: {suscripcion.fecha_inicio}")
        print(f"  Fecha fin: {suscripcion.fecha_fin}")
        print(f"  Vencida: {suscripcion.esta_vencida()}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
