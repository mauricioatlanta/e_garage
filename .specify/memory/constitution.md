<!--
SYNC IMPACT REPORT
==================
Version change: (empty scaffold) → 1.0.0
Added sections:
  - Core Principles (5 principles, 20 rules total)
  - Arquitectura de Settings y Deploy (8 rules)
  - Tests y Guardianes de Regresión (4 rules)
  - Governance
Modified principles: N/A (initial constitution)
Removed sections: N/A
Conceptual refinements applied before initial commit (2026-08-14):
  - Governance: separación explícita fuente descriptiva (código) vs normativa (Constitución).
  - Principio II: regla max_length generalizada a "no truncar identificadores existentes";
    PRES/max_length>=4 pasan a ser evidencia/constraint actual, no principio eterno.
  - Sección Settings: generalizada a "cadena de imports inequívoca"; base.py es arquitectura
    objetivo actual, no requisito eterno.
  - Principio IV: separación entre el principio arquitectónico (boundary async/transaccional)
    y su implementación actual (runtime/, OutboxEvent, OutboxService).
Deferred TODOs:
  - BUG #1 (Settings divergentes): TrustMiddleware / VerificarSuscripcionMiddleware inactivos
    en prod → pendiente de corrección técnica antes del próximo sprint.
  - BUG #2 (PAIS_CHOICES incompleto): 7 de 10 países operados sin choices → tarea técnica
    registrada.
  - BUG #3 (Tax engine ignorado en Documento.save()): servicios en PE/VE/otros sin IGV →
    tarea técnica de mayor prioridad por riesgo legal.
  - DEUDA (HostTenantMiddleware en base.py): test de stack de middleware pendiente.
  - DEUDA (bypass trial en signup_complete.py:222): política de verificación de email
    por plan no documentada formalmente.
-->

# eGarage Constitution

## Core Principles

### I. Aislamiento de Tenant (NON-NEGOTIABLE)

Todo modelo que almacena datos de negocio DEBE heredar de `core.models.TenantScoped`
o declarar explícitamente `empresa = ForeignKey("taller.Empresa")`. No existe modelo
"global" con datos de negocio sin FK a `Empresa`.

Toda vista Django que retorne datos de un modelo tenant DEBE filtrar por
`request.empresa`. Está prohibido usar `Modelo.objects.all()` sin scope posterior.
Está prohibido leer `request.user.empresa` directamente en vistas — ese acceso ignora
los `TeamMember` y produce datos incorrectos para usuarios que no son Owner; se DEBE
usar `get_user_empresa_safe()` de `taller/utils/empresa.py`.

`request.empresa` es seteada EXCLUSIVAMENTE por `EmpresaResolverMiddleware`. Ningún
view, form, signal ni tarea asíncrona puede setear `request.empresa` por cuenta propia.

El signal `enforce_tenant` (`taller/signals/tenant_guard.py`) bloquea cross-tenant en
`pre_save` de líneas de documento. Todo nuevo tipo de línea de documento
(e.g. `LineaServicioExterno`) DEBE registrar un receiver equivalente en ese mismo
módulo. Un PR que añada un modelo de línea sin su receiver DEBE ser bloqueado.

**Evidencia:** `core/models.py:34-42`, `taller/utils/empresa.py:8-36`,
`taller/middleware/empresa_resolver.py:34-63`, `taller/signals/tenant_guard.py`,
`taller/tests/test_tenant_isolation.py`, `taller/tests/README_TENANT_ISOLATION.md`.

### II. Integridad de Datos Financieros (NON-NEGOTIABLE)

La numeración de documentos DEBE generarse exclusivamente mediante
`DocumentSequence.next(empresa, tipo)` o `Documento.generar_numero_documento()` dentro
de un bloque `transaction.atomic()` que incluya `select_for_update()` sobre
`DocumentSequence`. Está prohibido calcular `max(numero) + 1` manualmente. Este
mecanismo requiere PostgreSQL en producción; SQLite en desarrollo serializa sin bloqueo
real.

