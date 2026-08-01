# Commerce Foundation Backlog

**Fecha:** 2026-07-31  
**Fuente:** Auditoría MonteAzul → eGarage (`docs/auditoria_monteazul_egarage.md`)  
**Objetivo:** Convertir eGarage en una plataforma Commerce reutilizable. MonteAzul será el primer suscriptor del perfil CASA_REPUESTOS, no un desarrollo a medida.

---

## Decisiones arquitectónicas (inamovibles antes del primer commit)

### 1. CommerceProduct es una capa sobre Repuesto, no una extensión

`Repuesto` es un modelo ERP. Commerce tiene otro ciclo de vida.

```
Repuesto (ERP)
    │  1:1
    ▼
CommerceProduct (Commerce)
    ├── slug
    ├── descripcion_larga
    ├── compare_at_price
    ├── meta_title / meta_description
    ├── og_image / canonical
    ├── is_publishable
    ├── ProductImage (1-4)
    ├── ProductCompatibility (vehículos)
    └── Rating / relacionados
```

`Repuesto` nunca conoce a `CommerceProduct`. El ERP sigue limpio. Commerce puede crecer (bundles, campañas, feeds de Google Shopping, TikTok Shop) sin contaminar el ERP.

**Analogía:** `CommerceProduct` es a `Repuesto` lo que `MovimientoInventario` es al stock — una capa separada que agrega capacidades sin modificar el modelo base.

### 2. CommerceCatalogGateway — las vistas nunca acceden al ERP

Las vistas de Commerce no importan nada de `taller/models/`. Todo pasa por el Gateway.

```
Vista
  │
  ▼
CommerceCatalogGateway   ← interfaz estable
  │
  ▼ (Sprint 1-2: implementación directa)
CommerceProduct + Repuesto
  │
  ▼ (Sprint 3+: implementación via runtime)
Contract Runtime
```

El Gateway expone métodos como `get_product(slug)`, `search(query)`, `get_category(slug)`. Sprint 1 implementa con lecturas directas. Sprint 3 reemplaza la implementación sin tocar una sola vista.

### 3. ERP → Contract Runtime → Commerce (regla dura)

Ninguna vista de Commerce consulta modelos del ERP directamente.  
El Gateway es el único punto de contacto, y solo en su implementación interna.  
Si aparece un import de `taller.models` en una vista de Commerce → smell que bloquea el merge.

### 4. CommerceOrder es independiente de Documento

```
Checkout
   │
   ▼
CommerceOrder (PENDING → PAID → SHIPPED → COMPLETED)
   │
   ▼ (cuando PAID)
OrderFulfillmentService
   ├── crea Documento ERP
   └── registra MovimientoInventario OUT
```

Esto permite vender por cualquier canal (online, teléfono, WhatsApp, marketplace) usando el mismo servicio de fulfillment. El `Documento` es consecuencia del pago, no del checkout.

---

## Grupo A — Catálogo público

> Sin esto MonteAzul no existe en eGarage. El cliente puede navegar pero no comprar.

| # | Capacidad | Notas de implementación |
|---|---|---|
| A1 | `CommerceProduct` (modelo nuevo, 1:1 con Repuesto) | slug, is_publishable, compare_at_price, descripcion_larga, meta_title, meta_description, og_image, canonical |
| A2 | `CommerceCatalogGateway` (interfaz + implementación directa) | Métodos: get_product, search, get_category, list_by_category |
| A3 | `CommerceCategory` (modelo nuevo, basado en CategoriaRepuesto con slug + parent) | 1:1 con CategoriaRepuesto o modelo independiente; slug, parent, image |
| A4 | `ProductImage` (modelo nuevo, FK a CommerceProduct) | Hasta 4 imágenes, position, is_primary, alt_text |
| A5 | Vista pública: home del catálogo | Categorías destacadas, buscador, productos destacados |
| A6 | Vista pública: lista de productos por categoría + paginación | Vía Gateway |
| A7 | Vista pública: ficha de producto (`/p/<slug>/`) | Imágenes, precio, compare_at_price, stock visible, descripción |
| A8 | Buscador público por texto (SKU, nombre, part_number) con sugerencias | Vía Gateway.search() |
| A9 | Meta tags + Open Graph + canonical en templates | Por producto y por categoría |
| A10 | `sitemap.xml` dinámico (productos, categorías publicados) | Solo is_publishable=True |
| A11 | `robots.txt` | Template estático |

