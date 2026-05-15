# 🔑 Cambiar Contraseña de Admin

**Usuario**: mauricio

---

## 🚀 MÉTODO RÁPIDO: Cambiar Contraseña

### **Opción 1: Desde la terminal (Recomendado)**

```bash
cd E:\projecto\e_garage
python manage.py changepassword mauricio
```

Te pedirá:
- Password: (nueva contraseña)
- Password (again): (confirma)

---

### **Opción 2: Desde el shell de Django**

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model

User = get_user_model()
usuario = User.objects.get(username='mauricio')

# Cambiar contraseña
usuario.set_password('tu_nueva_contraseña')
usuario.save()

print("✅ Contraseña cambiada exitosamente")
print(f"Usuario: {usuario.username}")
print(f"Email: {usuario.email}")

exit()
```

---

## 🔍 VERIFICAR ESTADO DEL USUARIO

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model

User = get_user_model()
usuario = User.objects.get(username='mauricio')

print("=" * 50)
print("INFORMACIÓN DEL USUARIO")
print("=" * 50)
print(f"Username: {usuario.username}")
print(f"Email: {usuario.email}")
print(f"Is Active: {usuario.is_active}")
print(f"Is Staff: {usuario.is_staff}")
print(f"Is Superuser: {usuario.is_superuser}")
print(f"Has usable password: {usuario.has_usable_password()}")
print("=" * 50)

# Si algo está mal, corregirlo
if not usuario.is_active:
    print("⚠️ Usuario inactivo, activando...")
    usuario.is_active = True
    usuario.save()

if not usuario.is_staff:
    print("⚠️ Usuario no es staff, corrigiendo...")
    usuario.is_staff = True
    usuario.save()

if not usuario.is_superuser:
    print("⚠️ Usuario no es superuser, corrigiendo...")
    usuario.is_superuser = True
    usuario.save()

print("✅ Usuario verificado y corregido")
exit()
```

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### **Problema 1: "Usuario no existe"**

Crear nuevo superusuario:
```bash
python manage.py createsuperuser
```

---

### **Problema 2: "Usuario inactivo"**

Activar usuario:
```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.get(username='mauricio')
u.is_active = True
u.save()
exit()
```

---

### **Problema 3: "No tiene permisos de staff"**

Dar permisos:
```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.get(username='mauricio')
u.is_staff = True
u.is_superuser = True
u.save()
exit()
```

---

## ✅ PASOS COMPLETOS PARA ARREGLAR

1. **Cambiar contraseña**:
   ```bash
   python manage.py changepassword mauricio
   ```

2. **Verificar y corregir permisos**:
   ```bash
   python manage.py shell
   ```
   ```python
   from django.contrib.auth import get_user_model
   User = get_user_model()
   u = User.objects.get(username='mauricio')
   u.is_active = True
   u.is_staff = True
   u.is_superuser = True
   u.save()
   print("✅ Usuario configurado correctamente")
   exit()
   ```

3. **Iniciar servidor**:
   ```bash
   python manage.py runserver
   ```

4. **Acceder al admin**:
   ```
   http://localhost:8000/admin/
   ```

5. **Iniciar sesión**:
   - Username: `mauricio`
   - Password: (la nueva contraseña que configuraste)

---

## 🔐 CONTRASEÑA SEGURA

Recomendaciones:
- Mínimo 8 caracteres
- Incluir mayúsculas y minúsculas
- Incluir números
- Incluir caracteres especiales (opcional)

Ejemplo: `Admin123!` o `Mauricio2025!`

---

**Última actualización**: 2025-01-27

