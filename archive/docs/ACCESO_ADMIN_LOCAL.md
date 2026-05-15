# 💻 Acceso a Admin en tu PC Local

**Fecha**: 2025-01-27

---

## 🚀 OPCIÓN 1: Crear Usuario Admin Nuevo (Recomendado)

### **Paso 1: Abrir terminal en el proyecto**

```bash
cd E:\projecto\e_garage
```

### **Paso 2: Crear superusuario**

```bash
python manage.py createsuperuser
```

**Te pedirá**:
- Username: (elige un nombre, ej: `admin`)
- Email: (opcional, ej: `admin@egarage.cl`)
- Password: (elige una contraseña segura)
- Password (again): (confirma la contraseña)

### **Paso 3: Iniciar servidor**

```bash
python manage.py runserver
```

### **Paso 4: Acceder al admin**

Abre tu navegador y ve a:
```
http://localhost:8000/admin/
```

O para el panel de suscriptores:
```
http://localhost:8000/admin/suscriptores/
```

---

## 🔄 OPCIÓN 2: Convertir Usuario Existente en Admin

Si ya tienes un usuario pero no es admin:

### **Paso 1: Abrir shell de Django**

```bash
cd E:\projecto\e_garage
python manage.py shell
```

### **Paso 2: Convertir usuario en admin**

```python
from django.contrib.auth import get_user_model

User = get_user_model()

# Opción A: Por email
usuario = User.objects.get(email='tu_email@ejemplo.com')
usuario.is_staff = True
usuario.is_superuser = True
usuario.save()

# Opción B: Por username
# usuario = User.objects.get(username='tu_username')
# usuario.is_staff = True
# usuario.is_superuser = True
# usuario.save()

# Verificar
print(f"✅ Usuario: {usuario.username}")
print(f"✅ Email: {usuario.email}")
print(f"✅ Is Staff: {usuario.is_staff}")
print(f"✅ Is Superuser: {usuario.is_superuser}")

# Salir
exit()
```

### **Paso 3: Iniciar servidor e iniciar sesión**

```bash
python manage.py runserver
```

Luego ve a:
```
http://localhost:8000/accounts/login/
```

Inicia sesión con tu usuario y luego accede a:
```
http://localhost:8000/admin/
```

---

## 🔍 OPCIÓN 3: Verificar Usuarios Existentes

### **Ver todos los usuarios**

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model

User = get_user_model()

# Ver todos los usuarios
usuarios = User.objects.all()
print(f"Total usuarios: {usuarios.count()}\n")

for u in usuarios:
    print(f"Username: {u.username}")
    print(f"Email: {u.email}")
    print(f"Is Staff: {u.is_staff}")
    print(f"Is Superuser: {u.is_superuser}")
    print(f"Is Active: {u.is_active}")
    print("-" * 40)

exit()
```

---

## 📋 COMANDOS RÁPIDOS

### **Crear superusuario**
```bash
python manage.py createsuperuser
```

### **Iniciar servidor**
```bash
python manage.py runserver
```

### **Abrir shell de Django**
```bash
python manage.py shell
```

### **Verificar usuarios admin**
```bash
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print([u.username for u in User.objects.filter(is_superuser=True)])"
```

---

## 🌐 URLs LOCALES

Una vez que tengas el servidor corriendo:

### **Login**
```
http://localhost:8000/accounts/login/
```

### **Admin de Django**
```
http://localhost:8000/admin/
```

### **Panel de Suscriptores** (si está activo)
```
http://localhost:8000/admin/suscriptores/
```

---

## ⚠️ NOTA IMPORTANTE

**El panel de suscriptores está temporalmente desactivado** porque el archivo `admin_suscriptores.py` no está en el servidor de producción. En tu PC local debería funcionar si el archivo existe.

Para verificar si existe:
```bash
dir taller\views_extra\admin_suscriptores.py
```

Si existe, descomenta las líneas en `gestion_taller/urls.py` que comentamos antes.

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### **Error: "No module named 'django'"**
```bash
# Activar entorno virtual si usas uno
venv\Scripts\activate  # Windows
# o
source venv/bin/activate  # Linux/Mac
```

### **Error: "Port 8000 already in use"**
```bash
# Usar otro puerto
python manage.py runserver 8001
```

### **No puedo iniciar sesión**
- Verifica que el usuario tenga `is_active = True`
- Verifica que el usuario tenga `is_staff = True` o `is_superuser = True`
- Verifica que la contraseña sea correcta

---

## ✅ CHECKLIST

- [ ] Crear superusuario o convertir usuario existente
- [ ] Iniciar servidor (`python manage.py runserver`)
- [ ] Acceder a `http://localhost:8000/admin/`
- [ ] Iniciar sesión con usuario admin
- [ ] Verificar que puedes acceder al panel

---

**Última actualización**: 2025-01-27

