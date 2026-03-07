# 🔍 Comandos de Diagnóstico - Ejecutar en el Servidor

Copia y pega estos comandos uno por uno en el servidor:

## 1. Buscar servicios de Gunicorn

```bash
systemctl list-units --all | grep -E "(gunicorn|egarage)"
```

## 2. Buscar procesos de Gunicorn corriendo

```bash
ps aux | grep gunicorn | grep -v grep
```

## 3. Buscar sockets Unix

```bash
find /opt /var/www /srv /tmp -name "*.sock" -type s 2>/dev/null
```

## 4. Verificar puertos TCP

```bash
netstat -tuln | grep -E ":(8000|8001|8002) "
# O si netstat no está disponible:
ss -tuln | grep -E ":(8000|8001|8002) "
```

## 5. Ver configuración de Nginx

```bash
# Ver qué archivos de configuración hay
ls -la /etc/nginx/sites-enabled/

# Ver la configuración completa
cat /etc/nginx/sites-enabled/*

# Buscar específicamente proxy_pass
grep -r "proxy_pass" /etc/nginx/sites-enabled/
```

## 6. Ver logs de error de Nginx

```bash
tail -50 /var/log/nginx/error.log
```

## 7. Buscar dónde está el código de la aplicación

```bash
find /opt /var/www /srv /home -name "manage.py" -type f 2>/dev/null
```

## 8. Verificar si hay un servicio systemd con otro nombre

```bash
systemctl list-units --type=service --all | grep -i python
systemctl list-units --type=service --all | grep -i django
```

---

## 🎯 Después de ejecutar estos comandos

Comparte los resultados y te ayudo a:
1. Identificar dónde está la aplicación
2. Crear/arreglar el servicio de Gunicorn
3. Configurar Nginx correctamente
4. Solucionar el error 502
