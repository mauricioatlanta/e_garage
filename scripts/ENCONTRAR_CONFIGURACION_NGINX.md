# Cómo Encontrar la Configuración de Nginx

Si `/etc/nginx/sites-enabled/egarage.cl` no existe, la configuración puede estar en otro lugar.

## Opción 1: Ejecutar Script de Búsqueda

```bash
sudo bash /ruta/al/proyecto/scripts/buscar_configuracion_nginx.sh
```

Este script buscará en:
- `/etc/nginx/sites-enabled/`
- `/etc/nginx/sites-available/`
- `/etc/nginx/conf.d/`
- `/etc/nginx/nginx.conf`
- Todos los archivos `.conf` buscando referencias a "egarage" o puerto 8001

## Opción 2: Búsqueda Manual

### Buscar en sites-available
```bash
ls -la /etc/nginx/sites-available/ | grep -i egarage
```

### Buscar en conf.d
```bash
ls -la /etc/nginx/conf.d/ | grep -i egarage
```

### Buscar en nginx.conf principal
```bash
cat /etc/nginx/nginx.conf | grep -i include
```

### Buscar por puerto de Gunicorn
```bash
sudo grep -r "8001\|127.0.0.1:8001" /etc/nginx/
```

### Buscar por dominio
```bash
sudo grep -r "egarage.cl\|server_name.*egarage" /etc/nginx/
```

## Opción 3: Verificar Configuración Activa

### Ver qué archivos está usando Nginx
```bash
sudo nginx -T 2>&1 | grep -A 20 "server_name.*egarage"
```

Este comando muestra toda la configuración activa de Nginx y filtra por "egarage".

## Opción 4: Si No Existe Configuración

Si no encuentras ninguna configuración para egarage.cl, puedes:

### A) Crear nueva configuración

**Ubicación recomendada:** `/etc/nginx/sites-available/egarage.cl`

```bash
sudo nano /etc/nginx/sites-available/egarage.cl
```

Pegar el contenido de `scripts/nginx_egarage_example.conf` (ajustando rutas y puertos).

Luego crear enlace simbólico:
```bash
sudo ln -s /etc/nginx/sites-available/egarage.cl /etc/nginx/sites-enabled/egarage.cl
```

### B) Agregar al archivo principal

Si usas una configuración única, edita `/etc/nginx/nginx.conf` o el archivo que esté usando.

## Verificar Estado de Nginx

```bash
# Ver estado
sudo systemctl status nginx

# Ver configuración activa
sudo nginx -T

# Verificar sintaxis
sudo nginx -t
```

## Después de Encontrar/Actualizar

1. **Agregar el header crítico** en `location / { ... }`:
   ```nginx
   proxy_set_header X-Forwarded-Proto $scheme;
   ```

2. **Verificar sintaxis:**
   ```bash
   sudo nginx -t
   ```

3. **Recargar Nginx:**
   ```bash
   sudo systemctl reload nginx
   ```

4. **Reiniciar Gunicorn:**
   ```bash
   sudo systemctl restart egarage-gunicorn
   ```

## Archivos de Referencia

- `scripts/buscar_configuracion_nginx.sh` - Script de búsqueda automática
- `scripts/nginx_egarage_example.conf` - Configuración completa de ejemplo
