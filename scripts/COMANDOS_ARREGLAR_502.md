# 🔧 Comandos para Arreglar 502 Bad Gateway

## 📋 Información Encontrada:
- **Código:** `/srv/egarage`
- **Nginx apunta a:** `http://127.0.0.1:8001`
- **Servicio:** `egarage-gunicorn.service` (está fallando)
- **Servicio alternativo:** `gunicorn.service` (también falló)

---

## 🚀 Solución Paso a Paso

### PASO 1: Ver por qué está fallando

```bash
sudo journalctl -u egarage-gunicorn.service -n 50 --no-pager
```

**Comparte la salida de este comando** para ver el error específico.

---

### PASO 2: Detener servicios actuales

```bash
sudo systemctl stop egarage-gunicorn.service
sudo systemctl stop gunicorn.service
```

---

### PASO 3: Verificar que Gunicorn está instalado

```bash
ls -la /srv/egarage/venv/bin/gunicorn
```

Si no existe:
```bash
cd /srv/egarage
source venv/bin/activate
pip install gunicorn
```

---

### PASO 4: Probar Gunicorn manualmente

```bash
cd /srv/egarage
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=gestion_taller.settings
gunicorn --bind 127.0.0.1:8001 gestion_taller.wsgi:application
```

**Si esto funciona**, presiona `Ctrl+C` y continúa. Si da error, comparte el error.

---

### PASO 5: Ver configuración actual del servicio

```bash
sudo systemctl cat egarage-gunicorn.service
```

---

### PASO 6: Crear/Actualizar servicio systemd

```bash
# Detectar usuario del directorio
APP_USER=$(stat -c '%U' /srv/egarage)
echo "Usuario: $APP_USER"

# Crear directorio de logs
sudo mkdir -p /srv/egarage/logs
sudo chown $APP_USER:$APP_USER /srv/egarage/logs
```

Luego crear el servicio:

```bash
sudo nano /etc/systemd/system/egarage-gunicorn.service
```

Pegar esta configuración (ajustar `User=` y `Group=` con el usuario real):

```ini
[Unit]
Description=eGarage Gunicorn
After=network.target postgresql.service

[Service]
Type=notify
User=TU_USUARIO_AQUI
Group=TU_GRUPO_AQUI
WorkingDirectory=/srv/egarage
Environment="PATH=/srv/egarage/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=gestion_taller.settings"
ExecStart=/srv/egarage/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8001 \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile /srv/egarage/logs/gunicorn-access.log \
    --error-logfile /srv/egarage/logs/gunicorn-error.log \
    gestion_taller.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
```

**Reemplazar `TU_USUARIO_AQUI` y `TU_GRUPO_AQUI`** con el usuario real (ej: `www-data`, `egarage`, etc.)

---

### PASO 7: Activar y iniciar servicio

```bash
sudo systemctl daemon-reload
sudo systemctl enable egarage-gunicorn.service
sudo systemctl start egarage-gunicorn.service
sudo systemctl status egarage-gunicorn.service
```

---

### PASO 8: Verificar que está escuchando

```bash
ss -tuln | grep 8001
```

Debería mostrar algo como:
```
tcp   LISTEN 0  128  127.0.0.1:8001  0.0.0.0:*
```

---

### PASO 9: Probar conexión local

```bash
curl -I http://127.0.0.1:8001/
```

---

### PASO 10: Recargar Nginx

```bash
sudo systemctl reload nginx
```

---

## 🔍 Si algo falla

### Ver logs en tiempo real:
```bash
sudo journalctl -u egarage-gunicorn.service -f
```

### Ver logs de error de Gunicorn:
```bash
tail -f /srv/egarage/logs/gunicorn-error.log
```

### Ver logs de Nginx:
```bash
sudo tail -f /var/log/nginx/error.log
```

---

## ✅ Verificación Final

1. ✅ `sudo systemctl status egarage-gunicorn.service` → debe estar "active (running)"
2. ✅ `ss -tuln | grep 8001` → debe mostrar el puerto escuchando
3. ✅ `curl http://127.0.0.1:8001/` → debe responder (no 502)
4. ✅ `sudo systemctl reload nginx` → debe recargar sin errores
5. ✅ Abrir https://www.egarage.cl/cl/es/bienvenida/ → debe cargar