**Hito A:** Un visitante entra a `monteazul.egarage.cl`, navega categorías, busca y ve la ficha de un producto. No puede comprar todavía.

---

## Grupo B — Venta

> Aquí MonteAzul cobra.

| # | Capacidad | Notas de implementación |
|---|---|---|
| B1 | `Cart` + `CartItem` (sesión, sin login requerido) | Carrito en sesión de Django; CartItem referencia CommerceProduct |
| B2 | Vistas carrito: ver, agregar, actualizar, eliminar | JS para actualizar sin reload |
| B3 | `CommerceOrder` + `CommerceOrderItem` | Modelo independiente de Documento; totales congelados |
| B4 | Checkout step 1: datos del comprador (nombre, email, teléfono, dirección) | |
| B5 | Checkout step 2: revisar pedido antes de pagar | |
| B6 | Integración WebPay Plus (Transbank) | iniciar → retorno → confirmación; solo Chile |
| B7 | Pago por transferencia bancaria | Alternativa para quienes no tienen tarjeta |
| B8 | Email de confirmación al cliente (template Commerce) | Vía `email_helper.py` existente |
| B9 | `OrderFulfillmentService`: cuando Order pasa a PAID → crea Documento + MovimientoInventario OUT | Servicio, no signal |
| B10 | Panel ops: gestión de pedidos Commerce (estados, búsqueda, cancelación) | |

**Hito B:** Un visitante puede agregar al carrito, pagar con WebPay y el stock se descuenta automáticamente vía ledger.

---

## Grupo C — Postventa

| # | Capacidad | Notas de implementación |
|---|---|---|
| C1 | `CommerceCustomer`: registro web, login, contraseña, email verificado | Separado de `Cliente` ERP |
| C2 | Vincular `CommerceOrder` a `CommerceCustomer` | Opcional en checkout, obliga post-registro |
| C3 | Portal cliente: historial de pedidos y estado | |
| C4 | Portal cliente: direcciones guardadas | |
| C5 | Tracking de estado visible al cliente (PENDING / PREPARACIÓN / ENVIADO) | |
| C6 | `WarrantyClaim`: reclamo post-venta vinculado a CommerceOrderItem | |
| C7 | Panel ops: gestión de garantías (aprobar, cambio, devolución) | |
| C8 | Panel ops: clientes Commerce | |

---

## Grupo D — Valor agregado

### D1 — Compatibilidad vehicular (crítico para MonteAzul, reutilizable en CASA_REPUESTOS)

| # | Capacidad |
|---|---|
| D1.1 | `VehicleBrand` + `VehicleModel` + `VehicleEngine` |
| D1.2 | `ProductCompatibility` (CommerceProduct, brand, model, engine, year_from, year_to, confidence) |
| D1.3 | Buscador público por vehículo (selección en cascada) |
| D1.4 | Sección "Compatible con" en ficha de producto |
| D1.5 | Panel ops: gestión de compatibilidades |

### D2 — SEO avanzado

| # | Capacidad |
|---|---|
| D2.1 | Blog: `BlogCategory` + `Post` + CRUD en ops |
| D2.2 | Sitemap ampliado (blog, landings de vehículo) |
| D2.3 | Structured data JSON-LD para productos |
| D2.4 | Landings SEO por modelo de vehículo |

### D3 — Conversión y engagement

| # | Capacidad |
|---|---|
| D3.1 | `Review` (reseñas verificadas, solo compradores) |
| D3.2 | Productos relacionados en ficha de producto |
| D3.3 | `quality_score` / `is_publishable` (semáforo de completitud del catálogo) |
| D3.4 | `TrackingEvent` propio (búsquedas, clics, add_to_cart) |

### D4 — Específico de MonteAzul

| # | Capacidad |
|---|---|
| D4.1 | Campos técnicos en CommerceProduct (euro_norm, material, diámetros, celdas, sensores) |
| D4.2 | Búsqueda de escapes por diámetro |
| D4.3 | Asistente de catalizadores |
| D4.4 | Normativas Euro 2/3/4/5 |

---

## Plan de sprints

