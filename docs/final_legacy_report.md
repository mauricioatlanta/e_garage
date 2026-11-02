# Final Legacy Billing Report

Goal: keep legacy compatibility during rollout while making modern plan codes the internal default for new payment and subscription flows.

## Remaining Legacy Classes

| Class | Examples | Status | Remove later? |
| --- | --- | --- | --- |
| Visible legacy | `templates/suspension/precios.html`, historical `templates/account/signup.html`, some country onboarding pricing copies | Highest cleanup priority because users may see divergent UI or old plan semantics. | Yes, after route audit confirms replacements. |
| Internal compatibility | Plan mappings in `plan_catalog.py`, form/view normalization accepting `basic`, `premium`, `enterprise`, `mensual`, `semestral`, `anual` | Required for rollback and old URLs/data. | Yes, after data migration and monitoring window. |
| Model/default legacy | Model choices/defaults in subscription-related models and migrations | Safe to keep temporarily; changing choices/defaults may require migration. | Requires schema/data migration plan. |
| Admin/operator legacy | Admin filters, analytics templates, management commands, business health scripts | Not usually visible to customers but can confuse operations. | Yes, after production data uses modern codes. |
| Historical docs/imports | `_loose_import`, valuation docs, old examples | Harmless but noisy. | Archive or update when billing migration is complete. |

## What Is Safe To Remove After Route Audit

- Public templates that are no longer referenced by URL patterns or views.
- Duplicate pricing cards once all active signup/onboarding/payment pages use `templates/includes/pricing_plan_card.html`.
- Legacy visible labels in help content, if the help center is regenerated or manually edited.

## What Requires Data Migration

- Existing `Empresa.plan` values using `basic`, `premium`, `enterprise`, `mensual`, `semestral` or `anual`.
- Existing `SuscripcionTransaccion.plan_code` rows with legacy plan codes.
- Existing `SuscripcionTransaccion.billing_cycle` rows with `mensual`, `semestral` or `anual`.
- Any reporting tables or denormalized analytics that group by legacy plan codes.

## What Requires Schema Migration

- Model choices/defaults that still name `basic`, `premium`, `enterprise` or period-style plans as plan codes.
- Defaults such as `plan_code="basic"` or `billing_cycle="mensual"` if they remain at model level.
- Any constraints that only allow legacy codes.

## What May Require Downtime

Downtime should not be needed if the cleanup is split into additive migrations, background backfill and compatibility removal. A short maintenance window may be useful only if a strict DB constraint is introduced at the same time old values are removed.

## Production Cleanup Strategy

1. Keep normalization and legacy acceptance during real payment tests.
2. Log new conversion and payment events with modern plan codes.
3. Backfill data from legacy to modern codes in a reversible data migration.
4. Update admin/reporting to modern names after backfill.
5. Remove visible legacy templates and route aliases.
6. Remove internal compatibility only after monitoring confirms no legacy writes for a full billing cycle.

## Current Recommendation

Do not remove legacy compatibility before production payment tests. The immediate priority is to prove onboarding, trial activation, payment confirmation, grace notices and renewal work end to end with modern visible UX.
