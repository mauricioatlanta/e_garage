# 🚀 Quick Start - Tests E2E egarage.cl

## ⚡ Instalación Rápida (3 comandos)

```bash
# 1. Instalar dependencias
npm install

# 2. Instalar navegadores
npx playwright install chromium

# 3. Ejecutaºr tests
npm test
```

## 📊 ¿Qué hace este test?

Este script de pruebas E2E valida **tres flujos críticos** de autenticación en **egarage.cl**:

1. ✅ **Registro (Sign Up)**
2. ✅ **Inicio de Sesión (Login)**  
3. ⚠️ **Recuperación de Contraseña (Password Reset)** - *Prioridad Alta*

### 🔍 Validaciones Visuales (A11y)

Para cada campo de input, el test verifica:

- **Contraste de colores**: Ratio mínimo 4.5:1 (WCAG AA)
- **Visibilidad**: Opacity = 1, Visibility = 'visible'
- **Colores adecuados**: Texto oscuro sobre fondo claro
- **Actualización de valores**: Los caracteres se escriben correctamente

## 📈 Interpretación de Resultados

### ✅ Test Pasa (Status: OK)

```
✅ Estado: OK
✅ Todos los checks pasaron correctamente
```

**Significado**: El formulario funciona correctamente. Los campos son visibles y tienen buen contraste.

### ⚠️ Test Pasa con Warnings

```
⚠️ Estado: WARNING
⚠️ Problemas detectados:
   - Contraste bajo: 3.2:1 (requerido: 4.5:1)
```

**Significado**: El formulario funciona pero puede tener problemas de legibilidad en ciertos dispositivos o modos (ej: modo oscuro del sistema).

### ❌ Test Falla (Status: ERROR)

```
❌ Estado: ERROR
❌ Problemas detectados:
   - Campo no visible (opacity o visibility)
```

**Significado**: Hay un bug real que necesita corrección inmediata.

## 🎯 Comandos Útiles

```bash
# Ver reporte HTML interactivo (recomendado)
npm run test:report

# Ejecutar solo en Desktop (1920x1080)
npm run test:desktop

# Ejecutar solo en Mobile (iPhone 12)
npm run test:mobile

# Ejecutar con interfaz visual
npm run test:ui

# Ejecutar en modo debug
npm run test:debug

# Ver el navegador mientras ejecuta
npm run test:headed
```

## 📸 Screenshots y Reportes

Después de ejecutar los tests:

- **Screenshots**: Se guardan en `test-results/` (solo cuando hay fallos)
- **Reporte HTML**: Ejecuta `npm run test:report` para ver un reporte interactivo
- **Logs en consola**: Información detallada de colores y contraste

## 🔧 Solución de Problemas

### "Cannot find module '@playwright/test'"

```bash
rm -rf node_modules package-lock.json
npm install
```

### "Executable doesn't exist"

```bash
npx playwright install --force
```

### Los tests no encuentran los campos

1. Revisa los screenshots en `test-results/`
2. Verifica que el sitio esté accesible en `https://egarage.cl`
3. Los selectores son flexibles y buscan múltiples variantes

## 📝 Ejemplo de Salida

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

## 🎨 ¿Qué esperar de este test?

Al ejecutar el código, obtendrás **dos resultados clave**:

### 1. Verificación Funcional
Sabrás si el formulario realmente está roto o si el sistema permite completar el proceso técnicamente.

### 2. Auditoría de Diseño (CSS)
El test te dirá en la consola algo como:

```
Input Contraseña: Fondo #FFFFFF (Blanco) - Texto #333333 (Gris Oscuro). STATUS: OK.
```

O, si hay un error:

```
Input Contraseña: Fondo #000000 - Texto #000000. STATUS: ERROR (Texto invisible).
```

Esto te confirmará si el problema es que el teléfono está forzando un "Modo Oscuro" que rompe la página, o si la página realmente tiene mal definidos los colores.

---

**¿Listo para empezar?** Ejecuta `npm install && npx playwright install chromium && npm test`





