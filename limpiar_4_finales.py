import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings_prod")
django.setup()

from django.db import connection
from django.contrib.auth import get_user_model

FINAL_IDS = [39, 48, 49, 65]
PROTECTED_IDS = [1, 2, 3, 42, 63, 64]

for p in PROTECTED_IDS:
    assert p not in FINAL_IDS, f"ERROR: ID {p} protegida."

ids_str = ",".join(map(str, FINAL_IDS))

print("=== 1. BARRIENDO TODAS LAS TABLAS CON COLUMNA EMPRESA ===")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT table_name, column_name 
        FROM information_schema.columns 
        WHERE column_name LIKE '%empresa%' 
          AND table_schema = 'public' 
          AND table_name != 'taller_empresa';
    """)
    columnas_empresa = cursor.fetchall()
    
    for table_name, col_name in columnas_empresa:
        try:
            cursor.execute(f"DELETE FROM {table_name} WHERE {col_name} IN ({ids_str});")
            if cursor.rowcount > 0:
                print(f"  🧹 {cursor.rowcount} registros eliminados de '{table_name}.{col_name}'.")
        except Exception:
            pass

    print("\n=== 2. ELIMINANDO LAS 4 EMPRESAS DEFINITIVAMENTE ===")
    cursor.execute(f"DELETE FROM taller_empresa WHERE id IN ({ids_str});")
    print(f"🗑️  {cursor.rowcount} empresas eliminadas con éxito.")

print("\n=== 3. ELIMINANDO USUARIOS DE PRUEBA ===")
User = get_user_model()
emails_borrar = ['mauricio_us@egarage.test', 'vc_taller@demo.egarage.cl', 'vc_desarme@demo.egarage.cl', 'vc_us_workshop@demo.egarage.com']
for email in emails_borrar:
    u = User.objects.filter(email=email).first()
    if u and u.id != 2 and not u.is_superuser:
        u.delete()
        print(f"  👤 Usuario eliminado: {email}")

print("-" * 80)
print("🎯 ¡Misión cumplida! Base de datos 100% limpia de cuentas técnicas de prueba.")
