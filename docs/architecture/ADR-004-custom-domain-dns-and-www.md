# ADR-004 — DNS Canónico y Soporte www para Dominios Personalizados

**Estado:** Aceptado
**Fecha:** 2026-08-26
**Autores:** Mauricio Alvarado
**Revisores:** —
**Relacionado con:** ADR-002 (Dominios Personalizados — Modelo y Verificación), ADR-003 (Arquitectura de Producción para Dominios Personalizados)

---

## 1. Resumen Ejecutivo

Este documento cierra dos decisiones que quedaron sin resolver formalmente
tras ADR-002/ADR-003, y que la auditoría de las Fases 340-342 demostró que
el código todavía no reflejaba correctamente:

1. **Qué registro DNS debe crear un tenant** para su dominio personalizado.
2. **Si el dominio debe servirse también bajo `www.<dominio>`** desde el
   primer día, y cómo modelarlo sin romper tenants que no lo necesiten.

**Decisión adoptada:**

- El patrón canónico de DNS es **A directo al VPS de eGarage** para el
  apex, y **CNAME al propio apex** para `www` (no un proxy intermedio).
- El soporte de `www` es **configurable por tenant** (`incluir_www`),
  con **`default=True`** — todo tenant nuevo recibe `www` automáticamente
  salvo que se desactive explícitamente.

---

## 2. Contexto

### 2.1 Lo que ADR-002 propuso y nunca se aceptó

ADR-002 (Estado: **Propuesto**, nunca pasó a Aceptado) diseñó una
arquitectura donde el tenant apunta su dominio vía **CNAME a
`proxy.egarage.cl`**, un registro Cloudflare-proxied que centralizaría el
tráfico de todos los dominios personalizados.

### 2.2 Lo que ADR-003 decidió realmente

ADR-003 (Estado: **Aceptado**, un día después) descartó Cloudflare SSL for
SaaS y adoptó certbot + Nginx por dominio — el stack que efectivamente se
implementó. Su §3.2 y §13 ya apuntaban a **"A directo al VPS"** como el
patrón de DNS, y afirmaban que esa instrucción "ya aparece correctamente en
`settings.html`".

### 2.3 La brecha encontrada (Fase 340-342)

Esa afirmación de ADR-003 era incorrecta. El código (`get_cname_target()`,
escrito el mismo día que ADR-002, nunca actualizado después) seguía
devolviendo `"proxy.egarage.cl"` de forma incondicional — un destino que
**nunca existió en DNS** (confirmado con consultas autoritativas directas
en la Fase 340).

La evidencia decisiva fue el DNS real del único tenant con dominio
personalizado ya operando en producción, **MonteAzul**:

```
monteazulspa.cl.      A      159.223.200.106
www.monteazulspa.cl.  CNAME  monteazulspa.cl.
```

`proxy.egarage.cl` nunca fue usado, ni siquiera para el caso que
efectivamente funciona. El certificado real de MonteAzul cubre ambos
nombres (`Domains: monteazulspa.cl www.monteazulspa.cl`), pero el código de
`ssl_issuance.py` vigente hasta esta fase solo soportaba un dominio único
— es decir, el `.conf` y el certificado de MonteAzul **no fueron generados
por el código actual**: son drift manual/histórico.

---

## 3. Decisión

### 3.1 Patrón canónico de DNS (supersede la parte de onboarding de ADR-002)

```
<dominio>       A      <IP del VPS de eGarage>   (settings.CUSTOM_DOMAIN_VPS_IP)
www.<dominio>   CNAME  <dominio>                  (opcional, ver 3.2)
_egarage-verify.<dominio>  TXT  egarage-verify=<token>
```

Esta sección de ADR-002 (el modelo CNAME→`proxy.egarage.cl`) queda
formalmente reemplazada por esta decisión. El resto de ADR-002 (modelo
`EmpresaDominio`, verificación TXT, ciclo de vida de estados) permanece
vigente sin cambios.

