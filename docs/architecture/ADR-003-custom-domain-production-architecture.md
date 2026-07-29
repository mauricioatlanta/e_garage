# ADR-003 — Arquitectura de Producción para Dominios Personalizados

**Estado:** Propuesto
**Fecha:** 2026-07-29
**Autores:** Mauricio Alvarado
**Revisores:** —
**Relacionado con:** ADR-002 (Dominios Personalizados — Modelo y Verificación)

---

## 1. Resumen Ejecutivo

Este documento cierra la arquitectura de producción antes de implementar la
emisión automática de certificados SSL y la configuración dinámica de Nginx.
Compara dos enfoques principales de terminación TLS para dominios de tenants
y selecciona uno como camino canónico.

**Decisión adoptada:** Cloudflare SSL for SaaS (Custom Hostnames) con Nginx
en modo catch-all y certificado de origen Cloudflare.

**Razón principal:** Es el único enfoque que escala a 10 000 dominios sin
cambios en Nginx por dominio, sin rate limits de ACME y sin tiempo de
inactividad durante recargas de configuración. El costo marginal es predecible
y inferior al costo de operar certbot a escala.

---

## 2. Contexto

### 2.1 Infraestructura actual

```
Browser
  │ HTTPS (TLS terminado en Cloudflare)
  ▼
Cloudflare CDN  (certificado wildcard *.egarage.cl gestionado por CF)
  │ HTTP con cabeceras CF-Connecting-IP, X-Forwarded-Proto: https
  ▼
Nginx (VPS/Droplet DigitalOcean)
  │ proxy_pass 127.0.0.1:8000
  ▼
Gunicorn / Django 4.2
```

Configuración Django relevante:

```python
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
ALLOWED_HOSTS = ["egarage.cl", "www.egarage.cl"]
```

### 2.2 Problema a resolver

Cuando un tenant verifica `taller-juan.cl`, ese dominio debe:

1. Llegar al servidor con TLS válido para el navegador.
2. Ser enrutado a Django con el header `Host: taller-juan.cl` intacto.
3. Ser resuelto por `HostTenantMiddleware` al tenant correcto sin ningún
   cambio en el proceso de arranque de Django.
4. Funcionar independientemente de si el dominio fue verificado hace un minuto
   o hace seis meses.

Los enfoques A (per-dominio) y B (catch-all/Cloudflare) resuelven estos cuatro
puntos de formas radicalmente distintas en costo operativo y escalabilidad.

---

## 3. Opciones Comparadas

### Opción A — Nginx por dominio + Let's Encrypt (certbot)

Cada vez que un dominio pasa a estado `ACTIVO`, un proceso genera un bloque
`server {}` individual y emite un certificado Let's Encrypt.

```nginx
# /etc/nginx/sites-enabled/tenant_taller-juan.cl.conf  (generado)
server {
    listen 443 ssl http2;
    server_name taller-juan.cl;

    ssl_certificate     /etc/letsencrypt/live/taller-juan.cl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/taller-juan.cl/privkey.pem;

    location / {
        proxy_pass          http://127.0.0.1:8000;
        proxy_set_header    Host              $host;
        proxy_set_header    X-Forwarded-Host  $host;
        proxy_set_header    X-Forwarded-Proto https;
    }
}
```

Flujo por dominio nuevo:

```
EmpresaDominio.estado → ACTIVO
  → SSLIssuanceService.emitir(ed)
      → certbot certonly --nginx -d taller-juan.cl
      → escribe /etc/nginx/sites-enabled/tenant_taller-juan.cl.conf
      → nginx -t && systemctl reload nginx
      → actualiza ssl_cert_path, ssl_key_path, ssl_expira_en en BD
      → estado → ACTIVO (ssl_emitido=True)
```

---

### Opción B — Nginx catch-all + Cloudflare SSL for SaaS

Un único bloque `server {}` acepta cualquier dominio. Cloudflare emite y
renueva el certificado para el dominio del tenant de forma automática.

