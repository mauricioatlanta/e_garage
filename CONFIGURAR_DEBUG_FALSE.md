# 🔧 Configurar DEBUG=False en PythonAnywhere

## ⚠️ PROBLEMA CRÍTICO
El servidor está ejecutándose con `DEBUG = True`, lo cual:
- Expone información sensible en errores
- Causa problemas de CSRF
- No es seguro para producción

## ✅ SOLUCIÓN: Configurar Variable de Entorno

### Opción 1: Archivo .env (Recomendado)

1. **Conectarte al servidor:**
   ```bash
   # En PythonAnywhere, consola Bash
   cd /home/atlantareciclajes/apps/egarage/current
   ```

2. **Crear o editar archivo .env:**
   ```bash
   nano .env
   # O si prefieres usar el editor de archivos del dashboard
   ```

3. **Agregar estas líneas:**
   ```bash
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=egarage.cl,www.egarage.cl
   DJANGO_CSRF_TRUSTED_ORIGINS=https://egarage.cl,https://www.egarage.cl,http://egarage.cl,http://www.egarage.cl
   ```

4. **Guardar y salir:**
   - Si usas nano: `Ctrl+X`, luego `Y`, luego `Enter`

### Opción 2: Variables de Entorno en PythonAnywhere Dashboard

1. Ve a: https://www.pythonanywhere.com/web_app_setup/
2. Busca tu aplicación
3. Haz clic en "Environment variables"
4. Agrega:
   - `DJANGO_DEBUG` = `False`
   - `DJANGO_ALLOWED_HOSTS` = `egarage.cl,www.egarage.cl`
   - `DJANGO_CSRF_TRUSTED_ORIGINS` = `https://egarage.cl,https://www.egarage.cl,http://egarage.cl,http://www.egarage.cl`

### Opción 3: Modificar settings.py directamente (Temporal)

Si no puedes usar variables de entorno, puedes modificar temporalmente:

```python
# En gestion_taller/settings.py, línea 27
DEBUG = env_bool("DJANGO_DEBUG", False)  # Cambiar True por False
```

**⚠️ ADVERTENCIA:** Esto no es recomendable porque se perderá en el próximo `git pull`. Mejor usa variables de entorno.

## 🔍 Verificar que Funcionó

Después de configurar, ejecuta:

```bash
cd /home/atlantareciclajes/apps/egarage/current
workon venv_egarage310
python manage.py shell

# En el shell:
from django.conf import settings
print("DEBUG:", settings.DEBUG)
print("CSRF_TRUSTED_ORIGINS:", settings.CSRF_TRUSTED_ORIGINS)
print("ALLOWED_HOSTS:", settings.ALLOWED_HOSTS)
exit()
```

Deberías ver:
- `DEBUG: False`
- `CSRF_TRUSTED_ORIGINS` con `egarage.cl`
- `ALLOWED_HOSTS` con `egarage.cl`

## 🔄 Recargar la Aplicación

Después de cambiar las variables de entorno:

```bash
# Limpiar caché
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null

# Recargar
touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py
```

O desde el Dashboard → Web → Reload

## ✅ Verificar que el Error CSRF se Solucionó

1. Abre: `https://egarage.cl/accounts/login/`
2. Deberías ver el formulario de login sin error 403
3. Intenta hacer login

## 📝 Notas Importantes

- **Los cambios en `settings.py` ya están aplicados** para incluir `egarage.cl` en CSRF_TRUSTED_ORIGINS incluso si DEBUG=True
- **Pero es CRÍTICO poner DEBUG=False** en producción por seguridad
- Las variables de entorno tienen prioridad sobre el código

---

**Después de configurar DEBUG=False, el error CSRF debería desaparecer.**







