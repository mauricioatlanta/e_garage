# ADR-002 — Dominios Personalizados para Tenants

**Estado:** Propuesto  
**Fecha:** 2026-07-28  
**Autores:** Mauricio Alvarado  
**Revisores:** —  
**Relacionado con:** ADR-001 (Arquitectura Multi-Tenant), VERTICAL_ARCHITECTURE_V1.md

---

## 1. Resumen Ejecutivo

Este documento describe el diseño técnico para permitir que cada tenant de eGarage exponga su workspace bajo un dominio propio (ej. `taller-juan.com`) en lugar de — o además de — la URL canónica `egarage.cl/cl/es/workspace/`.

La implementación se divide en dos fases:

- **Fase 1** (MVP): Verificación de dominio + redirección 302 al URL canónico de eGarage. Sin cambios en la capa de URLs ni en las vistas existentes. Cero riesgo para tenants actuales.
- **Fase 2** (Full): Workspace completo servido bajo el dominio personalizado, con SSL automático vía Let's Encrypt, sin redirección visible al usuario.

Ningún archivo Python, migración ni configuración de Nginx debe modificarse hasta que este documento sea aprobado.

---

## 2. Contexto y Motivación

### 2.1 Problema

Los tenants de eGarage actualmente acceden a su workspace mediante una URL que incluye el código de país y el prefijo de idioma:

```
https://egarage.cl/cl/es/workspace/
https://egarage.cl/mx/es/workspace/
```

Esto tiene dos consecuencias negativas para el posicionamiento comercial:

1. **Branding débil**: El URL visibiliza `egarage.cl`, no el nombre del negocio del cliente. Un taller que comparte un link con un cliente expone que usa una plataforma genérica.
2. **Fricción en la adopción vertical**: Los productos Workshop/Salvage/Parts (definidos en ADR-001) se posicionan como especializados. Si la URL sigue siendo genérica, el mensaje no es coherente.

### 2.2 Solución

Permitir que cada empresa configure un dominio propio que apunte a su workspace eGarage. Ejemplo:

| Tenant | URL actual | URL con dominio propio |
|---|---|---|
| Taller Juan | `egarage.cl/cl/es/workspace/` | `gestión.tallerjuan.cl/` |
| Desarmaduria Atlanta | `egarage.cl/cl/es/desarme/` | `stock.atlantareciclajes.cl/` |

---

## 3. Objetivos

### 3.1 Funcionales

- Un tenant puede registrar y verificar un dominio personalizado desde el panel de configuración.
- El dominio verificado responde con la misma interfaz que el workspace de eGarage.
- La verificación de dominio usa un registro TXT en DNS (método más universal, independiente del proveedor DNS del cliente).
- El certificado SSL se emite automáticamente para el dominio verificado.
- El dominio activo sirve como "front door" alternativo: el tenant puede acceder por el dominio propio o por el URL eGarage; ambos muestran el mismo workspace.

### 3.2 No-objetivos (fuera de alcance)

- Multi-dominio por tenant (un tenant = un dominio activo máximo en Fase 1).
- Sub-dominios wildcart de eGarage (ej. `juan.egarage.cl`): posible en Fase 3, no documentado aquí.
- Branding completo white-label (logo/colores del cliente): separado de la infraestructura de dominio.
- Reemplazar la URL canónica `egarage.cl`: ambas URLs coexisten.

---

## 4. Restricciones y Supuestos

| Restricción | Detalle |
|---|---|
| Infraestructura actual | Nginx + Gunicorn + Cloudflare (CDN + SSL). Let's Encrypt para cert de `egarage.cl`. |
| Django settings | `USE_X_FORWARDED_HOST = True`. `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`. |
| `ALLOWED_HOSTS` actual | Solo `["egarage.cl", "www.egarage.cl"]` — debe extenderse. |
| `CSRF_TRUSTED_ORIGINS` actual | Solo dominios de eGarage — debe extenderse dinámicamente. |
| Arquitectura URL | Prefijos de país/idioma `/cl/es/`, `/mx/es/` embebidos en todas las rutas. |
| Sin Kubernetes | Despliegue tradicional VPS/Droplet. No hay cert-manager automático. |
| Cloudflare en capa pública | Todos los requests entran via Cloudflare antes de llegar a Nginx. |

---

## 5. Arquitectura Actual

### 5.1 Stack de red

```
Browser
  │ HTTPS (SSL terminado en Cloudflare)
  ▼
Cloudflare CDN
  │ HTTP/HTTPS (X-Forwarded-Proto: https, CF-Connecting-IP)
  ▼
Nginx  (ssl_certificate: egarage.cl Let's Encrypt)
  │ proxy_pass a 127.0.0.1:8000
  ▼
Gunicorn (Django)
```

### 5.2 Stack de middleware Django (orden de ejecución)

```
01. SecurityMiddleware
02. SessionMiddleware
03. LocaleMiddleware
04. CommonMiddleware
05. CsrfViewMiddleware
06. AuthenticationMiddleware
07. allauth.AccountMiddleware
08. MessageMiddleware
09. XFrameOptionsMiddleware
10. EmpresaResolverMiddleware   ← inyecta request.empresa desde request.user
11. VerificarSuscripcionMiddleware
```

### 5.3 Resolución de tenant (flujo actual)

```
HTTP request
  → EmpresaResolverMiddleware
    → request.user.is_authenticated?
      → SÍ: get_user_empresa_safe(user) → request.empresa = Empresa
      → NO: request.empresa = None (rutas públicas pasan)
```

