# ✅ Checklist Final - Verificación Post-Fix

## 📋 Resumen de Correcciones Aplicadas

1. ✅ **X-Forwarded-Proto en Nginx**: Header crítico para que Django sepa que está detrás de HTTPS
2. ✅ **Rutas Placeholder en .env.systemd**: Reemplazadas por rutas reales de producción
3. ✅ **SECURE_PROXY_SSL_HEADER en Django**: Ya configurado en `settings_prod.py`

---

## 🔍 Verificación Paso a Paso

### 1. Verificar X-Forwarded-Proto en Nginx

```bash
# Verificar que el header está presente
sudo grep -r "X-Forwarded-Proto" /etc/nginx/sites-enabled /etc/nginx/sites-available

# O usar el script de verificación
sudo bash scripts/fix_nginx_x_forwarded_proto.sh
```

**Resultado esperado:**
```
✅ Header X-Forwarded-Proto encontrado
proxy_set_header X-Forwarded-Proto $scheme;
```

**Si falta, corregir con:**
```bash
sudo bash scripts/fix_nginx_x_forwarded_proto_auto.sh
```

---

### 2. Verificar Configuración de Django

```bash
# Verificar que SECURE_PROXY_SSL_HEADER está configurado
cd /srv/egarage  # Ajustar ruta según tu setup
source venv/bin/activate  # si usas venv
python manage.py shell
```

```python
from django.conf import settings
print(f"SECURE_PROXY_SSL_HEADER: {settings.SECURE_PROXY_SSL_HEADER}")
print(f"SECURE_SSL_REDIRECT: {settings.SECURE_SSL_REDIRECT}")
```

**Resultado esperado:**
```
SECURE_PROXY_SSL_HEADER: ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT: True
```

---

### 3. Verificar Rutas en .env.systemd

```bash
# Buscar y verificar el archivo
sudo find /etc/systemd /srv /opt /var/www -name ".env.systemd" -type f 2>/dev/null

# Ver rutas actuales
sudo grep -E "^(STATIC_ROOT|MEDIA_ROOT)=" /ruta/al/.env.systemd
```

**Resultado esperado:**
```
STATIC_ROOT=/srv/egarage/staticfiles
MEDIA_ROOT=/srv/egarage/media
```

**NO debe tener:**
```
STATIC_ROOT=/ruta/a/staticfiles  ❌
MEDIA_ROOT=/ruta/a/media  ❌
```

**Si tiene rutas placeholder, corregir con:**
```bash
sudo bash scripts/fix_env_systemd_rutas.sh
```

---

### 4. Verificar que los Directorios Existen

```bash
# Verificar directorios
ls -ld /srv/egarage/staticfiles
ls -ld /srv/egarage/media

# Verificar permisos
stat /srv/egarage/staticfiles
stat /srv/egarage/media
```

**Resultado esperado:**
- Los directorios deben existir
- Permisos: `755` para staticfiles, `775` para media
- Propietario: `egarage:www-data` (o según tu configuración)

---

### 5. Verificar que Nginx Apunta a las Rutas Correctas

```bash
# Verificar configuración de Nginx
sudo grep -A 5 "location /static/" /etc/nginx/sites-enabled/egarage
sudo grep -A 5 "location /media/" /etc/nginx/sites-enabled/egarage
```

**Resultado esperado:**
```nginx
location /static/ {
    alias /srv/egarage/staticfiles/;
    ...
}

location /media/ {
    alias /srv/egarage/media/;
    ...
}
```

---

### 6. Probar el Sitio Web

```bash
# Probar desde el servidor
curl -I https://egarage.cl/accounts/login/ | head -n 10
```

**Resultado esperado:**
```
HTTP/2 200
...
```

**NO debe aparecer:**
- `301` o `302` (redirecciones inesperadas)
- `500` (error interno)
- `502` (bad gateway)

---

### 7. Verificar Logs

```bash
# Logs de Nginx
sudo tail -n 50 /var/log/nginx/error.log

# Logs de Gunicorn
sudo journalctl -u egarage-gunicorn -n 30 --no-pager
```

**Resultado esperado:**
- Sin errores críticos
- Sin mensajes de redirección infinita
- Sin errores de permisos

---

## 🚀 Comandos de Verificación Rápida

Ejecuta estos comandos en secuencia:

