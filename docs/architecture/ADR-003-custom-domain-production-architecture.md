# ADR-003 — Arquitectura de Producción para Dominios Personalizados

**Estado:** Aceptado
**Fecha:** 2026-07-29
**Autores:** Mauricio Alvarado
**Revisores:** —
**Relacionado con:** ADR-002 (Dominios Personalizados — Modelo y Verificación)

---

## 1. Resumen Ejecutivo

Este documento cierra la arquitectura de producción antes de implementar la
emisión automática de certificados SSL y la configuración dinámica de Nginx.

**Decisión adoptada:** Let's Encrypt + certbot + plantillas Nginx por dominio,
con `SSLIssuanceService` como interfaz intercambiable y
`LetsEncryptSSLIssuanceService` como implementación oficial.

**Razón principal:** Es el stack ya desplegado y verificado en producción para
`egarage.cl`. No introduce dependencias externas nuevas, no tiene costo
marginal por dominio y es completamente reemplazable sin tocar el dominio de
negocio si en el futuro se decide cambiar el proveedor de certificados.

---

## 2. Contexto

### 2.1 Infraestructura actual

```
Browser
  │ HTTPS (puerto 443)
  ▼
Nginx (VPS/Droplet DigitalOcean)
  │ ssl_certificate: /etc/letsencrypt/live/egarage.cl/fullchain.pem
  │ proxy_pass http://127.0.0.1:8000
  ▼
Gunicorn / Django 4.2
```

Configuración Django relevante:

```python
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
ALLOWED_HOSTS = ["egarage.cl", "www.egarage.cl"]
```

certbot ya está instalado y en uso. El timer `certbot.timer` de systemd renueva
el certificado de `egarage.cl` automáticamente.

### 2.2 Problema a resolver

Cuando un tenant verifica `taller-juan.cl`, ese dominio debe:

1. Recibir tráfico HTTPS con un certificado TLS válido para el navegador.
2. Llegar a Django con el header `Host: taller-juan.cl` intacto.
3. Ser resuelto por `HostTenantMiddleware` al tenant correcto sin cambiar el
   proceso de arranque de Django.
4. Funcionar indefinidamente sin intervención manual por expiración de cert.

### 2.3 Alternativa descartada

Se evaluó Cloudflare SSL for SaaS (Custom Hostnames). Se descartó porque
requiere plan Enterprise en la zona origen de Cloudflare, introduce un costo
marginal por dominio activo y agrega dependencia de una API externa para cada
emisión de certificado. El stack Let's Encrypt + certbot resuelve los cuatro
puntos del §2.2 dentro de la infraestructura ya existente.

---

## 3. Arquitectura Adoptada

### 3.1 Stack completo con dominio de tenant activo

```
Browser
  │ HTTPS a taller-juan.cl (puerto 443)
  ▼
Nginx
  │ server_name taller-juan.cl;
  │ ssl_certificate /etc/letsencrypt/live/taller-juan.cl/fullchain.pem
  │ proxy_pass http://127.0.0.1:8000
  ▼
Gunicorn / Django 4.2
  │
  ├── HostTenantMiddleware       → resuelve EmpresaDominio[ACTIVO] por host
  └── EmpresaResolverMiddleware  → fija request.empresa desde la resolución
```

### 3.2 Flujo completo por dominio nuevo

```
Tenant configura DNS:
  taller-juan.cl  A  <IP del VPS>
  (o CNAME a egarage.cl si Nginx acepta el nombre en ambos bloques)

DomainVerificationService.verificar(ed)
  → consulta TXT _egarage-verify.taller-juan.cl
  → coincide con token → estado ACTIVO

LetsEncryptSSLIssuanceService.emitir(ed)
  → certbot certonly --nginx -d taller-juan.cl
  → escribe /etc/nginx/sites-enabled/tenant_taller-juan.cl.conf
  → nginx -t && systemctl reload nginx
  → ed.ssl_cert_path  = /etc/letsencrypt/live/taller-juan.cl/fullchain.pem
  → ed.ssl_key_path   = /etc/letsencrypt/live/taller-juan.cl/privkey.pem
  → ed.ssl_expira_en  = <fecha de vencimiento del cert>
  → ed.ssl_emitido    = True
  → ed.estado         = ACTIVO
  → save(update_fields=[...])

Desde ese momento, taller-juan.cl sirve el workspace del tenant.
```

---

## 4. Configuración Nginx por Dominio

### 4.1 Plantilla generada por `LetsEncryptSSLIssuanceService`

