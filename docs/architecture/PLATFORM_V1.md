# eGarage Platform — Estado al hito commerce-engine-v1.0

**Fecha:** 2026-08-01  
**Tag de referencia:** `commerce-engine-v1.0`  
**Rama de origen:** `feature/commerce-paid-consumer`

Este documento no es una ADR. Es una foto del sistema en el momento en que eGarage deja de ser exclusivamente un ERP y pasa a ser una plataforma con múltiples motores. Sirve como referencia para decisiones futuras.

---

## La plataforma

```
                    eGarage Platform
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
     ERP Engine      Commerce Engine     Brand Engine
        │                  │                  │
        └──────────────┬───┴──────────────────┘
                       │
               Suscriptor (Tenant)
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   Taller         Desarmaduría   Casa Repuestos
                       │
                 Storefront propio
                       │
            Dominio propio (opcional)
```

El **tenant** no es un tipo de negocio — es un nivel de orquestación. Activa los motores que necesita, no los que le fueron hardcodeados.

---

## Motores existentes

| Motor | Ubicación | Propósito |
|---|---|---|
| **ERP Engine** | `taller/` | Documentos, clientes, vehículos, técnicos, inventario, impuestos, suscripción |
| **Commerce Engine** | `commerce/` | Catálogo, storefront, carrito, pedidos, pagos |
| **Brand Engine** | `commerce/services/admin/brand_service.py` · `CommerceStorefrontSettings` | Identidad visual del tenant (logo, paleta, dominio) |
| **Import Engine** | `commerce/services/catalog/importer.py` | Importación de catálogos externos vía SQLite; extensible con adapters |
| **Media Engine** | `commerce/services/catalog/media_resolver.py` · `image_index.py` | Resolución y auditoría de imágenes del catálogo |
| **Contract Runtime** | `runtime/` | Ejecución de contratos de pago entre ERP y Commerce |

---

## Principios no negociables

**1. Multi-tenant por construcción**  
Todo modelo que pertenece a un suscriptor tiene `empresa = ForeignKey("Empresa")`. Las queries siempre filtran por empresa. No existen vistas cruzadas de tenants. Ver `taller/utils/query_scopes.py`.

**2. Capas separadas — nunca ORM directo en vistas**  
```
View → Service → ORM
```
Las vistas reciben request, llaman al servicio correspondiente, renderizan. El ORM vive exclusivamente en los servicios. Las vistas nunca hacen `.filter()`, `.get()` ni `.save()` directamente.

**3. Adapters para variaciones de cliente, no ramas del motor**  
El `CatalogImporter` es el motor genérico. `MonteAzulAdapter` es el adapter específico de un cliente. El segundo cliente crea su propio adapter extendiendo el motor — sin tocar el motor.

**4. ERP → Commerce solo vía contratos**  
ERP y Commerce son dominios separados. El ERP no importa modelos de Commerce ni al revés. La comunicación ocurre únicamente a través del Contract Runtime. Ver ADR-004.

**5. Configuración, no código**  
Lo que varía entre tenants va en `CommerceStorefrontSettings` o en variables de entorno del tenant. Nunca en código fuente. Ver ADR-000.

---

## Regla de priorización — Suscriptor First

A partir de `commerce-engine-v1.0`, ninguna funcionalidad nueva entra al proyecto si no responde afirmativamente a esta pregunta:

> **¿El suscriptor puede hacer su trabajo más rápido, con menos errores o con menos complejidad gracias a este cambio?**

Las mejoras técnicas que no habilitan una capacidad planificada concreta no tienen prioridad. La arquitectura interna ya alcanzó suficiencia para soportar el crecimiento planificado.

---

## Qué pertenece al núcleo vs. qué va en adapters o módulos

**Núcleo (cambia con precaución, afecta a todos los tenants):**
- Modelo `Empresa` y su cycle de vida
- Sistema de documentos (Cotización, OT, Boleta)
- Motor de impuestos (`taller/impuestos/engine.py`)
- Sistema de suscripción y planes
- Contract Runtime
- Gateway de pagos (el protocolo; no las implementaciones específicas)

**Adapters o módulos (pueden variar por tenant o cliente):**
- Importadores de catálogo (`commerce/services/catalog/adapters/`)
- Gateways de pago específicos por país (WebPay, MercadoPago, PayPal)
- Dominios personalizados por tenant
- Templates de storefront (el tenant configura; la plataforma renderiza)

**Lo que NUNCA entra al núcleo:**
- Lógica específica de un cliente o marca (MonteAzul, Atlanta, etc.)
- Hardcodes de país, moneda o método de pago
- URLs que asuman un único tenant

---

## Roadmap desde este hito

| Fase | Foco | Criterio de entrada |
|---|---|---|
| **7 — Commerce UX** | Editor de categorías, productos, imágenes, SEO, CMS | El administrador del suscriptor opera el catálogo sin fricción |
| **8 — Commerce Business** | Pedidos, clientes, promociones, cupones, reportes | El suscriptor puede vender y medir |
| **9 — Integración ERP** | ERP → Commerce → Marketplace → Canales | MonteAzul pasa a ser un canal, no un caso especial |

---

## Referencias

- `docs/architecture/ADR-000-platform-not-custom.md` — por qué plataforma y no desarrollo a medida  
- `docs/architecture/ADR-004-payment-events-only.md` — por qué los pagos van solo como eventos  
- `docs/architecture/VERTICAL_ARCHITECTURE_V1.md` — arquitectura de los tres productos ERP  
- `CLAUDE.md` — comandos, multi-tenant, estructura de apps (fuente de verdad técnica)
