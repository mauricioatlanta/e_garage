# MonteAzul Migration Masterplan

**Versión:** 1.1  
**Fecha:** 2026-07-31  
**Revisado:** 2026-07-31 — filosofía eventos-only, PaymentAttempt, split H1.1/H1.2  
**Estado:** ACTIVO — rama `feature/commerce-payments`  
**Dueño:** Mauricio Alvarado

---

## 1. Visión del proyecto

MonteAzul SpA es el **primer tenant de producción real del Commerce Engine de eGarage**. El objetivo no es construir un e-commerce a medida para MonteAzul, sino demostrar que eGarage puede servir como plataforma multi-tenant donde cualquier CASA_REPUESTOS puede activar su canal de ventas online con cero código nuevo, solo configuración.

**Resultado esperado:** `monteazul.cl` apunta a eGarage. Un visitante navega el catálogo, paga con WebPay y recibe su pedido. El ERP (Documentos, stock) se actualiza automáticamente por el Contract Runtime. Al mes siguiente se incorpora un segundo tenant cambiando únicamente branding, dominio y credenciales de pago.

**Principio fundacional (ADR-000):** MonteAzul no es un desarrollo a medida; es la validación del producto. Cada línea de código debe responder: ¿servirá igual para el segundo, tercero y décimo suscriptor? Si la respuesta es "no", probablemente no pertenece al núcleo de la plataforma.

**Principio de comunicación (ADR-004):** Commerce y el ERP hablan únicamente mediante eventos. El flujo es siempre:

```
Commerce → Outbox → Runtime → ERP → Outbox → Runtime → Commerce
```

Nunca `PaymentGateway → Documento`. Nunca una vista de Commerce importa un modelo ERP. El desacople que costó construir no se negocia.

---

## 2. Estado actual

### 2.1 ERP (taller/)
| Capacidad | Estado |
|-----------|--------|
| Modelo `Empresa` (tenant boundary) | ✅ Producción |
| `Documento` + `DetalleDocumento` | ✅ Producción |
| `DocumentSequence` con select_for_update | ✅ Validado |
| `LineaRepuesto` con `origen_repuesto` | ✅ Producción |
| `Cliente` (find-or-create por email) | ✅ Producción |
| `MovimientoInventario` (ledger de stock) | ✅ Producción |

### 2.2 Commerce Engine (commerce/)
| Capacidad | Estado |
|-----------|--------|
| `CommerceStorefrontSettings` + Brand Engine | ✅ Merged en main |
| `CommerceCatalogGateway` | ✅ Merged |
| `CommerceProduct` (1:1 sobre Repuesto) | ✅ Merged |
| `ProductImage` | ✅ Merged |
| `CommerceCategory` | ✅ Merged |
| `CommerceCart` + `CartItem` | ✅ Merged |
| `CommerceOrder` + `CommerceOrderItem` | ✅ Merged (sin campos de pago) |
| `OrderService.create_from_cart()` | ✅ Merged (emite OutboxEvent) |
| Vistas checkout (form → order_received) | ✅ Merged — **sin paso de pago** |
| `PaymentGateway` (interfaz) | ❌ No existe |
| `CommercePaymentTransaction` (modelo) | ❌ No existe |
| WebPay Plus integrado en Commerce | ❌ No existe |
| Transferencia bancaria en Commerce | ❌ No existe |
| `OrderFulfillmentService` (PAID → Documento) | ❌ No existe |
| Email de confirmación al cliente | ❌ No existe |

### 2.3 Contract Runtime (runtime/)
| Capacidad | Estado |
|-----------|--------|
| `OutboxEvent` + `ProcessedEvent` | ✅ Merged |
| `OutboxService.enqueue()` | ✅ Merged |
| `CommerceOrderConsumer` → crea Documento PTS BORRADOR | ✅ Merged |
| `process_outbox` management command | ✅ Merged |
| Evento `commerce.order.submitted` | ✅ Contrato activo |
| Evento `commerce.order.paid` | ❌ No existe |

### 2.4 Multi-tenant / Storefront
| Capacidad | Estado |
|-----------|--------|
| Middleware `commerce_empresa` por dominio | ✅ Merged |
| `CommerceStorefrontSettings` poblado MonteAzul | ✅ Importado |
| DNS `monteazul.cl` → eGarage | ❌ Pendiente (bloqueado por H5) |