```nginx
# /etc/nginx/sites-enabled/egarage_catchall.conf  (estático, nunca cambia)
server {
    listen 443 ssl http2 default_server;
    server_name _;

    # Certificado de origen Cloudflare (cubre *.egarage.cl + egarage.cl).
    # No es el cert del tenant; Cloudflare termina TLS antes de llegar aquí.
    ssl_certificate     /etc/ssl/cloudflare/origin_cert.pem;
    ssl_certificate_key /etc/ssl/cloudflare/origin_key.pem;

    # Solo aceptar tráfico que venga de Cloudflare (IPs oficiales CF).
    # Bloquea conexiones directas al VPS que bypaseen Cloudflare.
    include /etc/nginx/cloudflare_ips.conf;

    location / {
        proxy_pass          http://127.0.0.1:8000;
        proxy_set_header    Host              $host;
        proxy_set_header    X-Forwarded-Host  $host;
        proxy_set_header    X-Forwarded-Proto https;
        proxy_set_header    CF-Connecting-IP  $http_cf_connecting_ip;
    }
}
```

Flujo por dominio nuevo:

```
EmpresaDominio.estado → ACTIVO
  → SSLIssuanceService.emitir(ed)          ← llama API Cloudflare
      → POST /zones/{zone}/custom_hostnames
          { "hostname": "taller-juan.cl", "ssl": { "method": "http", "type": "dv" } }
      → Cloudflare emite cert para taller-juan.cl (DV, ~15 min)
      → actualiza ssl_emitido=True, ssl_expira_en en BD
      → estado → ACTIVO (ssl_emitido=True)
  → Nginx NO se toca
```

El tenant ya habría creado un CNAME:

```
taller-juan.cl  CNAME  proxy.egarage.cl
proxy.egarage.cl  A  <IP del VPS>  (o CNAME a CF zone)
```

---

## 4. Comparación Técnica

### 4.1 Configuración de Nginx

| Criterio | Opción A (per-dominio) | Opción B (catch-all) |
|---|---|---|
| Archivo de configuración | Uno por dominio (`tenant_<fqdn>.conf`) | Uno estático para siempre |
| Cambio al verificar dominio | Generar .conf + `nginx -t` + reload | Llamada API Cloudflare; nginx no cambia |
| Tiempo de nginx reload | ~1 s con 100 dominios / ~60 s con 10 000 | Cero (nginx no se recarga) |
| Riesgo de downtime en reload | `nginx -t` puede fallar si un .conf tiene error | Sin riesgo; configuración estática |
| Gestión de rutas legacy (`/cl/es/`) | Sin impacto | Sin impacto |

### 4.2 SSL / TLS

