from django.contrib.auth import get_user_model

User = get_user_model()
usuarios = ['taller1', 'taller2']
for username in usuarios:
    try:
        user = User.objects.get(username=username)
        user.set_password('laila2013')
        user.save()
        print(f"Contraseña de {username} actualizada a 'laila2013'")
    except User.DoesNotExist:
        print(f"Usuario {username} no encontrado")
