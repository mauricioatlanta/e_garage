# Verificación de Configuración Nginx + Cloudflare

## ✅ Configuraciones Django Confirmadas

En `settings.py` tenemos:

```python
# 🔥 OBLIGATORIO detrás de Cloudflare
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ❌ APÁGALO por ahora (para evitar bucles)
SECURE_SSL_REDIRECT = False
```

**Nota:** Si más adelante quieres activar `SECURE_SSL_REDIRECT = True`, está bien porque con `SECURE_PROXY_SSL_HEADER` configurado, Django ya entiende el proxy.

## 🔍 Verificar Configuraciones en el Servidor

### 1. Verificar Django Settings

Ejecuta en el servidor:

```bash
sudo -u egarage -H bash -lc '
cd /srv/egarage
set -a; source /srv/egarage/.env; set +a
/srv/egarage/venv/bin/python - <<PY
from django.conf import settings
print("SECURE_PROXY_SSL_HEADER:", getattr(settings,"SECURE_PROXY_SSL_HEADER", None))
print("SECURE_SSL_REDIRECT:", getattr(settings,"SECURE_SSL_REDIRECT", None))
PY
'
```

**Resultado esperado:**
```
SECURE_PROXY_SSL_HEADER: ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT: False
```

### 2. Resetear y Reiniciar Gunicorn

```bash
sudo systemctl reset-failed egarage-gunicorn
sudo systemctl restart egarage-gunicorn
systemctl is-active egarage-gunicorn && echo "Gunicorn estable ✅"
```

### 3. Verificar Configuración de Nginx

Ver las primeras 240 líneas:

```bash
sudo sed -n '1,240p' /etc/nginx/sites-available/egarage
```

## ⚠️ Puntos Críticos a Verificar en Nginx

### ✅ Bloque Puerto 80 (HTTP → HTTPS)

Debe tener solo UNA redirección:

```nginx
server {
    listen 80;
    server_name egarage.cl www.egarage.cl;
    return 301 https://$host$request_uri;  # Solo una redirección
}
```

### ✅ Bloque Puerto 443 (HTTPS)

Debe tener:

```nginx
server {
    listen 443 ssl http2;
    server_name egarage.cl www.egarage.cl;
    
    # Certificados SSL
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:8001;
        # ⚠️ CRÍTICO: Esta línea informa a Django que usa HTTPS
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

### ❌ Errores Comunes a Evitar

1. **Doble `location /` en el bloque 443** - Solo debe haber uno
2. **`proxy_pass` en el bloque 80** - El bloque 80 solo debe redirigir
3. **Falta `proxy_set_header X-Forwarded-Proto https;`** - Es esencial
4. **Múltiples redirecciones** - Solo una en el bloque 80

### 🔧 Verificar Sintaxis de Nginx

```bash
sudo nginx -t
```

Si hay errores, corrígelos antes de reiniciar.

### 🔄 Reiniciar Nginx

```bash
sudo systemctl restart nginx
```

## 📋 Checklist Final

- [ ] `SECURE_PROXY_SSL_HEADER` configurado en Django
- [ ] `SECURE_SSL_REDIRECT = False` (o `True` si prefieres, pero con el header configurado)
- [ ] Bloque 80 solo redirige (una sola redirección)
- [ ] Bloque 443 tiene `proxy_set_header X-Forwarded-Proto https;`
- [ ] Solo un `location /` en el bloque 443
- [ ] Gunicorn activo y estable
- [ ] Nginx sin errores de sintaxis
- [ ] Probar en ventana de incógnito