Los campos de tipo/código de documento (e.g., `Documento.tipo`, `DocumentSequence.tipo`)
tienen una longitud definida por los identificadores existentes en producción. Ninguna
migración DEBE reducir el `max_length` de un campo identificador si existen registros o
lógica que dependan de la longitud actual. La ampliación es siempre válida; la truncación
de un campo en uso es SIEMPRE un error de migración.

*Constraint actual:* `max_length >= 4` porque el identificador más largo en producción
es `"PRES"` (4 caracteres). La migración `0167_alter_documentsequence_tipo.py` documenta
el costo real de una truncación silenciosa en producción. Este constraint seguirá vigente
hasta que el identificador más largo en uso lo supere.

`MovimientoInventario` es un ledger append-only. Su método `save()` bloquea updates
sobre filas existentes y `delete()` lanza excepción. Toda corrección de stock DEBE ser
un movimiento compensatorio con `idempotency_key` distinto. Está prohibido `update()`,
`delete()`, o `bulk_update()` sobre este modelo.

`VehiculoDesarmeEvent` es append-only. Cualquier cambio de estado de `VehiculoDesarme`
DEBE pasar por `VehicleStateService.transition()` para garantizar: validación de la
matriz `_TRANSITIONS`, `select_for_update()` sobre el vehículo, creación del evento e
idempotencia.

Un `Documento` con `tipo="PRES"` (presupuesto) NUNCA debe generar un
`MovimientoInventario`, ni al emitirse ni al anularse.

`bulk_create()`, `update()` en batch y `delete()` en batch están PROHIBIDOS en los
modelos: `Documento`, `MovimientoInventario`, `VehiculoDesarmeEvent`, `DocumentSequence`.
Estos modelos tienen lógica crítica en `save()` y signals que `bulk_*` saltan.

**Evidencia:** `taller/models/sequence.py:19-25`, `taller/models/documento.py:491-530,
800-803`, `taller/models/movimiento_inventario.py:147-155`,
`taller/models/vehiculo_desarme_event.py:139-145`,
`taller/services/vehicle_state_service.py:23-33`,
`taller/documentos/signals_inventory.py:68-72`,
`taller/services/inventory_service.py:50`,
`tests/README_FLUJO_CRITICO_FINANCIERO.md`.

### III. Motor Fiscal Centralizado (NON-NEGOTIABLE)

Todo cálculo tributario en el sistema DEBE consumir
`taller.impuestos.engine.calcular_impuesto()` con el parámetro `applies_to` correcto
(`'parts'` para repuestos, `'services'` para servicios). El método `recompute_totals()`
de `Documento` DEBE obtener tasas separadas para repuestos y servicios usando
`resolve_tax_rate(empresa, ..., 'parts')` y `resolve_tax_rate(empresa, ..., 'services')`.

Está PROHIBIDO hardcodear constantes tributarias (`Decimal("0.19")`, `Decimal("0.18")`,
`Decimal("0.16")`, etc.) fuera de `taller/impuestos/` y `taller/utils/country_config.py`.
Un PR que introduzca una constante numérica tributaria en views, formularios o utilidades
fuera de esos módulos DEBE ser rechazado en revisión.

La lista canónica de países soportados DEBE vivir en un único módulo
(`taller/config/countries.py` o equivalente). `Empresa.PAIS_CHOICES`, la lista del
formulario de signup (`CustomSignupForm.COUNTRY_CHOICES`) y los archivos de
`taller/urls_extra/` DEBEN derivarse de esa única fuente. Todo país con URL activa en
`taller/urls_extra/` DEBE estar en `PAIS_CHOICES` del modelo `Empresa`.

**Evidencia:** `taller/impuestos/engine.py:19-140`, `taller/models/documento.py:329-389`,
`taller/forms/custom_signup.py:151-163`, `taller/urls_extra/` (10 archivos de país),
`taller/tests/test_tax_engine.py`, `taller/tests/test_country_features.py`.

