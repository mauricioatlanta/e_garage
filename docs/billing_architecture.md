# Billing Architecture

## Current Architecture

`taller/utils/plan_catalog.py` is the source of truth for modern plan codes, billing periods, prices, payment-method availability, and legacy mappings.

Modern internal plan codes:

- `trial`
- `entry`
- `growth`
- `business`

Modern billing periods:

- `monthly`
- `annual`

Legacy values are still accepted for compatibility and normalized at the boundary:

- Plans: `basic -> entry`, `premium -> growth`, `enterprise -> business`
- Period-style plans: `mensual -> entry/monthly`, `semestral -> growth/annual`, `anual -> business/annual`

No migrations were added in this phase.

## Visual Source Of Truth

The reusable visual include is:

- `templates/includes/pricing_plan_card.html`

It accepts:

- `plan`
- `pricing`
- `billing_cycle`
- `country`
- `payment_methods`
- `highlight`
- `cta_url`

It is currently wired into the main signup template `templates/auth/signup.html`. Historical country-specific signup/onboarding templates were cleaned to remove visible legacy names, but they are not fully collapsed into the include yet. That is intentionally staged to preserve rollback and avoid breaking active onboarding variants.

## Payment Flow

Payment entry points use `plan_catalog.py` through `payment_views.py`:

- Chile: Flow and bank transfer
- Mexico: MercadoPago, PayPal, and bank transfer
- USA: PayPal and bank transfer
- Default: PayPal and bank transfer

Gateway transaction creation goes through `SuscripcionTransaccionService.create_gateway_transaction`, which normalizes:

- `plan_code` to `trial/entry/growth/business`
- `billing_cycle` to `monthly/annual`
- `months_paid` via the catalog billing cycle

Approval paths call `approve_transaction`, then update:

- `Empresa.plan`
- `Empresa.valor_mensual`
- `Empresa.fecha_fin` through `Empresa.extender_suscripcion`

## Expiration Flow

Expiration and access rules remain owned by existing services and middleware:

- `Empresa.fecha_fin`
- `Empresa.fecha_expiracion`
- `Empresa.debe_bloquear`
- `SubscriptionAccessService`
- subscription middleware

This phase did not change critical access logic.

The soft UI notice is provided by:

- `taller/context_processors/subscription_notice.py`

It returns:

```python
subscription_notice = {
    "show": bool,
    "level": "info" | "warning" | "grace" | "blocked",
    "days_left": int | None,
    "message": str,
    "renew_url": str,
}
```

The banner is rendered in `templates/base.html`.

## Trial Flow

Trial eligibility is centralized in:

- `taller/services/trial_service.py`

Main helper:

```python
can_start_trial(empresa, user)
```

The helper is intentionally soft:

- no credit card requirement
- no aggressive blocking without identity
- checks `trial_already_used`
- checks `ha_usado_prueba`
- checks active/current trial
- checks prior companies with the same email or phone

It is used by:

- `RegistrationService`
- `signup_complete`

## Legacy Compatibility

Legacy compatibility is still required because several models, admin surfaces, old templates, tests, and scripts still reference old values.

Safe temporary legacy references:

| Area | Examples | Reason | Remove later |
| --- | --- | --- | --- |
| `plan_catalog.py` | `LEGACY_PLAN_MAPPING`, `LEGACY_BILLING_MAPPING` | Compatibility adapter | No, until data migration |
| Model choices | `Empresa.PLAN_CHOICES`, `SuscripcionTransaccion.BILLING_CYCLE_CHOICES` | DB compatibility without migrations | Yes, after migration |
| Tests | `taller/tests/*`, `tests/unit/*` | Need test update after full migration | Yes |
| Tools/scripts | `tools/*`, `scripts/*`, `_loose_import/*` | Historical/manual ops | Yes, or archive |

Potentially dangerous remaining references:

| File | Reason | Recommendation |
| --- | --- | --- |
| `taller/models/empresa.py` | `marcar_pago_recibido(plan=...)` accepts raw plan | Normalize plan at method boundary in a follow-up |
| `taller/models/suscripcion.py` | Legacy `tipo` choices and Flow price constants | Replace with catalog-backed adapter after migration plan |
| `taller/models/suscripcion_transaccion.py` | Defaults still `basic`/`mensual` | Requires migration or compatibility-safe model default change |
| `taller/admin.py` | Admin actions extend subscriptions without plan context | Add explicit modern plan selection before production admin use |
| `taller/views_extra/views_suscripciones.py` | Legacy UI dictionaries remain internally | Consolidate behind catalog view-model |
| `templates/suspension/precios.html` | Legacy pricing UI still exists outside the focused templates | Replace or retire route |
| `templates/analytics/*` | Admin-visible old labels and filters | Update admin analytics labels before external admin rollout |

## Production Readiness Audit

Settings:

- `gestion_taller/settings.py`
- `gestion_taller/settings/__init__.py`
- `gestion_taller/settings/base.py`
- `gestion_taller/settings_prod.py`

Hardening applied:

- Removed the hardcoded real Resend API key from default settings.
- Kept secrets environment-driven via `RESEND_API_KEY`, `DJANGO_SECRET_KEY`, and email settings.
- Context processor registered in all active settings entry points.

Gateway readiness:

- PayPal business email comes from `PAYPAL_BUSINESS_EMAIL`, falling back to support email.
- Flow requires `FLOW_ENABLED`, `FLOW_API_KEY`, `FLOW_SECRET_KEY`, and `FLOW_API_URL`.
- MercadoPago requires `MP_ENABLED` and `MP_ACCESS_TOKEN`.
- Callback URLs should be verified per deployment domain before production traffic.

Risks:

- Some helper scripts and older settings fragments still contain debug prints or operational assumptions.
- PayPal webhook signature verification is still marked TODO.
- Some email paths use `fail_silently=True`; that is acceptable for signup UX but should be observable in production logs.
- Several admin and analytics templates still show legacy labels outside the focused public signup/onboarding/payment surfaces.

## Manual Flow Checklist

Use a staging environment with test gateway credentials.

| Flow | Expected |
| --- | --- |
| Trial nuevo | `Empresa.plan=trial`, `fecha_fin` +30 days, notice hidden until <=7 days |
| Entry mensual | `Empresa.plan=entry`, `billing_cycle=monthly`, `months_paid=1` |
| Entry anual | `Empresa.plan=entry`, `billing_cycle=annual`, `months_paid=12` |
| Growth mensual | `Empresa.plan=growth`, `billing_cycle=monthly`, `months_paid=1` |
| Business anual | `Empresa.plan=business`, `billing_cycle=annual`, `months_paid=12` |
| Transferencia bancaria | Creates pending legacy payment, synced transaction stores modern plan |
| PayPal | Webhook stores modern plan and billing, no visible legacy names |
| MercadoPago | Preference and webhook resolve modern transaction |
| Flow | Order and webhook resolve modern transaction |
| Grace period | Banner `grace`, access behavior unchanged |
| Blocked | Banner `blocked`, access behavior owned by `SubscriptionAccessService` |
| Renovación exitosa | Extends from future `fecha_fin` when active, sends confirmation email |

## Future Cleanup Strategy

1. Add tests that assert modern plan and billing codes for every payment route.
2. Update model defaults from legacy values after a planned migration.
3. Consolidate all country-specific signup/onboarding templates into the pricing include.
4. Replace `Suscripcion.tipo` legacy choices with a catalog-backed compatibility layer.
5. Add PayPal webhook signature verification.
6. Add production monitoring for gateway callback failures and silent email failures.
