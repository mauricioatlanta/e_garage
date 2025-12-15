# 🚀 Instalación Rápida - Tests E2E Playwright

## Instalación en 3 Pasos

### Paso 1: Instalar dependencias de Node.js

```bash
npm install
```

### Paso 2: Instalar navegadores de Playwright

```bash
npx playwright install chromium
```

### Paso 3: Ejecutar los tests

```bash
npm test
```

## ✅ Verificación

Si todo está correcto, deberías ver:

```
Running 4 tests using 2 workers

  ✓ Desktop Chrome › auth-flows-visual.spec.js › 1. Registro (Sign Up) - Validación de campos y contraste
  ✓ Desktop Chrome › auth-flows-visual.spec.js › 2. Inicio de Sesión (Login) - Validación de campos y contraste
  ✓ Desktop Chrome › auth-flows-visual.spec.js › 3. Recuperación de Contraseña (Password Reset) - Validación crítica
  ✓ Desktop Chrome › auth-flows-visual.spec.js › 4. Resumen de Validaciones Visuales

  4 passed (30s)
```

## 🎯 Comandos Útiles

```bash
# Ver reporte HTML interactivo
npm run test:report

# Ejecutar solo en Desktop
npm run test:desktop

# Ejecutar solo en Mobile
npm run test:mobile

# Ejecutar con interfaz visual
npm run test:ui

# Ejecutar en modo debug
npm run test:debug
```

## ❌ Solución de Problemas

### Error: "npm: command not found"

Instala Node.js desde: https://nodejs.org/

### Error: "Cannot find module '@playwright/test'"

```bash
rm -rf node_modules package-lock.json
npm install
```

### Error: "Executable doesn't exist"

```bash
npx playwright install --force
```