**Bugs activos documentados (pendientes de corrección):**
- `taller/models/documento.py:356-362` aplica IVA solo a repuestos para todos los países,
  ignorando servicios en PE y VE.
- `taller/documentos/api.py:200`, `views_export.py:240`, `views_migrated.py:686,1555,1750`
  tienen tasas hardcodeadas.
- `Empresa.PAIS_CHOICES` solo incluye CL/US/MX aunque el sistema opera en 10 países.

### IV. Boundary Commerce / ERP (NON-NEGOTIABLE)

**Principio (invariante):** La comunicación entre dominios con boundary explícito
(Commerce → ERP, o cualquier otro par de dominios acoplados intencionalmente) DEBE ser
asíncrona y transaccional. Está PROHIBIDO que un dominio llame directamente a servicios
internos de otro dominio para mutar estado de ese otro dominio. Toda publicación
inter-dominio DEBE ejecutarse dentro de un bloque `@transaction.atomic()` para garantizar
que la publicación y la mutación local son atómicas. Este principio es NON-NEGOTIABLE
independientemente del mecanismo de transporte elegido.

**Implementación actual:** El mecanismo concreto que satisface este principio es el
patrón Outbox: `OutboxEvent` persisted en la misma transacción, consumido por workers
registrados en `_CONSUMER_REGISTRY`. En la implementación actual, `runtime/` es la app
autorizada a: (a) persistir `OutboxEvent` y `ProcessedEvent`, (b) registrar consumers.
Otras apps publican mediante `OutboxService.enqueue()`. Si en el futuro el mecanismo de
transporte cambia (e.g., Celery tasks, Kafka, Django Channels), el principio de
no-llamada-directa permanece NON-NEGOTIABLE; solo la implementación del transporte puede
cambiarse mediante enmienda.

Un PR que mezcle lógica de dos dominios distintos (ERP ↔ Commerce ↔ Contract Runtime)
en el mismo servicio o modelo ES UN SMELL ARQUITECTÓNICO y debe ser bloqueado hasta
separar las responsabilidades.

**Evidencia:** `commerce/services/order_service.py:109-113`,
`commerce/services/payment_service.py:211-214`,
`runtime/services/outbox_service.py:31-34`,
`runtime/consumers/commerce_order_consumer.py`,
`runtime/consumers/commerce_paid_consumer.py`.

### V. Rubros y Contratos de Configuración

La lista canónica de rubros vive en DOS lugares que DEBEN mantenerse sincronizados:
`ConfiguracionEmpresa.RUBRO_CHOICES` y `taller/constants/business_modules.py:MODULES_BY_RUBRO`.
Añadir un rubro nuevo requiere actualizar ambos, más `RUBRO_TO_PRODUCT` en
`taller/constants/product_profiles.py`, y `ConfiguracionEmpresa.get_secciones_visibles()`
si el rubro tiene comportamiento visual diferenciado.

`ConfiguracionEmpresa.has_completed_business_setup()` es la única fuente de verdad para
determinar si el onboarding de una empresa está completo. Está PROHIBIDO inspeccionar
`rubro_principal` directamente en vistas para tomar esa decisión.

El signal `ensure_owner_rbac` (`taller/signals/owner_rbac_signals.py`) es el único
mecanismo autorizado para crear `TeamMember(rol="Owner")`. Ningún view, form, migration
o fixture DEBE crear este registro directamente. Si se amplían los `choices` del campo
`rol`, `"Owner"` DEBE incluirse formalmente para evitar que `full_clean()` lo rechace.

**Evidencia:** `taller/models/configuracion.py:196-202, 250`,
`taller/constants/business_modules.py:22-53`,
`taller/constants/product_profiles.py`,
`taller/signals/owner_rbac_signals.py:16-70`,
`taller/models/team_member.py:39-45`.

## Arquitectura de Settings y Deploy

