# ⚡ Solución Rápida 502 Bad Gateway

## 🚀 Comandos Rápidos (Copiar y Pegar)

```bash
# 1. Verificar y reiniciar Gunicorn
sudo systemctl status egarage
sudo systemctl restart egarage
sudo systemctl status egarage

# 2. Verificar socket
ls -la /opt/egarage/egarage.sock
# Si no existe, el servicio no está corriendo

# 3. Recargar Nginx
sudo nginx -t && sudo systemctl reload nginx

# 4. Ver logs de error
sudo tail -20 /var/log/nginx/error.log
sudo journalctl -u egarage -n 20 --no-pager
```

## 🔍 Si el problema persiste:

```bash
# Ver qué servicio está configurado
systemctl list-units | grep -E "(gunicorn|egarage)"

# Ver logs en tiempo real
sudo tail -f /var/log/nginx/error.log

# Probar conexión local
curl -I http://localhost/
```

## 📋 Checklist Rápido

1. ✅ `sudo systemctl status egarage` → debe estar "active (running)"
2. ✅ `ls -la /opt/egarage/egarage.sock` → debe existir el archivo
3. ✅ `sudo nginx -t` → debe decir "syntax is ok"
4. ✅ `curl http://localhost/` → debe responder (no 502)

Si todos pasan pero sigue el 502, revisa los logs:
```bash
sudo tail -50 /var/log/nginx/error.log | grep -i "502\|connect\|upstream"
```
