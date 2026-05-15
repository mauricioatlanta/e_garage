# Fix Nginx robots.txt - Instrucciones

## Problema
El bloque `location = /robots.txt` en nginx está usando `add_header Content-Type` que no funciona correctamente. Necesitamos usar `default_type text/plain;` en su lugar.

## Solución

### Opción 1: Script Automático (Recomendado)

Ejecuta en el servidor:

```bash
cd /ruta/a/tu/proyecto
sudo bash scripts/fix_nginx_robots_txt.sh
```

### Opción 2: Manual (Si el script no funciona)

1. **Hacer backup:**
```bash
sudo cp /etc/nginx/sites-available/egarage /etc/nginx/sites-available/egarage.backup.$(date +%Y%m%d_%H%M%S)
```

2. **Editar el archivo:**
```bash
sudo nano /etc/nginx/sites-available/egarage
```

3. **Buscar el bloque actual:**
```nginx
location = /robots.txt {
  alias /srv/egarage/staticfiles/robots.txt;
  add_header Content-Type text/plain;
}
```

4. **Reemplazar por:**
```nginx
location = /robots.txt {
    default_type text/plain;
    alias /srv/egarage/staticfiles/robots.txt;
    access_log off;
    log_not_found off;
}
```

5. **Verificar y recargar:**
```bash
sudo nginx -t && sudo systemctl reload nginx
```

6. **Verificar que funciona:**
```bash
curl -i https://egarage.cl/robots.txt | head -n 20
```

Deberías ver:
- `HTTP/2 200`
- `Content-Type: text/plain`
- El contenido del archivo robots.txt

## Si aún da 404 (Plan B)

Si después del cambio sigue dando 404, usa esta versión alternativa:

```nginx
location = /robots.txt {
    default_type text/plain;
    try_files /robots.txt =404;
}
```

Y asegúrate de que el archivo existe en:
```bash
ls -la /srv/egarage/staticfiles/robots.txt
```

## Verificación Final

```bash
# Verificar que nginx está corriendo
sudo systemctl status nginx

# Verificar sintaxis
sudo nginx -t

# Probar robots.txt
curl -i https://egarage.cl/robots.txt

# Ver logs si hay problemas
sudo tail -f /var/log/nginx/egarage_error.log
```
