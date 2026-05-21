# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

eGarage is a multi-tenant SaaS platform for auto workshop management (talleres mecánicos) targeting Latin America (Chile, Mexico, USA, Argentina, Uruguay, Brazil, Peru, Venezuela). Each workshop is an `Empresa` tenant with isolated data.

## Commands

### Development server
```bash
python manage.py runserver
```

### Database migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Python tests (pytest-django)
```bash
pytest                                        # all tests
pytest taller/tests/test_documento_calculos.py  # single file
pytest -m "not slow"                          # skip slow tests
pytest -k "empresa"                           # filter by name
```

### E2E tests (Playwright)
```bash
npm test                          # all Playwright tests
npm run test:desktop              # Desktop Chrome only
npm run test:headed               # with browser UI
npm run test:report               # show last report
```

### Environment setup
```bash
cp env.example .env               # configure secrets
source venv/bin/activate
pip install -r requirements.txt
```

## Settings Architecture

There are **three parallel settings hierarchies** — use the right one:

| Module path | Used for |
|---|---|
| `gestion_taller.settings` (package `__init__.py`) | Default — pytest, `manage.py runserver`, production |
| `gestion_taller.settings.dev` | Development with PostgreSQL or email testing |
| `gestion_taller.settings.prod` | Production deploy (reads env vars strictly) |
| `gestion_taller/settings.py` | Legacy root-level file (kept for PythonAnywhere compatibility) |
| `gestion_taller/compacto/settings.py` | Slim variant for compacto sub-project |

`pytest.ini` sets `DJANGO_SETTINGS_MODULE = gestion_taller.settings` (the package).

## Multi-Tenant Architecture

Every model that belongs to a workshop has an `empresa = ForeignKey("Empresa")`. The `Empresa` model is the tenant boundary.

**Tenant isolation in queries** — always use `ScopeManager` or `scoped_qs()`:
- `taller/utils/query_scopes.py` — `scoped_qs(qs, request)` filters by `request.user.empresa`
- `ScopeManager` — base manager that subclasses override on tenant models
- Views must never return cross-tenant data; always filter by `empresa`

Standard fixture pattern in tests (`taller/tests/conftest.py`):
```python
empresa_chile(db, test_user)   # Empresa pais="CL"
empresa_usa(db)                # Empresa pais="US"
empresa_peru(db)               # Empresa pais="PE"
```

## Multi-Country Support

Countries: `CL`, `US`, `MX`, `AR`, `UY`, `BR`, `PE`, `VE`.

- **URL namespaces per country**: `cl/documentos/`, `us/documentos/`, `uy/documentos/`, `ar/documentos/` — all map to the same `taller.documentos.urls` but under different namespaces.
- **Country-specific URL files**: `taller/urls_extra/chile.py`, `usa.py`, `argentina.py`, etc.
- **Tax engine** (`taller/impuestos/engine.py`): `resolve_tax_rate(empresa, city, 'parts'|'services')` — Chile taxes only parts (IVA 19%), Peru taxes both (IGV 18%), USA uses state/city `TaxPolicy`.
- **Context processors** in `taller/context_processors/` inject country config, UI labels, and branding per tenant.
- **Payment gateways by country** (`taller/utils/plan_catalog.py`): Flow (CL), MercadoPago (MX/AR), PayPal (US).

## Core App Structure

### `taller/` — main business app
- `models/` — split by domain: `empresa.py`, `documento.py`, `vehiculos.py`, `cliente.py`, `tecnico.py`, `suscripcion.py`, etc.
- `documentos/` — sub-app for cotizaciones and órdenes de trabajo; has its own `models.py`, `views_*.py`, `services/`, `urls.py`
- `vehiculos/`, `clientes/`, `repuestos/` — sub-apps with their own URLs and views
- `impuestos/engine.py` — tax calculation, never import directly from templates
- `context_processors/` — per-feature processors registered in `TEMPLATES` settings
- `utils/plan_catalog.py` — plan names (`PLAN_TRIAL`, `PLAN_ENTRY`, `PLAN_GROWTH`, `PLAN_BUSINESS`) and payment method routing

### `gestion_taller/` — Django project config
- `urls.py` — root URL conf (`ROOT_URLCONF`)
- `settings/` — settings package (base/dev/prod)
- `compacto/` — alternate slim configuration variant
- `resend_backend.py` — custom email backend using Resend API

### Other apps
- `marketplace/` — marketplace listing features + WhatsApp integration
- `ubicacion/` — location models (Address, Estado, Ciudad) used for sales tax lookups
- `whatsapp/` — WhatsApp webhook and messaging
- `frontend/` — standalone React app (Create React App); built separately, not integrated into Django static pipeline

## Document System

`taller/documentos/` handles financial documents (cotizaciones, órdenes de trabajo):
- `models.py` / `taller/models/documento.py` — `Documento` model
- `taller/documentos/lineas_documento.py` / `DetalleDocumento` — line items with `tipo_item` choices: `REPUESTO`, `SERVICIO`, `OTRO`
- Subtotals are calculated automatically on save; `subtotal` field is `editable=False`
- `document_sequence.py` — sequence/numbering logic; race-condition-sensitive, see BAK files for history
- PDF export via Weasyprint: requires `libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0` on Linux

## Subscription / SaaS

Plans: `trial → entry → growth → business` (legacy aliases: `basic`, `premium`, `enterprise`).  
Billing: `monthly` or `annual`.  
`taller/models/suscripcion.py`, `suscripcion_transaccion.py` — subscription lifecycle.  
`taller/models/trial.py` — trial period logic.

## Tailwind CSS

Config in root `tailwind.config.js` scans `templates/**/*.html` and `static/js/**/*.js`. Custom fonts: Orbitron, Poppins. Extended colors: cyan, fuchsia, lime.
