// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Configuración de Playwright para pruebas E2E de egarage.cl
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  testDir: './tests/e2e',
  /* Ejecutar tests en paralelo */
  fullyParallel: true,
  /* Fallar el build si accidentalmente dejaste test.only en el código fuente */
  forbidOnly: !!process.env.CI,
  /* Reintentar en CI solo */
  retries: process.env.CI ? 2 : 0,
  /* Opcional: Limitar workers en CI */
  workers: process.env.CI ? 1 : undefined,
  /* Configuración del reporter */
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
    ['json', { outputFile: 'test-results.json' }]
  ],
  /* Configuración compartida para todos los proyectos */
  use: {
    /* URL base para usar en navegación */
    baseURL: 'https://egarage.cl',
    /* Recopilar trace cuando se repite un test fallido */
    trace: 'on-first-retry',
    /* Capturar screenshot solo cuando falla */
    screenshot: 'only-on-failure',
    /* Capturar video solo cuando falla */
    video: 'retain-on-failure',
    /* Timeout para acciones */
    actionTimeout: 15000,
    /* Timeout para navegación */
    navigationTimeout: 30000,
  },

  /* Configurar proyectos para diferentes navegadores y viewports */
  projects: [
    {
      name: 'Desktop Chrome',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
      },
    },
    {
      name: 'Mobile iPhone 12',
      use: { 
        ...devices['iPhone 12'],
      },
    },
  ],

  /* Ejecutar el servidor de desarrollo local antes de iniciar las pruebas */
  // webServer: {
  //   command: 'npm run start',
  //   url: 'http://127.0.0.1:3000',
  //   reuseExistingServer: !process.env.CI,
  // },
});



