# eGarage — Lista de módulos actuales (auditoría rápida)

Inventario generado a partir del análisis del proyecto eGarage.

---

## Apps Django

- [x] **gestion_taller** — Proyecto raíz; parche SSL PostgreSQL, config base.
- [x] **taller** — App principal: modelos (Empresa, Cliente, Vehiculo, Documento, etc.), vistas, URLs por país, reportes, documentos, clientes, vehículos, repuestos, servicios, tecnicos, portal, analytics, autocomplete.
- [x] **taller.whatsapp** — Notificaciones admin y click-to-WhatsApp (WhatsAppAdminNotificationLog).
- [x] **ubicacion** — Estados/ciudades (API multi-país bajo `/api/`).
- [x] **allauth** — Cuentas (login, signup, password reset).
- [x] **dal / dal_select2** — Autocomplete (Django Autocomplete Light).
- [ ] **marketplace** — Condicional (`EGARAGE_ENABLE_MARKETPLACE`); no obligatorio para MVP.

---

## URLs principales por país

- [x] **Chile** — `/cl/` → `/cl/es/` (bienvenida, dashboard, clientes, vehiculos, documentos, reportes, repuestos, servicios, config, centro-operaciones, precios, trial).
- [x] **USA** — `/us/` con `en/` y `es/` (usa `taller.urls_extra.usa`).
- [x] **Argentina** — `/ar/`, `/ar/es/` (try/except en `gestion_taller/urls.py`).
- [x] **Uruguay** — `/uy/`, `/uy/es/` (uruguay).
- [x] **Perú** — `/pe/es/` (peru).
- [x] **Colombia** — `/co/es/` (colombia).
- [x] **Ecuador** — `/ec/es/` (ecuador).
- [x] **Venezuela** — `/ve/es/` (venezuela).
- [x] **México** — `/mx/es/` (mexico).
- [x] **Brasil** — `/br/` (pt, brasil).
- [x] **Global** — `/` (selección país), `/accounts/login/`, `/accounts/signup/`, `/registro-trial/`, `/activar-trial/`, `/portal/`, `/health/`, `/api/v1/`, `/analytics/`.

---

## Modelos clave y propósito

| Modelo | App / ubicación | Propósito |
|--------|------------------|------------|
| Empresa | taller.models.empresa | Taller: nombre, país, moneda, timezone, plan (trial/basic/premium/enterprise), suscripción, branding. |
| Cliente | taller.models.clientes | Cliente del taller (tenant-scoped); datos de contacto, región/ciudad. |
| Vehiculo | taller.models.vehiculos | Vehículo vinculado a cliente; marca, modelo, motor, caja, kilometraje. |
| Documento | taller.models.documento | OT / Presupuesto / Factura; cliente, vehículo, técnico, estado (BORRADOR/EMITIDO/ANULADO), totales, impuestos. |
| DetalleDocumento / Lineas | documentos.models, taller.models.lineas_documento | Líneas de documento: repuesto, servicio, otro; subtotales. |
| Repuesto | taller.models.repuesto | Catálogo de repuestos por empresa. |
| Servicio / CategoriaServicio / SubcategoriaServicio | taller.servicios.models | Catálogo de servicios por taller. |
| Tecnico | taller.models.tecnico | Técnico/mecánico asignable a documentos. |
| Suscripcion | taller.models.suscripcion | Trial/mensual/semestral/anual; fechas y activa. |
| ComprobantePago / PagoPendiente | taller.models | Comprobantes para renovar suscripción. |
| ClienteToken / ClienteCredencial | taller.portal.models | Acceso portal cliente (token/link). |
| KilometrajeRegistro | taller.models.kilometraje | Registro de km para recordatorios y garantía. |
| Marca / Modelo (USA) | taller.models.marca, marcas_usa | Catálogo vehículos (MarcaVehiculo, ModeloVehiculo para USA). |
| Estado / Ciudad | taller.models.ubicacion | Ubicación (regiones/ciudades por país). |

---

## Flujos completos existentes (desde login hasta documento/reportes)

- [x] **Login** — `/accounts/login/` o `/cl/accounts/login/`, `country_aware_login`; redirect por país (`/cl/es/`, `/us/en/`, etc.).
- [x] **Signup** — `/accounts/signup/` (CustomSignupView); redirects `/cl/signup/`, `/us/signup/`, etc. con `?from=cl`.
- [x] **Registro trial** — `/registro-trial/`, `/activar-trial/`; Suscripcion 30 días; `ha_usado_prueba` en Empresa.
- [x] **Post-login** — Middleware Empresa, VerificarSuscripcion; redirect a bienvenida/dashboard del país.
- [x] **Clientes** — Lista, crear, editar, ver, eliminar; AJAX ciudades/regiones; autocomplete (DAL) en documentos.
- [x] **Vehículos** — Lista, crear, editar, ver, eliminar; APIs marca/modelo (jerárquico); vinculados a cliente.
- [x] **Documentos** — Lista (DocumentoListView), crear (DocumentoCreateView), editar (MigratedUpdateView), ver, eliminar; estados BORRADOR/EMITIDO/ANULADO; líneas repuesto/servicio; exportar PDF, enviar WhatsApp; APIs buscar repuestos/servicios.
- [x] **Reportes** — Dashboard, centro contable Chile, repuestos/servicios, por mecánico (PDF/WhatsApp), por fecha, kilometraje (recordatorios, historial, garantía), rentabilidad (si import OK).
- [x] **Portal cliente** — `/portal/`: login por token; historial; historial por vehículo; exportar PDF.
- [x] **Configuración** — Centro de ajustes (company_settings), configuración empresa, técnicos; branding.
- [x] **Precios / suscripción bloqueada** — Vista precios por país; suscripción bloqueada cuando `empresa.debe_bloquear`; subir comprobante.

---

## Lo que falta para vender un MVP real (priorizado)

### Crítico (bloquea venta o uso diario)

- [ ] **Cobro recurrente o proceso claro de pago** — Hoy: comprobante manual; falta pasarela o flujo “pago → activación” documentado y estable.
- [ ] **Onboarding guiado** — Primera vez: “crear 1 cliente, 1 vehículo, 1 documento” en <10 min; mensajes o checklist en app.
- [ ] **Estabilidad en un solo país** — Elegir Chile (o uno) y asegurar: cero 500 en flujo cliente→documento→PDF; mensajes de error claros.
- [ ] **Límites por plan** — Ej. Básico: N clientes o N documentos/mes; bloquear o avisar cuando se exceda (hoy no hay enforcement claro en código).

### Importante (mejora conversión o retención)

- [ ] **Email post-registro y recordatorio trial** — Confirmación de cuenta; recordatorio a los 7 y 21 días de trial.
- [ ] **Métricas mínimas** — Logins por semana, documentos creados por taller; dashboard interno o script para “talleres activos”.
- [ ] **Página de precios pública** — `/cl/es/precios/` existe; verificar que muestre planes y CTA (WhatsApp/contacto) de forma clara.
- [ ] **Documentación “cómo hacer la primera cotización”** — Video o PDF para dueño de taller.

### Deseable (post-MVP)

- [ ] **Más países** — Ya hay rutas; falta validar datos (impuestos, formatos) por país.
- [ ] **WhatsApp integrado (envío automático)** — Hoy hay enlace/click-to-WhatsApp; integración API WhatsApp Business sería siguiente paso.
- [ ] **App móvil o PWA** — Acceso web responsive ya existe; PWA podría mejorar uso en celular.

---

*Checklist listo para priorizar sprints y cerrar gaps antes de vender el primer plan de pago.*
