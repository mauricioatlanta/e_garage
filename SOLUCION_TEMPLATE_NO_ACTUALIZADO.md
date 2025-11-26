# 🔧 Solución: Template no actualizado en producción

## 📋 Problema

La página `/us/vehiculos/crear/` en producción muestra una página de login en lugar del formulario de crear vehículo que se ve en localhost.

## 🔍 Causas Posibles

1. **Templates no actualizados en el servidor**
2. **Archivos estáticos no recopilados**
3. **Caché de templates en el servidor**
4. **Problema de autenticación (redirección a login)**
5. **Archivos no se subieron correctamente**

## ✅ SOLUCIÓN PASO A PASO

### Paso 1: Verificar que los templates están actualizados

En el servidor (PythonAnywhere):

```bash
cd /home/atlantareciclajes/apps/egarage/current

# Verificar fecha de modificación del template
ls -la templates/us/en/vehiculos/crear_vehiculo.html

# Comparar con la fecha de modificación en local
# (En tu PC, verifica la fecha del mismo archivo)
```

### Paso 2: Verificar contenido del template en el servidor

```bash
# Ver las primeras líneas del template
head -20 templates/us/en/vehiculos/crear_vehiculo.html

# Debe mostrar el contenido del formulario, no una página de login
```

### Paso 3: Si el template está desactualizado, actualizarlo

**Opción A: Usar Git Pull (si los cambios están en GitHub)**

```bash
cd /home/atlantareciclajes/apps/egarage/current
workon venv_egarage310

# Obtener últimos cambios
git pull origin main

# Limpiar caché
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -name "*.pyc" -delete

# Recopilar archivos estáticos
python manage.py collectstatic --noinput
```

**Opción B: Subir archivo específico con FileZilla**

1. Conectar con FileZilla al servidor
2. Navegar a: `/home/atlantareciclajes/apps/egarage/current/templates/us/en/vehiculos/`
3. Subir el archivo `crear_vehiculo.html` desde tu PC

### Paso 4: Limpiar caché de templates

```bash
# Limpiar caché de Python
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -name "*.pyc" -delete

# Limpiar caché de Django (si usas caché)
python manage.py shell << 'PYTHON'
from django.core.cache import cache
cache.clear()
print("Caché limpiada")
exit()
PYTHON
```

### Paso 5: Recargar la aplicación

En el dashboard de PythonAnywhere:
- Ve a: https://www.pythonanywhere.com/user/atlantareciclajes/
- Pestaña: **"Web"**
- Clic en: **"Reload atlantareciclajes.pythonanywhere.com"**

### Paso 6: Verificar autenticación

Si sigue mostrando login, verifica que estás autenticado:

```bash
# Verificar que el usuario tiene empresa asignada
python manage.py shell << 'PYTHON'
from django.contrib.auth.models import User
user = User.objects.get(username='testuser_usa')
print(f"Usuario: {user.username}")
print(f"Empresa: {user.empresa if hasattr(user, 'empresa') else 'NO TIENE'}")
exit()
PYTHON
```

## 🔍 DIAGNÓSTICO ADICIONAL

### Verificar qué template se está usando

```bash
# Ver el código de la vista
grep -A 10 "def crear_vehiculo" taller/vehiculos/views_fbv.py

# Ver qué template se determina
grep -A 5 "_vehicle_template" taller/vehiculos/views_fbv.py
```

### Verificar logs de errores

En el dashboard de PythonAnywhere:
- Web → Error log
- Buscar errores relacionados con templates o autenticación

## 📝 NOTAS

- La URL `/us/vehiculos/crear/` redirige a `/us/en/vehiculos/crear/`
- La vista requiere `@login_required`
- El template debería ser: `templates/us/en/vehiculos/crear_vehiculo.html` o `templates/taller/us/en/vehiculos/crear_vehiculo.html`

---

**¡Solución lista!** 🚀

