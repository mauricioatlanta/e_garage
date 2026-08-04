# Auditoría MonteAzul → eGarage

**Fecha:** 2026-07-31  
**Pregunta central:** ¿Qué le falta a eGarage para reemplazar MonteAzul sin perder ninguna capacidad importante?

---

## 1. Stack MonteAzul

- **Framework:** Django 6.0
- **Base de datos:** SQLite (local) / PostgreSQL (producción)
- **Apps:** 15 apps propias — `accounts`, `audit`, `blog`, `cart`, `catalog`, `core`, `customers`, `inventory`, `ops`, `orders`, `payments`, `reports`, `reviews`, `shipping`, `tracking`
- **Pagos:** WebPay Plus (Transbank) integrado en `cart/views_webpay.py`; transferencia bancaria como alternativa
- **Email:** no identificado en este scope (probablemente Django email o servicio externo)
- **SEO:** Sitemaps propios (Static, Product, Category, BlogPost, VehicleLanding), robots.txt, meta/OG en templates
- **Analytics:** TrackingEvent propio (sin Google Analytics)
- **Proyecto hermano:** `cataliticos/` en `../cataliticos` — se carga dinámicamente si existe

---

## 2. Stack eGarage

- **Framework:** Django + pytest-django
- **Apps relevantes:** `taller/` (ERP), `marketplace/`, `whatsapp/`, `ubicacion/`
- **Email:** Resend (ResendBackend), helpers en `taller/utils/email_helper.py`
- **Multi-tenant:** `empresa` FK en todos los modelos de negocio
- **Inventario:** `MovimientoInventario` — ledger append-only, idempotencia SHA-256 ✅ más avanzado que MonteAzul
- **Contratos:** Contract Registry v2 diseñado, runtime pendiente de implementar
- **Pagos:** ninguno integrado aún para Commerce
- **SEO:** ninguno para canal público

---

## 3. Modelos — Comparativa

### Catálogo

| Modelo MonteAzul | Campos clave | Equivalente eGarage | Estado |
|---|---|---|---|
| `Category` | name, slug, parent (nested), is_active, default_warranty_days | `CategoriaRepuesto` | 🟡 Parcial — falta slug, parent/nesting, warranty defaults |
| `VehicleBrand` | name | — | ❌ No existe |
| `VehicleModel` | brand, name | — | ❌ No existe |
| `VehicleEngine` | model, name, fuel_type, displacement_cc | — | ❌ No existe |
| `Product` | sku, sku_canonico, name, **slug**, category, price, compare_at_price, cost_price, weight, dims, stock, euro_norm, material, ficha_tecnica, warranty_*, **is_publishable**, quality_score | `Repuesto` | 🟡 Muy parcial — Repuesto tiene solo 8 campos básicos |
| `ProductImage` | product, image, alt_text, is_primary, position (1-4) | — | ❌ No existe |
| `ProductCompatibility` | product, brand, model, engine, displacement_cc, year_from, year_to, confidence | — | ❌ No existe |
| `ProductViewStat` | product, views, last_viewed | — | ❌ No existe |
| `SearchLog` | query, cc, fuel, year, results_count | — | ❌ No existe |

### Carrito y Pedidos

| Modelo MonteAzul | Campos clave | Equivalente eGarage | Estado |
|---|---|---|---|
| `cart.Order` (checkout) | order_number, status (DRAFT→PAID), full_name, email, phone, delivery_method, region, comuna, address, subtotal, shipping_cost, total, webpay_* | — | ❌ No existe |
| `cart.OrderItem` | order, product_id, name, unit_price, quantity, line_total | — | ❌ No existe |
| `orders.Order` (lifecycle completo) | customer, status (PENDING→SHIPPED→COMPLETED), discount_total, tax_total, cancelled_at | — | ❌ No existe — `Documento` ERP no es equivalente Commerce |
| `orders.OrderItem` | product, unit_price_applied, discount_*, cost_price_snapshot, warranty_snapshot | `DetalleDocumento` | 🟡 Conceptualmente similar; no es Commerce |
| `orders.WarrantyClaim` | order_item, customer, claim_reason, status, resolution | — | ❌ No existe |

### Inventario

| Modelo MonteAzul | Campos clave | Equivalente eGarage | Estado |
|---|---|---|---|
| `StockMovement` | product, movement_type (IN/OUT/ADJUSTMENT/RETURN), quantity, related_order, reason | `MovimientoInventario` | ✅ **eGarage es superior** — ledger append-only con idempotencia SHA-256, TipoMovimiento más completo |

### Clientes y Usuarios

| Modelo MonteAzul | Campos clave | Equivalente eGarage | Estado |
|---|---|---|---|
| `CustomerProfile` | user (opcional), customer_type (WEB/INTERNO), discount_percent, company_name, rut, warranty_days_modifier | `Cliente` | 🟡 Parcial — `Cliente` ERP no tiene login web, historial de compras, direcciones Commerce |

