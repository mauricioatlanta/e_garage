# Generated migration for copying data from usuario to user field

from django.db import migrations

def migrate_usuario_to_user(apps, schema_editor):
    """Migrar datos del campo usuario al campo user"""
    Empresa = apps.get_model('taller', 'Empresa')
    
    for empresa in Empresa.objects.all():
        if empresa.usuario and not empresa.user:
            empresa.user = empresa.usuario
            empresa.save()
            print(f"✅ Migrado empresa {empresa.nombre_taller}: {empresa.usuario.username}")

def reverse_migration(apps, schema_editor):
    """Revertir migración copiando de user a usuario"""
    Empresa = apps.get_model('taller', 'Empresa')
    
    for empresa in Empresa.objects.all():
        if empresa.user and not empresa.usuario:
            empresa.usuario = empresa.user
            empresa.save()

class Migration(migrations.Migration):

    dependencies = [
        ('taller', '0006_add_user_field_migration'),
    ]

    operations = [
        migrations.RunPython(migrate_usuario_to_user, reverse_migration),
    ]