---

## 3. Hitos H1–H5

### H1.1 — Dominio de pagos (sin gateway)
**Rama:** `feature/commerce-payments`  
**Entregable:** La arquitectura de pagos existe y está probada antes de tocar Transbank. Cuando llegue WebPay, estaremos conectando una arquitectura terminada, no construyéndola mientras integramos el proveedor.

Componentes:
- Migración 0005: agregar campos de pago a `CommerceOrder`
  - `payment_status` (`sin_pago` / `iniciado` / `autorizado` / `pagado` / `fallido` / `devuelto`)
  - `payment_method` (`webpay` / `bank_transfer`)
  - `paid_at` (DateTimeField, null)
- `CommercePaymentTransaction` — registro de cada transacción (una por intento exitoso o fallido)
- `PaymentAttempt` — cada intento individual de pago (ver sección 11.3)
- Admin para ambos modelos
- Tests de modelo y transiciones de estado

### H1.2 — PaymentGateway interface + implementaciones
**Entregable:** Interfaz abstracta `PaymentGateway` con implementaciones para WebPay y transferencia. Sin vistas aún. Probada con mocks y contra sandbox de Transbank.

Componentes:
- `commerce/payments/gateway.py` — protocolo `PaymentGateway`
- `commerce/payments/result.py` — dataclasses `PaymentInitiation`, `PaymentResult`
- `commerce/payments/webpay.py` — `WebPayGateway` wrapping `transbank` SDK
- `commerce/payments/bank_transfer.py` — `BankTransferGateway` (flujo manual)
- `commerce/payments/factory.py` — resuelve gateway según `CommerceStorefrontSettings`
- Tests unitarios con mocks; test de integración contra sandbox TBK (aislado, no corre en CI normal)

### H2 — CommercePaymentService + Outbox
**Entregable:** El servicio que orquesta pago → evento. Las vistas del siguiente hito solo llaman al servicio; el servicio habla con el gateway y el outbox.

Flujo interno del servicio:
```
CommercePaymentService.initiate(order, gateway_key)
  → PaymentGateway.initiate()               ← I/O con proveedor
  → PaymentAttempt.create(status=initiated)
  → order.payment_status = "iniciado"
  → retorna redirect_url                    ← la vista solo redirige

CommercePaymentService.confirm(order, gateway_token)
  → PaymentGateway.confirm(gateway_token)   ← I/O con proveedor
  → PaymentAttempt.update(status=result)
  → si success:
      → order.payment_status = "pagado"
      → order.paid_at = now()
      → OutboxService.enqueue("commerce.order.paid")  ← ÚNICO punto de contacto con ERP
  → si failure:
      → order registra el intento fallido
      → sin evento (el ERP no sabe de intentos fallidos)
```

Componentes:
- `commerce/services/payment_service.py` — `CommercePaymentService`
- Tests del servicio con gateway mockeado

### H3 — Payment views (start, return, webhook)
**Entregable:** El flujo completo de pago funciona en integration (sandbox).

Componentes:
- `commerce/views/payment.py` — vistas `payment_start`, `payment_return`, `payment_cancel`
- URLs bajo `/storefront/<slug>/payment/`
- CSRF exempt en return (requiere POST de Transbank)
- Las vistas son deliberadamente delgadas: reciben request, llaman al servicio, redirigen

### H4 — CommercePaidConsumer (Runtime → ERP)
**Entregable:** Cuando el Runtime procesa `commerce.order.paid`, el Documento cambia a EMITIDO y el stock se descuenta. El Commerce no sabe nada de esto — solo emitió el evento.

Componentes:
- Contrato `commerce.order.paid` (schema + validación)
- `runtime/consumers/commerce_paid_consumer.py`
  - Idempotencia vía `ProcessedEvent`
  - Documento BORRADOR → EMITIDO
  - `MovimientoInventario` tipo OUT por cada línea (idempotente por `commerce_order_item_id`)
- Tests del consumer con fixtures ERP

### H5 — Ops panel + email + smoke test
**Entregable:** MonteAzul puede operar en producción.