Toda la resolución de tenant depende del usuario autenticado. **No existe ninguna lógica de resolución por nombre de host.**

---

## 6. Arquitectura Propuesta

### 6.1 Componentes nuevos

| Componente | Tipo | Responsabilidad |
|---|---|---|
| `EmpresaDominio` | Modelo Django | Almacena y controla el estado de cada dominio personalizado |
| `HostTenantMiddleware` | Middleware | Resuelve tenant desde el header `Host` antes que `EmpresaResolverMiddleware` |
| `DomainVerificationService` | Service class | Orquesta el flujo de verificación TXT + polling |
| `SSLIssuanceService` | Service class | Llama a certbot, almacena resultado, notifica Nginx |
| `generate_nginx_domains` | Management command | Genera fragmentos `.conf` por dominio y hace reload de Nginx |

### 6.2 Posición de `HostTenantMiddleware` en el stack

```
01. SecurityMiddleware
02. SessionMiddleware
03. LocaleMiddleware
04. CommonMiddleware
05. CsrfViewMiddleware
06. AuthenticationMiddleware
07. allauth.AccountMiddleware
08. MessageMiddleware
09. XFrameOptionsMiddleware
10. HostTenantMiddleware        ← NUEVO — antes de EmpresaResolverMiddleware
11. EmpresaResolverMiddleware   ← modificado para respetar pre-resolución
12. VerificarSuscripcionMiddleware
```

---

## 7. Diagrama del Flujo HTTP

### 7.1 Fase 1 — Redirección al URL canónico

```
Browser                Cloudflare            Nginx            Django
  │                        │                   │                 │
  ├─ GET taller.com/ ─────▶│                   │                 │
  │  (SSL @ Cloudflare)    ├── CF proxy ───────▶│                 │
  │                        │   Host: taller.com │── proxy_pass ──▶│
  │                        │                   │                 │
  │                        │                   │   HostTenantMW  │
  │                        │                   │   ┌─────────────┤
  │                        │                   │   │ lookup       │
  │                        │                   │   │ EmpresaDominio│
  │                        │                   │   │ WHERE        │
  │                        │                   │   │  dominio=    │
  │                        │                   │   │  "taller.com"│
  │                        │                   │   │  AND verificado│
  │                        │                   │   │              │
  │                        │                   │   │ → empresa_id=7│
  │                        │                   │   │ request.     │
  │                        │                   │   │  empresa = 7 │
  │                        │                   │   │ request.     │
  │                        │                   │   │  is_custom_  │
  │                        │                   │   │  domain=True │
  │                        │                   │   └─────────────┤
  │                        │                   │                 │
  │                        │                   │   → 302 redirect│
  │                        │                   │     to egarage.cl│
  │                        │                   │     /cl/es/     │
  │                        │                   │     workspace/  │
  │◀── 302 ────────────────│◀──────────────────│◀────────────────│
  │  Location: egarage.cl/ │                   │                 │
```

### 7.2 Fase 2 — Dominio propio completo

```
Browser                Cloudflare            Nginx            Django
  │                        │                   │                 │
  ├─ GET taller.com/ ─────▶│                   │                 │
  │  (SSL @ Cloudflare)    ├── CF proxy ───────▶│                 │
  │                        │   Host: taller.com │               │
  │                        │   X-Forwarded-For  │── proxy_pass ──▶│
  │                        │   X-Forwarded-Proto│                 │
  │                        │                   │   HostTenantMW  │
  │                        │                   │   → empresa = 7 │
  │                        │                   │   → request.    │
  │                        │                   │     country="CL"│
  │                        │                   │                 │
  │                        │                   │   EmpresaResolver│
  │                        │                   │   → empresa ya  │
  │                        │                   │     definida,   │
  │                        │                   │     skip lookup │
  │                        │                   │                 │
  │                        │                   │   CustomDomain  │
  │                        │                   │   RouterView    │
  │                        │                   │   → sirve       │
  │                        │                   │     workspace   │
  │◀── 200 workspace ──────│◀──────────────────│◀────────────────│
```

---

## 8. Diseño del Modelo `EmpresaDominio`

### 8.1 Código propuesto

