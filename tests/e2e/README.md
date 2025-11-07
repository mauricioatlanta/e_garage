# Tests End-to-End con Playwright

Este directorio contiene tests automatizados de frontend usando Playwright para validar la funcionalidad completa de la aplicación E-Garage.

## 🚀 Configuración Rápida

### 1. Instalar Playwright

```bash
# Instalar Playwright y navegadores
npm install
npx playwright install
```

### 2. Ejecutar Tests

```bash
# Ejecutar todos los tests
npm test

# Ejecutar con interfaz visual
npm run test:ui

# Ejecutar en modo headed (ver el navegador)
npm run test:headed

# Ejecutar en modo debug
npm run test:debug
```

## 📋 Tests Disponibles

### `test_busqueda_servicios_frontend.spec.js`

Valida la funcionalidad de búsqueda de servicios en tiempo real:

- ✅ Botón "+ Add Service" crea una nueva fila
- ✅ Campo de texto realiza búsqueda en tiempo real
- ✅ Dropdown muestra resultados del endpoint `/documentos/ajax/servicios/buscar/`
- ✅ Selección de servicio autocompleta nombre y precio
- ✅ Subtotal y total del documento se actualizan dinámicamente

## 🔧 Requisitos

- **Servidor Django**: Debe estar corriendo en `http://127.0.0.1:8000`
- **Usuario autenticado**: El test asume que hay un usuario logueado
- **Datos de prueba**: Debe haber servicios con "oil" en el nombre

## 🎯 Cómo Funciona

1. **Navegación**: Abre el formulario de documentos
2. **Interacción**: Hace clic en "+ Add Service"
3. **Búsqueda**: Escribe "oil" en el campo de servicio
4. **Selección**: Espera el dropdown y selecciona el primer resultado
5. **Validación**: Verifica que el precio se autocomplete y el total se actualice

## 🐛 Debugging

Si un test falla:

1. **Ver el navegador**: Usa `npm run test:headed`
2. **Modo debug**: Usa `npm run test:debug`
3. **Interfaz visual**: Usa `npm run test:ui`
4. **Logs detallados**: Revisa el reporte HTML generado

## 📁 Estructura

```
tests/e2e/
├── README.md
├── test_busqueda_servicios_frontend.spec.js
└── (más tests...)
```

## 🔄 Integración Continua

Los tests están configurados para ejecutarse en CI/CD:

- **Retry automático**: 2 reintentos en CI
- **Paralelización**: Tests ejecutan en paralelo
- **Reportes**: Genera reportes HTML automáticamente
- **Servidor**: Inicia automáticamente el servidor Django