Componentes:
- Panel de pedidos Commerce en ops (`/ops/pedidos/`)
- Email de confirmación al cliente (`commerce/emails/order_confirmation.html`)
- Email de notificación al taller (nueva venta)
- Smoke test completo: carrito → checkout → WebPay sandbox → Documento EMITIDO → stock decrementado

---

## 4. Checklist de migración completa

### Pre-producción
- [ ] H1.1 — `CommerceOrder` campos de pago — migración 0005 aplicada en clon
- [ ] H1.1 — `CommercePaymentTransaction` + `PaymentAttempt` con admin y tests
- [ ] H1.2 — `PaymentGateway` protocol + `WebPayGateway` + `BankTransferGateway` — tests con mocks
- [ ] H1.2 — Variables de entorno documentadas: `TBK_ENV`, `TBK_COMMERCE_CODE`, `TBK_API_KEY`, `TBK_RETURN_URL`
- [ ] H1.2 — Test de integración contra sandbox TBK (manual, no CI)
- [ ] H2 — `CommercePaymentService.initiate()` y `.confirm()` — emite `commerce.order.paid` via Outbox
- [ ] H2 — Verificar que service NUNCA importa modelos ERP directamente
- [ ] H3 — Flujo sandbox completo: carrito → checkout → WebPay → return → order_received
- [ ] H3 — Flujo transferencia bancaria: carrito → checkout → instrucciones → confirmación manual
- [ ] H4 — `CommercePaidConsumer`: Documento BORRADOR → EMITIDO — validado en clon
- [ ] H4 — `MovimientoInventario` OUT por cada línea — validado en clon
- [ ] H4 — Idempotencia: mismo evento dos veces no duplica Documento ni movimiento
- [ ] H5 — Email de confirmación: recibido en buzón real con datos correctos
- [ ] H5 — Panel ops: pedidos visibles, estado actualizable

### Infraestructura
- [ ] `transbank` SDK instalado en requirements.txt
- [ ] Variables `TBK_*` en `.env` de producción (nunca en código)
- [ ] TBK_COMMERCE_CODE de producción gestionado por MonteAzul (NO copiar el código de integración)
- [ ] `TBK_RETURN_URL` apunta al dominio real (`https://monteazul.cl/storefront/monteazul/payment/return/`)
- [ ] HTTPS obligatorio (Transbank rechaza HTTP)

### DNS Cutover (ver sección 5)
- [ ] Criterios de cutover cumplidos
- [ ] DNS propagado y verificado (`dig monteazul.cl`)
- [ ] Nginx configurado para el dominio
- [ ] WebPay en modo LIVE confirmado con primera transacción real

---

## 5. Criterio de "DNS Cutover Ready"

El dominio `monteazul.cl` no apunta a eGarage hasta que **todos** estos criterios estén verdes:

| Criterio | Cómo verificar |
|----------|----------------|
| WebPay en modo LIVE | `TBK_ENV=production` + transacción real de $1 confirmada |
| Flujo sandbox E2E sin errores 3 veces seguidas | Log de proceso_outbox sin FAILED |
| `OrderFulfillmentService` validado en clon | Documento generado + stock decrementado correcto |
| Email de confirmación funcional | Recibido en buzón MonteAzul con datos reales |
| Panel ops accesible | Pedido aparece y estado se puede cambiar |
| Migración 0005 aplicada en producción | `python manage.py showmigrations commerce` muestra [X] 0005 |
| `monteazul` importador corrido (catálogo 100%) | `commerce_seed --empresa monteazul --check` sin errores |
| HTTPS activo y redireccionando HTTP | `curl -I http://monteazul.cl` devuelve 301 a HTTPS |

---

## 6. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Transbank rechaza return URL no HTTPS | Alta | Bloqueante | Configurar SSL antes del primer test sandbox con dominio real |
| Token WebPay expira antes de commit (5 min) | Media | Alta | Medir latencia de los pasos; mostrar spinner; no pre-cargar pesado |
| Doble procesamiento del evento `commerce.order.paid` | Media | Alta | Idempotencia vía `ProcessedEvent` (ya implementado para `submitted`) |
| `select_for_update` ignorado en SQLite dev | Alta (dev) | Baja (prod) | Validar lock en PG antes del cutover (pendiente de audit task) |
| Stock descontado dos veces si retorno llega duplicado | Baja | Alta | `MovimientoInventario` with unique constraint en `commerce_order_item_id` |
| Credenciales TBK_API_KEY de producción expuestas | Baja | Crítica | Nunca en código; solo en `.env`; audit de secrets antes del cutover |
| TBK_COMMERCE_CODE de integración en producción | Media | Alta | Variable de entorno diferente por entorno; check en startup |

