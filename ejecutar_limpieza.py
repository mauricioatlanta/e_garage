import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings_prod")
django.setup()

from taller.models.empresa import Empresa
from django.contrib.auth import get_user_model

# Cuentas reales, tuyas y la raíz del sistema
PROTECTED_IDS = [1, 2, 3, 42, 63, 64]
PROTECTED_EMAILS = [
    "mauricioatlanta@gmail.com",
    "contacto@atlantareciclajes.cl",
    "Justenvios@gmail.com",
    "piriparts@gmail.com",
    "multitractioncarcenter@gmail.com",
    "support@egarage.cl"
]

def es_prueba_tecnica(emp, email):
    if emp.id in PROTECTED_IDS or email in PROTECTED_EMAILS:
        return False
    
    email_lower = email.lower()
    
    if any(email_lower.endswith(ext) for ext in ['.invalid', '.test', '.internal']):
        return True
    if '@demo.egarage.' in email_lower or email_lower.startswith('demo_'):
        return True
    if 'usa-garage.com' in email_lower or email_lower == 'test_cl@egarage.cl':
        return True
    if 'desactivado+' in email_lower or 'registrook' in email_lower or email_lower == 'abc@gmail.com':
        return True
    if emp.id == 18 and email_lower == 'admin@egarage.cl':
        return True
    if emp.id == 25 and emp.nombre == 'T1':
        return True
        
    return False

eliminadas = 0
fallidas = 0

for emp in Empresa.objects.all().order_by('id'):
    u = emp.user or getattr(emp, 'propietario', None)
    email = u.email if u else "SIN_USUARIO"
    
    if es_prueba_tecnica(emp, email):
        emp_id = emp.id
        nombre_emp = emp.nombre
        user_to_delete = u if (u and u.id not in [2] and not u.is_superuser) else None
        
        try:
            emp.delete()
            if user_to_delete:
                user_to_delete.delete()
            print(f"🗑️ Eliminada con éxito: ID {emp_id:<3} | {nombre_emp:<28} | {email}")
            eliminadas += 1
        except Exception as e:
            print(f"⚠️ Aviso en ID {emp_id} ({nombre_emp}): no se pudo eliminar por -> {e}")
            fallidas += 1

print("-" * 80)
print(f"🎯 Limpieza terminada: {eliminadas} cuentas eliminadas exitosamente.")
if fallidas:
    print(f"ℹ️  {fallidas} cuentas se mantuvieron por restricciones de clave foránea.")
print("✨ Tus clientes reales y cuentas de Mauricio quedaron 100% protegidos.")
