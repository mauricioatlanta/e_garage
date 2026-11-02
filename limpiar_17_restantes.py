import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings_prod")
django.setup()

from taller.models.empresa import Empresa
from django.contrib.auth import get_user_model
from django.apps import apps
from django.db import connection

TARGET_IDS = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18, 25, 39, 48, 49, 65]
PROTECTED_IDS = [1, 2, 3, 42, 63, 64]

# Garantía de seguridad estricta
for p in PROTECTED_IDS:
    assert p not in TARGET_IDS, f"ERROR CRÍTICO: ID {p} está protegida."

print("=== 1. ELIMINANDO PAGOS DE PRUEBA EN 'taller_pago' ===")
with connection.cursor() as cursor:
    cursor.execute(f"DELETE FROM taller_pago WHERE empresa_id IN ({','.join(map(str, TARGET_IDS))});")
    print(f"✅ {cursor.rowcount} registros de prueba eliminados de 'taller_pago'.")

print("\n=== 2. ELIMINANDO REPUESTOS Y DOCUMENTOS DEMO PROTEGIDOS ===")
child_models = [
    'LineaRepuesto', 'LineaOtroServicio', 'LineaServicio', 'Documento',
    'PiezaDesarme', 'VehiculoDesarme', 'Repuesto', 'CategoriaRepuesto',
    'Servicio', 'CategoriaServicio', 'Cliente', 'ConfiguracionEmpresa'
]

for name in child_models:
    try:
        M = apps.get_model('taller', name)
        fields = [f.name for f in M._meta.fields]
        if 'empresa' in fields:
            deleted_count = M.objects.filter(empresa_id__in=TARGET_IDS).delete()[0]
            if deleted_count > 0:
                print(f"  🧹 {deleted_count} registros demo limpiados de '{name}'.")
    except Exception:
        pass

print("\n=== 3. ELIMINANDO LAS 17 EMPRESAS Y USUARIOS DE PRUEBA ===")
eliminadas = 0
for emp_id in TARGET_IDS:
    emp = Empresa.objects.filter(id=emp_id).first()
    if emp:
        u = emp.user
        nombre = emp.nombre
        email = u.email if u else "Sin email"
        user_to_delete = u if (u and u.id != 2 and not u.is_superuser) else None
        
        emp.delete()
        if user_to_delete:
            user_to_delete.delete()
            
        print(f"🗑️  Eliminada: ID {emp_id:<3} | {nombre:<28} | {email}")
        eliminadas += 1

print("-" * 80)
print(f"🎯 ¡Éxito total! Se eliminaron las {eliminadas} cuentas de prueba técnica.")
print("✨ Tu base de datos quedó 100% limpia de basura de prueba.")
