# eGarage — Roadmap de Productos
**Versión:** 2.0  
**Fecha:** 2026-07-28  
**Arquitectura de referencia:** docs/architecture/VERTICAL_ARCHITECTURE_V1.md  
**Auditoría base:** docs/auditorias/auditoria_final_verticales_egarage.md  
**Cambios desde V1.0:** EmpresaModulo · auth antes de menú · MenuService · nomenclatura Workshop/Salvage/Parts

---

## Vista General

```
ESTADO ACTUAL ──────────────────────────────────────────────────────────▶ OBJETIVO

Una sola landing (talleres)           Workshop · Salvage · Parts landings
Menú idéntico para todos          →   MenuService construye el menú por empresa
Sin modelo de módulos                 Tabla EmpresaModulo normalizada
Onboarding no captura producto        Selector de producto en paso 1
Módulo Salvage accesible a todos      Gate @requiere_producto en todas las vistas
Casa de repuestos: stub mínimo        Producto Parts completo (E5, post-validación)
```

---

## Orden de Implementación y Razonamiento

Las épicas están ordenadas por un principio explícito:

> **Primero proteger, después mostrar.**

E2 (autorización backend) va antes que E3 (menú visual). El menú solo oculta un enlace. El decorator protege la URL real. Mostrar un menú diferenciado sin haber asegurado las URLs es seguridad cosmética.

```
E0 (Landings públicas)
    │
    └──▶ E1 (EmpresaModulo + Onboarding)
              │
              └──▶ E2 (Autorización backend @requiere_producto)
                        │
                        └──▶ E3 (MenuService + menú dinámico)
                                  │
                                  └──▶ E4 (Onboarding especializado por producto)
                                            │
                                            └──▶ E5 (Producto Parts completo)
E6 (SEO + contenido) ── paralelo a cualquier épica desde E0
```

---

## Épica 0 — Portal Público Diferenciado
**Estado:** Pendiente de inicio  
**Prioridad:** Alta — impacto comercial inmediato, cero riesgo técnico  
**Prerequisito:** Este documento aprobado  
**Tiempo estimado:** 3-5 días

### Objetivo

Crear tres landings públicas separadas sin tocar ningún código existente. El portal principal muestra el selector de producto.

### Tareas

| # | Tarea | Archivos a crear | Archivos a modificar |
|---|---|---|---|
| E0-1 | Base de landing compartida (nav mínimo, footer, SEO head) | `templates/public/base_landing.html` | — |
| E0-2 | Landing eGarage Workshop | `templates/public/landing_workshop.html` | — |
| E0-3 | Landing eGarage Salvage (incluye historia Atlanta, obligatoria) | `templates/public/landing_salvage.html` | — |
| E0-4 | Landing eGarage Parts (placeholder con CTA básico) | `templates/public/landing_parts.html` | — |
| E0-5 | Vista Python para las tres landings + selector de home | `taller/views/landing_views.py` | — |
| E0-6 | Registrar URLs públicas | — | `taller/urls_public.py` |
| E0-7 | Home principal: selector de producto (dos botones grandes mínimos) | — | `templates/landing_inicio.html` |

### Criterios de Aceptación

- `/talleres/` carga con copy de taller mecánico, CTA "Empieza gratis"
- `/desarmadurias/` carga con historia Atlanta visible, CTA "Empieza con Salvage"
- `/repuestos/` carga (placeholder aceptable en E0)
- Home muestra al menos los botones "Taller" y "Desarmaduría"
- `<title>`, `<meta description>`, `<link rel="canonical">` correctos en las tres
- Las URLs existentes (`/cl/es/`, `/us/en/`, etc.) no se rompen
- Sin modificar modelos, migraciones, middleware, sidebar ni dashboard

### Rollback

```bash
git revert HEAD  # o eliminar manualmente los 5-6 archivos nuevos
# No hay migración que revertir
```

---

## Épica 1 — Modelo EmpresaModulo y Onboarding con Selector
**Estado:** Pendiente  
**Prioridad:** Alta  
**Prerequisito:** E0 en producción  
**Tiempo estimado:** 5-7 días

### Objetivo

