# Verificación Allauth y prueba canónica login (HEAD)

## 1. Verificar que Allauth use el adapter configurado

En el servidor (con el usuario de la app, ej. `egarage`):

```bash
sudo -u egarage /srv/egarage/venv/bin/python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','gestion_taller.settings_prod')
import django; django.setup()
from django.conf import settings
print('ACCOUNT_ADAPTER =', getattr(settings,'ACCOUNT_ADAPTER',None))
"
```

**Esperado en este proyecto:**

`ACCOUNT_ADAPTER = taller.views_extra.account_adapter.CountryAwareAccountAdapter`

(Si en tu deploy usas otro adapter, el valor puede ser distinto, p. ej. `taller.adapters.allauth_adapter.EgarageAccountAdapter`.)

## 2. Prueba canónica para monitoreo futuro

Si en el futuro el login vuelve a dar 403, ejecuta:

```bash
curl -kI https://egarage.cl/accounts/login/ | head -n 12
```

**Esperado:** `HTTP/1.1 200` (o 302 si redirige). Si ves 403, revisar adapter Allauth y/o reglas de IP/rate limiting.

El middleware `RateLimitMiddleware` en `taller/middleware/rate_limiting.py` acepta **GET, POST, HEAD, OPTIONS** en rutas protegidas.