```python
# taller/models/empresa_dominio.py
import uuid

from django.db import models
from django.utils import timezone


class EmpresaDominio(models.Model):
    """
    Representa un dominio personalizado verificado que un tenant ha asociado
    a su cuenta de eGarage.

    Ciclo de vida de estados:
        PENDIENTE → VERIFICANDO → ACTIVO
                 ↘             → ERROR_VERIFICACION
                               → SUSPENDIDO (admin action)
    """

    class Estado(models.TextChoices):
        PENDIENTE        = "PENDIENTE",        "Pendiente de verificación"
        VERIFICANDO      = "VERIFICANDO",      "Verificación en curso"
        ACTIVO           = "ACTIVO",           "Activo"
        ERROR_DNS        = "ERROR_DNS",        "Error en verificación DNS"
        SSL_PENDIENTE    = "SSL_PENDIENTE",    "SSL en trámite"
        SUSPENDIDO       = "SUSPENDIDO",       "Suspendido por administrador"

    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="dominios_personalizados",
    )
    dominio = models.CharField(
        max_length=253,   # RFC 1035: longitud máxima de un FQDN
        unique=True,
        db_index=True,
    )
    estado = models.CharField(
        max_length=25,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        db_index=True,
    )

    # Verificación DNS
    token_verificacion = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        help_text="Valor del registro TXT: egarage-verify=<token>",
    )
    verificado_en = models.DateTimeField(null=True, blank=True)
    ultimo_check_dns = models.DateTimeField(null=True, blank=True)
    intentos_verificacion = models.PositiveSmallIntegerField(default=0)

    # SSL
    ssl_emitido = models.BooleanField(default=False)
    ssl_cert_path = models.CharField(max_length=512, blank=True)
    ssl_key_path  = models.CharField(max_length=512, blank=True)
    ssl_expira_en = models.DateField(null=True, blank=True)

    # Auditoría
    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_por     = models.ForeignKey(
        "auth.User",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        verbose_name = "Dominio personalizado"
        verbose_name_plural = "Dominios personalizados"
        indexes = [
            models.Index(fields=["dominio", "estado"]),
            models.Index(fields=["empresa", "estado"]),
        ]
        constraints = [
            # Solo un dominio ACTIVO por empresa a la vez
            models.UniqueConstraint(
                fields=["empresa"],
                condition=models.Q(estado="ACTIVO"),
                name="uq_empresa_dominio_activo",
            )
        ]

    def get_txt_record_name(self) -> str:
        """Nombre del registro TXT que el cliente debe crear."""
        return f"_egarage-verify.{self.dominio}"

    def get_txt_record_value(self) -> str:
        """Valor del registro TXT que el cliente debe crear."""
        return f"egarage-verify={self.token_verificacion}"

    def marcar_verificado(self) -> None:
        self.estado = self.Estado.ACTIVO
        self.verificado_en = timezone.now()
        self.save(update_fields=["estado", "verificado_en", "actualizado_en"])

    @property
    def esta_activo(self) -> bool:
        return self.estado == self.Estado.ACTIVO

    def __str__(self) -> str:
        return f"{self.dominio} → {self.empresa} [{self.estado}]"
```

### 8.2 Índice de lookup crítico

La query que ejecuta `HostTenantMiddleware` en **cada request** es:

```python
EmpresaDominio.objects.select_related("empresa").get(
    dominio=host,
    estado=EmpresaDominio.Estado.ACTIVO,
)
```

El índice `Index(fields=["dominio", "estado"])` cubre esta query exacta. **Debe existir antes del deploy de `HostTenantMiddleware`.**

### 8.3 Cache obligatorio

Con volúmenes altos de requests, esta query no puede ir a la base de datos en cada petición. Se debe implementar cache con TTL corto:

```python
# Cache key: custom_domain:{dominio}
# TTL: 300 segundos (5 minutos)
# Invalidar en: EmpresaDominio.save() via signal post_save
```

Candidatos: Redis (si disponible), Django `cache` con backend de memcached, o `functools.lru_cache` con TTL manual (solo válido en proceso single-worker).

---

## 9. Estrategia de `HostTenantMiddleware`

### 9.1 Lógica completa

```python
# taller/middleware/host_tenant.py

import logging
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseNotFound

logger = logging.getLogger(__name__)

# Hosts canónicos de eGarage: nunca hacer lookup por dominio personalizado
CANONICAL_HOSTS = frozenset(getattr(settings, "EGARAGE_CANONICAL_HOSTS", [
    "egarage.cl",
    "www.egarage.cl",
]))


class HostTenantMiddleware:
    """
    Resuelve el tenant (Empresa) desde el header HTTP Host cuando el request
    llega a través de un dominio personalizado verificado.

    Debe estar ANTES de EmpresaResolverMiddleware en MIDDLEWARE.

    Efectos secundarios en request:
        request.custom_domain   → EmpresaDominio | None
        request.empresa         → Empresa | None  (pre-resuelto)
        request.country         → str | None      (del tenant)
        request.is_custom_domain → bool
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.custom_domain    = None
        request.is_custom_domain = False

        host = self._get_host(request)

        if host and host not in CANONICAL_HOSTS:
            self._resolve_tenant(request, host)

        return self.get_response(request)

    @staticmethod
    def _get_host(request) -> str | None:
        """Extrae el hostname limpio (sin puerto)."""
        try:
            return request.get_host().split(":")[0].lower().strip()
        except Exception:
            return None

    def _resolve_tenant(self, request, host: str) -> None:
        from taller.models.empresa_dominio import EmpresaDominio  # import local

        cache_key = f"custom_domain:{host}"
        empresa_id = cache.get(cache_key)

        if empresa_id is None:
            try:
                ed = EmpresaDominio.objects.select_related("empresa").get(
                    dominio=host,
                    estado=EmpresaDominio.Estado.ACTIVO,
                )
                empresa_id = ed.empresa_id
                cache.set(cache_key, empresa_id, timeout=300)
                request.custom_domain    = ed
                request.empresa          = ed.empresa
                request.country          = getattr(ed.empresa, "pais", None)
                request.is_custom_domain = True
            except EmpresaDominio.DoesNotExist:
                logger.debug("Host %s no corresponde a ningún dominio verificado", host)
            except Exception as exc:
                logger.error("Error resolviendo dominio personalizado %s: %s", host, exc)
        else:
            # Hit de cache: solo tenemos empresa_id, cargamos empresa completa
            try:
                from taller.models.empresa import Empresa
                empresa = Empresa.objects.get(pk=empresa_id)
                request.empresa          = empresa
                request.country          = getattr(empresa, "pais", None)
                request.is_custom_domain = True
            except Exception as exc:
                cache.delete(cache_key)  # cache inválido, forzar re-lookup
                logger.error("Cache hit inválido para dominio %s: %s", host, exc)
```

