# Correo eGarage — flujo, despliegue y verificación

## Resumen del problema que esto resuelve

Un suscriptor respondió a un correo de eGarage y su respuesta **rebotó**:

```
550 5.1.1 Address does not exist.
Tu mensaje no se ha entregado a no-reply@egarage.cl
```

**Causa:** `egarage.cl` recibe correo vía **Cloudflare Email Routing**, que solo
entrega las direcciones con una regla configurada. `no-reply@egarage.cl` no
tiene regla → rebota. El correo se había enviado con ese remitente desde una
**campaña en el panel de Resend**.

## Arquitectura de correo

- **Envío:** [Resend](https://resend.com) por API HTTP (sin SMTP).
  Backend: `gestion_taller.resend_backend.ResendBackend` (`EMAIL_BACKEND`).
- **Recepción:** Cloudflare Email Routing reenvía `support@egarage.cl` (buzón
  real y monitoreado) al Gmail del equipo.
- **DNS:** SPF `v=spf1 include:_spf.mx.cloudflare.net include:spf.resend.com ~all`;
  MX → `route1/2/3.mx.cloudflare.net`.

### Reglas para no rebotar
1. **Nunca** enviar desde `no-reply@egarage.cl`. Usar `support@egarage.cl`.
2. En código, usar siempre los helpers de `taller/utils/email_helper.py`
   (`send_email_with_reply_to`, `send_template_email`), nunca `send_mail`.
3. `settings_prod.py` normaliza `DEFAULT_FROM_EMAIL` / `SERVER_EMAIL` /
   `SUPPORT_EMAIL`: direcciones legacy (`@atlantareciclajes.cl`) o `no-reply@`
   se fuerzan a `support@egarage.cl`. Así un `.env` desactualizado en el
   servidor no reintroduce rebotes.
4. `ResendBackend` respeta el `from` por mensaje y **siempre** adjunta
   `Reply-To` (el del mensaje, o `SUPPORT_EMAIL` como fallback).

### Lo que el código NO controla (acción manual)
- **Campañas/broadcasts de Resend** se envían desde el panel, no por código.
  Configurar su remitente o Reply-To a `support@egarage.cl`.
- **Cloudflare Email Routing:** mantener la regla de `support@egarage.cl` y,
  como red de seguridad, activar **catch-all**.

## Desplegar en el servidor (DigitalOcean)

El servidor vive en `/srv/egarage`, arranca con `run_gunicorn.sh`
(`source /srv/egarage/.env` + gunicorn sobre `gestion_taller.wsgi`), usa el
settings `gestion_taller.settings_prod` y se sirve tras nginx. La rama de
deploy es `prod-good-cache-servicios-20260429`.

> **Importante:** `.env` está en `.gitignore`, así que **`git pull` no
> actualiza el `.env` del servidor**. Los cambios de código sí viajan; los de
> `.env` hay que aplicarlos a mano en el servidor.

```bash
ssh tu_usuario@159.223.200.106
cd /srv/egarage

# Opción A — script de deploy con validaciones + rollback automático
./deploy_pro.sh prod-good-cache-servicios-20260429

# Opción B — manual
git pull --ff-only origin prod-good-cache-servicios-20260429
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

`deploy_pro.sh` hace: `git pull --ff-only` → `manage.py check` → compila los
`.py` de runtime → `migrate` → `collectstatic` → reinicia gunicorn/nginx →
health check (`/healthz/`) y smoke test. Si algo falla, hace rollback al commit
previo.

### (Opcional) Limpiar el `.env` del servidor
El código ya corrige direcciones legacy, pero conviene dejarlo prolijo:

```bash
nano /srv/egarage/.env
# Asegurar:
#   DEFAULT_FROM_EMAIL=support@egarage.cl
#   SERVER_EMAIL=support@egarage.cl
#   SUPPORT_EMAIL=support@egarage.cl
sudo systemctl restart gunicorn
```

## Verificar después del deploy

```bash
set -a; source /srv/egarage/.env; set +a
source /srv/egarage/venv/bin/activate     # o .venv

# 1) Solo revisar la config resuelta (NO envía):
python scripts/verificar_email_deploy.py

# 2) Enviar un correo de prueba real:
python scripts/verificar_email_deploy.py tu_correo@gmail.com
```

Debe mostrar `From: eGarage <support@egarage.cl>` y `Reply-To:
support@egarage.cl`, con `✅`. El script termina en código `1` si detecta
`no-reply`, dominio legacy, o un Reply-To que no sea `@egarage.cl`.

**Prueba end-to-end:** abre el correo de prueba en tu Gmail, pulsa
**Responder** y confirma que el destino es `support@egarage.cl` y **no rebota**.