```nginx
# /etc/nginx/sites-enabled/tenant_taller-juan.cl.conf
# Generado automáticamente por LetsEncryptSSLIssuanceService.
# No editar manualmente.

server {
    listen 80;
    server_name taller-juan.cl;

    # Necesario para que certbot renueve via HTTP-01 challenge.
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name taller-juan.cl;

    ssl_certificate     /etc/letsencrypt/live/taller-juan.cl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/taller-juan.cl/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    location / {
        proxy_pass          http://127.0.0.1:8000;
        proxy_set_header    Host             $host;
        proxy_set_header    X-Forwarded-Host $host;
        proxy_set_header    X-Forwarded-For  $proxy_add_x_forwarded_for;
        proxy_set_header    X-Forwarded-Proto https;
    }
}
```

### 4.2 Ruta de archivos generados

```
/etc/nginx/sites-enabled/
  egarage.cl.conf              ← bloque existente de egarage.cl (no tocar)
  tenant_taller-juan.cl.conf   ← generado por el servicio
  tenant_miautomotriz.com.conf ← generado por el servicio
  ...
```

El prefijo `tenant_` permite listar, auditar y eliminar archivos de tenants
sin riesgo de afectar la configuración principal.

### 4.3 Bloque de dominio principal (referencia)

El bloque existente de `egarage.cl` no cambia. Los bloques de tenants son
archivos adicionales e independientes. Nginx carga todos los archivos de
`sites-enabled/` al hacer reload.

---

## 5. Diseño de `SSLIssuanceService`

El dominio de negocio no debe conocer el proveedor de certificados. Se define
una interfaz abstracta y una implementación concreta para Let's Encrypt.

### 5.1 Interfaz

```python
# taller/services/ssl_issuance.py

from abc import ABC, abstractmethod
from taller.models.empresa_dominio import EmpresaDominio


class SSLIssuanceService(ABC):

    @abstractmethod
    def emitir(self, empresa_dominio: EmpresaDominio) -> None:
        """
        Emite un certificado TLS para el dominio del tenant y configura Nginx.
        Actualiza ssl_cert_path, ssl_key_path, ssl_expira_en, ssl_emitido en BD.
        Raises: SSLIssuanceError si la emisión falla.
        """

    @abstractmethod
    def revocar(self, empresa_dominio: EmpresaDominio) -> None:
        """
        Revoca y elimina el certificado y la configuración Nginx del dominio.
        Llamar al suspender un dominio activo.
        """
```

### 5.2 Implementación oficial: `LetsEncryptSSLIssuanceService`

```python
class LetsEncryptSSLIssuanceService(SSLIssuanceService):

    NGINX_CONF_DIR = Path("/etc/nginx/sites-enabled")
    CERTBOT_WEBROOT = Path("/var/www/certbot")

    def emitir(self, ed: EmpresaDominio) -> None:
        dominio = ed.dominio

        # 1. Emitir certificado via certbot HTTP-01
        resultado = subprocess.run(
            ["certbot", "certonly", "--webroot",
             "-w", str(self.CERTBOT_WEBROOT),
             "-d", dominio, "--non-interactive", "--agree-tos"],
            capture_output=True, text=True,
        )
        if resultado.returncode != 0:
            raise SSLIssuanceError(resultado.stderr)

        # 2. Escribir configuración Nginx
        conf_path = self.NGINX_CONF_DIR / f"tenant_{dominio}.conf"
        conf_path.write_text(self._render_nginx_conf(dominio))

        # 3. Validar y recargar Nginx
        subprocess.run(["nginx", "-t"], check=True)
        subprocess.run(["systemctl", "reload", "nginx"], check=True)

        # 4. Actualizar BD (una sola escritura)
        cert_base = Path(f"/etc/letsencrypt/live/{dominio}")
        expira_en = self._leer_expiracion(cert_base / "fullchain.pem")
        ed.ssl_cert_path = str(cert_base / "fullchain.pem")
        ed.ssl_key_path  = str(cert_base / "privkey.pem")
        ed.ssl_expira_en = expira_en
        ed.ssl_emitido   = True
        ed.save(update_fields=[
            "ssl_cert_path", "ssl_key_path",
            "ssl_expira_en", "ssl_emitido", "actualizado_en",
        ])

    def revocar(self, ed: EmpresaDominio) -> None:
        dominio = ed.dominio
        conf_path = self.NGINX_CONF_DIR / f"tenant_{dominio}.conf"
        if conf_path.exists():
            conf_path.unlink()
        subprocess.run(["nginx", "-t"], check=True)
        subprocess.run(["systemctl", "reload", "nginx"], check=True)
        subprocess.run(
            ["certbot", "delete", "--cert-name", dominio, "--non-interactive"],
            check=False,   # no fallar si el cert ya no existe
        )
        ed.ssl_emitido = False
        ed.ssl_cert_path = ""
        ed.ssl_key_path = ""
        ed.save(update_fields=[
            "ssl_emitido", "ssl_cert_path", "ssl_key_path", "actualizado_en",
        ])
```

