# Informe de Valoración de Mercado — eGarage

**Documento preparado para valoración por IA externa (Grok)**  
**Fecha:** Marzo 2025  
**Alcance:** Proyecto eGarage — Sistema de gestión para talleres mecánicos, casas de repuestos y centros de servicio automotriz.

---

## 1. Propuesta de Valor

eGarage es una **plataforma SaaS multi-país** que centraliza la operación de tres segmentos del mercado automotriz:

### 1.1 Talleres mecánicos
- **Problema que resuelve:** Desorden en órdenes de trabajo, presupuestos y facturación; pérdida de historial de clientes y vehículos; burocracia tributaria.
- **Solución:** Gestión unificada de **órdenes de trabajo (OT), presupuestos y facturas**; base de clientes y vehículos con historial; **exportación a formato SII (Chile)** para facturación; centro contable; recordatorios de mantenimiento y verificación de garantías por kilometraje.

### 1.2 Ventas de repuestos
- **Problema que resuelve:** Inventario disperso, precios desactualizados y falta de visibilidad para el cliente sin exponer márgenes.
- **Solución:** **Inventario por taller** (Repuesto, CategoriaRepuesto); **catálogo avanzado** (Part, PartI18N, PartPrice) con precios por empresa y vigencia; **marketplace opcional** (CasaRepuestos, ProductoCatalogo) para gestionar proveedores y referencias sin mostrar precios ni proveedores al cliente final.

### 1.3 Lavados y centros de servicio (detailing / estética)
- **Problema que resuelve:** Registro manual de servicios y dificultad para facturar y seguir clientes.
- **Solución:** Rubro **DETAILING** (“Lavado, detailing y estética”); catálogo de servicios (Service, ServiceI18N, ServicePrice) y servicios externos (terceros); mismos documentos (OT, presupuesto, factura) y flujo de clientes/vehículos que el resto del negocio.

**Mensaje de posicionamiento (Chile):** *“Gestiona servicios en segundos y genera archivos de facturación para el SII con un solo clic. Sin burocracia. Sin fricción. Prueba gratis 30 días.”*

---

## 2. Arquitectura Técnica

### 2.1 Stack
| Componente        | Tecnología                          |
|-------------------|-------------------------------------|
| Backend           | **Python 3.10+**, **Django 4.2** (&lt;5.0) |
| API               | Django REST Framework               |
| Base de datos     | **PostgreSQL** (producción) / SQLite (desarrollo) |
| Frontend          | Templates Django, Bootstrap 5 (Crispy), Autocomplete (django-autocomplete-light) |
| Estáticos         | WhiteNoise                          |
| OCR (patentes)    | EasyOCR + OpenCV                    |
| Autenticación     | django-allauth (email/teléfono, multi-país) |
| Monitoreo         | Sentry (opcional)                   |

### 2.2 Estructura de la base de datos (modelos principales)

- **Multi-tenant:** Toda la lógica de negocio está asociada a **Empresa** (tenant). Uso de `TenantScoped` y `TenantManager` (core) para aislamiento por empresa.

- **Clientes y vehículos:**
  - **Cliente:** empresa, nombre, apellido, teléfono, dirección, región/ciudad (Chile), estado/ciudad (USA), email, RUT/tax_id, giro; datos de facturación y auditoría.
  - **Vehiculo:** empresa, cliente (FK), marca/modelo (catálogo o texto), patente, año, color, VIN, motor, caja, millas; relación con documentos.
  - **CatalogoModeloAuto:** catálogo global marca-modelo (multi-tenant compartido).

- **Documentos (núcleo operativo):**
  - **Documento:** tipo (OT, PRES, FAC), número, estado (BORRADOR/EMITIDO/ANULADO), cliente, vehículo, técnico responsable, netos por concepto (repuestos, servicios, otros), descuento, impuestos, total, moneda, país.
  - **LineaRepuesto / LineaServicio / LineaOtroServicio:** líneas por documento.
  - **DetalleDocumento:** ítems genéricos (REPUESTO/SERVICIO/OTRO) para compatibilidad.