### feature/commerce-foundation

**Sprint 1 — Catálogo navegable** (Semanas 1-2, Agosto)

1. `CommerceCategory` — modelo con slug, parent, image (A3)
2. `CommerceProduct` — modelo 1:1 con Repuesto, campos Commerce (A1)
3. `ProductImage` — FK a CommerceProduct, hasta 4 imágenes (A4)
4. `CommerceCatalogGateway` — interfaz + implementación directa Sprint 1 (A2)
5. Vistas públicas: home, lista por categoría, ficha de producto (A5, A6, A7)
6. Buscador público básico (A8)
7. SEO mínimo en templates: meta, OG (A9)

✅ **Al final del Sprint 1:** `monteazul.egarage.cl` existe y es navegable. El Gateway lee directo de BD. Las vistas no saben cómo funciona por dentro.

---

**Sprint 2 — Sitemap + robots + refinamiento** (Semana 3, Agosto)

1. `sitemap.xml` para productos y categorías (A10)
2. `robots.txt` (A11)
3. canonical por URL
4. Open Graph completo (imagen primaria del producto)
5. Refinamiento de templates mobile

---

**Sprint 3 — Contract Runtime MVP** (Semana 4, Agosto)

1. ERP publica `catalog.product.changed` al guardar un Repuesto
2. ERP publica `inventory.stock.changed` al registrar MovimientoInventario
3. `CommerceCatalogGateway` reemplaza implementación directa por consumo de eventos
4. Las vistas no cambian — solo cambia la implementación del Gateway

✅ **Al final del Sprint 3:** Si cambia un precio en el ERP, el catálogo público se actualiza por evento, no por query directa. El ADR está activo al 100%.

---

### feature/commerce-cart

**Sprint 4 — Carrito + Checkout + Pago** (Semanas 1-3, Septiembre)

1. `Cart` + `CartItem` en sesión (B1, B2)
2. `CommerceOrder` + `CommerceOrderItem` (B3)
3. Checkout steps 1 y 2 (B4, B5)
4. WebPay Plus / Transbank (B6)
5. Transferencia bancaria (B7)
6. Email de confirmación (B8)
7. `OrderFulfillmentService`: PAID → Documento + MovimientoInventario OUT (B9)
8. Panel ops básico de pedidos (B10)

✅ **Al final del Sprint 4:** MonteAzul puede vender. Un visitante paga con WebPay y el stock se descuenta.

---

### feature/commerce-customer

**Sprint 5 — Cuenta de cliente** (Semana 4, Septiembre)

1. `CommerceCustomer` con registro y login (C1, C2)
2. Portal cliente: historial de pedidos, estado, direcciones (C3, C4, C5)

---

### feature/monteazul-go-live

**Sprint 6 — MonteAzul como suscriptor #1** (Octubre)

1. Configuración del tenant MonteAzul: perfil CASA_REPUESTOS + canal Commerce activado
2. Dominio: `monteazul.cl` → eGarage
3. Migración de productos y stock desde MonteAzul SPA → eGarage
4. Validación flujo completo en producción
5. Monitoreo post-lanzamiento

✅ **Hito final:** Un cliente entra a `monteazul.cl`, navega, compra y recibe su pedido. Todo servido por eGarage. Al día siguiente se replica para otro cliente cambiando branding y dominio.

---

## Resumen del roadmap

```
Agosto
  Sprint 1 — Catálogo navegable (CommerceProduct + Gateway + vistas)
  Sprint 2 — Sitemap + SEO
  Sprint 3 — Contract Runtime (Gateway con eventos reales)

Septiembre
  Sprint 4 — Carrito + Checkout + WebPay + OrderFulfillmentService
  Sprint 5 — Cuenta cliente

Octubre
  Sprint 6 — MonteAzul go-live
  Sprint 7+ — Grupo D (compatibilidad vehicular, blog, reviews)
```

---

## Lo que NO entra hasta después del go-live

- Blog y reseñas (D2.1, D3.1) — no bloquean la venta
- Compatibilidad vehicular (D1) — diferenciador, no bloqueante
- Búsqueda por diámetro y asistente catalizadores (D4) — se migran desde proyecto hermano
- Historial de inventario ERP y ajustes manuales — retoman después del go-live
