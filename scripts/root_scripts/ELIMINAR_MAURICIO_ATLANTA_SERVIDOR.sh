#!/bin/bash
# Script para eliminar la cuenta mauricioatlanta@gmail.com del servidor

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

python3 << 'PYEOF'
import os
import sys
import django

sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User

email = "mauricioatlanta@gmail.com"

print(f"🔍 Buscando: {email}\n")

# Eliminar EmailAddress PRIMERO (esto bloquea el registro)
try:
    from allauth.account.models import EmailAddress
    email_addresses = EmailAddress.objects.filter(email=email)
    count = email_addresses.count()
    if count > 0:
        print(f"⚠️  Encontrados {count} registro(s) en EmailAddress")
        deleted = email_addresses.delete()
        print(f"✅ {deleted[0]} registro(s) eliminado(s)")
    else:
        print("ℹ️  No hay registros en EmailAddress")
except Exception as e:
    print(f"⚠️  Error EmailAddress: {e}")

# Buscar y eliminar usuario
try:
    user = User.objects.get(email=email)
    print(f"✅ Usuario encontrado: {user.username} (ID: {user.id})")
    
    # Eliminar empresa
    try:
        from taller.models import Empresa
        empresa = user.empresa
        empresa.delete()
        print(f"✅ Empresa eliminada")
    except:
        pass
    
    # Eliminar usuario
    user.delete()
    print(f"✅ Usuario eliminado")
    print(f"\n✅✅✅ Email '{email}' DISPONIBLE ✅✅✅")
    
except User.DoesNotExist:
    print(f"❌ No hay usuario con ese email")
    print(f"\n✅✅✅ Email '{email}' DISPONIBLE (solo se eliminaron EmailAddress) ✅✅✅")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo ""
echo "✅ Proceso completado"