**Settings raíz única:** DEBE existir exactamente una cadena de imports inequívoca desde
el entrypoint de producción (`wsgi.py`) hasta el único archivo que define los valores
efectivos. Está PROHIBIDO que dos archivos del mismo paquete de settings definan el mismo
nombre de variable con valores distintos — la resolución implícita de Python entre un
paquete y un flat file es una fuente silenciosa de bugs de configuración.

*Arquitectura objetivo actual:* `wsgi.py` → `settings_prod.py` → `from .base import *`,
donde `base.py` centraliza la configuración de todos los entornos. Esta es la arquitectura
a alcanzar. El estado actual (BUG #1 documentado) diverge de ella: `settings/__init__.py`
actúa como raíz real de producción en lugar de `base.py`.

**Stack de middleware obligatorio:** El stack MIDDLEWARE efectivo en producción DEBE
contener estos tres middlewares en este orden exacto:
`taller.middleware.host_tenant.HostTenantMiddleware` →
`commerce.middleware.CommerceTenantMiddleware` →
`taller.middleware.empresa_resolver.EmpresaResolverMiddleware`.
Un test automatizado DEBE fallar si el orden se rompe o si alguno de los tres está
ausente. `TrustMiddleware` y `VerificarSuscripcionMiddleware` DEBEN estar presentes en
el stack de producción.

**Verificación de email:** `ACCOUNT_EMAIL_VERIFICATION` en producción DEBE ser
`'mandatory'`. Cualquier excepción por plan (e.g., omitir verificación para trial) DEBE
documentarse explícitamente en el spec del plan y en el código con un comentario que
referencie esa decisión. Un test automatizado DEBE validar el valor en el settings de
producción.

**Emails salientes:** Todo correo enviado por la aplicación DEBE usar los helpers de
`taller/utils/email_helper.py` (`send_email_with_reply_to`, `send_template_email`).
Está PROHIBIDO usar `send_mail()` directamente, usar `no-reply@egarage.cl` como
dirección From, o enviar sin un `Reply-To` real. El backend de producción es
`gestion_taller.resend_backend.ResendBackend`.

**Custom domains:** Solo puede haber UN `EmpresaDominio` con `estado="ACTIVO"` por
empresa. Los subdominios de `egarage.cl` están reservados y DEBEN ser rechazados por
`EmpresaDominio.clean()` vía `DOMINIOS_RESERVADOS`. Un dominio custom SOLO puede servir
una tienda Commerce si `HostTenantMiddleware` está activo antes de
`CommerceTenantMiddleware` en el stack.

**Archivos .BAK no importables:** Los archivos `*.py.BAK*`, `*.py.BAK_*`, y archivos
con timestamps en el nombre (e.g., `views_migrated.py.BAK_OTROS_FIX`) NO deben estar
en el árbol importable del proyecto. Son historial de decisiones, no código activo. Un
import accidental restaura bugs corregidos.

**Código legacy y aliases:** `Empresa.PLAN_CHOICES` mantiene tres familias de plan por
compatibilidad histórica (`trial/entry/growth/business`, `express/taller/pro`,
`basic/premium/enterprise`). Las reglas de negocio (límites, precios, features) DEBEN
operar sobre los canónicos (`trial/entry/growth/business`). Comparaciones directas con
`"premium"`, `"basic"` o `"enterprise"` en código nuevo DEBEN ser rechazadas en
revisión.

**Evidencia:** `gestion_taller/wsgi.py:7`, `gestion_taller/settings_prod.py:7,172,304-309`,
`gestion_taller/settings/__init__.py:27-36`, `gestion_taller/settings/base.py:59-91`,
`gestion_taller/resend_backend.py`, `taller/utils/email_helper.py`,
`taller/models/empresa_dominio.py:27-39,112-116`,
`taller/middleware/host_tenant.py:31-42`.

## Tests y Guardianes de Regresión

Todo módulo nuevo que toque las siguientes áreas DEBE incluir o actualizar los tests
correspondientes antes del merge:

**Aislamiento tenant:** Un test que verifique que ninguna vista de la app retorna datos
de un tenant distinto al autenticado. El módulo de referencia es
`taller/tests/test_tenant_isolation.py` y `taller/tests/README_TENANT_ISOLATION.md`.

**Flujo financiero crítico:** Un test end-to-end que cree un `Documento` con líneas de
repuesto y de servicio para empresas de distintos países (CL, PE, VE como mínimo),
emita el documento, y verifique que: (a) `MovimientoInventario` se creó para OT/FAC y
NO para PRES, (b) el `tax_amount` del documento para PE incluye IGV sobre servicios.
El módulo de referencia es `tests/README_FLUJO_CRITICO_FINANCIERO.md`.

**Stack de middleware:** Un test `tests/test_middleware_stack.py` DEBE verificar que el
settings efectivo de producción incluye `HostTenantMiddleware`,
`CommerceTenantMiddleware` y `EmpresaResolverMiddleware` en ese orden.

**Motor fiscal:** Los tests de `taller/tests/test_tax_engine.py` DEBEN cubrir el flujo
end-to-end (no solo el engine aislado): crear `Documento` → agregar líneas →
`Documento.save()` → verificar `Documento.tax_amount` para cada país soportado.

**Evidencia:** `taller/tests/test_tenant_isolation.py`,
`taller/tests/test_tax_engine.py`, `taller/tests/test_country_features.py`,
`tests/README_FLUJO_CRITICO_FINANCIERO.md`,
`taller/tests/test_signup_email_confirmation_flow.py`.

## Governance

Esta Constitución tiene precedencia normativa sobre `CLAUDE.md`, ADRs individuales, y
cualquier otro documento de referencia del proyecto cuando haya contradicción. Si `CLAUDE.md`
describe un comportamiento distinto al establecido aquí, la Constitución gana y `CLAUDE.md`
DEBE actualizarse.

**Dos tipos de fuente de verdad:**

- **Fuente descriptiva** — el código y la configuración efectiva en producción: describe
  cómo funciona eGarage *ahora mismo*. Es la evidencia de partida para cualquier análisis.
- **Fuente normativa** — esta Constitución: determina cómo *debe* funcionar el sistema.
  Es el destino al que el código debe converger.

Cuando código y Constitución difieren, NO se asume que el código gana. La discrepancia
se clasifica como bug o deuda técnica, se registra con evidencia (archivo, línea, test),
y se resuelve mediante spec/tarea antes de que un PR en el área afectada pueda aprobarse.

**Precedencia normativa:**
1. Esta Constitución.
2. ADRs específicos (ADR-000, ADR-004, etc.) cuando son coherentes con ella.
3. `CLAUDE.md` para orientación operacional de día a día.

**Proceso de enmienda:**
- Cualquier enmienda DEBE estar justificada con evidencia del repositorio (archivo,
  línea, test o comportamiento observable).
- Una enmienda que elimine o reduzca el alcance de un principio NON-NEGOTIABLE requiere
  evidencia de que el invariante ya no es necesario y confirmación explícita del PO.
- La versión de la Constitución se incrementa según semver:
  - MAJOR: eliminación o redefinición incompatible de un principio.
  - MINOR: nuevo principio o sección añadida.
  - PATCH: aclaraciones, redacción, correcciones menores.

**Compliance:**
- Todo PR DEBE verificar que no viola ningún principio de esta Constitución antes del
  merge. El revisor DEBE rechazar PRs que introduzcan: tasas tributarias hardcodeadas,
  acceso a `request.user.empresa` directo en vistas, `bulk_create/update` en modelos
  protegidos, o comunicación sincrónica directa entre `commerce/` y `taller/`.
- La revisión de compliance se hace contra el código, no contra descripciones funcionales.
- Los bugs documentados en la sección de principios (marcados como "Bugs activos
  documentados") tienen tarea técnica abierta y DEBEN corregirse antes de que cualquier
  PR que toque el área afectada pueda aprobarse.

**Version**: 1.0.0 | **Ratified**: 2026-08-14 | **Last Amended**: 2026-08-14