### 5.3 Extensión futura sin tocar el dominio de negocio

Si en el futuro se decide cambiar el proveedor de certificados, se crea una
nueva clase que implementa la misma interfaz:

```python
class CloudflareSSLIssuanceService(SSLIssuanceService):
    # Implementación alternativa — el resto del código no cambia.
    ...
```

El código que llama a `SSLIssuanceService.emitir()` en `DomainVerificationService`
o en el management command no necesita modificarse.

---

## 6. Renovación de Certificados

### 6.1 Mecanismo

certbot instala por defecto un timer systemd (`certbot.timer`) que ejecuta
`certbot renew` dos veces al día. Si algún certificado tiene menos de 30 días
de validez restante, certbot lo renueva automáticamente.

```
[systemd timer: certbot.timer, ejecuta certbot.service cada 12 h]
  certbot renew --quiet
    → si renueva algún cert:
        deploy-hook: systemctl reload nginx
```

### 6.2 Configuración del deploy-hook

```bash
# /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
#!/bin/bash
systemctl reload nginx
```

Con este archivo, certbot hace `reload` automáticamente después de cada
renovación exitosa, sin ningún cron adicional.

### 6.3 Sincronización de `ssl_expira_en` en BD

Certbot renueva los certs pero no actualiza la BD. Un management command
semanal sincroniza el campo:

```
manage.py sync_ssl_expiry
  → para cada EmpresaDominio[ssl_emitido=True]:
      leer fecha de expiración del cert en disco
      si difiere de ssl_expira_en → actualizar BD
```

Esto permite mostrar la fecha de vencimiento en el panel de admin y generar
alertas si un cert no se renovó por algún motivo.

---

## 7. Escalabilidad

### 7.1 100 dominios

| Aspecto | Análisis |
|---|---|
| Archivos Nginx | 100 archivos .conf — gestión trivial |
| Emisión de certs | 100 certs LE — bien dentro del free tier (50/dominio-raíz/semana) |
| Tiempo de nginx reload | ~1-2 s — sin impacto observable |
| Renovación | ~33 renovaciones/mes distribuidas por certbot.timer — sin problema |
| **Estado** | Sin restricciones operativas |

### 7.2 1 000 dominios

| Aspecto | Análisis |
|---|---|
| Archivos Nginx | 1 000 archivos .conf; `nginx -t` tarda ~2 s, reload ~8-10 s |
| Emisión de certs | Rate limit de LE relevante si muchos dominios se verifican el mismo día; máx. 50 certs por dominio raíz por semana (limitante si muchos tenants usan el mismo registrador) |
| Tiempo de nginx reload | ~10 s en el peor caso; Nginx recarga sin soltar conexiones activas (`nginx -s reload` usa graceful shutdown) — sin downtime hard |
| Renovación | ~333 renovaciones/mes — dentro del límite de LE (300 por 3 h) si se distribuyen uniformemente |
| **Estado** | Requiere cola de emisión con backoff para ráfagas; renovación automática sin problemas |

### 7.3 10 000 dominios

| Aspecto | Análisis |
|---|---|
| Archivos Nginx | 10 000 archivos .conf; reload puede tardar 30-60 s; nginx mantiene conexiones activas durante el reload pero el worker nuevo tarda en arrancar |
| Rate limit LE | 300 renovaciones por 3 h — con 10 000 dominios de 90 días de validez, se necesitan ~111 renovaciones/h de media; en picos (dominios emitidos el mismo día) puede superar el límite |
| Renovación | Requiere escalonado explícito en la emisión inicial: distribuir certbot-certonly en un periodo de 30 días para evitar picos de renovación simultánea |
| Alternativa a escala | A 10 000 dominios la arquitectura sigue siendo válida con una cola de emisión y un sistema de monitoreo de expiración. Si el rate limit se convierte en un bloqueo real, `CloudflareSSLIssuanceService` puede activarse para dominios nuevos sin tocar los existentes |
| **Estado** | Viable con cola + escalonado; requiere planificación antes de alcanzar este volumen |

