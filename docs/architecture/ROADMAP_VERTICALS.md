# eGarage — Roadmap de Verticales
**Versión:** 1.0  
**Fecha:** 2026-07-28  
**Arquitectura de referencia:** docs/architecture/VERTICAL_ARCHITECTURE_V1.md  
**Auditoría base:** docs/auditorias/auditoria_final_verticales_egarage.md

---

## Vista General

```
ESTADO ACTUAL ──────────────────────────────────────────────────────────▶ OBJETIVO

Una sola landing (talleres)           Tres landings especializadas
Menú idéntico para todos          →   Menú dinámico por vertical
Sin tipo de negocio en empresa        Campo de módulo en ConfiguracionEmpresa
Onboarding no captura vertical        Onboarding con selector de negocio
Módulo desarme accesible a todos      Gate de autorización por módulo
Casa de repuestos: solo stub          Vertical completa construida
```

---

## Épica 0 — Portal Público Diferenciado
**Estado:** Pendiente  
**Prioridad:** Alta — impacto comercial inmediato, cero riesgo técnico  
**Prerequisito:** Ninguno  
**Tiempo estimado:** 3-5 días

### Objetivo

Crear tres landings públicas separadas sin tocar ningún código existente. El portal principal mostrará dos botones grandes que llevan a cada landing.

### Tareas

| # | Tarea | Archivos a crear | Archivos a modificar |
|---|---|---|---|
| E0-1 | Crear vista `landing_talleres` con copy orientado a talleres mecánicos | `templates/public/landing_talleres.html`, `taller/views/landing_views.py` | — |
| E0-2 | Crear vista `landing_desarmadurias` con historia de Atlanta y propuesta de valor | `templates/public/landing_desarmadurias.html` | — |
| E0-3 | Crear vista `landing_repuestos` (placeholder, poca inversión ahora) | `templates/public/landing_repuestos.html` | — |
| E0-4 | Crear base de landing compartida | `templates/public/base_landing.html` | — |
| E0-5 | Registrar URLs en `urls_public.py` | — | `taller/urls_public.py` o `gestion_taller/urls.py` |
| E0-6 | Modificar `landing_inicio.html` para mostrar selector de vertical | — | `templates/landing_inicio.html` |

### Criterios de Aceptación

- `/talleres/` carga con copy de taller, CTA "Registrar mi taller"
- `/desarmadurias/` carga con historia de Atlanta, CTA "Registrar mi desarmaduría"
- `/repuestos/` carga (puede ser placeholder) con CTA
- El home principal muestra dos botones grandes: "Taller" y "Desarmaduría"
- Todas las páginas tienen `<title>`, `<meta description>`, canonical correcto
- Las URLs existentes no se rompen

### Rollback

Eliminar los 4 archivos nuevos y revertir el cambio en `landing_inicio.html`.

---

## Épica 1 — Campo de Módulo y Onboarding
**Estado:** Pendiente  
**Prioridad:** Alta  
**Prerequisito:** Épica 0 aprobada y en producción  
**Tiempo estimado:** 5-7 días

### Objetivo

Agregar al modelo `ConfiguracionEmpresa` los tres flags de módulo y modificar el onboarding para que el usuario elija su tipo de negocio al registrarse.

### Tareas

| # | Tarea | Archivos a crear | Archivos a modificar |
|---|---|---|---|
| E1-1 | Agregar `modulo_taller`, `modulo_desarmaduria`, `modulo_repuestos` a `ConfiguracionEmpresa` con `default=True` | `taller/migrations/XXXX_add_modulos_config.py` | `taller/models/configuracion.py` |
| E1-2 | Agregar selector de vertical al paso de identidad del onboarding | — | `templates/onboarding/paso_identidad.html`, `taller/forms/onboarding.py` |
| E1-3 | En `onboarding_guardar_paso` paso 1: mapear selección a flags de módulo | — | `taller/views/onboarding_views.py` |
| E1-4 | En `CompanyDefaultsService`: método `apply_modulos_por_tipo()` | — | `taller/services/company_defaults_service.py` |
| E1-5 | Actualizar context processor `empresa_contexto` para exponer `modulos_activos` | — | `taller/context_processors/empresa_contexto.py` |
| E1-6 | Pruebas unitarias de la migración y del onboarding | `taller/tests/test_onboarding_vertical.py` | — |

### Criterios de Aceptación

