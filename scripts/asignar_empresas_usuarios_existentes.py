from django.contrib.auth.models import User
from taller.models.empresa import Empresa

# Script para asignar empresa a todos los usuarios que no la tengan
creados = 0
for user in User.objects.all():
    if not hasattr(user, 'empresa'):
        Empresa.objects.create(nombre=user.username, usuario_admin=user)
        creados += 1
print(f"Empresas creadas para usuarios sin empresa: {creados}")