---

## 8. Impacto en `HostTenantMiddleware`

`HostTenantMiddleware` (en `taller/middleware/host_tenant.py`) resuelve el
tenant por host y no requiere cambios. El dominio llega a Django con
`Host: taller-juan.cl` gracias a `proxy_set_header Host $host` en Nginx.

### 8.1 `ALLOWED_HOSTS`

Con la arquitectura per-dominio, Nginx valida `server_name` antes de hacer
`proxy_pass`. Un request con un `Host` que no tenga bloque `server {}` en
Nginx nunca llega a Django. El bloque por defecto (`default_server`) puede
devolver 444 (sin respuesta) para hosts no reconocidos.

Configuración recomendada en producción:

```python
# gestion_taller/settings/__init__.py
if DEBUG:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
else:
    # Nginx filtra hosts inválidos antes de llegar a Django.
    # HostTenantMiddleware valida adicionalmente contra EmpresaDominio[ACTIVO].
    ALLOWED_HOSTS = ["egarage.cl", "www.egarage.cl", "*"]
```

El `"*"` es seguro en producción bajo esta arquitectura porque:
1. El puerto 8000 no está expuesto externamente (firewall del VPS).
2. Nginx solo hace `proxy_pass` a bloques con `server_name` explícito.
3. `HostTenantMiddleware` rechaza cualquier host que no tenga un
   `EmpresaDominio[estado=ACTIVO]` asociado.

### 8.2 `CSRF_TRUSTED_ORIGINS`

Las peticiones POST desde un dominio de tenant fallarán el check CSRF si el
origen no está en `CSRF_TRUSTED_ORIGINS`. La solución para el workspace
completo (Fase 3):

```python
class TenantAwareCsrfMiddleware(CsrfViewMiddleware):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        if getattr(request, "empresa", None) is not None:
            # Dominio ya validado por HostTenantMiddleware → confiar en el origen
            request.META["CSRF_COOKIE_USED"] = True
        return super().process_view(request, callback, callback_args, callback_kwargs)
```

Se implementa en Fase 3, cuando el workspace sirve bajo el dominio propio.

### 8.3 Cabeceras recibidas por Django

```
Host: taller-juan.cl          ← $host de Nginx (server_name)
X-Forwarded-Host: taller-juan.cl
X-Forwarded-Proto: https
X-Forwarded-For: <IP real del visitante>
```

`request.get_host()` con `USE_X_FORWARDED_HOST=True` devuelve `taller-juan.cl`.
No requiere ningún cambio en el middleware.

---

## 9. Impacto en `DomainVerificationService`

`DomainVerificationService` (en `taller/services/domain_verification.py`)
verifica el registro TXT y es completamente independiente del proveedor SSL.
No requiere cambios.

El flujo de Fase 3 añade la llamada a `SSLIssuanceService` después de la
verificación TXT exitosa:

```
DomainVerificationService.verificar(ed)
  → éxito → ed.estado = ACTIVO

LetsEncryptSSLIssuanceService.emitir(ed)
  → certbot, conf Nginx, reload
  → ed.ssl_emitido = True
  → ed.ssl_expira_en = <fecha>
```

Cualquier fallo en la emisión SSL no revierte la verificación TXT. El dominio
queda en `ACTIVO` con `ssl_emitido=False` y puede reintentarse sin volver a
verificar el TXT.

---

## 10. Campos del Modelo ya Preparados

`EmpresaDominio` tiene todos los campos necesarios para Fase 3 sin nuevas
migraciones:

| Campo | Uso con Let's Encrypt |
|---|---|
| `ssl_emitido` | `True` tras certbot exitoso + nginx reload |
| `ssl_cert_path` | `/etc/letsencrypt/live/<dominio>/fullchain.pem` |
| `ssl_key_path` | `/etc/letsencrypt/live/<dominio>/privkey.pem` |
| `ssl_expira_en` | Fecha leída del cert; sincronizada semanalmente |
| `estado = SSL_PENDIENTE` | Mientras certbot está en ejecución |
| `get_cname_target()` | Devuelve `"proxy.egarage.cl"` o la IP del VPS; ambas válidas |

---

## 11. Secuencia de Implementación (Fase 3)

