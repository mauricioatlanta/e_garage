import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings_prod")
django.setup()

from taller.models.empresa import Empresa
from django.contrib.auth import get_user_model

PROTECTED_IDS = [2, 3, 42, 63, 64]
PROTECTED_EMAILS = [
    "mauricioatlanta@gmail.com",
    "contacto@atlantareciclajes.cl",
    "Justenvios@gmail.com",
    "piriparts@gmail.com",
    "multitractioncarcenter@gmail.com"
]

def es_prueba_tecnica(emp, email):
    if emp.id in PROTECTED_IDS or email in PROTECTED_EMAILS:
        return False
    
    email_lower = email.lower()
    
    # 1. Dominios ficticios o de test
    if any(email_lower.endswith(ext) for ext in ['.invalid', '.test', '.internal']):
        return True
    if '@demo.egarage.' in email_lower or email_lower.startswith('demo_'):
        return True
    if 'usa-garage.com' in email_lower or email_lower == 'test_cl@egarage.cl':
        return True
        
    # 2. Pruebas técnicas específicas
    if 'desactivado+' in email_lower or 'registrook' in email_lower or email_lower == 'abc@gmail.com':
        return True
    if emp.id == 18 and email_lower == 'admin@egarage.cl':
        return True
    if emp.id == 1 and email_lower == 'support@egarage.cl':
        return True
    if emp.id == 25 and emp.nombre == 'T1':
        return True
        
    return False

candidatas = []
for emp in Empresa.objects.all().order_by('id'):
    u = emp.user or getattr(emp, 'propietario', None)
    email = u.email if u else "SIN_USUARIO"
    if es_prueba_tecnica(emp, email):
        candidatas.append((emp, u, email))

print(f"\n🔍 SIMULACIÓN: Se encontraron {len(candidatas)} cuentas de prueba técnica para eliminar:")
print("-" * 80)
for emp, u, email in candidatas:
    autos = emp.vehiculos_desarme.count() if hasattr(emp, 'vehiculos_desarme') else 0
    print(f"🗑️  A eliminar -> ID {emp.id:<3} | {emp.nombre:<28} | {email:<35} | ({autos} autos)")

print("-" * 80)
print(f"🛡️  Cuentas protegidas que NUNCA se tocan: {PROTECTED_IDS}")
print("⚠️  Modo simulación: La base de datos no fue modificada.")