```bash
# 1. Verificar X-Forwarded-Proto
echo "=== 1. X-Forwarded-Proto ==="
sudo grep "X-Forwarded-Proto" /etc/nginx/sites-enabled/* /etc/nginx/sites-available/* 2>/dev/null | head -1

# 2. Verificar rutas en .env.systemd
echo ""
echo "=== 2. Rutas .env.systemd ==="
ENV_FILE=$(sudo find /etc/systemd /srv /opt /var/www -name ".env.systemd" -type f 2>/dev/null | head -1)
if [ -n "$ENV_FILE" ]; then
    sudo grep -E "^(STATIC_ROOT|MEDIA_ROOT)=" "$ENV_FILE"
else
    echo "⚠️  No se encontró .env.systemd"
fi

# 3. Verificar directorios
echo ""
echo "=== 3. Directorios ==="
ls -ld /srv/egarage/staticfiles /srv/egarage/media 2>/dev/null || echo "⚠️  Directorios no encontrados"

# 4. Probar sitio
echo ""
echo "=== 4. Test HTTP ==="
curl -I https://egarage.cl/accounts/login/ 2>&1 | head -5

# 5. Verificar servicio
echo ""
echo "=== 5. Estado Servicio ==="
sudo systemctl is-active egarage-gunicorn
```

---

## ✅ Checklist Final

- [ ] X-Forwarded-Proto configurado en Nginx
- [ ] SECURE_PROXY_SSL_HEADER configurado en Django
- [ ] Rutas placeholder reemplazadas en .env.systemd
- [ ] Directorios staticfiles y media creados con permisos correctos
- [ ] Nginx apunta a las rutas correctas
- [ ] Servicio egarage-gunicorn está activo
- [ ] Sitio web responde correctamente (HTTP 200)
- [ ] No hay errores en logs de Nginx
- [ ] No hay errores en logs de Gunicorn
- [ ] No hay redirecciones inesperadas (301/302)

---

## 🔧 Script de Verificación Completa

Guarda este script como `verificar_fix_completo.sh`:

```bash
#!/bin/bash
# Script de verificación completa post-fix

echo "=========================================="
echo "🔍 Verificación Completa Post-Fix"
echo "=========================================="
echo ""

# 1. X-Forwarded-Proto
echo "[1] Verificando X-Forwarded-Proto..."
if sudo grep -q "X-Forwarded-Proto" /etc/nginx/sites-enabled/* /etc/nginx/sites-available/* 2>/dev/null; then
    echo "✅ X-Forwarded-Proto configurado"
else
    echo "❌ X-Forwarded-Proto NO configurado"
fi

# 2. Rutas .env.systemd
echo ""
echo "[2] Verificando rutas en .env.systemd..."
ENV_FILE=$(sudo find /etc/systemd /srv /opt /var/www -name ".env.systemd" -type f 2>/dev/null | head -1)
if [ -n "$ENV_FILE" ]; then
    if sudo grep -q "STATIC_ROOT=/ruta/a" "$ENV_FILE" || sudo grep -q "MEDIA_ROOT=/ruta/a" "$ENV_FILE"; then
        echo "❌ Rutas placeholder encontradas"
    else
        echo "✅ Rutas configuradas correctamente"
        sudo grep -E "^(STATIC_ROOT|MEDIA_ROOT)=" "$ENV_FILE"
    fi
else
    echo "⚠️  No se encontró .env.systemd"
fi

# 3. Directorios
echo ""
echo "[3] Verificando directorios..."
if [ -d "/srv/egarage/staticfiles" ] && [ -d "/srv/egarage/media" ]; then
    echo "✅ Directorios existen"
    ls -ld /srv/egarage/staticfiles /srv/egarage/media
else
    echo "❌ Directorios no encontrados"
fi

# 4. Servicio
echo ""
echo "[4] Verificando servicio..."
if sudo systemctl is-active --quiet egarage-gunicorn; then
    echo "✅ Servicio activo"
else
    echo "❌ Servicio inactivo"
fi

# 5. Test HTTP
echo ""
echo "[5] Probando sitio web..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://egarage.cl/accounts/login/)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Sitio responde correctamente (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "⚠️  Redirección detectada (HTTP $HTTP_CODE)"
else
    echo "❌ Error HTTP $HTTP_CODE"
fi

echo ""
echo "=========================================="
echo "✅ Verificación completada"
echo "=========================================="
```

---

## 📞 Si Algo Falla

1. **Redirección 301 inesperada**: Verificar X-Forwarded-Proto en Nginx
2. **Error 500**: Revisar logs de Gunicorn: `sudo journalctl -u egarage-gunicorn -n 50`
3. **Archivos estáticos no cargan**: Verificar rutas en Nginx y permisos de directorios
4. **Permisos denegados**: Verificar ownership: `sudo chown -R egarage:www-data /srv/egarage/staticfiles /srv/egarage/media`

---

## 🎯 Resultado Final Esperado

Al completar todas las verificaciones:

- ✅ `curl -I https://egarage.cl/accounts/login/` → HTTP/2 200
- ✅ Sin errores en logs
- ✅ Archivos estáticos se cargan correctamente
- ✅ No hay redirecciones inesperadas
- ✅ El sitio funciona normalmente

**🎉 Incidente cerrado**
