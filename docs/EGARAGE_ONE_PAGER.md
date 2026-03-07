# eGarage — One-Pager

**Pitch:** *"Deja de perder clientes en hojas de cálculo: eGarage pone en un solo lugar clientes, vehículos, cotizaciones y reportes para que tu taller facture más y trabaje menos."*

---

## 1. Problema principal (dolor del taller)

- **Desorden operativo:** Clientes y vehículos en Excel, WhatsApp o papel; no hay un solo lugar de verdad.
- **Pérdida de tiempo:** Buscar historial, armar cotizaciones y órdenes de trabajo a mano.
- **Poca visibilidad:** No se sabe qué se vendió, qué repuestos faltan ni cómo va el mes sin juntar varios archivos.
- **Comunicación fragmentada:** Presupuestos y documentos por WhatsApp/email sin trazabilidad ni formato profesional.

---

## 2. Cliente ideal

- **Tipo:** Taller mecánico o de autos pequeño/mediano (1–15 empleados).
- **Rol:** Dueño o administrador que toma decisiones de compra.
- **País/mercado:** Chile (principal), USA, Argentina, Uruguay, México, Colombia, Ecuador, Perú, Venezuela, Brasil (rutas e idioma ya soportados).
- **Dolor:** Usa Excel, cuadernos o software caro/complejo; quiere algo simple, en la nube y que no dependa de un solo PC.

---

## 3. Propuesta de valor (por qué eGarage es distinto)

- **Todo en uno:** Clientes, vehículos, documentos (OT, presupuesto, factura) y reportes en una sola plataforma multi-país.
- **Listo por país:** Moneda, idioma y flujos por país (CL, US, AR, UY, etc.) sin instalar nada.
- **Enfoque en el flujo real:** Crear documento → agregar líneas (repuestos/servicios) → emitir → PDF/WhatsApp; reportes por mecánico, por fecha, kilometraje y rentabilidad.
- **Pensado para el día a día:** Autocomplete de clientes/vehículos, portal del cliente (historial por token), recordatorios de kilometraje y opción de envío por WhatsApp.

---

## 4. Features esenciales (máximo 10)

1. **Gestión de clientes** — Alta, edición, búsqueda; región/ciudad/estado según país.
2. **Gestión de vehículos** — Vinculados a cliente; marca/modelo/motor/caja; catálogo por país (incl. USA).
3. **Documentos (OT / Presupuesto / Factura)** — Crear, editar, borrador/emitido/anulado; líneas repuesto/servicio/otro; totales e impuestos por país.
4. **Repuestos** — Catálogo por taller, búsqueda en documento, lista y exportación Excel.
5. **Servicios** — Catálogo (categorías/subcategorías), servicios externos; uso en documentos.
6. **Reportes** — Dashboard, centro contable, por mecánico, por fecha, repuestos/servicios, kilometraje (recordatorios, historial, garantía), rentabilidad.
7. **Portal del cliente** — Acceso por token/link; historial de documentos por vehículo; descarga PDF.
8. **Suscripción y trial** — Trial 30 días; planes básico/premium/empresarial; bloqueo por vencimiento; comprobante de pago.
9. **Multi-país e idioma** — Rutas `/cl/`, `/us/`, `/ar/`, etc.; español/inglés según país; moneda y timezone por empresa.
10. **Branding y configuración** — Nombre del taller, ajustes, técnicos; centro de operaciones (dashboard unificado).

---

## 5. Modelo de precios sugerido (3 planes)

| Plan        | Público objetivo        | Precio sugerido (referencia CLP) | Incluye |
|------------|-------------------------|-----------------------------------|---------|
| **Básico** | 1–2 usuarios, hasta 50 clientes | ~$15.000–20.000/mes              | Clientes, vehículos, documentos, reportes básicos, 1 usuario |
| **Premium**| 3–8 usuarios, crecimiento       | ~$25.000–40.000/mes              | Todo Básico + reportes por mecánico, kilometraje, portal cliente, más usuarios |
| **Empresarial** | Múltiples sedes / equipos | ~$45.000–70.000/mes          | Todo Premium + soporte prioritario, más almacenamiento, integraciones (ej. WhatsApp) |

- **Trial:** 30 días gratis; un trial por empresa (flag `ha_usado_prueba`).
- **Pago:** Por ahora manual (comprobante + activación); después integrar pasarela.

---

## 6. Diferenciadores reales vs Excel/otros

- **Vs Excel:** Un solo lugar en la nube; multi-usuario; documentos numerados y con estado; reportes en tiempo real; no se pierde el archivo.
- **Vs software de escritorio:** Acceso desde cualquier dispositivo; actualizaciones automáticas; no depende de un solo PC.
- **Vs soluciones genéricas:** Flujo pensado para taller (cliente → vehículo → documento → repuestos/servicios); catálogos de vehículos y servicios por país; portal para que el cliente vea su historial.
- **Real en el código:** Multi-tenant por empresa, filtro por `empresa` en listados; documentos con estados BORRADOR/EMITIDO/ANULADO; reportes por mecánico, fecha, kilometraje y rentabilidad; exportación PDF y enlace WhatsApp.

---

## 7. Roadmap 90 días (solo lo crítico)

- **Días 1–30:** Estabilizar flujo core en 1 país (Chile): registro → login → clientes → vehículos → crear/editar documento → emitir → PDF; fijar onboarding 60 min y métricas de uso.
- **Días 31–60:** Pagos: pasarela o proceso claro de “pago + activación” para planes de pago; emails/post-pago (confirmación, recordatorio vencimiento).
- **Días 61–90:** Primeras ventas validadas: 5–10 talleres pagando; retención semanal >60%; iterar según feedback (qué usan más: documentos, reportes, portal).

---

## 8. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Talleres no pagan después del trial | Oferta fundador clara (precio y límites); onboarding obligatorio; seguimiento por WhatsApp en día 7 y 14. |
| Complejidad percibida (demasiadas pantallas) | Un solo flujo “feliz”: Cliente → Vehículo → Documento; ocultar o simplificar reportes avanzados en planes básicos. |
| Dependencia de un solo país (Chile) | Mantener USA/AR/UY operativos; priorizar documentación y precios por país. |
| Bugs en producción que bloquean uso | Health checks (`/health/`); monitoreo de errores 5xx; rollback rápido y comunicación por WhatsApp. |
| Baja retención (no vuelven a entrar) | Métricas semanales (logins, documentos creados); recordatorios por email/WhatsApp; mejorar “primer valor” en el primer uso. |

---

*Documento generado a partir del análisis del repositorio eGarage. Actualizar precios y roadmap según decisión de producto.*