Crear la tabla `EmpresaModulo` (el modelo de autorización definitivo) y modificar el onboarding para que el usuario elija su producto eGarage al registrarse. El campo `rubro_principal` y los módulos se escriben en el mismo paso pero a modelos distintos.

### Tareas

| # | Tarea | Archivos a crear | Archivos a modificar |
|---|---|---|---|
| E1-1 | Modelo `EmpresaModulo` con choices `WORKSHOP / SALVAGE / PARTS` | `taller/models/empresa_modulo.py`, `taller/migrations/XXXX_create_empresa_modulo.py` | `taller/models/__init__.py` |
| E1-2 | Helper `empresa.tiene_producto()` y `empresa.productos_activos()` | — | `taller/models/empresa.py` |
| E1-3 | Backfill en la migración: crear `WORKSHOP + SALVAGE + PARTS` para todas las empresas existentes | — | (dentro de la migración M-01) |
| E1-4 | Agregar `SALVAGE` a `RUBRO_CHOICES` en `ConfiguracionEmpresa` | — | `taller/models/configuracion.py` |
| E1-5 | Servicio `provision_productos(empresa, tipo_producto)` en `CompanyDefaultsService` | — | `taller/services/company_defaults_service.py` |
| E1-6 | Agregar selector de producto al paso de identidad del onboarding | — | `templates/onboarding/paso_identidad.html`, `taller/forms/onboarding.py` |
| E1-7 | `onboarding_guardar_paso` paso 1: llamar a `provision_productos()` | — | `taller/views/onboarding_views.py` |
| E1-8 | Registrar `EmpresaModulo` en admin de Django | — | `taller/admin.py` |
| E1-9 | Tests: migración sin downtime; onboarding crea filas correctas; helper `tiene_producto()` | `taller/tests/test_empresa_modulo.py`, `taller/tests/test_onboarding_producto.py` | — |

### Criterios de Aceptación

- Todas las empresas existentes tienen filas en `EmpresaModulo` para los tres productos tras la migración
- Un registro nuevo con selección "Desarmaduría" crea solo `EmpresaModulo(codigo="SALVAGE")`
- `empresa.tiene_producto("SALVAGE")` retorna `True`/`False` correctamente
- El campo `rubro_principal` se escribe independientemente del módulo
- La migración aplica sin downtime ni error en producción (probar en clon primero)
- El admin de Django muestra y permite editar los módulos por empresa

### Rollback

```bash
python manage.py migrate taller <migración_anterior_a_M-01>
git revert HEAD~N  # revertir commits de E1
```

---

## Épica 2 — Autorización Backend (`@requiere_producto`)
**Estado:** Pendiente  
**Prioridad:** Alta  
**Prerequisito:** E1 en producción (necesita `EmpresaModulo` y `empresa.tiene_producto()`)  
**Tiempo estimado:** 4-6 días

> **Por qué E2 antes que E3:**  
> El menú dinámico (E3) oculta visualmente un enlace. El decorator (E2) protege la URL real. Si el menú se despliega antes que el decorator, durante el período de transición cualquier empresa podría acceder a las URLs de Salvage aunque el menú no las muestre. La seguridad va primero.

### Objetivo

Crear el decorator `@requiere_producto` y aplicarlo a todas las vistas de Salvage. Una empresa sin `SALVAGE` en `EmpresaModulo` que accede a `/cl/es/desarme/vehiculos/` recibe 403.

### Tareas

| # | Tarea | Archivos a crear | Archivos a modificar |
|---|---|---|---|
| E2-1 | Crear `taller/decorators.py` con `@requiere_producto` y `RequiereProductoMixin` | `taller/decorators.py` | — |
| E2-2 | Crear template de error 403 específico para producto no habilitado | `templates/errors/403_producto.html` | — |
| E2-3 | Aplicar `@requiere_producto("SALVAGE")` en todas las FBVs de `views.py` | — | `taller/desarme/views.py` |
| E2-4 | Aplicar en `views_venta.py` | — | `taller/desarme/views_venta.py` |
| E2-5 | Aplicar en `views_inventario.py` | — | `taller/desarme/views_inventario.py` |
| E2-6 | Aplicar en `views_pdf.py` | — | `taller/desarme/views_pdf.py` |
| E2-7 | Tests de integración: empresa sin SALVAGE → 403; con SALVAGE → 200; API → JSON 403 | `taller/tests/test_auth_productos.py` | — |