- **Inventario y catálogo:**
  - **Repuesto / CategoriaRepuesto:** por empresa; part_number, nombre, precios, stock, proveedor.
  - **Part, PartI18N, PartPrice:** catálogo global de repuestos con I18N y precios por empresa y vigencia.
  - **TaxPolicy:** impuestos por país/estado/ciudad para repuestos y/o servicios (Chile 19%, USA sales tax, etc.).

- **Servicios:**
  - **Service, ServiceI18N, ServicePrice:** catálogo de servicios con precios por empresa.
  - **ServicioBase, CategoriaServicio, SubcategoriaServicio:** estructura global.
  - **ServicioExterno:** servicios de terceros (costo taller / precio cliente).

- **Empresa y comercial:**
  - **Empresa:** usuario, nombre_taller, país (CL/US/MX), moneda, **plan** (trial, basic, premium, enterprise), fechas trial/suscripción, zona horaria, logo, dirección, teléfono, email.
  - **PrecioSuscripcion:** por país y tipo (mensual/semestral/anual); precio, moneda, características (documentos ilimitados, usuarios, soporte, reportes, diagnóstico IA, API, multisucursal).

### 2.3 Escalabilidad del código
- **Aislamiento por tenant:** consultas filtradas por `empresa`; managers con `for_company`, `for_request`, `for_tenant`.
- **Modularidad:** apps separadas (`taller`, `documentos`, `ubicacion`, `marketplace`, `whatsapp`, `core`) y submódulos por dominio (clientes, vehículos, repuestos, reportes, analytics, API).
- **Internacionalización:** rutas por país e idioma (`/cl/es/`, `/us/en/`, `/mx/es/`, etc.); traducciones y políticas fiscales por país.
- **API REST:** endpoints versionados (`/api/v1/`) para integraciones externas y posible uso móvil.

---

## 3. Diferenciación Única

### 3.1 Mercado de convertidores catalíticos y metales preciosos
- El producto está **preparado para** integrar el nicho de **convertidores catalíticos** y **metales preciosos** (Rhodium, Platinum, Palladium):
  - **Rubro EXHAUST:** “Taller de escapes y mufflers” (Chile) / “Exhaust & Muffler Shop” (USA).
  - **Catálogo de servicios:** “Revisión del sistema de escape y catalizador”, “Reparación de sistema de escape (flexibles, catalizador)” y servicios afines en scripts y categorías.
  - **Estructura de desarme:** existe un stub de rutas (`desarme/`) y assets (kanban) para un futuro módulo de desarmaduría; la base de repuestos (Part/categorías) y documentos permite extender hacia **cotización y trazabilidad de catalíticos** sin cambiar el núcleo.
- **Conclusión para valoración:** La diferenciación se plantea como **potencial de producto**: el catálogo de repuestos de escape, el rubro especializado y la futura rama de desarme permiten posicionar eGarage en talleres que compran/venden catalíticos o recicladores, con un posible módulo de **precios de chatarra electrónica/catalíticos** como extensión o integración externa.

### 3.2 Conexión con el catálogo de repuestos de escape
- **Part** y **PartPrice** permiten un catálogo por categoría (incluida escape/silenciadores).
- **Marketplace (CasaRepuestos, ProductoCatalogo):** gestión de proveedores y productos con `part_number` y precio de referencia, sin exponer esta información al cliente; adecuado para casas de repuestos de escape que trabajan con talleres.

---

## 4. Funcionalidades Core

