# Arquitectura de eGarage

## Resumen de propósito
Sistema multi-tenant para talleres y casas de repuestos, operando en Chile (CLP, IVA 19%) y USA (USD, sales tax). Permite gestión de documentos, inventario, clientes y dashboards.

## Estructura de apps Django
- Apps principales: taller, clientes, vehiculos, repuestos, servicios, configuracion, dashboards.
- settings.py: configuración multi-tenant, internacionalización, bases de datos, rutas de apps.
- Middleware: autenticación, auditoría, selección de empresa/tenant, localización.
- Context processors: info de empresa, usuario, branding, flags de features.

## Integraciones externas
- Email (SMTP, notificaciones)
- Storage (archivos/documentos, S3/local)
- Pagos (si aplica, integración pendiente)

## Entradas principales
- urls.py raíz: rutas a login, dashboard, documentos, configuración, etc.
- Views: CBV y FBV para CRUD de entidades y flujos principales.
- Templates base: `base.html`, `dashboard_base.html`, `documento_base.html`.
- Assets: estáticos en `/static/`, media en `/media/`.

## Especificidad Chile/USA
- Chile: CLP, IVA 19%, formato RUT, boletas/facturas.
- USA: USD, sales tax variable, formato EIN, invoices.

## Diagrama ASCII de flujo alto nivel

```
[Login]
   |
   v
[Selección Empresa/Tenant]
   |
   v
[Dashboard Principal]
   |
   v
[Documentos] <-> [Clientes] <-> [Vehículos]
   |
   v
[Configuración Empresa]
   |
   v
[Dashboards/KPIs]
```
