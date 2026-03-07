# 🔍 Diagnóstico Final - Connection Reset

El servicio está corriendo pero se cae al recibir peticiones. Necesitamos ver los logs de error.

## Comandos de Diagnóstico:

```bash
# 1. Ver logs de error de Gunicorn (MUY IMPORTANTE)
sudo tail -50 /srv/egarage/logs/gunicorn_error.log

# 2. Ver si los workers están arrancando
sudo journalctl -u egarage-gunicorn.service -n 100 --no-pager | grep -i "worker\|error\|boot"

# 3. Verificar que el puerto está escuchando
ss -tuln | grep 8001

# 4. Probar manualmente para ver el error
cd /srv/egarage
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=gestion_taller.settings
export EGARAGE_ENV=prod
[ -f .env ] && source .env
/srv/egarage/venv/bin/gunicorn gestion_taller.wsgi:application --bind 127.0.0.1:8001 --log-level debug
```

El comando 4 mostrará el error en tiempo real cuando intentes hacer una petición.
