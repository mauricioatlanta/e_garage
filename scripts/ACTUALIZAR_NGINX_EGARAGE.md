# Actualizar Configuración de Nginx - egarage

## Estado Actual

✅ **Archivo encontrado:** `/etc/nginx/sites-available/egarage`  
✅ **Ya habilitado:** `/etc/nginx/sites-enabled/egarage` (enlace simbólico)  
✅ **Header X-Forwarded-Proto:** Ya está configurado según `nginx -T`

## Verificación

La configuración activa muestra que ya tienes:

```nginx
location / {
    proxy_pass http://127.0.0.1:8001;

    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;  # ✅ YA ESTÁ
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Real-IP $remote_addr;

    proxy_redirect off;
}
```

## Mejoras Recomendadas

### 1. Ver el archivo completo

```bash
sudo cat /etc/nginx/sites-available/egarage
```

### 2. Agregar bloqueo de archivos ocultos (seguridad)

Agregar dentro del bloque `server { ... }` que tiene `server_name egarage.cl;`:

```nginx
# Bloquear acceso a .env, .git, etc. (excepto .well-known para Let's Encrypt)
location ~ /\.(?!well-known) {
    deny all;
    return 404;
}
```

### 3. Mejorar timeouts (opcional pero recomendado)

Agregar en `location / { ... }`:

```nginx
location / {
    proxy_pass http://127.0.0.1:8001;

    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Real-IP $remote_addr;

    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    proxy_redirect off;
}
```

## Pasos para Actualizar

### Paso 1: Hacer backup
```bash
sudo cp /etc/nginx/sites-available/egarage /etc/nginx/sites-available/egarage.backup.$(date +%Y%m%d_%H%M%S)
```

### Paso 2: Editar archivo
```bash
sudo nano /etc/nginx/sites-available/egarage
```

### Paso 3: Verificar sintaxis
```bash
sudo nginx -t
```

### Paso 4: Recargar Nginx
```bash
sudo systemctl reload nginx
```

### Paso 5: Reiniciar Gunicorn
```bash
sudo systemctl restart egarage-gunicorn
```

## Validación

### Test 1: Verificar que no hay 301 incorrecto
```bash
curl -I http://127.0.0.1:8001/cl/es/centro-operaciones/ | head -n 12
```

**Esperado:** `200` o `302` (nunca `301` a `https://127.0.0.1:8001`)

### Test 2: Verificar dominio público
```bash
curl -s -L -o /dev/null -w "CODE=%{http_code} FINAL=%{url_effective}\n" \
  https://egarage.cl/cl/es/centro-operaciones/
```

**Esperado:** `CODE=200` o `CODE=302`

## Nota Importante

Si el header `X-Forwarded-Proto` ya está configurado (como muestra `nginx -T`), entonces el problema puede estar en:

1. **Django no está leyendo el header correctamente** - Verificar que `SECURE_PROXY_SSL_HEADER` esté configurado
2. **Cache de Nginx** - Probar con `curl` directo
3. **Configuración de Django en producción** - Verificar que esté usando `settings/prod.py` correctamente

## Verificar Configuración de Django

```bash
sudo -u egarage -H bash -lc '
cd /srv/egarage
set -a; source /srv/egarage/.env 2>/dev/null || true; set +a
/srv/egarage/venv/bin/python manage.py shell -c "
from django.conf import settings
print(\"SESSION_ENGINE:\", settings.SESSION_ENGINE)
print(\"SECURE_PROXY_SSL_HEADER:\", settings.SECURE_PROXY_SSL_HEADER)
print(\"SECURE_SSL_REDIRECT:\", settings.SECURE_SSL_REDIRECT)
"
'
```

**Esperado:**
- `SESSION_ENGINE: django.contrib.sessions.backends.db`
- `SECURE_PROXY_SSL_HEADER: ('HTTP_X_FORWARDED_PROTO', 'https')`
- `SECURE_SSL_REDIRECT: True` (o `False` si prefieres)