```
Paso 1 — Infraestructura (sin código Django):
  a. Verificar que certbot, certbot.timer y el deploy-hook están activos.
  b. Crear /var/www/certbot con permisos correctos para HTTP-01 challenge.
  c. Añadir bloque Nginx default_server que devuelva 444 para hosts
     sin bloque explícito (previene requests a Django con host desconocido).
  d. Verificar que el puerto 8000 no está expuesto externamente.

Paso 2 — Django settings:
  a. ALLOWED_HOSTS: añadir "*" en producción (ver §8.1).
  b. CSRF: planificar TenantAwareCsrfMiddleware (implementar al activar workspace).

Paso 3 — ssl_issuance.py (código nuevo):
  a. Definir SSLIssuanceService (ABC).
  b. Implementar LetsEncryptSSLIssuanceService.emitir() y .revocar().
  c. Tests unitarios con mock de subprocess.run.

Paso 4 — Management command verify_custom_domain:
  a. Recibe --dominio o --all (todos los PENDIENTE/ERROR_DNS).
  b. Llama a DomainVerificationService.verificar(ed).
  c. Si éxito, llama a LetsEncryptSSLIssuanceService.emitir(ed).
  d. Registra resultado en log estructurado.

Paso 5 — Management command sync_ssl_expiry:
  a. Lee fecha de expiración de cada cert en disco.
  b. Actualiza ssl_expira_en si difiere.
  c. Alerta si ssl_expira_en < 14 días y ssl_emitido=True.

Paso 6 — Revocación al suspender:
  a. DomainService.suspender() llama a LetsEncryptSSLIssuanceService.revocar().
  b. Elimina conf Nginx + cert certbot + nginx reload.

Paso 7 — Notificación al tenant:
  a. Email de confirmación al activar SSL (ssl_emitido = True).
  b. Email de aviso si ssl_expira_en < 14 días (desde sync_ssl_expiry).
```

---

## 12. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Rate limit LE en ráfaga de verificaciones | Media | Medio | Cola de emisión con backoff exponencial en `LetsEncryptSSLIssuanceService`; espaciar emisiones cuando se superen 40 certs/dominio-raíz/semana |
| `nginx -t` falla al recargar | Baja | Alto | Ejecutar `nginx -t` antes del reload; si falla, deshacer el archivo .conf generado y registrar el error; no llegar a `reload` |
| certbot no puede renovar (HTTP-01 bloqueado) | Baja | Alto | Verificar que `/.well-known/acme-challenge/` está accesible en el bloque por dominio; usar `certbot renew --dry-run` en staging |
| Tenant cambia el DNS después de verificar | Media | Medio | El cert ya existe; Nginx sigue sirviendo aunque el DNS cambie. El dominio quedaría huérfano. Monitoreo periódico de resolución DNS activo |
| Tenant borra el registro TXT antes de verificar | Alta | Bajo | `DomainVerificationService` detecta la ausencia y marca `ERROR_DNS`; el flujo ya lo maneja |
| Nginx reload lento a > 1 000 dominios | Media | Bajo | `nginx -s reload` no interrumpe conexiones activas; el impacto es latencia en el arranque del nuevo worker, no downtime. Aceptable hasta 10 000 dominios |
| cert expirado no detectado | Baja | Alto | `sync_ssl_expiry` semanal + alerta a 14 días + monitoreo externo (Uptime Robot o similar) del dominio del tenant |

---

## 13. Consecuencias de Esta Decisión

**Positivas:**
- Stack 100% conocido: certbot, Nginx y systemd ya están operando en el VPS.
- Costo cero por dominio adicional (Let's Encrypt es gratuito).
- Sin dependencias de API externas en el flujo crítico de emisión.
- `SSLIssuanceService` como interfaz garantiza que un cambio de proveedor
  en el futuro no afecta al dominio de negocio.
- El renovado automático vía `certbot.timer` ya funciona para `egarage.cl`;
  se extiende sin configuración adicional a los dominios de tenants.

**Negativas:**
- A partir de ~1 000 dominios la emisión en ráfaga requiere una cola con
  backoff. No es un trabajo trivial pero es predecible e implementable.
- `nginx reload` agrega latencia al flujo de activación (~2-10 s). No es
  perceptible para el tenant porque el proceso ocurre en background.
- certbot necesita ejecutarse con permisos elevados (root o `sudo`). El
  management command que lo invoca debe ejecutarse desde un entorno controlado,
  no desde el proceso web de Django.

**Neutrales:**
- `HostTenantMiddleware` y `DomainVerificationService` no requieren cambios.
- `EmpresaDominio` no requiere nuevas migraciones para Fase 3.
- La instrucción de DNS para el tenant (registro A a la IP del VPS) ya
  aparece correctamente en `settings.html` y puede actualizarse si se añade
  un balanceador en el futuro.
