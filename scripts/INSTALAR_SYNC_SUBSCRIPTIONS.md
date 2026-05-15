# Instalación de Sync Subscriptions

Este comando sincroniza automáticamente el estado de las suscripciones cada noche.

## ¿Qué hace?

- Si `fecha_fin < now` → `suscripcion_activa=False` + `notificacion_vencido=True`
- Si faltan exactamente 5 días → `notificacion_5_dias=True`
- Si falta exactamente 1 día → `notificacion_1_dia=True`

## Opción 1: Cron (Linux/Mac)

### Paso 1: Editar el script
Edita `scripts/sync_subscriptions_cron.sh` y ajusta las rutas según tu instalación.

### Paso 2: Dar permisos de ejecución
```bash
chmod +x scripts/sync_subscriptions_cron.sh
```

### Paso 3: Agregar a crontab
```bash
crontab -e
```

Agrega esta línea (ejecuta a las 2:00 AM todos los días):
```
0 2 * * * /ruta/completa/al/proyecto/scripts/sync_subscriptions_cron.sh >> /var/log/egarage_sync_subscriptions.log 2>&1
```

### Paso 4: Verificar
```bash
# Probar manualmente



# Ver logs
tail -f /var/log/egarage_sync_subscriptions.log
```

## Opción 2: Systemd Timer (Linux - Recomendado)

### Paso 1: Editar los archivos
Edita `scripts/sync_subscriptions.service` y `scripts/sync_subscriptions.timer`:
- Cambia `/ruta/completa/al/proyecto` por la ruta real
- Cambia `/ruta/al/venv/bin/python` por la ruta a tu Python del venv
- Cambia `User=www-data` si usas otro usuario

### Paso 2: Copiar archivos a systemd
```bash
sudo cp scripts/sync_subscriptions.service /etc/systemd/system/
sudo cp scripts/sync_subscriptions.timer /etc/systemd/system/
```

### Paso 3: Recargar systemd
```bash
sudo systemctl daemon-reload
```

### Paso 4: Activar el timer
```bash
sudo systemctl enable sync_subscriptions.timer
sudo systemctl start sync_subscriptions.timer
```

### Paso 5: Verificar estado
```bash
# Ver estado del timer
sudo systemctl status sync_subscriptions.timer

# Ver próximas ejecuciones
sudo systemctl list-timers sync_subscriptions.timer

# Ver logs del último servicio
sudo journalctl -u sync_subscriptions.service -n 50

# Probar manualmente
sudo systemctl start sync_subscriptions.service
```

## Opción 3: PythonAnywhere (Si usas PythonAnywhere)

En PythonAnywhere, usa las Tasks programadas:

1. Ve a la pestaña "Tasks"
2. Crea una nueva tarea:
   - **Command**: `python3.10 /home/tuusuario/mysite/manage.py sync_subscriptions`
   - **Hour**: 2
   - **Minute**: 0
   - **Enabled**: ✓

## Modo de prueba

Para probar sin hacer cambios reales:
```bash
python manage.py sync_subscriptions --dry-run
```

## Verificación manual

```bash
# Ver suscripciones vencidas
python manage.py shell
>>> from taller.models.empresa import Empresa
>>> from django.utils import timezone
>>> Empresa.objects.filter(fecha_fin__lt=timezone.now(), suscripcion_activa=True).count()

# Ver próximas a vencer
>>> from datetime import timedelta
>>> hoy = timezone.now().date()
>>> Empresa.objects.filter(fecha_fin__date=hoy + timedelta(days=1)).count()
>>> Empresa.objects.filter(fecha_fin__date=hoy + timedelta(days=5)).count()
```

## Notas importantes

- Este comando **NO envía notificaciones**, solo sincroniza el estado
- Para enviar notificaciones, usa el comando `notificar_vencimientos` que ya existe
- Se recomienda ejecutar `notificar_vencimientos` después de `sync_subscriptions`
- Puedes crear un script que ejecute ambos comandos en secuencia

## Script combinado (ejecutar ambos comandos)

Crea `scripts/sync_and_notify.sh`:
```bash
#!/bin/bash
cd "$(dirname "$0")/.." || exit 1

# Activar venv si existe
[ -d "venv" ] && source venv/bin/activate
[ -d ".venv" ] && source .venv/bin/activate
[ -d "env" ] && source env/bin/activate

# Sincronizar primero
python manage.py sync_subscriptions

# Luego notificar
python manage.py notificar_vencimientos

exit $?
```
