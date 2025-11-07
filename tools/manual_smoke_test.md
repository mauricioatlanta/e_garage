# 🧪 **SMOKE TEST MANUAL MULTI-TENANT**

## ✅ **COMPRESIÓN ESTÁTICA ACTIVADA**
- WhiteNoise configurado ✅
- collectstatic ejecutado ✅
- Archivos comprimidos ✅

## 🧪 **SMOKE TESTS REQUERIDOS**

### **1. Chile (CLP + IVA 19%)**
- **URL**: http://127.0.0.1:8000/cl/es/documentos/form/
- **Usuario**: admin_chile
- **Contraseña**: admin123
- **Verificar**:
  - ✅ Formulario carga correctamente
  - ✅ Moneda CLP mostrada
  - ✅ IVA 19% aplicado
  - ✅ JavaScript documentos_form.js cargado

### **2. Estados Unidos (USD + Sales Tax 0%)**
- **URL**: http://127.0.0.1:8000/us/en/documentos/form/
- **Usuario**: testuser_usa
- **Contraseña**: TestUSA2025!
- **Verificar**:
  - ✅ Formulario carga correctamente
  - ✅ Moneda USD mostrada
  - ✅ Sales Tax 0% aplicado
  - ✅ JavaScript documentos_form.js cargado

### **3. JavaScript de Cálculos**
- **URL**: http://127.0.0.1:8000/static/taller/common/js/documentos_form.js
- **Verificar**:
  - ✅ Archivo carga correctamente
  - ✅ Función recalcTotals presente
  - ✅ Variable VAT_PCT presente
  - ✅ Función formatMoney presente

## 🎯 **INSTRUCCIONES**

1. **Abrir navegador** y ir a las URLs indicadas
2. **Hacer login** con las credenciales proporcionadas
3. **Verificar** que los formularios cargan sin errores
4. **Comprobar** que las monedas e IVA son correctos por país
5. **Abrir DevTools** y verificar que no hay errores de JavaScript

## ✅ **CRITERIOS DE ÉXITO**

- ✅ Formularios cargan sin errores 404/500
- ✅ Login funciona en ambos países
- ✅ Monedas correctas (CLP vs USD)
- ✅ IVA correcto (19% vs 0%)
- ✅ JavaScript sin errores en consola
- ✅ Archivos estáticos comprimidos cargan correctamente

---

**Estado**: ✅ **LISTO PARA SMOKE TEST MANUAL**