### 9.2 Decisión de diseño: no lanzar 404 en dominios desconocidos

Si un dominio llega y no está en `EmpresaDominio`, `HostTenantMiddleware` no bloquea el request — simplemente deja `request.is_custom_domain = False`. El resto del stack maneja el caso (usuario no autenticado → redirige a login).

Esto permite que Nginx reciba requests de dominios no registrados sin que Django interrumpa el flujo con un 404 genérico, que podría romper el challenge de ACME/certbot.

---

## 10. Integración con `EmpresaResolverMiddleware`

### 10.1 Modificación requerida

`EmpresaResolverMiddleware` actualmente siempre sobrescribe `request.empresa`:

```python
# ANTES (actual):
def __call__(self, request):
    request.empresa = None   # ← PROBLEMA: borra lo que HostTenantMW puso
    ...
    if request.user.is_authenticated:
        empresa = get_user_empresa_safe(request.user)
        request.empresa = empresa
```

Debe modificarse para respetar la pre-resolución:

```python
# DESPUÉS (propuesto):
def __call__(self, request):
    # Si HostTenantMiddleware ya resolvió la empresa (dominio personalizado),
    # no sobrescribir — solo inicializar campos que faltan.
    if not getattr(request, "empresa", None):
        request.empresa = None
    if not getattr(request, "company", None):
        request.company = None
    if not getattr(request, "country", None):
        request.country = None

    if request.user.is_authenticated:
        if request.empresa is None:
            # Flujo normal: resolver desde el usuario
            empresa = get_user_empresa_safe(request.user)
            if empresa is not None:
                request.empresa = empresa
                request.company = empresa
                request.country = getattr(empresa, "pais", None)
            elif not self._is_exempt(request.path):
                logout(request)
                return redirect("account_login")
        else:
            # Dominio personalizado pre-resuelto: sincronizar aliases
            request.company = request.empresa
            # country ya viene de HostTenantMiddleware

    return self.get_response(request)
```

### 10.2 Invariante de seguridad

**El usuario autenticado DEBE pertenecer al tenant del dominio personalizado.**

Si `request.empresa` fue resuelto por dominio y el usuario está autenticado pero pertenece a una empresa distinta, se debe redirigir o dar error 403. Esto se maneja en `EmpresaResolverMiddleware` con una validación adicional:

```python
# Validación de cruce de tenant
if request.is_custom_domain and request.user.is_authenticated:
    user_empresa = get_user_empresa_safe(request.user)
    if user_empresa and user_empresa.pk != request.empresa.pk:
        # Usuario autenticado en empresa B accediendo al dominio de empresa A
        logout(request)
        return redirect("account_login")
```

---

## 11. Compatibilidad Hacia Atrás

### 11.1 Impacto en tenants existentes

| Elemento | Impacto | Acción requerida |
|---|---|---|
| URLs canónicas `egarage.cl/cl/es/...` | **Ninguno** — siguen funcionando exactamente igual | Nada |
| `EmpresaResolverMiddleware` | Modificación menor: agrega condición `if not request.empresa` | Requiere tests de regresión |
| Contexto de templates | `request.empresa`, `request.country` siguen disponibles igual | Nada |
| Vistas existentes | No saben nada del dominio personalizado | Nada |
| Tests existentes | Tests que crean `Client()` sin `HTTP_HOST` siguen pasando | Nada |
| `ALLOWED_HOSTS` | Debe extenderse | Ver §14.3 |

### 11.2 Tenants sin dominio personalizado

`EmpresaDominio` no es obligatorio. Un tenant sin dominio registrado no es afectado en absoluto. `HostTenantMiddleware` hace un lookup en la tabla, no encuentra nada para hosts canónicos, y pasa el request sin modificar.

### 11.3 Período de transición sin downtime

- Desplegar `EmpresaDominio` (migración solo-additive: CREATE TABLE).
- Desplegar `HostTenantMiddleware` sin activar ningún dominio en la tabla.
- Desplegar modificación de `EmpresaResolverMiddleware`.
- Verificar que todo el tráfico existente es idéntico (los lookups devuelven `DoesNotExist` para todos los hosts de eGarage).
- Activar el primer dominio de cliente como prueba piloto.

---

## 12. Flujo de Verificación DNS

### 12.1 Diagrama de estados de `EmpresaDominio`

```
┌─────────────┐     registrar()      ┌──────────────┐
│  (no existe) │ ──────────────────→ │  PENDIENTE   │
└─────────────┘                      └──────┬───────┘
                                            │ iniciar_verificacion()
                                            ▼
                                     ┌──────────────┐
                                     │ VERIFICANDO  │◄─── retry (max 10)
                                     └──────┬───────┘
                                     /      │       \
                          TXT ok    /       │        \ TXT no encontrado
                                   ▼    (timeout)    ▼
                           ┌──────────┐          ┌───────────────┐
                           │  ACTIVO  │          │  ERROR_DNS    │
                           └────┬─────┘          └───────────────┘
                                │  emitir_ssl()
                                ▼
                         ┌─────────────┐
                         │SSL_PENDIENTE│
                         └──────┬──────┘
                                │ ssl_ok
                                ▼
                           ┌──────────┐
                           │  ACTIVO  │ (con ssl_emitido=True)
                           └──────────┘
```

### 12.2 Instrucción al usuario (UI)

