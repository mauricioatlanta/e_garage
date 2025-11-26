# 🔍 VERIFICAR: Empresa del Usuario vs Empresa del Documento

## ✅ Diagnóstico

El documento con `pk=2` **SÍ existe** y pertenece a la **empresa 3**.

El usuario tiene **1 documento** que es el documento #2.

## 🔍 Problema Posible

El usuario `testuser_usa` puede no estar asociado a la empresa 3, o hay un problema con el filtro en `get_queryset()`.

## ✅ Verificación Necesaria

Ejecuta estos comandos en la Bash Console del servidor:

```bash
cd /home/atlantareciclajes/apps/egarage/current
python manage.py shell
```

Luego en Python:

```python
from taller.models import Documento
from django.contrib.auth.models import User

# 1. Verificar el usuario
user = User.objects.get(username='testuser_usa')
print(f"Usuario: {user.username}")
print(f"Usuario tiene empresa: {hasattr(user, 'empresa')}")

# 2. Verificar la empresa del usuario
if hasattr(user, 'empresa'):
    empresa_user = user.empresa
    print(f"Empresa del usuario: ID={empresa_user.id}, Nombre={empresa_user.nombre_taller}")
else:
    print("⚠️ Usuario NO tiene empresa asociada")

# 3. Verificar el documento
doc = Documento.objects.get(pk=2)
print(f"\nDocumento #2:")
print(f"  - Empresa ID: {doc.empresa_id}")
print(f"  - Empresa: {doc.empresa.nombre_taller if doc.empresa else 'N/A'}")

# 4. Verificar si coinciden
if hasattr(user, 'empresa'):
    if user.empresa_id == doc.empresa_id:
        print("\n✅ Las empresas COINCIDEN - El documento debería ser accesible")
    else:
        print(f"\n❌ Las empresas NO COINCIDEN:")
        print(f"   Usuario empresa ID: {user.empresa_id}")
        print(f"   Documento empresa ID: {doc.empresa_id}")
        print("   Por eso el documento no se encuentra en el queryset filtrado")
else:
    print("\n❌ Usuario sin empresa - Por eso el queryset está vacío")

# 5. Verificar el queryset filtrado
if hasattr(user, 'empresa'):
    qs = Documento.objects.filter(empresa=user.empresa)
    print(f"\nDocumentos en queryset filtrado: {qs.count()}")
    for d in qs:
        print(f"  - Documento #{d.id}")
else:
    print("\n⚠️ No se puede filtrar porque el usuario no tiene empresa")
```

---

## 🔧 Soluciones Posibles

### **Solución 1: Asociar Usuario a la Empresa Correcta**

Si el usuario no está asociado a la empresa 3:

```python
from taller.models import Documento, Empresa
from django.contrib.auth.models import User

user = User.objects.get(username='testuser_usa')
doc = Documento.objects.get(pk=2)
empresa_doc = doc.empresa

# Asociar usuario a la empresa del documento
user.empresa = empresa_doc
user.save()

print(f"✅ Usuario {user.username} ahora está asociado a empresa {empresa_doc.id}")
```

### **Solución 2: Verificar si hay Múltiples Empresas**

```python
from taller.models import Empresa

# Ver todas las empresas
empresas = Empresa.objects.all()
print(f"Total empresas: {empresas.count()}")
for emp in empresas:
    print(f"  - Empresa ID={emp.id}: {emp.nombre_taller}")
    users = emp.user_set.all()
    print(f"    Usuarios: {users.count()}")
    for u in users:
        print(f"      - {u.username}")
```

---

**Fecha**: 2025-11-25
**Problema**: Documento existe pero no se encuentra en queryset filtrado
**Causa probable**: Usuario no asociado a la empresa del documento