| Módulo / Área              | Funcionalidad                                                                 |
|----------------------------|-------------------------------------------------------------------------------|
| **Gestión de órdenes**     | Creación/edición de OT, presupuestos y facturas; líneas repuesto/servicio/otro; estados (borrador/emitido/anulado); secuencia de numeración por tipo. |
| **Documentos**             | Export PDF, envío por email y WhatsApp; vista de impresión; APIs internas de búsqueda de repuestos, servicios y vehículos por cliente. |
| **Facturación SII (Chile)**| Exportación **CSV para SII** por documento; validación previa de datos de facturación del cliente (RUT, giro, dirección); completar datos desde el flujo de exportación; utilidades para validación masiva (`validar_documentos_para_exportacion_sii`, `generar_csv_sii_validado`). |
| **Búsqueda de precios**    | APIs de repuestos por código y búsqueda; catálogo Part con precios por empresa; **no hay en el código actual** un módulo específico de “precios de chatarra electrónica” ni de “precios de catalíticos en tiempo real”; la base de datos y APIs permiten añadirlo. |
| **Reportes y analíticas**  | Centro contable Chile; diagnóstico IA; recordatorios de mantenimiento (por kilometraje); verificación de garantía (km recorridos desde OT anterior); reportes por mecánico; exportación PDF/Excel. |
| **API REST (v1)**         | Clientes (listar, buscar, info, verificar/completar facturación, crear onboarding); vehículos por cliente y crear; repuestos (by-code, buscar, crear); servicios y otros servicios; modelos/motores/cajas; métricas operativas; **procesar foto de patente** (OCR). |
| **Portal y trial**         | Registro trial 30 días; activación de trial; registro por país con selección de plan; flujos de pago por país (Chile, USA, México, etc.). |

---

## 5. Potencial de Monetización (Modelo SaaS)

### 5.1 Modelo de planes
- **Planes:** Trial (prueba gratuita), Basic, Premium, Enterprise.
- **Suscripción:** mensual, semestral y anual; precios por **país** (CL, US, MX y otros según configuración).
- **PrecioSuscripcion:** tabla de precios activos por país y tipo de plan (mensual/semestral/anual), con moneda coherente (CLP, USD, MXN).

### 5.2 Características por plan (según modelo)
- Documentos ilimitados, cantidad de usuarios incluidos, soporte prioritario, reportes avanzados, diagnóstico IA, API incluida, multisucursal (tipicamente en planes superiores).
- Trial: 30 días de acceso completo antes de elegir plan de pago.

### 5.3 Flujos de pago por mercado
- **Chile:** transferencia/voucher; subida de comprobante; referencia de pago (ej. `eGarage-{empresa_id}-{plan}`).
- **USA:** PayPal u otro gateway; `item_name` / `item_number` por plan.
- **México:** flujo específico con template de pago (MXN).

### 5.4 Administración de suscripciones
- Dashboard de suscripciones (por empresa o global para staff); extensión de vigencia vía AJAX; recordatorios de vencimiento (comando `enviar_recordatorios`); estado de suscripción (activa, por vencer, vencida) y bloqueo de acceso cuando corresponda.

### 5.5 Indicadores para valoración
- **Recurrencia:** ingresos mensuales o anuales por suscripción.
- **Multi-país:** mismo producto con precios y monedas localizadas (CL, US, MX, y expansión a otros países de LATAM).
- **Upsell:** trial → básico → premium → enterprise; semestral/anual con posible descuento implícito.
- **Extensibilidad:** módulo de catalíticos/metales o de precios de chatarra como add-on o plan superior podría aumentar ARPU en un segmento específico.

---

## Resumen Ejecutivo para Valoración (Grok)

- **Qué es:** SaaS de gestión operativa y comercial para talleres mecánicos, casas de repuestos y centros de lavado/detailing, con foco multi-país (Chile, USA, México y otros).
- **Propuesta de valor:** Un solo sistema para órdenes de trabajo, presupuestos, facturación (incl. export SII Chile), inventario, catálogo de repuestos y servicios, y reportes (centro contable, IA, recordatorios, garantías).
- **Diferenciación:** Base preparada para el nicho de **escapistas y catalíticos** (rubro EXHAUST, servicios de escape/catalizador, stub de desarme); potencial de módulo de precios de catalíticos/metales preciosos y conexión con catálogo de repuestos de escape.
- **Stack:** Django 4.2, PostgreSQL, API REST, multi-tenant, I18N por país.
- **Monetización:** Suscripción mensual/semestral/anual por país; planes trial → basic → premium → enterprise; flujos de pago localizados (transferencia, PayPal, etc.).

*Documento generado a partir del análisis del código del proyecto eGarage. Para detalles de implementación, consultar el repositorio y los modelos/vistas referenciados.*