El panel de configuración muestra:

```
Paso 1: Crea un registro TXT en tu proveedor DNS

  Nombre:  _egarage-verify.tudominio.com
  Tipo:    TXT
  Valor:   egarage-verify=a3f8e2d1-...
  TTL:     300 (5 minutos)

Paso 2: Crea un registro CNAME

  Nombre:  tudominio.com   (o el subdominio que quieras)
  Tipo:    CNAME
  Valor:   proxy.egarage.cl
  TTL:     300

Paso 3: Haz clic en "Verificar dominio"
```

### 12.3 Lógica de verificación

```python
# taller/services/domain_verification.py

import dns.resolver   # dnspython

class DomainVerificationService:
    MAX_INTENTOS = 10
    TIMEOUT_POR_INTENTO = 10  # segundos

    @classmethod
    def verificar(cls, empresa_dominio: EmpresaDominio) -> bool:
        expected = empresa_dominio.get_txt_record_value()
        fqdn     = empresa_dominio.get_txt_record_name()

        empresa_dominio.intentos_verificacion += 1
        empresa_dominio.ultimo_check_dns = timezone.now()

        try:
            answers = dns.resolver.resolve(fqdn, "TXT", lifetime=cls.TIMEOUT_POR_INTENTO)
            for rdata in answers:
                for txt_string in rdata.strings:
                    if txt_string.decode("utf-8", errors="ignore") == expected:
                        empresa_dominio.marcar_verificado()
                        return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.Timeout):
            pass

        if empresa_dominio.intentos_verificacion >= cls.MAX_INTENTOS:
            empresa_dominio.estado = EmpresaDominio.Estado.ERROR_DNS
        else:
            empresa_dominio.estado = EmpresaDominio.Estado.VERIFICANDO

        empresa_dominio.save(
            update_fields=["estado", "intentos_verificacion", "ultimo_check_dns", "actualizado_en"]
        )
        return False
```

### 12.4 Polling

- El usuario hace clic en "Verificar" → tarea Celery (o sincrónica con polling en UI) ejecuta `DomainVerificationService.verificar()`.
- Si falla: muestra el intento número N/10 y sugiere esperar propagación DNS.
- Si no hay Celery: ejecutar sincrónico con timeout de 15s y devolver estado inmediato.

---

## 13. Flujo de Emisión SSL

### 13.1 Prerrequisito

El dominio debe estar en estado `ACTIVO` (TXT verificado) **y** el CNAME debe apuntar a `proxy.egarage.cl` (verificado implícitamente por el challenge HTTP-01).

### 13.2 Método recomendado: Certbot HTTP-01

```
[Django trigger]
     │
     ▼
[Management command: python manage.py emitir_ssl --dominio tudominio.com]
     │
     ▼
[certbot certonly --webroot -w /var/www/certbot -d tudominio.com]
     │
     ▼ (certbot sirve challenge en /.well-known/acme-challenge/)
     │
[Let's Encrypt valida el CNAME → proxy.egarage.cl]
     │
     ▼
[cert emitido en /etc/letsencrypt/live/tudominio.com/]
     │
     ▼
[EmpresaDominio.ssl_cert_path y ssl_key_path actualizados]
     │
     ▼
[Management command: python manage.py generate_nginx_domains]
     │
     ▼
[Nginx reload: nginx -s reload]
```

### 13.3 Prerrequisito en Nginx para el challenge

El bloque catch-all de Nginx debe servir los challenges **antes** de tener el cert:

```nginx
server {
    listen 80;
    server_name _;

    # Let's Encrypt ACME challenge — sin autenticación, sin redirect
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
        try_files $uri =404;
    }

    # Todo lo demás → HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}
```

### 13.4 Renovación automática

Let's Encrypt emite certs por 90 días. La renovación se gestiona con:

```bash
# /etc/cron.d/certbot-renew
0 3 * * * root certbot renew --quiet && python manage.py generate_nginx_domains && nginx -s reload
```

`EmpresaDominio.ssl_expira_en` debe actualizarse después de cada renovación. Un management command `sync_ssl_expiry` puede leer la fecha del archivo de cert y actualizar el campo.

---

## 14. Cambios en Nginx

### 14.1 Estructura de configuración propuesta

```
/etc/nginx/
├── nginx.conf
├── sites-enabled/
│   ├── egarage.cl.conf          ← configuración actual (sin cambios)
│   └── custom-domains.conf      ← NUEVO: incluye fragmentos dinámicos
└── custom-domains/
    ├── taller-juan.com.conf     ← generado por management command
    ├── atlanta.cl.conf
    └── ...
```

### 14.2 Fragmento por dominio (generado automáticamente)

```nginx
# /etc/nginx/custom-domains/taller-juan.com.conf
# Generado por: python manage.py generate_nginx_domains
# No editar manualmente.

server {
    listen 443 ssl http2;
    server_name taller-juan.com;

    ssl_certificate     /etc/letsencrypt/live/taller-juan.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/taller-juan.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 50M;

    # Pasar el host original al backend
    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    location / {
        proxy_pass http://127.0.0.1:8000;
    }

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
}
```

### 14.3 `custom-domains.conf` (incluido desde nginx.conf)

```nginx
# /etc/nginx/sites-enabled/custom-domains.conf
include /etc/nginx/custom-domains/*.conf;
```

### 14.4 Cambios en Django settings para dominios dinámicos

