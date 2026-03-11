# Gunicorn + systemd (eGarage)

Forma estándar en producción: **systemd → EnvironmentFile → Gunicorn → Django**.

Así Gunicorn carga automáticamente `.env.prod` y no vuelves a tener:

- `ImproperlyConfigured: SECRET_KEY`
- Variables de email faltantes (RESEND_API_KEY, DEFAULT_FROM_EMAIL)
- Variables de base de datos no cargadas

**No dependas de `source .env.prod`** en SSH; eso solo vive en tu sesión.

Configuración orientada a **estabilidad con muchos talleres**: 4 workers, 2 threads, timeout 60s, reinicio periódico de workers (max-requests) y logs en archivo.

---

## 1. Crear carpeta de logs (antes de arrancar)

Logs reales en disco permiten diagnosticar errores 500 sin depender solo de journald:

```bash
sudo mkdir -p /var/log/gunicorn
sudo chown -R root:www-data /var/log/gunicorn
sudo chmod -R 775 /var/log/gunicorn
```

Quedan:

- `/var/log/gunicorn/access.log`
- `/var/log/gunicorn/error.log`

Ver errores en vivo:

```bash
tail -f /var/log/gunicorn/error.log
```

## 2. Editar el servicio de Gunicorn

```bash
sudo nano /etc/systemd/system/gunicorn.service
# o si usas override:
sudo systemctl edit gunicorn
```

## 3. Contenido correcto (ejemplo)

Ver `gunicorn.service.example`. Incluye:

- `EnvironmentFile=/srv/egarage/.env.prod`
- `Environment=DJANGO_SETTINGS_MODULE=gestion_taller.settings_prod`
- `Environment=PYTHONPATH=/srv/egarage`
- `--workers 4 --threads 2 --timeout 60`
- `--max-requests 1000 --max-requests-jitter 50` (evita memory leaks)
- `--access-logfile` / `--error-logfile` en `/var/log/gunicorn/`

| Parámetro        | Efecto |
|------------------|--------|
| workers          | Más procesos concurrentes |
| threads          | Cada worker atiende más requests |
| timeout          | Evita procesos colgados |
| max-requests     | Reinicia workers antes de memory leaks |

## 4. Usar solo overrides (recomendado)

Si ya tienes un `gunicorn.service` base:

```bash
sudo mkdir -p /etc/systemd/system/gunicorn.service.d
sudo cp scripts/gunicorn.service.d/override-environment.conf /etc/systemd/system/gunicorn.service.d/
sudo cp scripts/gunicorn.service.d/override-execstart.conf /etc/systemd/system/gunicorn.service.d/
```

## 5. Recargar y reiniciar

```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
```

## 6. Verificar

```bash
sudo systemctl status gunicorn
# Debe mostrar: Active: active (running)

sudo journalctl -u gunicorn -n 50 --no-pager
tail -f /var/log/gunicorn/error.log
```

## 7. Monitorear el servidor

- `htop` o `top`: CPU, RAM, procesos gunicorn

## 8. Test final

- https://egarage.cl/… (login, signup, envío de email)

---

## Escalado (100+ talleres)

| Recurso  | Recomendado |
|----------|-------------|
| CPU      | 4 vCPU      |
| RAM      | 8 GB        |
| workers  | 5–7         |

## Mejora futura (Redis + Celery)

Para escalar a nivel global y no bloquear el servidor web:

- **Redis** + **Celery** + cola de tareas
- Mover a la cola: envío de emails, procesamiento de imágenes, OCR de vehículos y tareas pesadas