---

## 7. Dependencias

### Dependencias de código
```
H1 (modelo) → H2 (interfaz) → H3 (vistas) → H4 (fulfillment) → H5 (ops)
```
Son estrictamente secuenciales: cada hito construye sobre el anterior.

### Dependencias externas
- **Transbank SDK:** `pip install transbank-sdk` — necesario para H2
- **Credenciales producción:** MonteAzul debe proveer `TBK_COMMERCE_CODE` y `TBK_API_KEY` reales
- **Dominio:** `monteazul.cl` DNS en control de MonteAzul; coordinar cutover
- **HTTPS:** Certificado SSL activo antes de cualquier test con dominio real

### Dependencias de proceso
- El `process_outbox` management command debe correr como cron o daemon en producción
- Los events FAILED requieren monitoreo y reintento manual (no hay dead-letter automático aún)

---

## 8. ADRs relacionados

| ADR | Título | Relevancia |
|-----|--------|-----------|
| [ADR-000](architecture/ADR-000-platform-not-custom.md) | Plataforma, no desarrollo a medida | Cada decisión debe servir al segundo y décimo tenant, no solo a MonteAzul |
| ADR-001 (implícito en commerce_foundation_backlog.md) | CommerceCatalogGateway — vistas nunca importan ERP | Las payment views tampoco importan taller.models directamente |
| ADR-002 | Custom domains / Multi-tenant | El middleware resuelve `commerce_empresa` por dominio; los payments deben respetar el tenant |
| ADR-003 | Custom domain production architecture | Configuración Nginx para `monteazul.cl` |
| [ADR-004](architecture/ADR-004-payment-events-only.md) | Commerce ↔ ERP solo via eventos | PaymentGateway → Outbox → Runtime → ERP; nunca directo |
| ADR-005 (a crear) | Contrato `commerce.order.paid` — schema v1.0.0 | Evento que activa `CommercePaidConsumer` |
| ADR-006 (implícito) | PAID es la causa, Documento es la consecuencia | Separación: Commerce registra el pago, ERP ejecuta el fulfillment |
| ADR-007 (en runtime/) | Resolución de identidad — find-or-create por email | Aplica al `CommercePaidConsumer` igual que al `CommerceOrderConsumer` |

---

## 9. Tabla de progreso

| Hito | Descripción | Tareas | Completadas | % |
|------|-------------|--------|-------------|---|
| H1.1 ✅ | Dominio de pagos — modelos + estados + tests | 4 | 4 | 100% |
| H1.2 | PaymentGateway + implementaciones + sandbox | 5 | 0 | 0% |
| H2 | CommercePaymentService + Outbox | 4 | 0 | 0% |
| H3 | Payment views (start, return, cancel) | 4 | 0 | 0% |
| H4 | CommercePaidConsumer (Runtime → ERP) | 5 | 0 | 0% |
| H5 | Ops + email + smoke test | 4 | 0 | 0% |
| **Total** | | **26** | **4** | **15%** |

**H1.1 cerrado:** commit `81603ecc` — 2026-07-31  
Nota técnica: Django 4.2 incluye `{}` en `empty_values`; `raw_response` y `metadata` requieren `blank=True` para permitir dicts vacíos en `full_clean()`. Migración 0006 es metadata-only (sin schema change).

---

## 10. Auditoría de estado actual (2026-07-31)

### 10.1 Flujo WebPay de MonteAzul (fuente: /mnt/datos/projecto/monteazulspa)

El WebPay del proyecto MonteAzul original opera así:

```
GET /cart/webpay/start/<order_id>/
  → tx.create(buy_order, session_id, amount, return_url)  # Transbank SDK
  → guarda order.webpay_token
  → render webpay_redirect.html  (form auto-submit con token_ws)
  ↓
[Transbank]
  ↓
POST /cart/webpay/return/  (csrf_exempt)
  → tx.commit(token_ws)
  → si response_code==0 y status=="AUTHORIZED" → payment_success()
  → si no → render payment_fail.html
```