### Blog y Contenido

| Modelo MonteAzul | Campos clave | Equivalente eGarage | Estado |
|---|---|---|---|
| `BlogCategory` | name, slug | — | ❌ No existe |
| `Post` | title, slug, excerpt, content, cover_image, published_at, is_published | — | ❌ No existe |
| `Review` | product, user, order, rating (1-5), title, body, is_approved | — | ❌ No existe |

### Configuración y Analytics

| Modelo MonteAzul | Campos clave | Equivalente eGarage | Estado |
|---|---|---|---|
| `ConfiguracionEmpresa` | warranty_days, comision_vendedores_pct, margen_minimo, bloqueo_venta_sin_stock, notif_* | `Empresa` | 🟡 Parcial — eGarage tiene config de empresa pero sin campos Commerce |
| `TrackingEvent` | event (search/cart/click), payload, ip, user_agent | — | ❌ No existe |

---

## 4. Pantallas — Comparativa

### Sitio Público

| Pantalla | URL MonteAzul | Estado eGarage | Notas |
|---|---|---|---|
| Home | `/` o `/inicio/` | ❌ | No existe home público de catálogo |
| Lista de categorías | navegación | ❌ | |
| Lista de productos | `/productos/` | ❌ | Búsqueda ERP existe pero no es pública |
| Buscador por texto | `/productos/buscar/` | ❌ | |
| Buscador por vehículo (marca/modelo/año) | `/productos/buscador-vehiculo/` | ❌ | Crítico para MonteAzul |
| Búsqueda de escapes por diámetro | `/productos/busqueda-escape/` | ❌ | Específico de MonteAzul |
| Asistente catalizadores | `/productos/asistente-cataliticos/` | ❌ | Específico de MonteAzul |
| Ficha de producto | `/productos/<slug>/` | ❌ | No hay URL pública por slug |
| Reseña de producto | `/productos/<slug>/reseña/` | ❌ | |
| Lista de precios | `/productos/listado-precios/` | ❌ | |
| Normativas Euro 2-5 | `/normativas/` | ❌ | Específico de MonteAzul |
| Blog | `/blog/` | ❌ | |
| Post de blog | `/blog/<slug>/` | ❌ | |
| Página Nosotros | `/nosotros/` | ❌ | |
| Página Garantías | `/garantias/` | ❌ | |
| Página FAQ | `/faq/` | ❌ | |
| Carrito | `/carrito/` | ❌ | |
| Checkout (datos comprador) | `/carrito/checkout/` | ❌ | |
| Revisar pedido | `/carrito/checkout/revisar/<id>/` | ❌ | |
| Pago WebPay | `/carrito/webpay/iniciar/<id>/` | ❌ | |
| Retorno WebPay | `/carrito/webpay/retorno/` | ❌ | |
| Pago transferencia | `/carrito/checkout/transferencia/<id>/` | ❌ | |
| Sitemap.xml | `/sitemap.xml` | ❌ | |
| robots.txt | `/robots.txt` | ❌ | |

### Panel de Operaciones (Ops)

| Pantalla | URL MonteAzul | Estado eGarage | Notas |
|---|---|---|---|
| Dashboard | `/ops/` | ✅ | Workspace 2.0 con KPIs por rubro |
| Catálogo (lista) | `/ops/catalogo/` | 🟡 | CRUD de repuestos existe; falta slug, imágenes, publishable |
| Catálogo (agregar/editar) | `/ops/catalogo/agregar/` | 🟡 | Formulario de repuesto básico |
| SEO dashboard | `/ops/seo/` | ❌ | No existe |
| Ventas (lista) | `/ops/sales/` | ❌ | Documentos ERP ≠ ventas Commerce |
| Ventas (detalle) | `/ops/sales/<pk>/` | ❌ | |
| Inventario (lista) | `/ops/inventory/` | ✅ | Vista de stock por repuesto |
| Movimientos de inventario | `/ops/inventory/movements/` | 🟡 | Ledger existe; falta vista de usuario final |
| Clientes | `/ops/customers/` | 🟡 | Cliente ERP; falta CustomerProfile Commerce |
| Garantías | `/ops/warranties/` | ❌ | |
| Reportes de ventas | `/ops/reports/sales/` | ❌ | Para Commerce |
| Configuración empresa | `/ops/settings/` | 🟡 | Parcialmente en Empresa |

---

## 5. Flujo de compra — Gap analysis

