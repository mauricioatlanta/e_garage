# 🔧 Solución Error 502 Bad Gateway - egarage.cl

## 📋 Resumen

El error **502 Bad Gateway** indica que Nginx está funcionando pero no puede comunicarse con el servidor de aplicación (Gunicorn). Esto generalmente significa que:

1. **Gunicorn no está corriendo** - El servicio se detuvo o no inició
2. **Socket/Puerto incorrecto** - Nginx está configurado para conectarse a un socket/puerto que no existe
3. **Permisos incorrectos** - Nginx no puede acceder al socket de Gunicorn
4. **Timeout** - Gunicorn está tardando demasiado en responder
5. **Error en la aplicación** - Django está crasheando al iniciar

---

## 🚀 Solución Rápida

### Opción 1: Usar el script de diagnóstico

```bash
# En el servidor, ejecutar:
sudo bash scripts/fix_502_bad_gateway.sh
```

El script:
- ✅ Detecta automáticamente el problema
- ✅ Verifica estado de servicios
- ✅ Revisa logs de error
- ✅ Ofrece soluciones específicas
- ✅ Puede aplicar correcciones automáticas

### Opción 2: Solución manual paso a paso

#### 1. Verificar estado de Gunicorn

```bash
# Buscar el servicio
systemctl list-units | grep -E "(gunicorn|egarage)"

# Verificar estado (reemplaza 'egarage' con el nombre real)
sudo systemctl status egarage
# O
sudo systemctl status gunicorn-egarage

# Si no está corriendo, iniciarlo
sudo systemctl start egarage
sudo systemctl enable egarage  # Para iniciar automáticamente
```

#### 2. Verificar que Gunicorn está escuchando

```bash
# Si usa socket Unix:
ls -la /opt/egarage/egarage.sock
# O
ls -la /var/www/egarage/egarage.sock

# Si usa puerto TCP:
netstat -tuln | grep 8000
# O
ss -tuln | grep 8000
```

#### 3. Verificar permisos del socket

```bash
# Ver permisos actuales
ls -la /opt/egarage/egarage.sock

# Si nginx no puede leerlo, ajustar permisos:
sudo chmod 666 /opt/egarage/egarage.sock

# O agregar nginx al grupo del socket:
sudo usermod -a -G egarage nginx
sudo systemctl restart nginx
```

#### 4. Revisar logs de error

```bash
# Logs de Nginx
sudo tail -50 /var/log/nginx/error.log
sudo tail -50 /var/log/nginx/egarage_error.log

# Logs de Gunicorn
sudo journalctl -u egarage -n 50 --no-pager
# O
sudo journalctl -u gunicorn-egarage -n 50 --no-pager
```

#### 5. Reiniciar servicios

```bash
# Reiniciar Gunicorn
sudo systemctl restart egarage

# Recargar Nginx (sin desconexión)
sudo systemctl reload nginx

# O reiniciar Nginx completamente
sudo systemctl restart nginx
```

#### 6. Verificar configuración de Nginx

```bash
# Verificar sintaxis
sudo nginx -t

# Ver configuración actual
sudo cat /etc/nginx/sites-enabled/egarage
# O
sudo cat /etc/nginx/sites-enabled/egarage.cl
```

---

## 🔍 Diagnóstico Detallado

### Verificar qué servicio está configurado

```bash
# Buscar todos los servicios relacionados
systemctl list-units --all | grep -E "(gunicorn|egarage)"

# Ver detalles de un servicio específico
systemctl cat egarage
```

### Verificar proceso de Gunicorn

```bash
# Ver si hay procesos de Gunicorn corriendo
ps aux | grep gunicorn

# Ver puertos en uso
sudo netstat -tulpn | grep gunicorn
# O
sudo ss -tulpn | grep gunicorn
```

### Verificar configuración de proxy en Nginx

La configuración debe tener algo como:

```nginx
location / {
    proxy_pass http://unix:/opt/egarage/egarage.sock;
    # O si usa TCP:
    # proxy_pass http://127.0.0.1:8000;
    
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**Importante:** El `proxy_pass` debe coincidir con cómo está configurado Gunicorn:
- Si Gunicorn usa `--bind unix:/opt/egarage/egarage.sock` → Nginx debe usar `http://unix:/opt/egarage/egarage.sock`
- Si Gunicorn usa `--bind 127.0.0.1:8000` → Nginx debe usar `http://127.0.0.1:8000`