```python
# gestion_taller/settings/prod.py

# ALLOWED_HOSTS debe aceptar dominios personalizados verificados.
# Opción A (permisiva, segura porque la validación real la hace HostTenantMiddleware):
ALLOWED_HOSTS = ["*"]

# Opción B (precisa, requiere consultar DB en cada deploy — no recomendado):
# ALLOWED_HOSTS = ["egarage.cl", "www.egarage.cl"] + list_from_db()

# CSRF: agregar dominios personalizados cuando se verifican
# Se implementa con una función que lee EmpresaDominio activos:
def get_csrf_trusted_origins():
    base = ["https://egarage.cl", "https://www.egarage.cl"]
    try:
        from taller.models.empresa_dominio import EmpresaDominio
        activos = EmpresaDominio.objects.filter(
            estado="ACTIVO"
        ).values_list("dominio", flat=True)
        return base + [f"https://{d}" for d in activos]
    except Exception:
        return base  # fallback si la DB no está disponible

CSRF_TRUSTED_ORIGINS = get_csrf_trusted_origins()
```

**Nota sobre `ALLOWED_HOSTS = ["*"]`**: Cambiar a wildcard es seguro en este caso porque:
1. Nginx hace bind solo en las IPs del servidor (no expuesto a internet en puertos arbitrarios).
2. `HostTenantMiddleware` valida que el host existe en `EmpresaDominio` antes de continuar.
3. Django no usa `ALLOWED_HOSTS` para autorización de negocio, solo para prevenir ataques de Host Header injection.

---

## 15. Cambios en Cloudflare

### 15.1 Configuración en la cuenta eGarage

| Registro | Tipo | Valor | Proxy |
|---|---|---|---|
| `proxy.egarage.cl` | A | IP del servidor | ✅ Proxied |
| `egarage.cl` | A | IP del servidor | ✅ Proxied |
| `www.egarage.cl` | CNAME | `egarage.cl` | ✅ Proxied |

`proxy.egarage.cl` es el target al que los clientes apuntan su CNAME.

### 15.2 Configuración en la cuenta DNS del cliente

El cliente crea (en su proveedor DNS, cualquiera):

```
_egarage-verify.tudominio.com  TXT  "egarage-verify=<token-uuid>"
tudominio.com                  CNAME  proxy.egarage.cl
```

**No se requiere que el cliente use Cloudflare.** Funciona con cualquier proveedor DNS (GoDaddy, Namecheap, Route53, etc.).

### 15.3 Implicaciones del modo proxy de Cloudflare

Cuando el cliente apunta su CNAME a `proxy.egarage.cl` y Cloudflare está en la capa de eGarage (proxied):

- Cloudflare maneja el SSL hacia el browser del cliente.
- Nginx recibe la request con `Host: proxy.egarage.cl` (no el dominio del cliente).
- Para preservar el host original, Cloudflare debe enviar el header `CF-Connecting-IP` y el header `Host` original.

**Solución**: Configurar en Nginx que use `$http_cf_connecting_ip` o confiar en el header `X-Forwarded-Host` enviado por Cloudflare (ya hay soporte via `USE_X_FORWARDED_HOST = True` en Django).

Nginx debe pasar el host original:
```nginx
proxy_set_header X-Forwarded-Host $http_host;
```

Y `HostTenantMiddleware` debe leer de `HTTP_X_FORWARDED_HOST` cuando `USE_X_FORWARDED_HOST` está activo (Django lo hace automáticamente via `request.get_host()`).

### 15.4 Alternativa con Cloudflare SSL for SaaS

Cloudflare ofrece "Custom Hostnames" (SSL for SaaS) en plan Business/Enterprise. Con esta opción:

- El cliente crea un CNAME a `tudominio.com → proxy.egarage.cl`.
- Se registra el dominio como Custom Hostname en la zona de Cloudflare de eGarage.
- Cloudflare emite el cert automáticamente (sin certbot).
- Se elimina la necesidad de `SSLIssuanceService` y `generate_nginx_domains`.

**Ventaja**: mucho más simple operativamente.  
**Desventaja**: requiere plan Business de Cloudflare (~$200/mes) y vínculo estrecho con Cloudflare.

Esta opción se documenta como **ruta alternativa para Fase 3** si el volumen de dominios justifica el costo.

---

## 16. Plan de Migración Sin Downtime

### 16.1 Secuencia de despliegue

```
PASO 1 — Solo migración (additive, sin comportamiento nuevo)
  ├── python manage.py makemigrations taller  (nueva tabla EmpresaDominio)
  ├── python manage.py migrate                (CREATE TABLE)
  └── ⚠️  No desplegado ningún middleware todavía.

PASO 2 — Código desplegado, middleware en settings
  ├── Desplegar taller/models/empresa_dominio.py
  ├── Desplegar taller/middleware/host_tenant.py
  ├── Agregar HostTenantMiddleware a MIDDLEWARE (antes de EmpresaResolver)
  ├── Modificar EmpresaResolverMiddleware (condicional)
  ├── EmpresaDominio tabla está VACÍA → HostTenantMiddleware hace DoesNotExist en cada request
  └── ✅ Tráfico actual inalterado. Cero dominios activos.

PASO 3 — Nginx preparado para dominios personalizados
  ├── Crear directorio /etc/nginx/custom-domains/
  ├── Crear /etc/nginx/sites-enabled/custom-domains.conf con include
  ├── Crear bloque HTTP catch-all para ACME challenge
  └── nginx -t && nginx -s reload

PASO 4 — Primer dominio piloto
  ├── Crear EmpresaDominio para un tenant piloto
  ├── Verificar DNS → estado ACTIVO
  ├── Emitir SSL → certbot
  ├── Ejecutar: python manage.py generate_nginx_domains
  ├── nginx -s reload
  └── ✅ Probar acceso desde dominio piloto

PASO 5 — Abrir a todos los tenants
  ├── Habilitar UI de configuración de dominio en el panel
  └── Monitor de errores en HostTenantMiddleware y DNS checker
```

