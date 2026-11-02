// @ts-check
const { test, expect } = require('@playwright/test');

test('gateway CTA posts public analytics event before navigation', async ({ page }) => {
  let eventPayload = null;

  await page.route('**/analytics/public/event/', async (route) => {
    const request = route.request();
    if (request.method() === 'POST') {
      eventPayload = request.postDataJSON();
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ ok: true, created: true, event_id: 1 }),
    });
  });

  await page.goto('/');

  const trialCta = page.getByText(/Prueba gratis/i).first();
  const gatewayCta = page.getByLabel('eGarage Chile').first();
  const target = (await trialCta.count()) > 0 ? trialCta : gatewayCta;

  await Promise.all([
    page.waitForRequest((request) => (
      request.method() === 'POST' &&
      request.url().includes('/analytics/public/event/')
    )),
    target.click(),
  ]);

  expect(eventPayload).toMatchObject({
    event_type: 'cta_click',
    path: '/',
  });
  expect(eventPayload.dedupe_key).toBeTruthy();
  expect(eventPayload.metadata).toMatchObject({
    cta_id: expect.any(String),
    href: expect.any(String),
  });
});