---

## 🐛 Problemas Comunes y Soluciones

### Problema 1: "Connection refused" en logs de Nginx

**Causa:** Gunicorn no está corriendo o el socket/puerto no existe.

**Solución:**
```bash
# Iniciar Gunicorn
sudo systemctl start egarage

# Verificar que arrancó
sudo systemctl status egarage
```

### Problema 2: "Permission denied" en logs de Nginx

**Causa:** Nginx no tiene permisos para leer el socket.

**Solución:**
```bash
# Opción 1: Cambiar permisos del socket
sudo chmod 666 /opt/egarage/egarage.sock

# Opción 2: Agregar nginx al grupo del socket
sudo usermod -a -G egarage nginx
sudo systemctl restart nginx
```

### Problema 3: "Upstream timeout" en logs

**Causa:** Gunicorn está tardando demasiado en responder (posible error en Django).

**Solución:**
```bash
# Revisar logs de Gunicorn para ver el error real
sudo journalctl -u egarage -n 100

# Aumentar timeout en Nginx (temporal)
# Editar /etc/nginx/sites-enabled/egarage y agregar:
# proxy_read_timeout 120s;
```

### Problema 4: Gunicorn se inicia pero se detiene inmediatamente

**Causa:** Error en la aplicación Django (imports, configuración, base de datos).

**Solución:**
```bash
# Ver logs detallados
sudo journalctl -u egarage -n 100 --no-pager

# Probar ejecutar Gunicorn manualmente para ver el error
cd /opt/egarage  # O la ruta correcta
source venv/bin/activate
gunicorn gestion_taller.wsgi:application --bind unix:/opt/egarage/egarage.sock
```

### Problema 5: Socket no se crea

**Causa:** El directorio del socket no existe o no tiene permisos.

**Solución:**
```bash
# Crear directorio si no existe
sudo mkdir -p /opt/egarage
sudo chown egarage:egarage /opt/egarage

# Verificar permisos del directorio padre
ls -la /opt/
```

---

## 📝 Verificación Post-Fix

Después de aplicar las soluciones:

1. **Verificar que el servicio está activo:**
   ```bash
   sudo systemctl status egarage
   ```

2. **Verificar que el socket existe:**
   ```bash
   ls -la /opt/egarage/egarage.sock
   ```

3. **Probar conexión local:**
   ```bash
   curl -I http://localhost/
   ```

4. **Verificar en el navegador:**
   - Abrir: https://www.egarage.cl/cl/es/bienvenida/
   - Debe cargar sin error 502

5. **Monitorear logs en tiempo real:**
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

---

## 🔄 Comandos de Reinicio Rápido

```bash
# Reinicio completo (si todo lo demás falla)
sudo systemctl restart egarage
sudo systemctl restart nginx

# Verificar inmediatamente
sudo systemctl status egarage
curl -I http://localhost/
```

---

## 📞 Información Adicional

- **Ubicación típica del código:** `/opt/egarage` o `/var/www/egarage`
- **Usuario del servicio:** `egarage` o `www-data`
- **Socket típico:** `/opt/egarage/egarage.sock`
- **Puerto típico:** `8000` o `8001`

Para encontrar la configuración exacta en tu servidor:
```bash
# Buscar configuración de Gunicorn
sudo systemctl cat egarage | grep ExecStart

# Buscar configuración de Nginx
sudo grep -r "proxy_pass" /etc/nginx/sites-enabled/
```

---

## ✅ Checklist de Verificación

- [ ] Servicio Gunicorn está activo (`systemctl status`)
- [ ] Socket/puerto existe y es accesible
- [ ] Permisos del socket son correctos
- [ ] Nginx puede leer el socket
- [ ] Configuración de Nginx es válida (`nginx -t`)
- [ ] No hay errores en logs de Nginx
- [ ] No hay errores en logs de Gunicorn
- [ ] La aplicación responde localmente (`curl localhost`)
- [ ] El sitio web carga correctamente

Si todos los items están marcados y el problema persiste, revisa los logs de Django/Gunicorn para errores específicos de la aplicación.