### 16.2 Invariante de seguridad durante la migración

En ningún paso existe una ventana donde un request pueda "filtrarse" al tenant incorrecto:

- Mientras `EmpresaDominio` está vacío: ningún host custom es reconocido.
- Cuando se activa el primer dominio: solo ese dominio es reconocido.
- La validación de cruce de tenant en `EmpresaResolverMiddleware` impide login cruzado.

---

## 17. Plan de Rollback

### 17.1 Rollback de Fase 2 (dominio full) → Fase 1 (redirect)

Cambiar `estado = ACTIVO` a `estado = PENDIENTE` en el registro `EmpresaDominio`. El middleware no encontrará el dominio y el usuario deberá acceder por el URL canónico.

```python
# En Django admin o management command:
EmpresaDominio.objects.filter(dominio="taller-juan.com").update(estado="PENDIENTE")
cache.delete("custom_domain:taller-juan.com")
```

Tiempo de rollback: < 5 minutos. No requiere deploy.

### 17.2 Rollback de middleware

Eliminar `HostTenantMiddleware` de `MIDDLEWARE` en settings y desplegar. Dado que la modificación de `EmpresaResolverMiddleware` es retrocompatible (`if not request.empresa` es siempre verdadero sin el middleware), el comportamiento vuelve al estado inicial.

### 17.3 Rollback de migración

`EmpresaDominio` es una tabla nueva sin referencias de FK inversas en modelos existentes. Se puede eliminar con `DROP TABLE` sin afectar datos existentes.

```sql
-- Rollback de emergencia (solo si es absolutamente necesario)
DROP TABLE taller_empresadominio;
```

---

## 18. Casos de Prueba

### 18.1 Unitarios (`HostTenantMiddleware`)

| Caso | Input (`HTTP_HOST`) | Estado en DB | Resultado esperado |
|---|---|---|---|
| Host canónico | `egarage.cl` | — | `request.is_custom_domain = False` |
| Dominio activo | `taller.com` | ACTIVO | `request.empresa = empresa_X`, `is_custom_domain = True` |
| Dominio pendiente | `taller.com` | PENDIENTE | `request.is_custom_domain = False` |
| Dominio desconocido | `otro.com` | no existe | `request.is_custom_domain = False` |
| DB unavailable | cualquiera | error de conexión | No propagar excepción, loguear, `is_custom_domain = False` |
| Host con puerto | `taller.com:8000` | ACTIVO | Strip del puerto, resuelve correctamente |

### 18.2 Integración (`EmpresaResolverMiddleware` modificado)

| Caso | `request.empresa` pre-seteado | Usuario autenticado | Resultado esperado |
|---|---|---|---|
| Flujo normal | None | Sí (owner empresa A) | `request.empresa = empresa_A` |
| Dominio propio, mismo usuario | empresa_A | Sí (owner empresa A) | `request.empresa = empresa_A`, sin re-lookup |
| Dominio propio, usuario cruzado | empresa_A | Sí (owner empresa B) | logout + redirect login |
| Dominio propio, no autenticado | empresa_A | No | `request.empresa = empresa_A` (páginas públicas del workspace) |

### 18.3 Verificación DNS

| Caso | Registro TXT en DNS | Resultado esperado |
|---|---|---|
| Token correcto | `egarage-verify=<uuid>` | `estado = ACTIVO` |
| Token incorrecto | `egarage-verify=otro-valor` | sigue en VERIFICANDO |
| Registro ausente | — | sigue en VERIFICANDO |
| NXDOMAIN | — | sigue en VERIFICANDO |
| 10 intentos fallidos | — | `estado = ERROR_DNS` |

### 18.4 CSRF con dominio personalizado

| Caso | `Origin` header | `CSRF_TRUSTED_ORIGINS` | Resultado esperado |
|---|---|---|---|
| POST desde dominio propio (Fase 2) | `https://taller.com` | incluye `https://taller.com` | 200 OK |
| POST desde dominio propio (Fase 2) | `https://taller.com` | no incluye `https://taller.com` | 403 Forbidden |
| POST desde eGarage canónico | `https://egarage.cl` | incluye `https://egarage.cl` | 200 OK |

### 18.5 E2E (Playwright)

```
Escenario: Acceso completo por dominio personalizado (Fase 2)

1. Configurar DNS local: taller-test.com → 127.0.0.1
2. Registrar EmpresaDominio(dominio="taller-test.com", estado=ACTIVO, empresa=empresa_fixture)
3. Navegador: GET http://taller-test.com/
4. Verificar: página de login del workspace (no redirección a egarage.cl)
5. Login con credenciales de empresa_fixture
6. Verificar: workspace visible con datos del tenant correcto
7. Verificar: ningún dato de otro tenant es accesible
```

---

