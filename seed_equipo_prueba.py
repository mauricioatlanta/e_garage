"""
seed_equipo_prueba.py
=====================
Crea usuarios ficticios para probar permisos multi-usuario en eGarage.
Roles: Owner (tú), Admin, Vendedor.

Uso:
    python manage.py shell < seed_equipo_prueba.py

Qué hace:
    1. Encuentra la Empresa de mauricioatlanta@gmail.com
    2. Sube el plan a "Taller" si es necesario (owner + 2 usuarios)
    3. Crea 2 usuarios Django ficticios
    4. Crea los TeamMember vinculados a tu Empresa
    5. Imprime tabla de credenciales y checklist de prueba
"""

import django
import os

# ─── Configuración ────────────────────────────────────────────────────────────
OWNER_EMAIL   = "mauricioatlanta@gmail.com"
PLAN_OBJETIVO = "taller"
PASSWORD_TEST = "Test1234!"

USUARIOS_FICTICIOS = [
    {
        "email":      "admin.egarage@test.local",
        "username":   "admin.egarage",
        "first_name": "Carlos",
        "last_name":  "Admin",
        "rol":        "Admin",
        "notas":      "Usuario de prueba — Administrador del negocio",
    },
    {
        "email":      "vendedor.egarage@test.local",
        "username":   "vendedor.egarage",
        "first_name": "Pedro",
        "last_name":  "Vendedor",
        "rol":        "Vendedor",
        "notas":      "Usuario de prueba — Vendedor / Cotizador",
    },
]

# ─── Colores consola ──────────────────────────────────────────────────────────
class C:
    OK   = "\033[92m"
    WARN = "\033[93m"
    ERR  = "\033[91m"
    BOLD = "\033[1m"
    DIM  = "\033[2m"
    RST  = "\033[0m"

def ok(m):   print(f"  {C.OK}✓{C.RST} {m}")
def warn(m): print(f"  {C.WARN}⚠{C.RST} {m}")
def err(m):  print(f"  {C.ERR}✗{C.RST} {m}")
def sep():   print(f"  {C.DIM}{'─' * 58}{C.RST}")
def titulo(m): print(f"\n  {C.BOLD}{m}{C.RST}")

# ─── Imports Django ───────────────────────────────────────────────────────────
from django.contrib.auth.models import User
from taller.models.team_member import TeamMember

try:
    from taller.models.empresa import Empresa
except ImportError:
    from taller.models import Empresa


