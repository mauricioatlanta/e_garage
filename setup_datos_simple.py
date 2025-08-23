"""
Ejecuta esto paso a paso en el shell de Django:
python manage.py shell

Luego copia y pega estos comandos uno por uno:
"""

# 1. Crear usuario admin
from django.contrib.auth.models import User
user, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@test.com', 'is_staff': True, 'is_superuser': True})
if created:
    user.set_password('admin123')
    user.save()
    print("✅ Usuario admin creado")
else:
    print("ℹ️ Usuario admin ya existe")

# 2. Crear empresa
from taller.models.empresa import Empresa
empresa, created = Empresa.objects.get_or_create(usuario=user, defaults={'nombre_taller': 'Mi Taller', 'telefono': '555-1234', 'email': 'taller@test.com'})
print(f"{'✅ Empresa creada' if created else 'ℹ️ Empresa ya existe'}: {empresa.nombre_taller}")

# 3. Crear perfil
from taller.models.perfil_usuario import PerfilUsuario
perfil, created = PerfilUsuario.objects.get_or_create(user=user, defaults={'empresa': empresa})
print(f"{'✅ Perfil creado' if created else 'ℹ️ Perfil ya existe'}")

# 4. Crear técnicos
from taller.models.tecnico import Tecnico
nombres = ['Juan Pérez', 'María López', 'Carlos García', 'Ana Martínez', 'Luis Inactivo']
for i, nombre in enumerate(nombres):
    activo = i < 4  # Los primeros 4 activos, el último inactivo
    tecnico, created = Tecnico.objects.get_or_create(empresa=empresa, nombre=nombre, defaults={'activo': activo})
    if created:
        status = "✅ ACTIVO" if tecnico.activo else "❌ INACTIVO"
        print(f"{status} {tecnico.nombre}")

print("\n🎉 ¡Listo! Ahora prueba:")
print("http://127.0.0.1:8000/configuracion/")  
print("http://127.0.0.1:8000/configuracion/tecnicos/")
print("Usuario: admin / admin123")
