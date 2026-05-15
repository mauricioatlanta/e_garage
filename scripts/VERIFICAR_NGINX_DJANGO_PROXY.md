# Verificación de Configuración Nginx + Django Proxy

## Problema
Django está detrás de un proxy reverso (Nginx) y necesita saber que la conexión original era HTTPS para evitar redirecciones incorrectas.

## Solución

### 1. Verificar/Actualizar Nginx

**Ubicación típica:** `/etc/nginx/sites-enabled/egarage.cl`

Dentro de `location / { ... }` debe existir:

```nginx
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header Host $host;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Real-IP $remote_addr;
```

**Si falta `X-Forwarded-Proto`, agrégalo.**

Luego verificar y recargar:
```bash
sudo nginx -t && sudo systemctl reload nginx
```

### 2. Verificar Django Settings

**Archivo:** `gestion_taller/settings.py` o `gestion_taller/settings/prod.py`

Debe existir:
```python
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
```

✅ **Ya está configurado en el proyecto**

### 3. Reiniciar Gunicorn

```bash
sudo systemctl restart egarage-gunicorn
```

### 4. Validación

#### Test 1: Verificar que no hay redirección 301 incorrecta
```bash
curl -I http://127.0.0.1:8001/cl/es/centro-operaciones/ | head -n 12
```

**Esperado:**
- `200` (si estás logueado)
- `302` hacia `/accounts/login/` (si no estás logueado)
- **NUNCA** `301` a `https://127.0.0.1:8001`

#### Test 2: Verificar header X-Forwarded-Proto
```bash
curl -s -H "X-Forwarded-Proto: https" -H "Host: egarage.cl" \
  http://127.0.0.1:8001/accounts/login/ -I | head -n 15
```

Si con este header deja de redirigir raro, entonces es 100% problema del header de Nginx.

#### Test 3: Verificar desde el dominio público
```bash
curl -s -L -o /dev/null -w "CODE=%{http_code} FINAL=%{url_effective}\n" \
  https://egarage.cl/cl/es/centro-operaciones/
```

**Esperado:** `CODE=200` o `CODE=302` (nunca `301`)

## Seguridad Adicional

### Bloquear acceso a archivos ocultos

En Nginx, agregar dentro del `server { ... }`:

```nginx
# Bloquear .env, .git, etc. (excepto .well-known para Let's Encrypt)
location ~ /\.(?!well-known) {
    deny all;
    return 404;
}
```

Esto bloquea intentos de bots de leer `.env`, archivos AWS, etc.

## Checklist Final

- [ ] Nginx tiene `proxy_set_header X-Forwarded-Proto $scheme;` en `location /`
- [ ] Django tiene `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`
- [ ] Nginx recargado: `sudo nginx -t && sudo systemctl reload nginx`
- [ ] Gunicorn reiniciado: `sudo systemctl restart egarage-gunicorn`
- [ ] Test 1 pasa (no hay 301 incorrecto)
- [ ] Test 2 pasa (header funciona)
- [ ] Test 3 pasa (dominio público funciona)
- [ ] Bloqueo de archivos ocultos configurado

## Archivos de Referencia

- `scripts/nginx_egarage_example.conf` - Configuración completa de ejemplo
- `gestion_taller/settings.py` - Ya tiene `SECURE_PROXY_SSL_HEADER` configurado
- `gestion_taller/settings/prod.py` - Ya tiene `SECURE_PROXY_SSL_HEADER` configurado