**Estado del Order en MonteAzul:**
- `DRAFT` → `PENDING_PAYMENT` (al iniciar) → `PAID` (en `payment_success`)
- Campos de trazabilidad: `webpay_token`, `webpay_status`, `webpay_authorization_code`, `webpay_response_code`, `webpay_payment_type`, `webpay_card_last4`

**Wrapper Transbank (`webpay.py`):**
```python
def webpay_tx() -> Transaction:
    env = IntegrationType.TEST if TBK_ENV == "integration" else IntegrationType.LIVE
    return Transaction(WebpayOptions(commerce_code, api_key, env))
```

### 10.2 Runtime actual

El runtime actual maneja un solo evento: `commerce.order.submitted`.

```
OrderService.create_from_cart()
  → CommerceOrder (PENDING)
  → OutboxEvent { event_type: "commerce.order.submitted" }
  
process_outbox (cron)
  → CommerceOrderConsumer.handle(event)
     → valida idempotencia (ProcessedEvent)
     → resuelve/crea Cliente guest
     → Documento PTS BORRADOR
     → DocumentSequence.next() [select_for_update]
     → LineaRepuesto × items
     → ProcessedEvent registrado
```

**Brecha crítica:** El evento `commerce.order.submitted` se emite cuando se crea el pedido, **antes de que se tome el pago**. El Documento PTS BORRADOR es correcto para este momento. Pero cuando el pago se confirme, se necesita un segundo evento (`commerce.order.paid`) que cambie el Documento a EMITIDO y descuente stock.

### 10.3 Modelo CommerceOrder actual

```python
class CommerceOrder(TenantScoped):
    order_number    # CharField, unique
    session_key     # para recuperar carrito
    status          # PENDING/CONFIRMED/PROCESSING/SHIPPED/DELIVERED/CANCELLED
    customer_name, customer_email, customer_phone
    shipping_address, notes
    total           # Decimal, congelado

    # FALTAN:
    # payment_status  — ciclo de vida del pago (sin_pago/pendiente/autorizado/pagado/fallido)
    # payment_method  — webpay / bank_transfer
    # payment_gateway_ref — token Transbank o referencia banco
    # paid_at         — timestamp de confirmación
```

El estado `status` refleja el ciclo logístico (PENDING → SHIPPED → DELIVERED), no el de pago. Son ortogonales y deben ser campos separados. Un pedido puede estar en PROCESSING logístico y PAID financiero al mismo tiempo.

### 10.4 Lógica de pagos duplicada — verificación

**ERP subscription payments (`taller/utils/payment_config.py`, `payment_views.py`):**
- Propósito: cobrar suscripciones SaaS (Flow, MercadoPago, PayPal, transferencia)
- Modelo: `SuscripcionTransaccion`
- Sujeto: `Empresa` (tenant que paga su plan mensual/anual)

**Commerce payments (a construir):**
- Propósito: cobrar pedidos e-commerce (WebPay, transferencia)
- Modelo: `CommercePaymentTransaction` (nuevo, aislado)
- Sujeto: `CommerceOrder` (cliente que compra un repuesto)

**Veredicto:** No hay duplicación porque sirven a dominios distintos. **No reutilizar** `SuscripcionTransaccion` ni `FlowHelper` para Commerce — eso violaría la boundary entre ERP y Commerce. Commerce necesita su propia implementación de pago.

---

## 11. Diseño de interfaz PaymentGateway

### 11.1 Principios

1. **Opaco al proveedor:** Las vistas y servicios de Commerce solo conocen `PaymentGateway`. Nunca importan `transbank` directamente.
2. **Inmutable en la frontera:** El método `initiate()` retorna una URL y un token; el `confirm()` retorna un `PaymentResult`. Sin side effects en el gateway.
3. **Side effects en el servicio:** `CommercePaymentService` es quien actualiza el modelo y emite eventos. El gateway es puro I/O con el proveedor externo.
4. **Configurable por tenant:** `CommerceStorefrontSettings` determina qué gateway usar. Hoy MonteAzul → WebPay. Mañana otro tenant → Stripe, MercadoPago.