- Un registro nuevo con selección "Taller" produce `modulo_taller=True`, `modulo_desarmaduria=False`, `modulo_repuestos=False`
- Un registro nuevo con selección "Desarmaduría" produce `modulo_desarmaduria=True`, `modulo_taller=False`
- Las empresas existentes (sin el campo aún) tienen `True` en los tres por `default`
- El context processor expone `modulos_activos` correctamente en templates
- La migración se aplica sin downtime ni backfill manual

### Rollback

```bash
python manage.py migrate taller XXXX-1  # migración anterior
git revert HEAD~N  # revertir commits de esta épica
```

---

## Épica 2 — Menú y Workspace Diferenciados
**Estado:** Pendiente  
**Prioridad:** Alta  
**Prerequisito:** Épica 1 en producción  
**Tiempo estimado:** 3-5 días

### Objetivo

El menú principal y el workspace home muestran solo los módulos habilitados para la empresa.

### Tareas

| # | Tarea | Archivos a crear | Archivos a modificar |
|---|---|---|---|
| E2-1 | Separar navegación en `base.html` en bloques con condicionales por módulo | — | `templates/base.html:807-875` |
| E2-2 | Reescribir `components/sidebar.html` para usar `modulos_activos` | — | `templates/components/sidebar.html` |
| E2-3 | Actualizar `workspace_home.html` para mostrar tarjetas según módulos | — | `templates/taller/common/workspace_home.html` |
| E2-4 | Crear secciones de dashboard por módulo | `templates/dashboard/sections/_taller_metrics.html`, `_desarme_metrics.html`, `_repuestos_metrics.html` | `templates/dashboard/index.html` |
| E2-5 | Pruebas visuales: verificar menú con empresa solo-taller, solo-desarme, multivertical | — | — |

### Criterios de Aceptación

- Empresa con `modulo_desarmaduria=False` NO ve el botón "Desarme" en el menú
- Empresa con `modulo_taller=False` NO ve "Servicios", "Técnicos" en el menú
- Empresa multivertical (`True` en los tres) ve todos los botones
- El workspace muestra solo las tarjetas de módulos habilitados
- Las URLs de módulos no habilitados aún son accesibles (se protegen en Épica 3)

### Rollback

Revertir los cambios en `base.html`, `sidebar.html` y `workspace_home.html`.

---

## Épica 3 — Autorización Backend por Módulo
**Estado:** Pendiente  
**Prioridad:** Alta  
**Prerequisito:** Épica 1 en producción  
**Tiempo estimado:** 5-7 días

### Objetivo

Crear el decorator `@requiere_modulo` y aplicarlo a todas las vistas del módulo de desarmadurías. Un taller sin `modulo_desarmaduria=True` que navega a `/cl/es/desarme/vehiculos/` recibe 403.

### Tareas

| # | Tarea | Archivos a crear | Archivos a modificar |
|---|---|---|---|
| E3-1 | Crear `taller/decorators.py` con `@requiere_modulo` y `RequiereModuloMixin` | `taller/decorators.py` | — |
| E3-2 | Aplicar `@requiere_modulo("DESARMADURIA")` a todas las vistas en `views.py` | — | `taller/desarme/views.py` (todas las FBVs) |
| E3-3 | Aplicar `@requiere_modulo("DESARMADURIA")` a vistas en `views_venta.py` | — | `taller/desarme/views_venta.py` |
| E3-4 | Aplicar `@requiere_modulo("DESARMADURIA")` a vistas en `views_inventario.py` | — | `taller/desarme/views_inventario.py` |
| E3-5 | Aplicar `@requiere_modulo("DESARMADURIA")` a vistas en `views_pdf.py` | — | `taller/desarme/views_pdf.py` |
| E3-6 | Crear template de error 403 por módulo no habilitado | `templates/errors/403_modulo.html` | — |
| E3-7 | Pruebas de integración: empresa sin módulo → 403; empresa con módulo → 200 | `taller/tests/test_modulo_access.py` | — |

### Criterios de Aceptación

- Empresa con `modulo_desarmaduria=False`: `/cl/es/desarme/vehiculos/` → 403
- Empresa con `modulo_desarmaduria=True`: `/cl/es/desarme/vehiculos/` → 200
- Las APIs de desarme (`/api/vendedores/`) también retornan 403 JSON
- El kiosco público (`/tienda/<slug>/`) no requiere el decorator (es público)
- Las pruebas unitarias pasan

