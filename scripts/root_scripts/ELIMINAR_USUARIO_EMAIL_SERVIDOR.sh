#!/bin/bash
# Script para eliminar un usuario por email del sistema

cd /home/atlantareciclajes/apps/egarage/current && \
python3 << 'PYEOF'
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models import Empresa

# Email a eliminar
email = "mauricioatlanta@gmail.com"

try:
    # Buscar usuario por email
    try:
        user = User.objects.get(email=email)
        print(f"✅ Usuario encontrado: {user.username} (ID: {user.id})")
        print(f"   Email: {user.email}")
        print(f"   Fecha de registro: {user.date_joined}")
        
        # Obtener empresa asociada (OneToOneField)
        empresa = None
        try:
            empresa = user.empresa
            print(f"⚠️  El usuario tiene una empresa asociada:")
            print(f"   - {empresa.nombre_taller} (ID: {empresa.id})")
            print(f"   - País: {empresa.pais}")
        except Empresa.DoesNotExist:
            print("ℹ️  El usuario no tiene empresa asociada")
        
        # Verificar si hay Account de allauth
        try:
            from allauth.account.models import EmailAddress
            email_addresses = EmailAddress.objects.filter(email=email)
            email_count = email_addresses.count()
            if email_count > 0:
                print(f"⚠️  El usuario tiene {email_count} registro(s) en EmailAddress (allauth):")
                for ea in email_addresses:
                    print(f"   - {ea.email} (verificado: {ea.verified})")
        except ImportError:
            pass
        except Exception as e:
            print(f"⚠️  Error al verificar EmailAddress: {e}")
        
        print("\n🗑️  Eliminando usuario y datos asociados...")
        
        # Eliminar empresa primero si existe (aunque CASCADE debería hacerlo automáticamente)
        if empresa:
            print(f"   Eliminando empresa: {empresa.nombre_taller}")
            empresa.delete()
            print(f"✅ Empresa eliminada")
        
        # Eliminar EmailAddress de allauth si existe
        try:
            from allauth.account.models import EmailAddress
            deleted_emails = EmailAddress.objects.filter(email=email).delete()
            if deleted_emails[0] > 0:
                print(f"✅ {deleted_emails[0]} registro(s) de EmailAddress eliminado(s)")
        except:
            pass
        
        # Eliminar usuario (esto debería eliminar automáticamente la empresa por CASCADE)
        username = user.username
        user_id = user.id
        user.delete()
        
        print(f"✅ Usuario '{username}' (ID: {user_id}) eliminado correctamente")
        print(f"✅ Email '{email}' ahora está disponible para registro")
        
    except User.DoesNotExist:
        print(f"❌ No se encontró usuario con email: {email}")
        
        # Verificar si existe por username
        try:
            user_by_username = User.objects.get(username=email)
            print(f"⚠️  Pero existe un usuario con username='{email}' (ID: {user_by_username.id})")
            print(f"   Email del usuario: {user_by_username.email}")
            print("\n🗑️  Eliminando usuario por username...")
            
            # Eliminar empresa si existe
            try:
                empresa = user_by_username.empresa
                print(f"   Eliminando empresa: {empresa.nombre_taller}")
                empresa.delete()
            except:
                pass
            
            # Eliminar EmailAddress
            try:
                from allauth.account.models import EmailAddress
                EmailAddress.objects.filter(email=user_by_username.email).delete()
            except:
                pass
            
            user_by_username.delete()
            print(f"✅ Usuario eliminado correctamente")
            print(f"✅ Email '{email}' ahora está disponible para registro")
        except User.DoesNotExist:
            print("ℹ️  El email ya está disponible para registro")
            
            # Verificar EmailAddress de allauth
            try:
                from allauth.account.models import EmailAddress
                email_addresses = EmailAddress.objects.filter(email=email)
                if email_addresses.exists():
                    print(f"⚠️  Pero hay {email_addresses.count()} registro(s) en EmailAddress (allauth)")
                    print("🗑️  Eliminando registros de EmailAddress...")
                    email_addresses.delete()
                    print(f"✅ Registros de EmailAddress eliminados")
                    print(f"✅ Email '{email}' ahora está completamente disponible")
            except:
                pass
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

PYEOF

echo "✅ Script ejecutado"