### 11.2 PaymentAttempt — por qué es un modelo separado

Un `CommerceOrder` puede tener múltiples intentos de pago:

```
CommerceOrder (uno)
  └── PaymentAttempt (muchos)
        ├── Intento 1: WebPay — rechazado (tarjeta insuficiente)
        ├── Intento 2: WebPay — timeout
        └── Intento 3: WebPay — AUTHORIZED ✅
```

El pedido es uno. El pago confirmado es uno. Los intentos pueden ser muchos.

`PaymentAttempt` no es oro por ahora; es prevención de dolor en seis meses. Sirve para:
- **Auditoría:** saber exactamente qué pasó antes del pago exitoso
- **Soporte:** "el cliente dice que le cobró dos veces" → revisar intentos vs. autorizaciones
- **Fraude:** detectar patrones (mismo email, muchos intentos rechazados)
- **UX:** mostrar mensaje apropiado según el tipo de error
- **KPIs:** tasa de conversión de checkout, tasa de abandono por gateway

```python
# Propuesta de modelo

class PaymentAttempt(models.Model):
    """Registro inmutable de cada intento de pago. Nunca se modifica, solo se crea."""

    INITIATED = "initiated"
    AUTHORIZED = "authorized"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PENDING_VERIFICATION = "pending_verification"  # transferencia manual

    order = models.ForeignKey(CommerceOrder, on_delete=models.PROTECT, related_name="payment_attempts")
    gateway = models.CharField(max_length=30)          # "webpay" / "bank_transfer"
    gateway_token = models.CharField(max_length=255, blank=True, default="")
    gateway_ref = models.CharField(max_length=100, blank=True, default="")  # authorization_code
    status = models.CharField(max_length=30)
    amount = models.PositiveIntegerField()             # CLP, sin decimales
    raw_response = models.JSONField(default=dict)      # respuesta cruda del proveedor
    card_last4 = models.CharField(max_length=4, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Intento de pago"
        verbose_name_plural = "Intentos de pago"
```

`CommercePaymentTransaction` (renombrado a `PaymentAttempt`) reemplaza el concepto anterior. Es más honesto con lo que modela.

### 11.3 Interfaz propuesta

```python
# commerce/payments/gateway.py

from dataclasses import dataclass
from typing import Protocol


@dataclass
class PaymentInitiation:
    """Resultado de iniciar un pago."""
    redirect_url: str    # URL a la que redirigir al usuario
    gateway_token: str   # Token opaco del proveedor (guardar en CommerceOrder)


@dataclass
class PaymentResult:
    """Resultado de confirmar un pago."""
    success: bool
    gateway_ref: str          # Código de autorización o referencia
    raw_status: str           # Estado crudo devuelto por el proveedor
    amount_authorized: int    # Monto autorizado (entero CLP)
    card_last4: str = ""      # Últimos 4 dígitos (opcional)
    error_message: str = ""   # Solo si success=False


class PaymentGateway(Protocol):
    """
    Contrato mínimo para un proveedor de pagos de Commerce.

    Cada implementación (WebPay, BankTransfer, etc.) debe satisfacer
    este protocolo. Las vistas y servicios de Commerce solo dependen
    de este contrato, nunca del SDK concreto.
    """

    def initiate(
        self,
        order_number: str,
        amount: int,           # Monto en moneda entera (CLP: pesos, sin decimales)
        return_url: str,
        session_id: str = "",
    ) -> PaymentInitiation:
        """
        Inicia una transacción con el proveedor.
        Retorna la URL de redirección y el token para rastrear la transacción.
        No modifica ningún modelo — eso lo hace CommercePaymentService.
        """
        ...

    def confirm(self, gateway_token: str) -> PaymentResult:
        """
        Confirma (commit) una transacción iniciada.
        Transbank llama a esta etapa después de que el usuario autoriza.
        No modifica ningún modelo — eso lo hace CommercePaymentService.
        """
        ...
```

### 11.3 Implementación WebPay