### Criterios de Aceptación

- `empresa.tiene_producto("SALVAGE") == False` → cualquier URL de desarme devuelve 403
- `empresa.tiene_producto("SALVAGE") == True` → acceso normal
- Las APIs (AJAX, JSON) devuelven `{"error": "...", "codigo": "SALVAGE"}` con status 403
- El kiosco público (`/tienda/<slug>/`) no aplica el decorator (es público)
- Los tests pasan en clon contra PostgreSQL (no SQLite)
- El usuario ve `templates/errors/403_producto.html` con un mensaje claro

### Rollback

```bash
# Eliminar taller/decorators.py
# Quitar los @requiere_producto de las 4 vistas de desarme
# Sin migración que revertir
git revert HEAD~N
```

---

## Épica 3 — MenuService y Menú Dinámico
**Estado:** Pendiente  
**Prioridad:** Alta  
**Prerequisito:** E2 en producción  
**Tiempo estimado:** 4-5 días

> **Por qué E3 después de E2:**  
> El menú dinámico solo tiene sentido cuando las URLs que oculta ya están protegidas. Además, `MenuService` puede construirse y testearse en paralelo con E2 sin necesidad de modificar `base.html` hasta que E2 esté confirmado.

### Objetivo

Crear `MenuService` y reemplazar los condicionales y el contenido hardcodeado del menú en `base.html` por una iteración sobre la lista que devuelve el servicio. Los templates no deciden qué mostrar; solo renderizan lo que reciben.

### Tareas

| # | Tarea | Archivos a crear | Archivos a modificar |
|---|---|---|---|
| E3-1 | Crear `MenuService` con `CORE_ITEMS`, `WORKSHOP_ITEMS`, `SALVAGE_ITEMS`, `PARTS_ITEMS` y método `build_groups_for(empresa, user)` | `taller/services/menu_service.py` | — |
| E3-2 | Tests unitarios del servicio: empresa Workshop → sin Salvage; empresa multiproducto → todo | `taller/tests/test_menu_service.py` | — |
| E3-3 | Actualizar `empresa_contexto` context processor para exponer `menu_groups` | — | `taller/context_processors/empresa_contexto.py` |
| E3-4 | Reemplazar sección de navegación en `base.html` (líneas 807-875) con iteración sobre `menu_groups` | — | `templates/base.html` |
| E3-5 | Reescribir `components/sidebar.html` para usar `menu_groups` | — | `templates/components/sidebar.html` |
| E3-6 | Actualizar `workspace_home.html` para mostrar tarjetas solo de productos activos | — | `templates/taller/common/workspace_home.html` |
| E3-7 | Test de regresión visual: empresas existentes (todos los productos activos) ven el mismo menú que antes | — | — |

### Criterios de Aceptación

- Empresa con solo `WORKSHOP` activo: menú no muestra "Desarme" ni "Interchange"
- Empresa con solo `SALVAGE` activo: menú no muestra "Servicios" ni "Técnicos"
- Empresa multiproducto (`WORKSHOP + SALVAGE`): menú muestra todo
- Todas las empresas existentes (backfill con los tres productos) ven menú completo
- `MenuService` tiene cobertura de tests unitarios ≥ 90%
- `base.html` no contiene ningún `{% if modulo... %}` o equivalente de lógica de negocio

### Rollback

```bash
git revert HEAD~N  # revertir base.html, sidebar.html, workspace_home.html, empresa_contexto.py
# menu_service.py puede quedarse (es código nuevo sin side-effects)
```

---

## Épica 4 — Onboarding Especializado por Producto
**Estado:** Pendiente  
**Prioridad:** Media  
**Prerequisito:** E1, E2 y E3 en producción  
**Tiempo estimado:** 4-6 días

### Objetivo

Después de elegir el producto en el paso de identidad, el resto del onboarding usa textos, ejemplos y datos de demo correspondientes al producto seleccionado.

### Tareas