| Paso | MonteAzul | eGarage | Estado |
|---|---|---|---|
| 1. Búsqueda por texto | `product_search_api` + smart_search | Buscador ERP (no público) | 🟡 Existe; no es público |
| 2. Búsqueda por vehículo | `vehicle_search_page` + APIs marca/modelo/año | ❌ | ❌ |
| 3. Ficha producto (slug + SEO) | `product_detail` con meta/OG | ❌ | ❌ |
| 4. Agregar al carrito | `cart_add` (sesión) | ❌ | ❌ |
| 5. Ver carrito | `cart_view` | ❌ | ❌ |
| 6. Checkout (datos comprador) | `checkout` → Order DRAFT | ❌ | ❌ |
| 7. Pago WebPay | `webpay_start` → `webpay_return` → Order PAID | ❌ | ❌ |
| 8. Pago transferencia | `checkout_transfer` → Order PENDING_PAYMENT | ❌ | ❌ |
| 9. Confirmación y email | Signal post_save + email al cliente | ❌ | ❌ — email helper existe pero no templates Commerce |
| 10. Descuento de stock automático | `StockMovement OUT` al pagar | 🟡 | `MovimientoInventario` existe; falta hook desde Order |
| 11. Historial de pedido | `ops/sales/<pk>/` | ❌ | ❌ |
| 12. Tracking de comportamiento | `TrackingEvent` | ❌ | ❌ |

---

## 6. Integraciones externas

| Integración | MonteAzul | eGarage | Estado |
|---|---|---|---|
| WebPay Plus (Transbank) | ✅ `views_webpay.py` | ❌ | ❌ — bloqueante para Chile |
| Transferencia bancaria | ✅ `checkout_transfer` | ❌ | ❌ |
| Email transaccional | ✅ (confirmación, despacho) | 🟡 Resend vía `email_helper.py` | 🟡 — infraestructura lista; falta templates Commerce |
| WhatsApp | 🟡 solo tracking de click | ✅ app `whatsapp/` completa | ✅ eGarage tiene más que MonteAzul |
| Sitemap dinámico | ✅ 5 sitemaps | ❌ | ❌ |
| SEO (meta, OG, canonical) | ✅ en templates | ❌ | ❌ |
| robots.txt | ✅ | ❌ | ❌ |
| Analytics propio | ✅ TrackingEvent | ❌ | ❌ |

---

## 7. Características especiales de MonteAzul (dominio escapes/catalizadores)

Estas son capacidades específicas del negocio de MonteAzul que no forman parte de un Commerce Engine genérico:

| Feature | Estado en eGarage | Prioridad |
|---|---|---|
| Compatibilidad vehicular (VehicleBrand/Model/Engine/year) | ❌ | Alta para MonteAzul; genérica para Commerce |
| Búsqueda por diámetro de escape (EscapeSearchView) | ❌ | Específica de MonteAzul |
| Asistente de catalizadores | ❌ | Específica de MonteAzul |
| Normativas Euro 2/3/4/5 | ❌ | Específica de MonteAzul |
| Campos técnicos del producto (euro_norm, material, install_type, diámetros, celdas, sensores) | ❌ | Específica de MonteAzul |
| Proyecto hermano `cataliticos/` | ❌ | Específica de MonteAzul |
| `sku_canonico` para matching con imágenes/zips | ❌ | Específica de MonteAzul |
| `quality_score` / `is_publishable` (score ≥70 para publicar) | ❌ | Útil para cualquier Commerce |
| Garantías por jerarquía (producto → categoría → empresa → settings) | ❌ | Útil para cualquier Commerce |
| `WarrantyClaim` (reclamo post-venta) | ❌ | Útil para cualquier Commerce |
| Reseñas verificadas (solo compradores pueden opinar) | ❌ | Útil para cualquier Commerce |

---

## 8. Resumen ejecutivo

| Categoría | MonteAzul | eGarage | % listo |
|---|---|---|---|
| **Modelos de datos** | 18 modelos | 4 parciales / 3 completos / 11 inexistentes | ~22% |
| **Pantallas públicas** | 22 pantallas | 0 listas / 0 parciales / 22 inexistentes | 0% |
| **Panel de operaciones** | 12 secciones | 3 listas / 4 parciales / 5 inexistentes | ~42% |
| **Flujo de compra** | 12 pasos | 0 listos / 2 parciales / 10 inexistentes | ~8% |
| **Integraciones** | 8 | 2 listas / 2 parciales / 4 inexistentes | ~31% |

**Total capacidades identificadas: ~56**
- ✅ Listas en eGarage: ~9 (16%)
- 🟡 Parciales (requieren extensión): ~11 (20%)
- ❌ Inexistentes (construir desde cero): ~36 (64%)

**Nota sobre el ledger:** En el único módulo donde eGarage supera a MonteAzul es en inventario — `MovimientoInventario` con idempotencia SHA-256 es más robusto que `StockMovement` de MonteAzul.

