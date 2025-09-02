import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models import Empresa

# Cambiar TODAS las empresas relacionadas con testuser_usa
user = User.objects.get(username='testuser_usa')
print(f"Usuario: {user.username}")

# Buscar por todos los campos posibles
empresas = Empresa.objects.filter(user=user)
print(f"Empresas por campo 'user': {empresas.count()}")
for empresa in empresas:
    print(f"ANTES - Empresa: {empresa.nombre_taller}, País: {empresa.pais}")
    empresa.pais = 'US'
    empresa.save()
    print(f"DESPUÉS - Empresa: {empresa.nombre_taller}, País: {empresa.pais}")

# También por campo usuario (legacy)
empresas2 = Empresa.objects.filter(usuario=user)  
print(f"Empresas por campo 'usuario': {empresas2.count()}")
for empresa in empresas2:
    print(f"ANTES - Empresa legacy: {empresa.nombre_taller}, País: {empresa.pais}")
    empresa.pais = 'US'
    empresa.save()
    print(f"DESPUÉS - Empresa legacy: {empresa.nombre_taller}, País: {empresa.pais}")

print("✅ CAMBIO COMPLETADO")
