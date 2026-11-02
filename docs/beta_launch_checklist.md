# Beta Launch Checklist

Goal: start real onboarding and payment tests with low operational risk. Do not add new features until these checks pass.

## Manual Flow Tests

- Create a new Trial account from the public signup.
- Confirm Trial starts with 30 days, no card request and one user.
- Create Entry monthly.
- Create Entry annual.
- Create Growth monthly and confirm the "Más popular" badge is visible.
- Create Business annual.
- Confirm annual savings copy is visible but not noisy.
- Confirm signup error states for duplicate email and invalid phone.
- Confirm signup success redirect and first dashboard load.
- Confirm suspension page shows modern plans only.
- Confirm renewal page CTA goes to a valid payment path.

## Payment Tests

- Chile: Flow start, return and webhook in sandbox.
- Chile: bank transfer upload with valid file.
- Chile: bank transfer upload with missing file.
- Mexico: Mercado Pago sandbox approval.
- Mexico: Mercado Pago sandbox rejection.
- Mexico: PayPal sandbox/manual reference flow.
- Mexico: bank transfer instructions and confirmation email.
- USA: PayPal sandbox approval.
- USA: PayPal cancel return.
- USA: bank transfer fallback.
- Double callback test for Flow.
- Double callback test for Mercado Pago.
- Double webhook test for PayPal sale id.
- Timeout/provider unavailable test for each gateway.

## Mobile QA

- 360px wide signup.
- 390px wide signup.
- 360px payment Chile.
- 360px payment Mexico.
- 360px payment USA.
- Suspension page on mobile.
- Subscription banner on mobile in info, warning, grace and blocked levels.
- Email preview on a narrow mobile client.

## Domains and URLs

- Production domain points to the correct app.
- HTTPS certificate is active.
- `ALLOWED_HOSTS` contains only expected hosts.
- `CSRF_TRUSTED_ORIGINS` includes the production HTTPS origins.
- PayPal return/cancel/webhook URLs point to production.
- Flow return/confirmation URLs point to production.
- Mercado Pago success/failure/pending/webhook URLs point to production.

## Email

- From address uses the verified sending domain.
- SPF configured.
- DKIM configured.
- DMARC configured.
- Welcome email received.
- Trial expiration email received.
- Subscription confirmed email received.
- Renewal success email received.
- Payment failure/cancel messaging is clear and calm.

## Backups and Rollback

- Database backup completed before beta.
- Restore procedure tested in a staging or local environment.
- Media/comprobante storage backup confirmed.
- Rollback plan documented for template-only release.
- Rollback plan documented for settings-only release.
- Payment provider credentials can be disabled quickly.

## Monitoring and Support

- Error monitoring enabled.
- Payment webhook errors alert the team.
- Signup errors alert or appear in logs.
- Logs include conversion events from `taller.services.conversion_events`.
- Support inbox monitored during beta.
- WhatsApp/support channel prepared with short answer templates.
- Internal owner assigned for manual payment approvals.

## Metrics To Watch

- Signup started.
- Signup completed.
- Trial activated.
- Trial to paid conversion.
- Payment success.
- Payment failed.
- Renewal success.
- Payment method selected by country.
- Time to manual activation.
- Support tickets per beta account.
- Churn/cancel reason.

## Beta Go/No-Go

Go only if:

- Signup works on mobile and desktop.
- Trial activation works without card.
- At least one payment method per target country works end to end.
- Subscription banner is visible but not disruptive before expiration.
- Duplicate callbacks do not extend subscriptions twice.
- Support can manually recover a payment or account issue.

No-go if:

- Signup template fails to load.
- A payment button leads to a dead route.
- Any visible page shows old public plan names.
- Provider callbacks point to sandbox in production.
- No recent database backup exists.
