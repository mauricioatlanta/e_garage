# 🔒 Solución Error CSRF 403 en egarage.cl

## ⚠️ Problema
Error "CSRF verification failed" al intentar acceder a `/accounts/` en `egarage.cl`

## ✅ Solución

### 1. Verificar Variables de Entorno en el Servidor

En PythonAnywhere, necesitas configurar las variables de entorno correctamente:

```bash
# En la consola Bash del servidor
cd /home/atlantareciclajes/apps/egarage/current

# Verificar si existe archivo .env
ls -la .env

# Si no existe, crearlo
nano .env
```

### 2. Agregar estas líneas al archivo .env:

```bash
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=egarage.cl,www.egarage.cl
DJANGO_CSRF_TRUSTED_ORIGINS=https://egarage.cl,https://www.egarage.cl,http://egarage.cl,http://www.egarage.cl
```

### 3. O Configurar Directamente en settings.py (Temporal)

Si no puedes usar variables de entorno, el código ya está actualizado para incluir automáticamente `egarage.cl` en `CSRF_TRUSTED_ORIGINS` cuando `DEBUG=False`.

### 4. Verificar que DEBUG esté en False

```bash
# En la consola del servidor
cd /home/atlantareciclajes/apps/egarage/current
workon venv_egarage310
python manage.py shell

# En el shell de Python:
from django.conf import settings
print("DEBUG:", settings.DEBUG)
print("CSRF_TRUSTED_ORIGINS:", settings.CSRF_TRUSTED_ORIGINS)
print("ALLOWED_HOSTS:", settings.ALLOWED_HOSTS)
exit()
```

### 5. Recargar la Aplicación

```bash
# Limpiar caché
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -name "*.pyc" -delete

# Recargar
touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py
```

O desde el Dashboard → Web → Reload

### 6. Verificar que Funcionó

1. Abre: `https://egarage.cl/accounts/login/`
2. Deberías ver el formulario de login sin error 403
3. Intenta hacer login

## 🔍 Diagnóstico

Si el error persiste, verifica:

### A. Verificar configuración actual:

```bash
python manage.py shell -c "from django.conf import settings; print('DEBUG:', settings.DEBUG); print('CSRF_TRUSTED_ORIGINS:', settings.CSRF_TRUSTED_ORIGINS)"
```

### B. Verificar que el dominio esté en ALLOWED_HOSTS:

```bash
python manage.py shell -c "from django.conf import settings; print('ALLOWED_HOSTS:', settings.ALLOWED_HOSTS)"
```

### C. Verificar logs de errores:

En PythonAnywhere Dashboard → Web → Error log

## 📝 Notas Importantes

1. **CSRF_TRUSTED_ORIGINS** debe incluir el protocolo (`https://` o `http://`)
2. **ALLOWED_HOSTS** solo necesita el dominio sin protocolo
3. Si usas HTTPS, asegúrate de que `CSRF_COOKIE_SECURE = True` en producción
4. El código ya está actualizado para incluir automáticamente `egarage.cl` cuando `DEBUG=False`

## 🚨 Si AÚN no funciona:

1. Verifica que el dominio `egarage.cl` esté correctamente configurado en PythonAnywhere
2. Verifica que no haya un proxy/CDN delante que esté modificando los headers
3. Revisa los logs del servidor para más detalles del error

---

**Los cambios en `gestion_taller/settings.py` ya están aplicados y deberían funcionar automáticamente cuando `DEBUG=False`.**