```python
# commerce/payments/webpay.py

from transbank.common.integration_type import IntegrationType
from transbank.common.options import WebpayOptions
from transbank.webpay.webpay_plus.transaction import Transaction

from .gateway import PaymentGateway, PaymentInitiation, PaymentResult


class WebPayGateway:
    """
    WebPay Plus (Transbank) para Chile.
    Configurable vía settings: TBK_ENV, TBK_COMMERCE_CODE, TBK_API_KEY.
    """

    def __init__(self, commerce_code: str, api_key: str, live: bool = False):
        integration = IntegrationType.LIVE if live else IntegrationType.TEST
        self._tx = Transaction(WebpayOptions(commerce_code, api_key, integration))

    def initiate(self, order_number, amount, return_url, session_id="") -> PaymentInitiation:
        resp = self._tx.create(order_number, session_id or order_number, amount, return_url)
        return PaymentInitiation(
            redirect_url=resp["url"],
            gateway_token=resp["token"],
        )

    def confirm(self, gateway_token: str) -> PaymentResult:
        resp = self._tx.commit(gateway_token)
        response_code = resp.get("response_code")
        status = (resp.get("status") or "").upper()
        success = response_code == 0 and status in ("AUTHORIZED", "APPROVED")
        card = resp.get("card_detail") or {}
        card_num = card.get("card_number") or ""
        last4 = card_num[-4:] if len(card_num) >= 4 else ""
        return PaymentResult(
            success=success,
            gateway_ref=resp.get("authorization_code") or "",
            raw_status=status,
            amount_authorized=int(resp.get("amount") or 0),
            card_last4=last4,
            error_message="" if success else f"response_code={response_code}",
        )
```

### 11.4 Implementación BankTransfer

```python
# commerce/payments/bank_transfer.py

from .gateway import PaymentGateway, PaymentInitiation, PaymentResult


class BankTransferGateway:
    """
    Transferencia bancaria manual. No hay redirección externa.
    El 'confirm' solo marca el intento como pendiente-de-verificación manual.
    """

    def initiate(self, order_number, amount, return_url, session_id="") -> PaymentInitiation:
        # No hay URL externa; el return_url es la misma página de instrucciones.
        return PaymentInitiation(
            redirect_url=return_url,
            gateway_token=f"TRANSFER-{order_number}",
        )

    def confirm(self, gateway_token: str) -> PaymentResult:
        # No hay API que confirme; el pago queda pendiente de verificación manual.
        return PaymentResult(
            success=False,   # No es éxito automático
            gateway_ref=gateway_token,
            raw_status="PENDING_MANUAL_VERIFICATION",
            amount_authorized=0,
            error_message="Transferencia pendiente de verificación por el equipo de ventas.",
        )
```

### 11.5 Modelo CommercePaymentTransaction (propuesta)

```python
# En commerce/models/payment.py

class CommercePaymentTransaction(TenantScoped):
    """Log inmutable de cada intento de pago para un CommerceOrder."""

    INITIATED = "initiated"
    AUTHORIZED = "authorized"
    FAILED = "failed"
    PENDING_VERIFICATION = "pending_verification"  # solo transferencia

    order = models.ForeignKey(CommerceOrder, on_delete=models.PROTECT, related_name="payment_attempts")
    gateway = models.CharField(max_length=30)       # "webpay" / "bank_transfer"
    gateway_token = models.CharField(max_length=255, blank=True, default="")
    gateway_ref = models.CharField(max_length=100, blank=True, default="")
    status = models.CharField(max_length=30)
    amount = models.PositiveIntegerField()
    raw_response = models.JSONField(default=dict)
    card_last4 = models.CharField(max_length=4, blank=True, default="")
    initiated_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
```

### 11.6 Campos adicionales en CommerceOrder (migración 0005)

```python
# Agregar a CommerceOrder:

PAYMENT_PENDING = "sin_pago"
PAYMENT_INITIATED = "iniciado"
PAYMENT_AUTHORIZED = "autorizado"
PAYMENT_PAID = "pagado"
PAYMENT_FAILED = "fallido"
PAYMENT_REFUNDED = "devuelto"

PAYMENT_STATUS_CHOICES = [...]

payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="sin_pago")
payment_method = models.CharField(max_length=30, blank=True, default="")
payment_gateway_ref = models.CharField(max_length=100, blank=True, default="")
paid_at = models.DateTimeField(null=True, blank=True)
```

