# Pruebas E2E de Autenticación - egarage.cl

Este directorio contiene pruebas End-to-End (E2E) con Playwright para validar los flujos de autenticación del sitio **egarage.cl**, incluyendo validaciones críticas de legibilidad visual (contraste y colores).

## 🎯 Objetivos

Las pruebas validan tres flujos críticos:

1. **Registro (Sign Up)** - Creación de nueva cuenta
2. **Inicio de Sesión (Login)** - Autenticación de usuarios
3. **Recuperación de Contraseña (Password Reset)** - ⚠️ **PRIORIDAD ALTA** - Aquí se reportó el error de visibilidad

## 🔍 Validaciones Visuales

Cada test verifica:

- ✅ **Contraste de colores**: Ratio mínimo 4.5:1 (WCAG AA)
- ✅ **Visibilidad**: Opacity = 1 y Visibility = 'visible'
- ✅ **Colores adecuados**: Texto oscuro sobre fondo claro
- ✅ **Actualización de valores**: Verifica que los caracteres se escriban correctamente
- ✅ **Checkbox de Términos**: Visible y cliqueable (en reset password)

## 📋 Requisitos Previos

### 1. Instalar Node.js y npm

Asegúrate de tener Node.js instalado (versión 16 o superior):

```bash
node --version
npm --version
```

### 2. Instalar Playwright

Desde la raíz del proyecto:

```bash
npm install
```

O si prefieres instalar Playwright globalmente:

```bash
npm install -g @playwright/test
npx playwright install
```

### 3. Instalar navegadores de Playwright

```bash
npx playwright install chromium
```

## 🚀 Ejecución de Tests

### Ejecutar todos los tests

```bash
npx playwright test
```

### Ejecutar tests en un viewport específico

**Desktop (1920x1080):**
```bash
npx playwright test --project="Desktop Chrome"
```

**Mobile (iPhone 12):**
```bash
npx playwright test --project="Mobile iPhone 12"
```

### Ejecutar un test específico

```bash
npx playwright test auth-flows-visual.spec.js
```

### Ejecutar en modo UI (interactivo)

```bash
npx playwright test --ui
```

### Ejecutar en modo debug

```bash
npx playwright test --debug
```

## 📊 Ver Reportes

### Reporte HTML (recomendado)

```bash
npx playwright show-report
```

Esto abrirá un reporte HTML interactivo con:
- Screenshots de fallos
- Videos de ejecución
- Traces de errores
- Información detallada de cada test

### Reporte en consola

Los tests imprimen información detallada en la consola sobre:
- Colores HEX de texto y fondo
- Ratio de contraste
- Estado de visibilidad
- Problemas detectados

Ejemplo de salida:

```
============================================================
📋 VALIDACIÓN VISUAL: Nueva Contraseña (RESET - CRÍTICO)
============================================================
📍 Selector: input[name="password1"]
🎨 Color Texto: #333333 (RGB: rgb(51, 51, 51))
🎨 Color Fondo: #FFFFFF (RGB: rgb(255, 255, 255))
👁️  Opacity: 1
👁️  Visibility: visible
📊 Ratio de Contraste: 12.63:1
✅ Estado: OK
✅ Todos los checks pasaron correctamente
============================================================
```

## 🐛 Interpretación de Resultados

### ✅ Test Pasa (Status: OK)

- El campo es visible
- Tiene buen contraste (≥ 4.5:1)
- Colores adecuados (texto oscuro, fondo claro)
- Los valores se escriben correctamente

**Conclusión**: El formulario funciona correctamente desde el punto de vista técnico y visual.

### ⚠️ Test Pasa con Warnings

- El campo es visible pero tiene contraste bajo (< 4.5:1)
- O los colores no son ideales (texto claro sobre fondo oscuro, etc.)

**Conclusión**: El formulario funciona pero puede tener problemas de legibilidad en ciertos dispositivos o modos (ej: modo oscuro).

### ❌ Test Falla (Status: ERROR)

- El campo no es visible (opacity < 1 o visibility != 'visible')
- Los valores no se actualizan correctamente al escribir

**Conclusión**: Hay un bug real que necesita corrección.

## 🔧 Solución de Problemas

### Error: "Cannot find module '@playwright/test'"

```bash
npm install
```

### Error: "Executable doesn't exist"

```bash
npx playwright install
```

### Los tests no encuentran los campos

Los selectores están diseñados para ser flexibles y buscar múltiples variantes. Si fallan:

1. Revisa los screenshots en `test-results/`
2. Verifica la estructura HTML real del sitio
3. Ajusta los selectores en `auth-flows-visual.spec.js`

### El test de Password Reset falla porque no hay token válido

Esto es esperado. El test intenta navegar a la página de "Nueva Contraseña" pero sin un token real del email, puede que la página muestre un error. El test aún validará los campos si están presentes.

Para un test completo con token real:
1. Configura un backend de pruebas que genere tokens
2. O usa un token de prueba pre-generado

## 📁 Estructura de Archivos

```
tests/e2e/
├── README.md                    # Este archivo
├── auth-flows-visual.spec.js    # Tests principales
└── ...

playwright.config.js             # Configuración de Playwright (raíz del proyecto)
test-results/                    # Screenshots y videos (generado automáticamente)
playwright-report/               # Reporte HTML (generado automáticamente)
```

## 🎨 Personalización

### Cambiar la URL base

Edita `playwright.config.js`:

```javascript
use: {
  baseURL: 'https://tu-dominio.com',
  // ...
}
```

### Agregar más viewports

Edita `playwright.config.js` en la sección `projects`:

```javascript
projects: [
  {
    name: 'Tablet',
    use: { 
      ...devices['iPad Pro'],
    },
  },
  // ...
]
```

### Ajustar timeouts

En `playwright.config.js`:

```javascript
use: {
  actionTimeout: 20000,      // Timeout para acciones (click, type, etc.)
  navigationTimeout: 60000,  // Timeout para navegación
}
```

## 📝 Notas Importantes

1. **Tokens de Reset**: El test de password reset intenta acceder a una URL de reset sin token válido. En producción, necesitarías un token real del email.

2. **Datos de Prueba**: Los tests usan datos de prueba (`test@example.com`, `TestPassword123!`). No intentan crear cuentas reales.

3. **Screenshots**: Se capturan automáticamente cuando un test falla o al final de cada test exitoso.

4. **Modo Headless**: Por defecto, los tests corren en modo headless. Usa `--headed` para ver el navegador:

```bash
npx playwright test --headed
```

## 🤝 Contribuir

Si encuentras problemas o mejoras:

1. Revisa los screenshots en `test-results/`
2. Verifica los logs en la consola
3. Ajusta los selectores si la estructura HTML cambió
4. Actualiza este README con nuevas instrucciones

---

**Creado por**: Senior QA Automation Engineer  
**Framework**: Playwright  
**Última actualización**: Diciembre 2025
