from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.mecanico import Mecanico
from taller.models.perfilusuario import PerfilUsuario

class Command(BaseCommand):
    help = 'Crea datos de prueba para mecánicos'

    def handle(self, *args, **options):
        self.stdout.write("🔧 Creando datos de prueba para mecánicos...")
        
        # Crear usuario de prueba si no existe
        user, created = User.objects.get_or_create(
            username='admin_taller',
            defaults={
                'email': 'admin@taller.com',
                'first_name': 'Admin',
                'last_name': 'Taller',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f"✅ Usuario creado: {user.username}"))
        else:
            self.stdout.write(f"ℹ️ Usuario ya existe: {user.username}")
        
        # Crear empresa de prueba
        empresa, created = Empresa.objects.get_or_create(
            usuario=user,
            defaults={
                'nombre_taller': 'Taller de Prueba',
                'direccion': 'Calle Falsa 123',
                'telefono': '+1234567890',
                'email': 'taller@prueba.com'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ Empresa creada: {empresa.nombre_taller}"))
        else:
            self.stdout.write(f"ℹ️ Empresa ya existe: {empresa.nombre_taller}")
        
        # Crear perfil de usuario
        perfil, created = PerfilUsuario.objects.get_or_create(
            user=user,
            defaults={
                'empresa': empresa,
                'es_superadmin': False
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ Perfil creado para: {user.username}"))
        else:
            self.stdout.write(f"ℹ️ Perfil ya existe para: {user.username}")
        
        # Crear mecánicos de prueba
        mecanicos_datos = [
            {'nombre': 'Juan Carlos', 'activo': True},
            {'nombre': 'María González', 'activo': True},
            {'nombre': 'Pedro Martínez', 'activo': True},
            {'nombre': 'Ana López', 'activo': False},  # Inactivo para probar filtrado
            {'nombre': 'Luis Rodriguez', 'activo': True},
        ]
        
        for mec_data in mecanicos_datos:
            mecanico, created = Mecanico.objects.get_or_create(
                empresa=empresa,
                nombre=mec_data['nombre'],
                defaults={'activo': mec_data['activo']}
            )
            
            if created:
                status = "✅ ACTIVO" if mecanico.activo else "❌ INACTIVO"
                self.stdout.write(self.style.SUCCESS(f"{status} Mecánico creado: {mecanico.nombre}"))
            else:
                status = "✅ ACTIVO" if mecanico.activo else "❌ INACTIVO"
                self.stdout.write(f"{status} Mecánico ya existe: {mecanico.nombre}")
        
        self.stdout.write(self.style.SUCCESS("\n🎉 Datos de prueba creados exitosamente!"))
        self.stdout.write("\n📝 Para probar:")
        self.stdout.write(f"1. Ve a http://127.0.0.1:8000/admin/ (usuario: {user.username}, password: admin123)")
        self.stdout.write("2. Ve a http://127.0.0.1:8000/configuracion/ para configuración")
        self.stdout.write("3. Ve a http://127.0.0.1:8000/configuracion/mecanicos/ para gestionar mecánicos")
        self.stdout.write("4. Ve a http://127.0.0.1:8000/documentos/ para documentos")
        self.stdout.write("\n🔍 Deberías ver solo los mecánicos activos en formularios de documentos")