---

## 12. Flujo objetivo completo (post H5)

El principio que gobierna todo el flujo: **Commerce nunca llama al ERP. El ERP nunca llama a Commerce. Ambos hablan solo a través de eventos en el Outbox.**

```
VISITANTE
  │
  ▼
checkout_view (POST)
  → CheckoutForm válido
  → OrderService.create_from_cart()
     → CommerceOrder { status=PENDING, payment_status=sin_pago }
     → CommerceOrderItem × n
     → CartService.clear()
     → OutboxService.enqueue("commerce.order.submitted")
  │
  │   [paralelo — Runtime procesa el evento]
  │   process_outbox → CommerceOrderConsumer
  │     → Documento PTS BORRADOR (el ERP ya sabe que hay un pedido)
  │     → ProcessedEvent registrado
  │
  ▼
redirect → payment_select (GET)
  → usuario elige WebPay o Transferencia bancaria
  │
  ├─── RUTA WEBPAY ──────────────────────────────────────────
  │
  ▼
payment_start (POST, gateway=webpay)
  → CommercePaymentService.initiate(order, gateway="webpay")
     → factory resuelve WebPayGateway según CommerceStorefrontSettings
     → WebPayGateway.initiate(order_number, amount, return_url)  ← I/O Transbank
     → PaymentAttempt.create(status="initiated", gateway_token=...)
     → order.payment_status = "iniciado" ; order.payment_method = "webpay"
  ↓
redirect → Transbank URL (auto-submit form con token_ws)
  ↓
[usuario ve formulario Transbank, ingresa tarjeta]
  ↓
POST /storefront/<slug>/payment/return/  (csrf_exempt, Transbank redirige aquí)
  → token_ws = request.POST["token_ws"]
  → CommercePaymentService.confirm(order, token_ws)
     → WebPayGateway.confirm(token_ws)  ← I/O Transbank (commit)
     │
     ├─ si AUTHORIZED:
     │    → PaymentAttempt.update(status="authorized", gateway_ref=auth_code, ...)
     │    → order.payment_status = "pagado" ; order.paid_at = now()
     │    → OutboxService.enqueue("commerce.order.paid")
     │         │
     │         │   [Runtime procesa el evento]
     │         │   process_outbox → CommercePaidConsumer
     │         │     → Documento BORRADOR → EMITIDO
     │         │     → MovimientoInventario OUT × líneas
     │         │     → ProcessedEvent registrado
     │         │
     │    → redirect → order_received ✅
     │
     └─ si FAILED / CANCELLED:
          → PaymentAttempt.create(status="failed", error_message=...)
          → order.payment_status permanece "iniciado" (puede reintentar)
          → redirect → payment_select (puede elegir otro método o reintentar)
  │
  ├─── RUTA TRANSFERENCIA ────────────────────────────────────
  │
  ▼
payment_start (POST, gateway=bank_transfer)
  → CommercePaymentService.initiate(order, gateway="bank_transfer")
     → BankTransferGateway.initiate()  ← sin I/O externo
     → PaymentAttempt.create(status="pending_verification")
     → order.payment_status = "iniciado" ; order.payment_method = "bank_transfer"
  ↓
redirect → bank_transfer_instructions (GET)
  → datos bancarios del tenant desde CommerceStorefrontSettings
  → cliente transfiere y envía voucher por WhatsApp / email
  ↓
[ops verifica voucher en panel]
  → CommercePaymentService.mark_paid_manual(order, ops_user)
     → PaymentAttempt.update(status="authorized")
     → order.payment_status = "pagado" ; order.paid_at = now()
     → OutboxService.enqueue("commerce.order.paid")
          │
          │   [Runtime procesa el evento — mismo consumer que WebPay]
          │   CommercePaidConsumer → Documento EMITIDO + stock OUT
          │
     → notificación al cliente
```

**Lo que nunca aparece en este flujo:**
- `from taller.models import Documento` — en ninguna vista ni servicio de Commerce
- `from taller.models import MovimientoInventario` — ídem
- Llamada directa del `PaymentGateway` al ERP
- El ERP reaccionando a algo que no sea un evento del Outbox

---

*Documento vivo. Actualizar tabla de progreso (sección 9) al cerrar cada hito.*
