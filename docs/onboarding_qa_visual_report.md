# Onboarding and Payment UX QA Report

Scope: static audit of signup, onboarding, pricing, renewal, suspension, payment and billing emails for Chile, Mexico and USA. This report uses descriptions instead of screenshots because no browser session was launched in this pass.

## Findings

| File | Area | Severity | Description | Proposed fix |
| --- | --- | --- | --- | --- |
| `templates/auth/signup.html` | Main signup | Low | Uses the reusable pricing card include and modern plan names. A small JS compatibility map still accepts legacy `semestral`. | Keep for rollback until data migration. Remove after legacy plan values are no longer accepted from URLs/forms. |
| `templates/account/signup.html` | Historical signup | High | Template still loads `widget_tweaks`; loading it failed in the previous template smoke test if the tag library is not installed. It also has its own pricing markup. | Confirm route usage. Retire or replace with `templates/auth/signup.html`; if still active, add dependency or remove `widget_tweaks` usage. |
| `templates/*/es/account/signup.html` | Country signup variants | Medium | Multiple country-specific copies still define their own cards and plan selection UI. Copy is mostly modern, but visual divergence can return. | Move country variants to the reusable `includes/pricing_plan_card.html` or route all countries through the central signup. |
| `templates/*/es/onboarding/bienvenida.html` | Onboarding | Medium | Hardcoded pricing/savings copy appears in several country files. Some sections use wide glass tables that may overflow on mobile. | Replace pricing blocks with catalog-fed partials and test 360px mobile width. |
| `templates/suspension/precios.html` | Renewal/pricing | High | Legacy visual logic remains (`premium-card`, `plan_key == 'premium'`, `semestral`). This is the highest risk visible legacy template. | Replace with the modern plan include or redirect users to the modern renewal/payment route. |
| `templates/suspension/suspension.html` | Suspension | Low | Public copy uses Entry/Growth/Business and a non-aggressive tone. Banner/action density is acceptable. | Verify mobile spacing with real data and long bank strings. |
| `templates/cl/es/suscripcion/pago.html` | Chile payment | Low | Flow and bank transfer are visible. MercadoPago and PayPal are not shown, matching country rules. Copy needed clearer activation timing. | Done: added Flow as fastest option and clarified bank transfer activation in 24-48 business hours. |
| `templates/mx/es/suscripcion/pago.html` | Mexico payment | Medium | Mercado Pago and PayPal availability were shown as plain alerts, while transfer was the only actionable path. This can confuse users. | Done: changed to explicit method cards and transfer instructions. Add real MP/PayPal buttons only when backend routes are country-correct. |
| `templates/us/en/suscripcion/pago.html` | USA payment | Low | PayPal action is present; bank transfer fallback is clear but activation timing was not explicit. | Done: added simple PayPal note and 24-48 business hour manual activation copy. |
| `templates/base.html` | Subscription banner | Low | Banner is subtle and non-modal. Blocked state uses stronger color, as intended. | QA with mobile and long translated messages before launch. |
| `templates/emails/*.html` | Email UX | Low | Billing emails use modern names through mappings and soft language. Base email is responsive and clean. | Keep subjects short; avoid adding urgent wording except blocked/expired flows. |
| `templates/analytics/*`, `templates/admin*` | Internal/admin | Low | Legacy names remain in admin/analytics filters and labels. Not part of public onboarding, but can confuse operators. | Document as internal legacy and update after data migration. |

## Payment Method Matrix

| Country | Expected | Current visible state |
| --- | --- | --- |
| Chile | Flow, bank transfer. No MercadoPago. No PayPal unless catalog enables it. | Matches current visible payment template. |
| Mexico | MercadoPago, PayPal, bank transfer. No Flow. | Shows all three as methods; only transfer is fully actionable in this template. Backend country-specific online checkout should be completed before making MP/PayPal primary CTAs. |
| USA | PayPal, bank transfer. No Flow. No MercadoPago. | Matches current visible payment template. |
| Default | PayPal, bank transfer. | Needs route-by-route verification outside CL/MX/US. |

## Manual QA Checklist

- Signup mobile: 360px width, annual/monthly selector, Trial/Entry/Growth/Business cards, no text overflow.
- Signup desktop: 1280px width, pricing cards aligned, one primary CTA per card.
- Onboarding: country-specific welcome pages do not show old plan names.
- Payment Chile: Flow CTA works when enabled; transfer upload remains available.
- Payment Mexico: method copy is clear; no Flow shown; no broken online-payment button.
- Payment USA: PayPal posts correct `custom` reference; bank transfer fallback is visible.
- Suspension: banner and renewal CTA are visible without blocking non-critical actions before expiration.
- Emails: preview on mobile width; CTA visible above the fold; no legacy visible plan names.