| Criterio | Opción A (Let's Encrypt) | Opción B (Cloudflare SSL for SaaS) |
|---|---|---|
| Emisión del certificado | certbot (ACME HTTP-01 o DNS-01) | API Cloudflare REST |
| Rate limit de emisión | 50 certs/dominio registrado/semana; 5 fallos/hora/IP | Sin rate limit práctico |
| Validez del certificado | 90 días | 90 días (gestionado por Cloudflare) |
| Renovación | cron/systemd + `certbot renew` + nginx reload | Automática en Cloudflare, sin intervención |
| Wildcard | No (per-dominio) | No necesario (cada custom hostname tiene su cert) |
| Terminación TLS | En Nginx (origin) | En Cloudflare (edge); origin usa cert de origen CF |
| Soporte SNI multi-dominio | Requiere un `server {}` por dominio | Nativo en Cloudflare |
| Costo | Gratuito | Gratuito primeros 100 custom hostnames; $0.10/hostname/mes después |

### 4.3 Renovación de certificados

**Opción A:**

```
[systemd timer: cada 12 h]
  certbot renew --quiet
    → si renueva algún cert:
        systemctl reload nginx
```

Con 10 000 dominios: certbot renew itera todos los dominios localmente.
Let's Encrypt permite 300 renovaciones por 3 horas. Con 10 000 dominios de
90 días de validez, se necesitarían ~111 dominios renovados por hora como
media. Con picos (si muchos se emitieron el mismo día), puede superar el
límite y comenzar a fallar. Requiere escalonar la emisión y monitorear
`/var/log/letsencrypt/letsencrypt.log`.

**Opción B:**

Sin intervención. Cloudflare renueva automáticamente 30 días antes del
vencimiento. La BD en `ssl_expira_en` puede actualizarse vía webhook o
consultando la API de Cloudflare periódicamente. No hay ningún proceso local.

### 4.4 Escalabilidad

#### 100 dominios

| | Opción A | Opción B |
|---|---|---|
| Nginx | 100 archivos .conf — viable | 0 cambios |
| SSL | 100 certs LE — dentro del free tier | 100 custom hostnames — gratuito |
| Reload Nginx | ~2 s | 0 |
| Renovación | 100 dominios cada 60–90 días — sin problemas | Automática |
| **Veredicto** | ✅ Viable | ✅ Ideal |

#### 1 000 dominios

| | Opción A | Opción B |
|---|---|---|
| Nginx | 1 000 archivos .conf; reload ~10 s | 0 cambios |
| SSL | Rate limit LE empieza a ser relevante si hay ráfagas | 900 × $0.10 = $90/mes (>100) |
| Reload Nginx | Cada dominio nuevo fuerza reload; riesgo de cola | 0 |
| Renovación | ~333 renovaciones/mes; potencialmente problemático en picos | Automática |
| Procesos root | certbot y nginx-reload necesitan sudo | Solo llamada a API CF |
| **Veredicto** | ⚠️ Gestionable con cuidado | ✅ Ideal |

#### 10 000 dominios

| | Opción A | Opción B |
|---|---|---|
| Nginx | 10 000 archivos .conf; reload ~60 s (gap de disponibilidad) | 0 cambios |
| SSL | Rate limit LE crítico; necesita sistema de cola con backoff y retry | 9 900 × $0.10 = $990/mes |
| Reload Nginx | Recargas frecuentes causan downtime observable; `nginx -s reload` no es instantáneo a esta escala | 0 |
| Renovación | ~3 333 renovaciones/mes; supera tasa permitida sin escalonado explícito | Automática |
| Monitoreo SSL | Proceso propio de alerta de expiración para 10 000 certs | Webhook CF o API poll |
| **Veredicto** | ❌ Inviable sin infraestructura adicional (Vault, cert-manager, etc.) | ✅ Escala sin cambios |

---

## 5. Impacto en `HostTenantMiddleware`

`HostTenantMiddleware` (en `taller/middleware/host_tenant.py`) ya resuelve el
tenant por host y funciona de forma idéntica en ambas opciones. Los puntos de
atención son:

### 5.1 `ALLOWED_HOSTS`

Con la configuración actual `ALLOWED_HOSTS = ["egarage.cl", "www.egarage.cl"]`,
cualquier dominio de tenant causará un `400 Bad Request` de Django antes de
llegar al middleware.

**Solución adoptada (ambas opciones):** Añadir una subclase de
`SecurityMiddleware` o una entrada dinámica usando la caché de
`DomainResolverService`. El patrón más simple y seguro es un backend de
`ALLOWED_HOSTS` que consulte el caché:

```python
# gestion_taller/settings/__init__.py
ALLOWED_HOSTS = ["egarage.cl", "www.egarage.cl", "proxy.egarage.cl"]
# Los dominios de tenants los valida HostTenantMiddleware DESPUÉS de que
# Django resuelve el host. Para pasar el check de ALLOWED_HOSTS sin
# listar cada dominio de tenant, se añade una entrada wildcard
# SOLO si el servidor está detrás de un proxy confiable (Cloudflare/Nginx):
if not DEBUG:
    ALLOWED_HOSTS.append("*")   # la validación real la hace HostTenantMiddleware
```

**Por qué es seguro en Opción B:** Nginx solo acepta conexiones de IPs de
Cloudflare (`cloudflare_ips.conf`). Un atacante no puede forjar un header
`Host` arbitrario desde internet. `HostTenantMiddleware` valida que el host
existe en `EmpresaDominio[estado=ACTIVO]` antes de fijar `request.empresa`.

**Por qué es seguro en Opción A:** Nginx valida `server_name` antes de
proxy_pass. Un host que no tenga un bloque `server {}` no llega a Django.

### 5.2 `CSRF_TRUSTED_ORIGINS`

Las peticiones POST desde un dominio de tenant fallarán el check CSRF si el
origen no está en `CSRF_TRUSTED_ORIGINS`. Opciones:

```python
# Opción 1: middleware que añade el dominio del request al contexto CSRF
# Opción 2: sobrescribir CsrfViewMiddleware para consultar DomainResolverService
# Opción 3: desactivar CSRF solo para las vistas públicas del dominio de tenant
#            (presupuesto aprobado, formulario de contacto, etc.)
```

La opción 2 es la correcta para el workspace completo:

```python
class TenantAwareCsrfMiddleware(CsrfViewMiddleware):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        if getattr(request, "empresa", None) is not None:
            # Dominio de tenant verificado → confiar en el origen
            request.META["CSRF_COOKIE_USED"] = True
        return super().process_view(request, callback, callback_args, callback_kwargs)
```

Esto se implementa en Fase 3 (cuando el workspace sirve bajo el dominio propio).

### 5.3 Cabeceras en Opción B

Con Cloudflare como proxy, Django recibe:

```
Host: taller-juan.cl               ← el dominio del tenant (correcto)
X-Forwarded-Proto: https           ← ya configurado con SECURE_PROXY_SSL_HEADER
CF-Connecting-IP: 1.2.3.4         ← IP real del visitante
X-Forwarded-For: 1.2.3.4          ← también enviado por CF
```

`HostTenantMiddleware` usa `request.get_host()` que con `USE_X_FORWARDED_HOST=True`
devuelve el valor del header `X-Forwarded-Host` (enviado por Nginx como `$host`).
No requiere ningún cambio.

---

## 6. Impacto en `DomainVerificationService`

`DomainVerificationService` (en `taller/services/domain_verification.py`)
verifica el registro TXT antes de que se active el dominio. Este servicio es
**independiente de la opción de SSL** y no requiere cambios en ninguna opción.

El flujo de Fase 3 añade una llamada posterior:

```
DomainVerificationService.verificar(ed)  → estado ACTIVO
  ↓ (solo si verificación exitosa)
SSLIssuanceService.emitir(ed)
  ├── Opción A: certbot + nginx reload
  └── Opción B: Cloudflare API /custom_hostnames
```

`DomainVerificationService` no necesita saber qué opción SSL se usa.

---

## 7. Estrategia de Renovación de Certificados

### Opción A (Let's Encrypt)

```
Emisión inicial:
  certbot certonly --nginx -d <dominio>  (en SSLIssuanceService)

Renovación (systemd timer, cada 12 h):
  certbot renew --quiet --deploy-hook "systemctl reload nginx"

Monitoreo:
  Consultar ssl_expira_en en BD, alertar si < 30 días y ssl_emitido=True
  pero el cert no se ha renovado.

Consideraciones de rate limit:
  - 50 certificados nuevos por dominio raíz por semana (ej. 50 subdominio de
    distintos clientes bajo midominio.cl/semana).
  - 300 renovaciones por 3 horas por cuenta ACME.
  - Implementar cola con backoff exponencial en SSLIssuanceService.
```

### Opción B (Cloudflare)

```
Emisión inicial:
  POST /zones/{zone_id}/custom_hostnames
  { "hostname": "<dominio>", "ssl": { "method": "http", "type": "dv" } }

Renovación:
  Automática. Cloudflare renueva 30 días antes de expirar.
  No se requiere ningún proceso local.

Sincronización de BD:
  Management command semanal:
    GET /zones/{zone_id}/custom_hostnames?hostname=<dominio>
    Actualizar ssl_expira_en si cambió.
  Alternativa: webhook Cloudflare a un endpoint interno.

Revocación al suspender dominio:
  DELETE /zones/{zone_id}/custom_hostnames/{id}
```

---

## 8. Comparación Final y Decisión

| Criterio | Peso | Opción A | Opción B |
|---|---|---|---|
| Escala a 10 000 dominios | Alto | ❌ | ✅ |
| Nginx sin cambios en caliente | Alto | ❌ | ✅ |
| Sin rate limits SSL | Alto | ❌ | ✅ |
| Renovación automática | Alto | ⚠️ (cron) | ✅ |
| Dependencia externa (Cloudflare) | Medio | ✅ ninguna | ⚠️ alta |
| Costo a 1 000 dominios | Medio | ✅ gratuito | ⚠️ ~$90/mes |
| Simplicidad operativa | Medio | ❌ sudo, procesos root | ✅ API REST |
| Tiempo de implementación Fase 3 | Bajo | ⚠️ mayor | ✅ menor |
| Sin downtime en configuración | Alto | ❌ nginx reload | ✅ |

**Decisión: Opción B — Cloudflare SSL for SaaS + Nginx catch-all.**

La dependencia de Cloudflare ya existe (es el CDN y termina TLS para
`egarage.cl`). Adoptar Custom Hostnames no introduce una dependencia nueva,
sino que extiende la ya existente. El costo a 1 000 dominios (~$90/mes) es
absorbible si esos 1 000 tenants están en planes Entry o superiores.

---

## 9. Secuencia de Implementación (Fase 3)

```
Paso 1 — Infraestructura (sin código Django):
  a. Crear Custom Hostname "catch-all zone" en dashboard Cloudflare.
  b. Añadir registro DNS: proxy.egarage.cl → A → IP del VPS.
  c. Actualizar nginx a configuración catch-all (ver §3, Opción B).
  d. Instalar certificado de origen Cloudflare en /etc/ssl/cloudflare/.
  e. Habilitar "Authenticated Origin Pulls" en Cloudflare.
  f. Añadir cloudflare_ips.conf a Nginx (deny all; solo IPs CF).

Paso 2 — Django settings:
  a. ALLOWED_HOSTS: añadir "*" en producción (protegido por CF IP allowlist).
  b. CSRF: implementar TenantAwareCsrfMiddleware (ver §5.2).
  c. Añadir CF_ZONE_ID y CF_API_TOKEN a variables de entorno.

Paso 3 — SSLIssuanceService (código nuevo):
  a. POST /custom_hostnames vía Cloudflare API.
  b. Polling de estado (pending → active) hasta que CF emite el cert.
  c. Actualizar ssl_emitido, ssl_expira_en en BD.
  d. Notificar al tenant por email.

Paso 4 — Revocación y suspensión:
  a. Al suspender: DELETE /custom_hostnames/{id} en Cloudflare.
  b. Al reactivar: POST /custom_hostnames nuevamente.

Paso 5 — Sincronización periódica:
  a. Management command semanal: verificar estado de custom hostnames en CF.
  b. Actualizar ssl_expira_en si cambió.
  c. Alertar si algún hostname está en estado "failed" en CF.

Paso 6 — Documentación para tenants:
  a. Instrucciones de CNAME: taller-juan.cl → proxy.egarage.cl
  b. Ya implementado en settings.html (tab "Dominio Personalizado").
```

---

## 10. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Cloudflare modifica o depreca SSL for SaaS | Baja | Alto | Diseñar `SSLIssuanceService` como interfaz con implementaciones intercambiables; la Opción A es el fallback |
| IP allowlist de CF desactualizada | Media | Alto | Script semanal que descarga `https://www.cloudflare.com/ips-v4` y actualiza `cloudflare_ips.conf` |
| Tenant borra el CNAME antes de verificar | Media | Bajo | `DomainVerificationService` detecta la falta del TXT y marca ERROR_DNS; el flujo ya lo maneja |
| Custom Hostname falla en CF durante emisión | Media | Medio | Polling con backoff; estado SSL_PENDIENTE ya modelado en `EmpresaDominio` |
| Tenant en país con acceso restringido a CF | Baja | Medio | Fuera del alcance de los mercados objetivo (CL, MX, AR, PE, CO) |
| Costo escalando > 5 000 dominios | Media | Medio | Revisar pricing CF en esa escala; alternativa: acme.sh con DNS-01 para dominios de volumen alto en planes básicos |

---

## 11. Campos del Modelo ya Preparados

`EmpresaDominio` ya tiene todos los campos necesarios para Fase 3 sin
necesidad de nuevas migraciones:

| Campo | Uso en Opción B |
|---|---|
| `ssl_emitido` | True cuando Cloudflare confirma que el cert está activo |
| `ssl_cert_path` | Vacío (CF gestiona los certs, no el VPS) — puede usarse para el ID de custom hostname en CF |
| `ssl_key_path` | Vacío — puede usarse para el hostname_id de la API CF |
| `ssl_expira_en` | Fecha de expiración sincronizada desde la API CF |
| `estado` = `SSL_PENDIENTE` | Mientras CF procesa el cert (tras verificación TXT) |
| `get_cname_target()` | Devuelve `"proxy.egarage.cl"` — instrucción ya correcta |

---

## 12. Preguntas Abiertas

Deben resolverse antes de iniciar Paso 1:

1. **¿Cloudflare está en el plan Enterprise o Business?** SSL for SaaS
   (Custom Hostnames) requiere mínimo plan Enterprise en la zona origen.
   En planes Free/Pro/Business, Custom Hostnames no está disponible.
   → Verificar el plan de la zona `egarage.cl` en el dashboard Cloudflare.

2. **¿Se usará HTTP-01 o DNS-01 como método de validación de CF?**
   HTTP-01 requiere que el dominio del tenant ya apunte a `proxy.egarage.cl`
   antes de solicitar el cert. DNS-01 permite emitir el cert en paralelo a la
   verificación del CNAME. Se recomienda HTTP-01 ya que el CNAME es
   prerequisito del flujo de activación.

3. **¿Se usará Authenticated Origin Pulls (mTLS)?** Añade seguridad extra
   garantizando que Nginx solo acepta tráfico que viene de Cloudflare con un
   certificado de cliente válido. Recomendado activar junto con el IP allowlist.

4. **¿Se notifica al tenant cuando el cert está activo?** El email de
   confirmación de dominio verificado es una pieza de retención. Definir
   template en `taller/emails/` antes de Fase 3.

---

## 13. Consecuencias de Esta Decisión

**Positivas:**
- Nginx tiene una sola configuración que nunca cambia por la incorporación
  de tenants.
- No hay procesos root en el flujo de negocio (certbot requería sudo).
- La renovación de certificados desaparece como preocupación operativa.
- La escala a 10 000 dominios no requiere rediseño.

**Negativas:**
- Se incrementa el costo con el volumen (compensable con el pricing del plan).
- El tiempo hasta cert activo depende de Cloudflare (~15 min típico vs.
  certbot que puede ser inmediato).
- Si Cloudflare tiene una interrupción, los dominios de tenants quedan sin TLS
  válido aunque egarage.cl siga funcionando (ya ocurre hoy con el CDN).

**Neutrales:**
- `HostTenantMiddleware` y `DomainVerificationService` no requieren cambios.
- `EmpresaDominio` no requiere nuevas migraciones para Fase 3.
- La instrucción CNAME para el tenant (`proxy.egarage.cl`) ya aparece
  correctamente en `settings.html` y en `get_cname_target()`.
