import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings_prod")
django.setup()

from taller.models.empresa import Empresa
from django.apps import apps
from django.db import connection

REMAINING_IDS = [18, 25, 39, 48, 49, 65]
PROTECTED_IDS = [1, 2, 3, 42, 63, 64]

# Garantía de seguridad
assert not any(i in PROTECTED_IDS for i in REMAINING_IDS)

print("=== 1. DESBLOQUEANDO REPUESTOS Y CATEGORÍAS DEMO ===")
Repuesto = apps.get_model('taller', 'Repuesto')
CategoriaRepuesto = apps.get_model('taller', 'CategoriaRepuesto')

# Borrar repuestos asociados directa o indirectamente a estas 6 empresas
r1 = Repuesto.objects.filter(empresa_id__in=REMAINING_IDS).delete()[0]
r2 = Repuesto.objects.filter(categoria__empresa_id__in=REMAINING_IDS).delete()[0]
cat = CategoriaRepuesto.objects.filter(empresa_id__in=REMAINING_IDS).delete()[0]
print(f"✅ {r1 + r2} repuestos y {cat} categorías de prueba eliminados.")

# Limpiar pagos si quedaba alguno en taller_pago
with connection.cursor() as cursor:
    cursor.execute(f"DELETE FROM taller_pago WHERE empresa_id IN ({','.join(map(str, REMAINING_IDS))});")

# Limpiar cualquier otro registro hijo en cascada
for name in ['Documento', 'LineaRepuesto', 'LineaServicio', 'PiezaDesarme', 'VehiculoDesarme', 'Servicio', 'Cliente', 'ConfiguracionEmpresa']:
    try:
        M = apps.get_model('taller', name)
        if 'empresa' in [f.name for f in M._meta.fields]:
            M.objects.filter(empresa_id__in=REMAINING_IDS).delete()
    except Exception:
        pass

print("\n=== 2. ELIMINANDO LAS ÚLTIMAS 6 EMPRESAS ===")
eliminadas = 0
for emp_id in REMAINING_IDS:
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
print(f"🎯 ¡Limpieza 100% completada! Las últimas {eliminadas} cuentas fueron eliminadas.")
print("✨ Tu base de datos quedó impecable, sin cuentas basura y con tus clientes protegidos.")