| # | Tarea | Archivos a crear | Archivos a modificar |
|---|---|---|---|
| E4-1 | Template de finalización para Workshop | `templates/onboarding/paso_finalizar_workshop.html` | — |
| E4-2 | Template de finalización para Salvage | `templates/onboarding/paso_finalizar_salvage.html` | — |
| E4-3 | Selección de template en la vista según `rubro_principal` | — | `taller/views/onboarding_views.py` |
| E4-4 | Demo data de Salvage: al menos un `VehiculoDesarme` + 5 `PiezaDesarme` | — | Management command de demo existente |
| E4-5 | Checklist de inicio en dashboard post-onboarding, diferenciado por producto | `templates/dashboard/checklist_workshop.html`, `templates/dashboard/checklist_salvage.html` | `templates/dashboard/index.html` |

### Criterios de Aceptación

- Un usuario nuevo que elige "Desarmaduría" ve ejemplos de desarmaduría en el finalizar
- Los datos de demo de Salvage incluyen un vehículo y piezas, no datos de taller
- El dashboard post-onboarding muestra el checklist correcto para el producto

### Rollback

```bash
git revert HEAD~N  # solo templates y lógica de selección de template
```

---

## Épica 5 — Producto Parts Completo
**Estado:** Pendiente — iniciar solo después de validación comercial  
**Prioridad:** Media-Baja  
**Prerequisito:** E1, E2, E3 confirmados; al menos 5 clientes interesados en Parts  
**Tiempo estimado:** 4-6 semanas

### Prerequisito comercial

No construir Parts hasta tener evidencia de demanda real. Workshop y Salvage ya tienen producto funcional. Parts requiere construcción nueva sustancial. Invertir sin validar es el error clásico de SaaS temprano.

**Trigger para iniciar E5:** Al menos 5 empresas registradas con `rubro_principal=PARTS` o 5 solicitudes directas de una casa de repuestos.

### Sub-épicas

#### E5-A — Proveedores
- Modelo `Proveedor` (ficha completa)
- CRUD con listado, búsqueda, estado activo/inactivo

#### E5-B — Órdenes de Compra
- Modelos `OrdenCompra` + `LineaOrdenCompra`
- Flujo de estados: borrador → enviada → recibida parcial → recibida total
- Actualización automática de `Repuesto.cantidad_stock` vía `MovimientoStock`

#### E5-C — Movimientos de Stock
- Modelo `MovimientoStock`
- Trazabilidad completa (quién, cuándo, qué cantidad, por qué razón)
- Integración transparente con el `Repuesto` existente (sin tabla nueva para repuestos)

#### E5-D — Venta Directa
- Mini-POS: selección de producto → cantidad → precio → generar `Documento` tipo venta
- Crea `MovimientoStock(tipo="SALIDA_VENTA")` automáticamente

#### E5-E — Dashboard Parts
- Valor del inventario en tiempo real
- SKUs bajo mínimo (tabla + alerta)
- Margen bruto por categoría
- Top 10 por rotación

### Criterios de Aceptación (E5 completa)

- Una casa de repuestos puede: registrar proveedor → OC → recibir → stock actualizado → venta directa → movimiento registrado
- El módulo solo es accesible para empresas con `EmpresaModulo(codigo="PARTS", activo=True)`
- Los tests de integración cubren el flujo completo (sin datos de taller contaminados)

---

## Épica 6 — SEO y Contenido de Landings
**Estado:** Pendiente  
**Prioridad:** Media  
**Prerequisito:** E0 (landings creadas)  
**Tiempo estimado:** 2-3 semanas (mayormente redacción, no código)  
**Puede ejecutarse en paralelo con cualquier otra épica desde E0**

### Tareas

| # | Tarea |
|---|---|
| E6-1 | Copy definitivo para `landing_salvage.html` (historia Atlanta, diferencial, casos de uso, CTA por país) |
| E6-2 | Copy para `landing_workshop.html` (diferencial vs Excel/cuaderno, casos Chile+USA) |
| E6-3 | Schema.org `SoftwareApplication` en las tres landings |
| E6-4 | `sitemap.xml` actualizado con las landings especializadas |
| E6-5 | Open Graph images distintas por producto |
| E6-6 | Landing en inglés: `/us/en/salvage-yards/` con copy para mercado latino-USA |
| E6-7 | Landing en inglés: `/us/en/workshops/` |
| E6-8 | Meta tags de verificación Google Search Console por país |

---