### Rollback

Eliminar `taller/decorators.py` y revertir los cambios en las vistas de desarme.

---

## Épica 4 — Onboarding Especializado por Vertical
**Estado:** Pendiente  
**Prioridad:** Media  
**Prerequisito:** Épicas 1, 2 y 3 en producción  
**Tiempo estimado:** 5-7 días

### Objetivo

Después de que el usuario elige su vertical en el onboarding, el resto del proceso se adapta: los textos, los datos de demostración y la pantalla de bienvenida corresponden a su tipo de negocio.

### Tareas

| # | Tarea | Archivos a crear | Archivos a modificar |
|---|---|---|---|
| E4-1 | Crear template de finalización para desarmadurías | `templates/onboarding/paso_finalizar_desarmaduria.html` | — |
| E4-2 | Crear template de finalización para talleres | `templates/onboarding/paso_finalizar_taller.html` | — |
| E4-3 | La vista de onboarding elige template según módulos de la empresa | — | `taller/views/onboarding_views.py` |
| E4-4 | Datos de demo: comando `seed_demo` carga datos según vertical | — | Management command existente |
| E4-5 | Dashboard post-onboarding: primer ingreso muestra guía de inicio según vertical | `templates/dashboard/onboarding_checklist_desarme.html`, `_taller.html` | `templates/dashboard/index.html` |

### Criterios de Aceptación

- Un nuevo usuario de tipo "Desarmaduría" ve en el onboarding pasos y ejemplos de desarmadurías
- Los datos de demo incluyen un vehículo de desarme y piezas si eligió esa vertical
- El dashboard post-registro muestra un checklist de inicio relevante para su tipo de negocio

### Rollback

Revertir templates y la lógica de selección en `onboarding_views.py`.

---

## Épica 5 — Vertical Casa de Repuestos (Construcción)
**Estado:** Pendiente — diseño pendiente de aprobación separada  
**Prioridad:** Media-Baja (según demanda real)  
**Prerequisito:** Épicas 1, 2 y 3 en producción; validación comercial de la vertical  
**Tiempo estimado:** 4-6 semanas

### Objetivo

Construir los módulos necesarios para que una casa de repuestos pueda administrar proveedores, compras, stock y ventas directas de manera profesional.

### Sub-épicas

#### E5-A — Proveedores
- Modelo `Proveedor` (ficha completa)
- CRUD de proveedores
- Asociación proveedor → repuesto

#### E5-B — Órdenes de Compra
- Modelo `OrdenCompra` + `LineaOrdenCompra`
- Flujo: borrador → enviada → recibida parcial → recibida total
- Actualización automática de stock al recibir

#### E5-C — Movimientos de Stock
- Modelo `MovimientoStock`
- Trazabilidad completa: quién, cuándo, qué cantidad, por qué razón
- Integración con el modelo `Repuesto` existente (sin duplicar)

#### E5-D — Venta Directa de Repuestos
- Flujo de venta sin necesidad de OT (point of sale básico)
- Genera `Documento` de tipo venta + descuenta stock via `MovimientoStock`

#### E5-E — Dashboard Casa de Repuestos
- Valor del inventario
- SKUs bajo mínimo
- Rotación por categoría
- Margen bruto

#### E5-F — Catálogo con Búsqueda
- Filtros por categoría, proveedor, disponibilidad, precio
- Búsqueda por nombre y part_number
- Vista móvil para uso en bodega

### Criterios de Aceptación (E5 completa)

- Una casa de repuestos puede registrar un proveedor, crear una orden de compra, recibir mercadería y ver el stock actualizado
- Puede hacer una venta directa de un producto sin crear una OT
- El dashboard muestra valor de inventario, SKUs críticos y margen del mes
- El módulo solo es accesible para empresas con `modulo_repuestos=True`

---

## Épica 6 — SEO y Contenido
**Estado:** Pendiente  
**Prioridad:** Media  
**Prerequisito:** Épica 0  
**Tiempo estimado:** 2-3 semanas (mayormente redacción)

### Objetivo

Optimizar las landings especializadas para posicionamiento orgánico por vertical e idioma.

### Tareas