`proxy.egarage.cl` **no es parte del onboarding actual**. Un futuro proxy
central/CDN (por ejemplo, si el volumen de tenants justifica Cloudflare
Enterprise/SaaS) requeriría un ADR nuevo — no reutiliza este nombre sin
revisión.

### 3.2 Soporte `www` — configurable, `default=True`

`EmpresaDominio.incluir_www` (`BooleanField`, `default=True`):

- **`True` (default):** certbot solicita `-d <apex> -d www.<apex>` (ambos
  como SAN del mismo certificado, con `--cert-name` = apex, igual que el
  patrón ya operando en MonteAzul); el bloque Nginx generado usa
  `server_name <apex> www.<apex>;`.
- **`False`:** certbot y Nginx usan solo el apex — comportamiento idéntico
  al que existía antes de esta fase. Pensado para un tenant que no puede o
  no quiere configurar el CNAME de `www`.

El apex (`EmpresaDominio.dominio`) sigue siendo la clave canónica del
tenant en todos los casos — `incluir_www` solo decide qué alias adicional
se incluye en el certificado y en el bloque Nginx.

### 3.3 HTTP-01 vía catch-all genérico en `:80`

Confirmado y ya desplegado en producción (Fase 341): un bloque
`default_server` en `/etc/nginx` (fuera de este repo) sirve
`/.well-known/acme-challenge/` para cualquier Host sin bloque propio, antes
de que exista el `.conf` específico del tenant. Esto resuelve el
chicken-and-egg documentado en `ssl_issuance.py` sin requerir cambios en
este servicio.

### 3.4 Nginx/Let's Encrypt por tenant

Sin cambios respecto a ADR-003: un `.conf` por tenant en
`sites-enabled/tenant_<apex>.conf`, certificado vía certbot webroot,
`ssl_certificate`/`ssl_certificate_key` siempre bajo
`/etc/letsencrypt/live/<apex>/` (el path del certificado nunca depende de
`www`, porque certbot usa el primer `-d` — el apex — como nombre del
certificado independientemente de cuántos SAN tenga).

### 3.5 El apex sigue siendo la clave canónica del resolver

`DomainResolverService.normalize_host()` sigue despojando el prefijo
`www.` antes de resolver — un request a `www.<dominio>` y a `<dominio>`
resuelven al MISMO `EmpresaDominio`, independientemente de `incluir_www`.
Sin cambios en esta fase.

---

## 4. Consecuencias

**Positivas:**
- El código ahora refleja la arquitectura que YA está operando en
  producción (MonteAzul), en vez de una arquitectura nunca implementada.
- Onboarding de un tenant nuevo funciona con cualquier proveedor DNS (A es
  universal), sin depender de que el cliente pueda hacer CNAME flattening
  en su apex.
- `incluir_www=True` por defecto preserva el comportamiento ya esperado
  (MonteAzul, y el DNS histórico de Atlanta, ya usaban `www`).

**Negativas / riesgos aceptados:**
- Un futuro tenant con `incluir_www=True` cuyo DNS de `www` no esté listo
  hará fallar el `-d www.<apex>` completo de certbot (no se usa
  `--allow-subset-of-names` por decisión explícita de esta fase) — el
  tenant deberá desactivar `incluir_www` o completar su DNS de `www` antes
  de reintentar.
- Cambiar la IP del VPS requiere que cada tenant actualice su registro A
  individualmente (sin punto único de cambio, a diferencia del modelo
  proxy descartado) — aceptado como tradeoff por la sección 10 de la
  auditoría Fase 342 (menor dependencia de infraestructura intermedia,
  mayor universalidad de onboarding).

---

## 5. Alcance explícitamente fuera de esta decisión

- Cambiar el DNS real de Atlanta Reciclajes (fase de implementación
  separada, posterior).
- Ejecutar `verify_custom_domain` o `certbot` contra un dominio real.
- Resolver el catch-all ACME de infraestructura (ya resuelto en Fase 341,
  fuera de este repo).
- Migrar MonteAzul a que su `.conf`/certificado sea regenerado por el
  código actualizado (su configuración manual sigue funcionando; no se
  toca en esta fase).
