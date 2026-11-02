# Production Checklist

Purpose: prepare eGarage for real onboarding and payment tests without adding new product complexity.

## Environment

- `DJANGO_DEBUG=False`.
- `DJANGO_SECRET_KEY` set to a strong secret outside the repository.
- `DJANGO_ALLOWED_HOSTS` includes every production domain.
- `DJANGO_CSRF_TRUSTED_ORIGINS` includes the HTTPS origins used by the app and payment callbacks.
- Database credentials are configured through environment variables or the production platform secret store.
- Email credentials are configured through environment variables, including `RESEND_API_KEY` or the active provider key.
- No real payment or email secret is committed in settings, docs, templates or logs.

## HTTPS and Django Security

- HTTPS is enforced at the load balancer/proxy.
- `SECURE_SSL_REDIRECT=True` once the proxy headers are confirmed.
- `SECURE_PROXY_SSL_HEADER` matches the proxy configuration.
- `SESSION_COOKIE_SECURE=True`.
- `CSRF_COOKIE_SECURE=True`.
- `CSRF_COOKIE_HTTPONLY` and cookie SameSite policies are reviewed for the login/payment flow.
- `ALLOWED_HOSTS` does not contain wildcard hosts in production.
- CSRF trusted origins include protocol and domain.
- Rate limiting is enabled for login, signup, password reset, payment start and webhook endpoints.

## PayPal Live

- Live business email/client configuration is present.
- Sandbox endpoints are not used in production.
- IPN/webhook URL points to the public HTTPS production domain.
- Return and cancel URLs point to production.
- A real payment test confirms the `custom` reference is received.
- Logs do not include full payloads with sensitive payer details beyond what is needed for audit.

## Flow Live

- `FLOW_ENABLED=True` only after live credentials are loaded.
- `FLOW_API_URL` points to the live Flow API, not sandbox.
- `FLOW_API_KEY` and `FLOW_SECRET_KEY` are present in the environment.
- Return URL and confirmation URL are public HTTPS URLs.
- A live low-value payment test confirms pending, success and rejected states.
- Unknown Flow tokens are logged without exposing customer-sensitive data.

## Mercado Pago Live

- `MP_ENABLED=True` only after live credentials are loaded.
- Live access token/public key are set through environment variables.
- Success, failure, pending and webhook URLs use the public HTTPS production domain.
- Country routing is validated before exposing Mercado Pago as a primary CTA outside the supported country.
- A live low-value payment test confirms approved and rejected states.

## Bank Transfer

- Bank account data is complete by country.
- Confirmation email inbox is monitored during business hours.
- Reference format is visible in payment pages and emails.
- Manual activation SLA is communicated as 24-48 business hours.
- Internal approval process records who approved each payment.

## Email

- From domain is verified.
- SPF is configured.
- DKIM is configured.
- DMARC is configured at least in monitoring mode.
- Password reset, welcome, trial, expiration, payment confirmation and renewal emails are tested on mobile.
- Subjects are short, clear and non-threatening.

## Cron and Background Jobs

- Subscription expiration checks are scheduled and monitored.
- Trial expiration warnings are scheduled and monitored.
- Renewal/payment reconciliation jobs are scheduled if used.
- Failed jobs emit alerts.
- Job logs avoid sensitive payment payloads.

## Observability

- Structured application logs are enabled.
- Error monitoring is configured, preferably Sentry or equivalent.
- Payment webhook exceptions alert the team.
- Signup, trial and payment conversion events are logged through `taller.services.conversion_events`.
- Dashboards separate operational errors from expected payment failures.

## Backups and Recovery

- Database backups run automatically.
- Backup restore is tested before launch.
- Media/file uploads for comprobantes are backed up or stored durably.
- Rollback plan exists for settings-only and template-only releases.
- Payment provider credentials can be rotated quickly.

## Pre-Launch Smoke Tests

- Signup started.
- Signup completed.
- Trial activated without card.
- Entry monthly payment.
- Entry annual payment.
- Growth monthly payment.
- Business annual payment.
- Chile Flow.
- Chile bank transfer.
- Mexico Mercado Pago.
- Mexico PayPal.
- Mexico bank transfer.
- USA PayPal.
- USA bank transfer.
- Grace notice.
- Blocked notice.
- Renewal success.
