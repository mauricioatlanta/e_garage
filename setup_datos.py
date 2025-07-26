"""
Ejecuta esto para crear un usuario admin y datos de prueba
"""

# Crear superusuario
from django.contrib.auth.models import User
user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@test.com', 
        'is_staff': True,
        'is_superuser': True
    }
)
if created:
    user.set_password('admin123')
    user.save()
    print(f"✅ Superusuario creado: admin / admin123")
else:
    print(f"ℹ️ Superusuario ya existe: admin")

# Crear empresa
from taller.models.empresa import Empresa
empresa, created = Empresa.objects.get_or_create(
    usuario=user,
    defaults={
        'nombre_taller': 'Mi Taller de Prueba',
        'telefono': '555-1234',
        'email': 'taller@test.com'
    }
)
if created:
    print(f"✅ Empresa creada: {empresa.nombre_taller}")
else:
    print(f"ℹ️ Empresa ya existe: {empresa.nombre_taller}")

# Crear perfil
from taller.models.perfil_usuario import PerfilUsuario
perfil, created = PerfilUsuario.objects.get_or_create(
    user=user,
    defaults={
        'empresa': empresa,
        'es_superadmin': False
    }
)
if created:
    print(f"✅ Perfil creado")
else:
    print(f"ℹ️ Perfil ya existe")

# Crear mecánicos
from taller.models.mecanico import Mecanico
mecanicos_datos = [
    'Juan Pérez - Mecánico Jefe',
    'María González - Especialista en Frenos', 
    'Carlos López - Electricista',
    'Ana Martínez - Diagnóstico',
    'Luis Rodríguez - Suspensión'
]

for i, nombre in enumerate(mecanicos_datos):
    activo = i < 4  # Los primeros 4 activos, el último inactivo
    mecanico, created = Mecanico.objects.get_or_create(
        empresa=empresa,
        nombre=nombre,
        defaults={'activo': activo}
    )
    if created:
        status = "✅ ACTIVO" if mecanico.activo else "❌ INACTIVO" 
        print(f"{status} Mecánico: {mecanico.nombre}")

print("\n🎉 ¡Datos creados! Ahora puedes:")
print("1. Ingresar a http://127.0.0.1:8000/admin/ con admin / admin123")
print("2. Probar http://127.0.0.1:8000/configuracion/")
print("3. Probar http://127.0.0.1:8000/configuracion/mecanicos/")
