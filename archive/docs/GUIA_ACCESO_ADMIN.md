# 🔐 Guía de Acceso al Panel de Administración

**Fecha**: 2025-01-27

---

## 📍 URLs DE ADMINISTRACIÓN

### **1. Admin de Django (Estándar)**
```
URL: /admin/
```
Panel estándar de Django para gestionar modelos del sistema.

### **2. Panel de Suscriptores (Nuevo)**
```
URL: /admin/suscriptores/
```
Panel personalizado para gestionar suscriptores, extender planes y enviar notificaciones.

---

## 🔑 REQUISITOS DE ACCESO

### **Para acceder a CUALQUIER panel de admin necesitas**:

1. **Usuario con permisos de staff o superuser**
   - `is_staff = True` O
   - `is_superuser = True`

2. **Estar autenticado**
   - Debes haber iniciado sesión

---

## 🚀 CÓMO ACCEDER

### **OPCIÓN 1: Desde el navegador**

1. **Iniciar sesión**:
   ```
   URL: /accounts/login/
   ```
   O según tu país:
   ```
   /cl/accounts/login/
   /us/accounts/login/
   ```

2. **Acceder al panel de suscriptores**:
   ```
   URL: /admin/suscriptores/
   ```

3. **O acceder al admin de Django**:
   ```
   URL: /admin/
   ```

---

### **OPCIÓN 2: Crear usuario admin desde consola**

Si no tienes un usuario admin, créalo así:

```bash
# Activar entorno virtual (si usas uno)
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Ir al directorio del proyecto
cd /ruta/al/proyecto

# Crear superusuario
python manage.py createsuperuser
```

**Datos que te pedirá**:
- Username (nombre de usuario)
- Email (opcional)
- Password (contraseña)

---

### **OPCIÓN 3: Convertir usuario existente en admin**

```bash
# Abrir shell de Django
python manage.py shell
```

```python
from django.contrib.auth import get_user_model

User = get_user_model()

# Opción A: Por email
usuario = User.objects.get(email='tu_email@ejemplo.com')
usuario.is_staff = True
usuario.is_superuser = True
usuario.save()

# Opción B: Por username
usuario = User.objects.get(username='tu_username')
usuario.is_staff = True
usuario.is_superuser = True
usuario.save()

# Verificar
print(f"Usuario: {usuario.username}")
print(f"Staff: {usuario.is_staff}")
print(f"Superuser: {usuario.is_superuser}")
```

---

## 🔍 VERIFICAR SI ERES ADMIN

### **Desde el shell de Django**:

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model

User = get_user_model()

# Verificar tu usuario
usuario = User.objects.get(email='tu_email@ejemplo.com')
# o
usuario = User.objects.get(username='tu_username')

print(f"Username: {usuario.username}")
print(f"Email: {usuario.email}")
print(f"Is Staff: {usuario.is_staff}")
print(f"Is Superuser: {usuario.is_superuser}")
print(f"Is Active: {usuario.is_active}")
```

---

## ⚠️ SOLUCIÓN DE PROBLEMAS

### **Problema 1: "No tienes permisos para acceder"**

**Solución**:
```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model

User = get_user_model()
usuario = User.objects.get(email='tu_email@ejemplo.com')
usuario.is_staff = True
usuario.is_superuser = True
usuario.save()
```

---

### **Problema 2: "Redirige al login"**

**Causa**: No estás autenticado o la sesión expiró.

**Solución**:
1. Ir a `/accounts/login/`
2. Iniciar sesión
3. Luego ir a `/admin/suscriptores/`

---

### **Problema 3: "404 Not Found" en `/admin/suscriptores/`**

**Causa**: El archivo no está en el servidor o las URLs no están configuradas.

**Solución**:
1. Verificar que existe `taller/views_extra/admin_suscriptores.py`
2. Verificar que en `gestion_taller/urls.py` está:
   ```python
   path("admin/suscriptores/", admin_suscriptores, name="admin_suscriptores"),
   ```
3. Reiniciar servidor si es necesario

---

## 📋 CHECKLIST DE ACCESO

- [ ] Tengo un usuario en el sistema
- [ ] Mi usuario tiene `is_staff = True` o `is_superuser = True`
- [ ] Estoy autenticado (inicié sesión)
- [ ] Puedo acceder a `/admin/` (admin de Django)
- [ ] Puedo acceder a `/admin/suscriptores/` (panel de suscriptores)

---

## 🎯 ACCESO RÁPIDO

### **URLs directas** (después de iniciar sesión):

```
Admin Django:        http://tudominio.com/admin/
Panel Suscriptores:  http://tudominio.com/admin/suscriptores/
Login:               http://tudominio.com/accounts/login/
```

---

## 💡 TIPS

1. **Guardar en favoritos**: Guarda `/admin/suscriptores/` en favoritos para acceso rápido

2. **Verificar permisos**: Si no puedes acceder, verifica que tu usuario tenga `is_staff = True`

3. **Múltiples usuarios admin**: Puedes tener varios usuarios con permisos de admin

4. **Seguridad**: Solo da permisos de admin a usuarios de confianza

---

**Última actualización**: 2025-01-27