## Cronograma Tentativo

| Semana | Épica | Entregable visible |
|---|---|---|
| 1 | E0 | Tres landings públicas en producción; home con selector |
| 2-3 | E1 | `EmpresaModulo` en producción; onboarding captura producto |
| 3-4 | E2 | Vistas de Salvage protegidas con 403 para empresas sin el producto |
| 4-5 | E3 | Menú dinámico vía `MenuService`; workspace diferenciado |
| 5-6 | E4 | Onboarding con flujo y demo data por producto |
| 6-8 | E6 | SEO y contenido (paralelo) |
| 9+ | E5 | Solo si hay validación comercial de Parts |

---

## Checklist Antes de Iniciar Cada Épica

- [ ] El clon de producción está actualizado con los datos reales más recientes.
- [ ] La épica tiene al menos los tests críticos escritos antes de implementar.
- [ ] Existe un plan de rollback documentado y probado mentalmente.
- [ ] Los commits serán pequeños y atómicos (un cambio por commit, no una épica entera en un commit).
- [ ] La épica se valida en el clon antes de hacer push a producción.
- [ ] Ningún commit modifica migraciones ya aplicadas en producción.
- [ ] El ROADMAP se actualiza con el estado real al terminar cada épica.

---

## Métricas de Éxito

| Métrica | Hoy | Meta (6 meses) |
|---|---|---|
| Registros desde `/desarmadurias/` | 0 | 20 empresas con `codigo="SALVAGE"` |
| Porcentaje de nuevas empresas que completan el selector de producto | 0% | 100% (bloqueante en onboarding) |
| Empresas con módulo Salvage activo y al menos 1 VehiculoDesarme | Desconocido | 15 |
| Posición Google "software desarmaduría Chile" | No rastreable | Top 10 |
| Tiempo de onboarding (registro → workspace) | ~5 min | < 3 min |
| Tests de `MenuService` | 0 | ≥ 90% cobertura |

---

## Riesgos y Mitigaciones

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Migración M-01 rompe producción | Muy baja | Alto | Probar en clon. El backfill es solo INSERT, no UPDATE. |
| El decorator 403 bloquea accidentalmente a empresas que sí usan Salvage | Baja | Alto | El backfill de M-01 da los tres productos a todas las empresas existentes. Si tienen la tabla, tienen acceso. |
| `MenuService` no cubre un caso de URL country-aware | Media | Medio | Tests unitarios por URL canónica. El servicio retorna `url_name` para `{% country_url %}`; no URLs hardcodeadas. |
| E5 (Parts) tarda más de lo estimado | Alta | Bajo | No bloquea E0-E4. E5 es completamente independiente. |
| El copy de la landing de Salvage no convierte | Media | Medio | La historia de Atlanta es el diferencial real. A/B testeable sin tocar el código. |

---

## Glosario

| Término | Definición |
|---|---|
| Workshop | eGarage Workshop — producto para talleres mecánicos y servicios automotrices. Código interno: `WORKSHOP`. |
| Salvage | eGarage Salvage — producto para desarmadurías y recicladores. Código interno: `SALVAGE`. |
| Parts | eGarage Parts — producto para casas de repuestos. Código interno: `PARTS`. |
| `rubro_principal` | Campo en `ConfiguracionEmpresa`. Identidad del negocio. Controla presentación y UX. No controla acceso. |
| `EmpresaModulo` | Tabla normalizada. Registra qué productos eGarage tiene habilitados una empresa. Controla autorización. |
| `MenuService` | Servicio Python que construye la lista de ítems de menú según los productos activos de la empresa. |
| `@requiere_producto` | Decorator que verifica `empresa.tiene_producto(codigo)` antes de ejecutar una vista. |
| Gate de acceso | Mecanismo que impide acceder a URLs de un producto no habilitado. Implementado vía `@requiere_producto`. |
| Core | Módulos compartidos por todos los productos: Empresa, Cliente, Documento, Impuestos, Suscripción. |
| Backfill | Script dentro de una migración que rellena datos en filas existentes. M-01 hace backfill al crear `EmpresaModulo`. |

---

*Ver VERTICAL_ARCHITECTURE_V1.md para el diseño técnico detallado de cada componente, modelo y servicio.*
