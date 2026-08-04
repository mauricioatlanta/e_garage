# ADR-000 — Plataforma, no desarrollo a medida

**Estado:** ACEPTADO  
**Fecha:** 2026-07-31  
**Autor:** Mauricio Alvarado  
**Categoría:** Meta-decisión — aplica a todas las demás ADRs

---

## Contexto

MonteAzul SpA es el primer tenant real del Commerce Engine de eGarage. Existe la tentación natural de construir exactamente lo que MonteAzul necesita, porque es el cliente concreto que tenemos hoy.

Esa tentación produce código acoplado, datos hardcodeados, flujos que asumen "Chile", "WebPay", "CLP" y "repuestos de escape". Funciona para MonteAzul. Falla para el segundo cliente.

## Decisión

**MonteAzul no es un desarrollo a medida. Es la validación del producto.**

Cada línea de código escrita durante la migración de MonteAzul debe responder esta pregunta antes de ser mergeada:

> ¿Servirá igual para el segundo, tercero y décimo suscriptor del perfil CASA_REPUESTOS?

Si la respuesta es "no" o "solo si cambiamos el código", la implementación tiene un defecto de plataforma.

## Consecuencias concretas

**Configuración, no código:**  
Lo que varía entre tenants va en `CommerceStorefrontSettings` o en variables de entorno del tenant. Nunca en el código fuente.

**Gateway como plugin:**  
WebPay es la implementación de Chile. El protocolo `PaymentGateway` es la plataforma. Un tenant en Argentina usa `MercadoPagoGateway` implementando el mismo protocolo. Las vistas no cambian.

**Dominio como configuración:**  
`monteazul.cl` resuelve al tenant MonteAzul porque el middleware lo mapea. `repuestosGarcia.cl` resolvería al tenant García. Cero código nuevo.

**Templates sin nombres de marca:**  
Los templates de Commerce no dicen "MonteAzul". Dicen `{{ brand.name }}`. El logo viene de `brand.logo_url`. El color viene de `brand.accent_color`.

**Datos de negocio en BD, no en código:**  
Los datos bancarios para transferencia, el número de WhatsApp, las FAQs, el mensaje de garantías — todo va en `CommerceStorefrontSettings` o en tablas configurables. No en templates hardcodeados.

## Lo que SÍ puede ser específico de MonteAzul

El **importador** `commerce/importers/monteazul.py` es específico. Importa el catálogo histórico de MonteAzul desde su estructura de BD propia. Eso no necesita ser genérico — cada tenant tendrá su propio proceso de onboarding o importador.

Los **fixtures de datos** de MonteAzul (logo, paleta, URLs) son específicos. Los campos que los almacenan son genéricos.

## Regla de revisión

En cada PR de Commerce, además del diff de código, revisar:

1. ¿Hay algún string con "MonteAzul" fuera de fixtures/importadores?
2. ¿Hay algún hardcode de "CL", "CLP", "WebPay" fuera del gateway y la configuración del tenant?
3. ¿Hay alguna vista que asuma un único tenant?

Si alguna respuesta es "sí", el PR necesita corrección antes del merge.

## Relación con otras ADRs

Este ADR es el "por qué" detrás de todas las demás decisiones de arquitectura. ADR-001 (Gateway), ADR-002 (custom domains), ADR-004 (payment events) — todos son consecuencias de esta decisión fundacional.

Si una nueva ADR contradice este principio, la nueva ADR es incorrecta.