# ══════════════════════════════════════════════════════════════════════════════
def run():
    print()
    sep()
    print(f"  {C.BOLD}eGarage — Seed de equipo de prueba{C.RST}")
    sep()

    # ── 1. Owner y empresa ────────────────────────────────────────────────
    titulo("[1/4] Buscando empresa")
    try:
        owner = User.objects.get(email__iexact=OWNER_EMAIL)
        ok(f"Owner: {owner.get_full_name() or owner.username} ({owner.email})")
    except User.DoesNotExist:
        err(f"No existe un usuario con email '{OWNER_EMAIL}'")
        err("¿Estás en la base de datos correcta?")
        return

    try:
        empresa = owner.empresa
        ok(f"Empresa: {empresa.nombre_taller}")
        ok(f"Plan actual: {empresa.plan}")
    except Exception:
        err("El owner no tiene Empresa asociada. Completa el onboarding primero.")
        return

    # ── 2. Plan ───────────────────────────────────────────────────────────
    titulo("[2/4] Verificando plan")
    planes_ok = {"taller", "growth", "pro", "business"}
    if (empresa.plan or "").lower() in planes_ok:
        ok(f"Plan '{empresa.plan}' ya permite TeamMembers.")
    else:
        warn(f"Plan '{empresa.plan}' no permite agregar usuarios.")
        warn(f"Cambiando a '{PLAN_OBJETIVO}' para esta prueba…")
        empresa.plan = PLAN_OBJETIVO
        empresa.save(update_fields=["plan"])
        empresa.refresh_from_db()
        ok(f"Plan actualizado a: {empresa.plan}")

    # ── 3. Crear usuarios ─────────────────────────────────────────────────
    titulo("[3/4] Creando usuarios ficticios")
    errores = []

    for d in USUARIOS_FICTICIOS:
        try:
            user, nuevo = User.objects.get_or_create(
                username=d["username"],
                defaults={
                    "email":      d["email"],
                    "first_name": d["first_name"],
                    "last_name":  d["last_name"],
                    "is_active":  True,
                },
            )
            # Siempre actualizar password y datos por si el seed se corre de nuevo
            user.first_name = d["first_name"]
            user.last_name  = d["last_name"]
            user.email      = d["email"]
            user.is_active  = True
            user.set_password(PASSWORD_TEST)
            user.save()

            tm, tm_nuevo = TeamMember.objects.get_or_create(
                user=user,
                empresa=empresa,
                defaults={
                    "rol":        d["rol"],
                    "notas":      d["notas"],
                    "is_active":  True,
                    "creado_por": owner,
                },
            )
            if not tm_nuevo:
                tm.rol      = d["rol"]
                tm.notas    = d["notas"]
                tm.is_active = True
                tm.save()
                warn(f"Ya existía → actualizado: {d['first_name']} ({d['rol']})")
            else:
                ok(f"Creado: {d['first_name']} {d['last_name']} → {d['rol']}")

        except Exception as e:
            errores.append((d["email"], str(e)))
            err(f"Error con {d['email']}: {e}")

    # ── 4. Resumen ────────────────────────────────────────────────────────
    titulo("[4/4] Resumen")
    sep()
    total = TeamMember.objects.filter(empresa=empresa, is_active=True).count()
    print(f"\n  Empresa : {C.BOLD}{empresa.nombre_taller}{C.RST}")
    print(f"  Plan    : {C.BOLD}{empresa.plan}{C.RST}")
    print(f"  Equipo  : {total} miembro(s) activo(s) + owner\n")

    # Tabla de credenciales
    print(f"  {C.BOLD}{'ROL':<12} {'NOMBRE':<18} {'EMAIL':<35} CONTRASEÑA{C.RST}")
    sep()
    nombre_owner = owner.get_full_name() or owner.username
    print(f"  {'Owner':<12} {nombre_owner:<18} {OWNER_EMAIL:<35} (tu contraseña)")
    for d in USUARIOS_FICTICIOS:
        nombre = f"{d['first_name']} {d['last_name']}"
        print(f"  {d['rol']:<12} {nombre:<18} {d['email']:<35} {PASSWORD_TEST}")
    sep()

    if errores:
        print(f"\n  {C.ERR}Errores:{C.RST}")
        for email, msg in errores:
            print(f"    · {email}: {msg}")

    # Checklist de prueba
    print(f"""
  {C.BOLD}Checklist para probar permisos:{C.RST}

  {C.BOLD}Owner{C.RST} (mauricioatlanta@gmail.com)
    □ Ve la sección Suscripción / Plan / Usuarios
    □ Puede agregar y desactivar TeamMembers
    □ Ve todo el negocio (mismo acceso que Admin)

  {C.BOLD}Admin{C.RST} (Carlos)
    □ NO ve la sección Suscripción/Plan
    □ Ve reportes, caja, inventario, configuración del negocio
    □ Puede gestionar clientes, OT, presupuestos

  {C.BOLD}Vendedor{C.RST} (Pedro)
    □ NO ve reportes financieros ni caja
    □ Solo ve sus propias OT y presupuestos
    □ Puede crear clientes y presupuestos

  {C.BOLD}Prueba de límite de plan:{C.RST}
    □ Intenta crear un 3er TeamMember → debe bloquearse
      (plan Taller permite owner + 3, pero es bueno verificar
       que el contador funciona correctamente)

  {C.DIM}Para limpiar: python manage.py shell < seed_limpiar_prueba.py{C.RST}
""")


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
    django.setup()

run()