| # | Tarea |
|---|---|
| E6-1 | Redactar copy definitivo para `/desarmadurias/` (historia Atlanta, diferencial, casos de uso) |
| E6-2 | Redactar copy para `/talleres/` (diferencial vs Excel/cuaderno, casos de uso Chile+USA) |
| E6-3 | Agregar schema.org `SoftwareApplication` a las tres landings |
| E6-4 | Agregar sitemap.xml con las landings especializadas |
| E6-5 | Open Graph images por vertical |
| E6-6 | Landing en inglés: `/us/en/salvage-yards/` con copy para el mercado latino-USA |
| E6-7 | Landing en inglés: `/us/en/workshops/` |

---

## Dependencias entre Épicas

```
E0 (Landings) ──────────────────────── independiente
    │
    ├──▶ E6 (SEO) ─── independiente de E1-E5
    │
E1 (Modelo + Onboarding) ──────────── requiere solo E0 aprobada
    │
    ├──▶ E2 (Menú) ─────── requiere E1
    │
    └──▶ E3 (Auth) ──────── requiere E1
              │
              └──▶ E4 (Onboarding especializado) ─── requiere E1, E2, E3
                        │
                        └──▶ E5 (Casa de Repuestos) ─── requiere E1, E2, E3 + validación comercial
```

---

## Cronograma Tentativo

| Semana | Épica | Entregable |
|---|---|---|
| 1 | E0 | Tres landings públicas en producción |
| 2 | E1 | Migración + onboarding con selector de vertical |
| 3 | E2 | Menú diferenciado visualmente |
| 3-4 | E3 | Autorización backend: 403 para módulos no habilitados |
| 4-5 | E4 | Onboarding y bienvenida especializada por vertical |
| 5-6 | E6 | SEO y contenido de landings |
| 7-12 | E5 | Vertical Casa de Repuestos (según prioridad comercial) |

---

## Métricas de Éxito

| Métrica | Hoy | Meta (6 meses) |
|---|---|---|
| Registros desde `/desarmadurias/` | 0 | 20 nuevas empresas de desarme |
| Registros desde `/talleres/` | Todos los actuales | +30% conversión desde landing especializada |
| Tiempo promedio de onboarding | ~5 min | ~3 min (más claro, menos confusión) |
| Módulo de desarme activado en empresas nuevas | 100% (default) | 50% activado, 50% desactivado (elección real) |
| Posición en Google "software desarmaduría Chile" | No rastreable | Top 10 |

---

## Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Migración M-01 rompe producción | Muy baja | Alto | `default=True` hace la migración trivial. Probar en clon antes de prod. |
| El menú condicional oculta algo que una empresa usa | Media | Medio | `default=True` en todos los flags asegura retrocompatibilidad total. |
| Casa de Repuestos interfiere con `Repuesto` de talleres | Media | Alto | `MovimientoStock` es una tabla nueva que no modifica la tabla `Repuesto`. |
| Cambiar `base.html` rompe el layout en algún país | Media | Medio | Probar con todas las variantes de país antes de deployar E2. |
| E5 tarda más de lo esperado | Alta | Bajo | No bloquea las otras épicas. E5 es independiente. |

---

## Checklist Antes de Implementar Cada Épica

- [ ] El documento de arquitectura `VERTICAL_ARCHITECTURE_V1.md` fue aprobado.
- [ ] El clon de producción tiene los datos actualizados.
- [ ] La épica tiene pruebas escritas antes de implementar (TDD cuando aplique).
- [ ] Existe un plan de rollback documentado para esa épica.
- [ ] Los cambios se hacen en commits pequeños y atómicos.
- [ ] La épica se despliega en staging (clon) antes de producción.
- [ ] Ningún commit modifica migraciones ya aplicadas en producción.

---

## Glosario

| Término | Definición |
|---|---|
| Vertical | Tipo de negocio automotriz con su propio conjunto de módulos, landing y onboarding |
| Módulo | Conjunto de funcionalidades habilitables por empresa via flag booleano |
| Flag de módulo | Campo booleano en `ConfiguracionEmpresa`: `modulo_taller`, `modulo_desarmaduria`, `modulo_repuestos` |
| Gate de acceso | Mecanismo que impide acceder a URLs de un módulo no habilitado |
| Retrocompatibilidad | Las empresas existentes no ven cambios en su experiencia actual |
| Core | Módulos compartidos por todas las verticales (Empresa, Cliente, Documento, Impuestos, Suscripción) |
| Tenant | Empresa en el contexto multi-tenant de eGarage |

---

*Ver VERTICAL_ARCHITECTURE_V1.md para el diseño técnico detallado de cada componente.*
