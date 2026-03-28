# 403 CSRF / PROPFIND en logs: bots, no bug de formularios

## Qué ves en logs

Ejemplos típicos (journalctl / access log):

- `PROPFIND /` → `403 Forbidden` (método que suelen usar bots; **no es la condición técnica del rechazo**)
- Mensaje Django: `Referer checking failed - Referer is insecure while host is secure.`
- Referer raro: `http://<ip>:443/` o sin Referer

## Causa raíz

No es un usuario real ni un formulario roto de eGarage. Son **escáneres/bots** que golpean el sitio con peticiones que Django trata como **inseguras para CSRF** mientras el **host se considera HTTPS** (p. ej. por `X-Forwarded-Proto: https` y `SECURE_PROXY_SSL_HEADER`).

El bloqueo **no depende específicamente de `PROPFIND`**: depende de que, en ese contexto, la petición sea **insegura para CSRF** (p. ej. Referer ausente o `http://...` frente a un sitio visto como seguro). `PROPFIND` es solo el método raro que a menudo usan esos bots; **lo mismo podría ocurrir con otros métodos no seguros** si llegan sin un Referer válido para ese esquema.

**Es comportamiento correcto de Django, no un bug de la app.**

## Qué no hacer

- No desactivar `CsrfViewMiddleware`.
- No relajar CSRF “para que desaparezca el 403”.
- No usar `CSRF_TRUSTED_ORIGINS` para “blanquear” escaneos por IP o tráfico basura: ese setting sirve para **validar Origin/Referer de orígenes legítimos** de tu aplicación, no para abrir la puerta a peticiones automatizadas arbitrarias. Por eso **no** conviene añadir IPs u orígenes al azar solo porque aparecen en logs de bots.

## Problema secundario: `Referrer-Policy` duplicado

Si en la misma respuesta aparecen **dos** headers `Referrer-Policy` (p. ej. Django `strict-origin-when-cross-origin` y Nginx `same-origin`), hay **inconsistencia**; **no es la causa** del 403 CSRF descrito arriba, pero conviene unificar.

**Recomendación:** una sola fuente de verdad.

- Mantener en Django (ya en `settings_prod.py`):  
  `SECURE_REFERRER_POLICY` / `DJANGO_SECURE_REFERRER_POLICY` → `strict-origin-when-cross-origin`
- **Quitar** del vhost Nginx la línea:  
  `add_header Referrer-Policy "same-origin" always;`

Luego:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

Verificar con `curl -I https://tu-dominio/` que quede **un solo** `Referrer-Policy`.

## Reducir ruido (opcional)

- Filtrar o bajar verbosidad de logs para 403 de bots.
- En Nginx, rechazar métodos no usados (`PROPFIND`, etc.) **antes** del upstream, si no los necesitás (endurecimiento, no “arreglo” de bug).

## Conclusión

El **403 CSRF** visto en logs **no es un bug de formularios de eGarage**, sino el **bloqueo correcto** de peticiones automatizadas hacia un sitio HTTPS con Referer **ausente o inseguro**; la **única corrección real** detectada en app/infra fue **unificar `Referrer-Policy`** para evitar headers duplicados entre Django y Nginx.