---

## 9. Backlog priorizado

Ordenado por impacto: lo que bloquea el flujo de compra primero, SEO segundo, capacidades nice-to-have al final.

### Bloque 1 — Sin esto no hay comercio (bloqueante)

| # | Capacidad | Tipo |
|---|---|---|
| 1 | `Repuesto` → Commerce Product (slug, is_publishable, compare_at_price, images, warranty) | Extensión modelo |
| 2 | `CategoriaRepuesto` → Category pública (slug, parent/nesting, image) | Extensión modelo |
| 3 | `ProductImage` (hasta 4 imágenes por producto) | Modelo nuevo |
| 4 | Catálogo público: home, lista, navegación por categoría | Vistas nuevas |
| 5 | Ficha de producto pública (`/productos/<slug>/`) | Vista nueva |
| 6 | Carrito (sesión) + Cart/CartItem | Modelo + vistas nuevos |
| 7 | Checkout (datos de comprador) → Order Commerce | Modelo + vista nuevos |
| 8 | WebPay Plus (Transbank) | Integración nueva |
| 9 | Transferencia bancaria como alternativa de pago | Vista nueva |
| 10 | Email de confirmación de pedido (template Commerce) | Template nuevo |
| 11 | Descuento automático de stock al pagar (hook Order → MovimientoInventario) | Lógica nueva |

### Bloque 2 — SEO y visibilidad (importante para adquisición)

| # | Capacidad | Tipo |
|---|---|---|
| 12 | Meta tags, Open Graph, canonical por producto/categoría | Templates |
| 13 | Sitemap.xml dinámico (productos, categorías, blog) | Config nueva |
| 14 | robots.txt | Template nuevo |
| 15 | Buscador público por texto (con sugerencias) | Vista nueva |
| 16 | Blog (BlogCategory + Post + CRUD en ops) | App nueva |

### Bloque 3 — Contract Runtime (arquitectura)

| # | Capacidad | Tipo |
|---|---|---|
| 17 | Contract Runtime operativo: ERP publica eventos → Commerce consume | Infraestructura |
| 18 | `catalog.product.changed` → Commerce actualiza catálogo | Evento nuevo |
| 19 | `inventory.stock.changed` → Commerce actualiza stock visible | Evento nuevo |

### Bloque 4 — Cuenta de cliente y post-venta

| # | Capacidad | Tipo |
|---|---|---|
| 20 | CustomerProfile Commerce (registro web, login, historial de pedidos, direcciones) | Modelo + vistas nuevos |
| 21 | Historial de pedidos para el cliente | Vista nueva |
| 22 | Tracking/estado del pedido | Vista nueva |
| 23 | Panel ops: gestión de pedidos Commerce (estados: PENDING→SHIPPED→COMPLETED) | Vista nueva |
| 24 | Panel ops: clientes Commerce | Vista nueva |

### Bloque 5 — Específico de MonteAzul (capa sobre Commerce Engine genérico)

| # | Capacidad | Tipo |
|---|---|---|
| 25 | `VehicleBrand` + `VehicleModel` + `VehicleEngine` | Modelos nuevos |
| 26 | `ProductCompatibility` (marca/modelo/año/motor) | Modelo nuevo |
| 27 | Buscador por vehículo (selección en cascada) | Vista + APIs nuevas |
| 28 | Campos técnicos del producto (euro_norm, material, diámetros, celdas, sensores) | Extensión modelo |
| 29 | Búsqueda de escapes por diámetro (EscapeSearchView) | Vista especializada |
| 30 | Asistente de catalizadores | Vista especializada |
| 31 | Normativas Euro 2-5 | Página estática |

### Bloque 6 — Nice-to-have

| # | Capacidad | Tipo |
|---|---|---|
| 32 | `Review` (reseñas verificadas de compradores) | Modelo + vista nuevos |
| 33 | `WarrantyClaim` (reclamos post-venta) | Modelo + flujo nuevos |
| 34 | `TrackingEvent` (analytics propio) | Modelo + JS nuevos |
| 35 | `quality_score` / `is_publishable` (semáforo de calidad de catálogo) | Lógica nueva |
| 36 | Páginas estáticas (Nosotros, FAQ, Garantías, Devoluciones) | Templates nuevos |

---

## 10. Regla arquitectónica (recordatorio)

**Nada de Commerce lee directamente del ERP.**  
El flujo obligatorio es: `ERP → Contract Runtime → Commerce Engine`.  
Si en cualquier PR de Commerce aparece un import directo de modelos del ERP, es un smell que bloquea el merge.

Los ítems del Bloque 3 (Contract Runtime) pueden desarrollarse en paralelo con el Bloque 1, pero el primer flujo de Commerce en producción debe consumir eventos, no queries directas.