## 19. Riesgos y Mitigaciones

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|
| R1 | Query `EmpresaDominio` en cada request añade latencia | Media | Alto | Cache Redis con TTL 300s; el lookup solo ocurre si el host no es canónico |
| R2 | `ALLOWED_HOSTS = ["*"]` amplía superficie de ataque | Baja | Medio | Validación real en middleware; Nginx bound a IP específica; Cloudflare filtra IPs |
| R3 | `CSRF_TRUSTED_ORIGINS` calculado en startup no incluye dominios registrados post-deploy | Media | Alto | Función que lee de DB en cada startup + señal post_save para restart controlado |
| R4 | Certbot falla si el CNAME aún no propagó | Alta | Bajo | Verificar CNAME antes de intentar SSL; retry automático |
| R5 | Nginx reload falla después de cert issuance | Baja | Medio | `nginx -t` antes del reload; rollback automático al config previo |
| R6 | Cliente apunta dominio a eGarage antes de verificar TXT | Media | Bajo | El middleware no reconoce el dominio hasta estado ACTIVO; UI advierte la secuencia correcta |
| R7 | Un tenant registra el dominio de otro tenant | Baja | Crítico | Verificación TXT: solo quien controla el DNS puede agregar el registro; unicidad de dominio en DB |
| R8 | Cert caducado sin renovación automática | Baja | Alto | `ssl_expira_en` en modelo; alerta cuando faltan 30 días; cron de renovación automática |
| R9 | Cruce de tenants: usuario de empresa B accede a dominio de empresa A | Baja | Crítico | Validación explícita en `EmpresaResolverMiddleware` (§10.2); tests de integración obligatorios |

---

## 20. Roadmap de Implementación por Fases

### Fase 0 — Fundación (sin comportamiento visible para el usuario)

**Prerrequisito antes de escribir ningún código.**

- [ ] Aprobación de este ADR por el equipo
- [ ] Decisión: `ALLOWED_HOSTS = ["*"]` vs alternativa
- [ ] Decisión: certbot HTTP-01 vs Cloudflare SSL for SaaS
- [ ] Tests de aceptación escritos (casos §18)
- [ ] Plan de monitoreo (errores de resolución de dominio)

**Estimación**: 1 día de diseño + revisión.

---

### Fase 1 — Modelo y verificación DNS (backend only)

**Resultado**: Tenant puede registrar y verificar un dominio. No hay acceso por ese dominio todavía.

- [ ] Crear `taller/models/empresa_dominio.py` con el modelo `EmpresaDominio`
- [ ] Migración (`makemigrations` + `migrate`)
- [ ] Crear `taller/services/domain_verification.py`
- [ ] Management command `verify_custom_domain`
- [ ] Panel de admin Django para gestionar dominios
- [ ] Tests unitarios de verificación DNS (con mock de `dns.resolver`)
- [ ] Tests de integración del modelo

**Estimación**: 2–3 días de desarrollo.

---

### Fase 2 — Middleware y redirección (Fase 1 del ADR: redirect MVP)

**Resultado**: Un dominio verificado redirige al workspace en egarage.cl.

- [ ] Crear `taller/middleware/host_tenant.py`
- [ ] Modificar `taller/middleware/empresa_resolver.py` (condición pre-resolución)
- [ ] Agregar `HostTenantMiddleware` al stack en settings
- [ ] Tests de `HostTenantMiddleware` (unitarios + integración)
- [ ] Preparar Nginx (catch-all HTTP para ACME challenge)
- [ ] Deploy y verificación en producción con 0 dominios activos
- [ ] Piloto con 1 tenant de prueba

**Estimación**: 2–3 días.

---

### Fase 3 — SSL automático y workspace completo (Fase 2 del ADR: full custom domain)

**Resultado**: El workspace completo es accesible en el dominio personalizado.

- [ ] Crear `taller/services/ssl_issuance.py` (wrapper de certbot)
- [ ] Management command `emitir_ssl --dominio <d>`
- [ ] Management command `generate_nginx_domains`
- [ ] Cron de renovación de certs
- [ ] Vista `CustomDomainRouterView` (o modificar URLs existentes)
- [ ] Actualizar `CSRF_TRUSTED_ORIGINS` dinámicamente
- [ ] Tests E2E con Playwright
- [ ] UI de configuración de dominio en el panel del tenant

**Estimación**: 4–5 días.

---

### Fase 4 — Operaciones y observabilidad

- [ ] Dashboard de estado de dominios (SSL expiry, último check DNS)
- [ ] Alertas cuando SSL expira en < 30 días
- [ ] Métricas: requests por dominio personalizado
- [ ] Documentación de operación (cómo agregar/revocar dominios)

**Estimación**: 2 días.

---

## 21. Decisión

Se aprueba la arquitectura descrita en este documento para implementación en cuatro fases.

**Puntos no negociables:**
1. `HostTenantMiddleware` SIEMPRE va antes de `EmpresaResolverMiddleware`.
2. Los tests del §18 deben existir antes de comenzar Fase 2.
3. La validación de cruce de tenant (§10.2) es obligatoria en Fase 2.
4. El índice `Index(fields=["dominio", "estado"])` debe crearse en la migración de Fase 1.
5. El cache de resolución de dominio es obligatorio antes de cualquier deploy a producción.

**Decisiones postergadas para Fase 3:**
- `ALLOWED_HOSTS = ["*"]` vs lista dinámica.
- Certbot HTTP-01 vs Cloudflare SSL for SaaS.
- Manejo de URL paths en dominio personalizado (redirect vs router propio).

---

*Este documento es la especificación para la implementación. Ningún código debe modificarse hasta que Fase 0 esté completa.*
