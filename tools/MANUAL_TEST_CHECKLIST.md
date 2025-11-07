# 🧪 **TEST MANUAL COMPLETO - FORMULARIO DINÁMICO**

## 🎯 **OBJETIVO**
Verificar todas las funciones clave del flujo "crear documento" (frontend):
- Autonumeración
- Cliente→vehículo
- Subtotal/total dinámico
- IVA por país
- Payment Status
- CRUD de líneas
- Coherencia visual

---

## ✅ **PREPARACIÓN**

### 🧹 **Limpiar Navegador**
- [ ] Abre la consola (F12 → Console)
- [ ] Limpia cache y recarga dura (Ctrl + F5)
- [ ] Verifica ruta estática: `view-source:http://127.0.0.1:8000/cl/es/documentos/form/`

### 📜 **Scripts Cargados (solo estos 5)**
- [ ] `vendor/jquery/jquery-3.6.0.min.js`
- [ ] `vendor/dist/js/jquery-ui.min.js`
- [ ] `vendor/dist/js/select2.min.js`
- [ ] `autocomplete_light_custom/autocomplete.init.js`
- [ ] `taller/common/js/documentos_form.js`

### 🚫 **Sin Errores en Consola**
- [ ] No aparece `Identifier 'COUNTRY' has already been declared`
- [ ] Mensaje: `🚀 Inicializando documento form... COUNTRY= CL VAT= 19`
- [ ] Mensaje: `✅ Documento form listo: {COUNTRY: "CL", CURRENCY: "CLP", VAT_PCT: 19}`

---

## 🧩 **TEST 1 – Numeración Automática**

| Acción | Resultado Esperado | ✅ |
|--------|-------------------|-----|
| Selecciona un "Tipo de documento" | Campo Número se completa automáticamente con el siguiente correlativo | [ ] |
| Cambia a otro tipo | El número cambia dinámicamente | [ ] |
| Refresca la página | Se mantiene el último número asignado | [ ] |

---

## 🚗 **TEST 2 – Cliente → Vehículo**

| Acción | Resultado Esperado | ✅ |
|--------|-------------------|-----|
| Selecciona un cliente (usando autocompletado DAL) | El campo Vehículo se limpia y muestra solo los vehículos de ese cliente | [ ] |
| Cambia a otro cliente | Lista de vehículos se actualiza | [ ] |
| Sin cliente seleccionado | Lista de vehículos vacía | [ ] |

**Nota**: Verificar que en `forms.py` el widget de vehículo tenga `forward=['cliente']`

---

## 💰 **TEST 3 – Subtotales y Totales**

### 🇨🇱 **Chile (/cl/) - IVA 19%**

| Acción | Resultado Esperado | ✅ |
|--------|-------------------|-----|
| Agrega 1 fila de repuesto (qty = 2, price = 10000) | Subtotal = 20000 CLP | [ ] |
| Agrega 1 fila de servicio (qty = 1, price = 5000) | Subtotal = 5000 CLP | [ ] |
| Agrega 1 fila de externo (precio cliente = 3000) | Subtotal = 3000 CLP | [ ] |
| **Totales al pie** | **Partes = 20000, Servicios = 5000, Externos = 3000, IVA = 3800, Total = 31800 CLP** | [ ] |

### 🇺🇸 **Estados Unidos (/us/) - Sales Tax 0%**

| Acción | Resultado Esperado | ✅ |
|--------|-------------------|-----|
| Mismos valores que Chile | IVA = 0 USD, Total = 28000 USD | [ ] |

---

## 🧾 **TEST 4 – Payment Status**

| Acción | Resultado Esperado | ✅ |
|--------|-------------------|-----|
| Campo visible con 4 opciones | Pending, Paid, Partial, Canceled / Pendiente, Pagado, Parcial, Anulado | [ ] |
| Marca el checkbox "Document paid" | Select cambia a "Paid" / "Pagado" | [ ] |
| Desmarca el checkbox | Vuelve a "Pending" / "Pendiente" | [ ] |

**Nota**: El select debe mostrarse incluso si antes estaba oculto

---

## 🧱 **TEST 5 – CRUD de Líneas**

| Acción | Resultado Esperado | ✅ |
|--------|-------------------|-----|
| Clic en "Add part/service/other" | Inserta nueva fila y recalcula totales | [ ] |
| Edita cantidad o precio | Subtotal y total se actualizan instantáneamente | [ ] |
| Pulsa ✖ (eliminar fila) | Fila desaparece y total recalculado sin error | [ ] |
| Agrega varias filas seguidas | Ningún retardo ni error de JS | [ ] |

---

## 📊 **TEST 6 – IVA por País**

| Contexto | Resultado Esperado | ✅ |
|----------|-------------------|-----|
| URL `/cl/...` | IVA = 19% sobre total repuestos | [ ] |
| URL `/us/...` | IVA = 0 (oculto o $0) | [ ] |
| Cambia país manualmente | Se actualiza moneda y porcentaje (recalcular totales para comprobar) | [ ] |

---

## 🎨 **TEST 7 – Interfaz Visual**

| Elemento | Resultado Esperado | ✅ |
|----------|-------------------|-----|
| Fecha de emisión | Aparece primera | [ ] |
| Payment Status | Visible bajo fecha/tipo/número | [ ] |
| Estilo coherente | `futurista-input` y botones `btn btn-cyan/emerald/purple` | [ ] |
| KPIs de totales | Bien alineados y legibles | [ ] |

---

## 🧮 **TEST 8 – Persistencia (Backend)**

| Acción | Resultado Esperado | ✅ |
|--------|-------------------|-----|
| Envía el formulario | Revisa en la base de datos (Documento, LineaRepuesto, LineaServicio, LineaOtroServicio) | [ ] |
| Confirma subtotales | Los subtotales guardados coinciden con los calculados en el front | [ ] |
| Vista detalle/pdf | Los totales deben corresponder | [ ] |

---

## 🧭 **TEST 9 – Regresión / Compatibilidad**

| Acción | Resultado Esperado | ✅ |
|--------|-------------------|-----|
| Abre un documento existente | Campos cargan correctamente, sin duplicar scripts | [ ] |
| Edita y guarda | Totales se mantienen consistentes | [ ] |
| No hay alertas | Ni errores en consola JS | [ ] |

---

## 🧩 **TEST 10 – Performance**

| Métrica | Resultado Esperado | ✅ |
|---------|-------------------|-----|
| Tiempo de carga | < 2s con WhiteNoise (ver Network tab) | [ ] |
| Solicitudes vendor | Solo 1 solicitud a cada vendor JS | [ ] |
| Sin requests basura | No hay requests a `postcss.config.js`, `reportWebVitals.js`, etc. | [ ] |

---

## 🎯 **URLs de Prueba**

### 🇨🇱 **Chile**
- **Crear**: `http://127.0.0.1:8000/cl/es/documentos/form/`
- **Editar**: `http://127.0.0.1:8000/cl/es/documentos/form/4/`
- **Ver**: `http://127.0.0.1:8000/cl/es/documentos/4/`

### 🇺🇸 **Estados Unidos**
- **Crear**: `http://127.0.0.1:8000/us/en/documentos/form/`
- **Editar**: `http://127.0.0.1:8000/us/en/documentos/form/4/`
- **Ver**: `http://127.0.0.1:8000/us/en/documentos/4/`

---

## 🎉 **CRITERIO DE ÉXITO**

**✅ PRODUCTION-READY**: Todos los tests pasan sin errores
- Multi-país ✅
- Multi-moneda ✅
- Estable ✅
- Limpio ✅

---

## 📝 **NOTAS ADICIONALES**

### 🔧 **Debugging**
- Si hay errores, revisar consola del navegador
- Verificar que `documentos_form.js` se carga correctamente
- Confirmar que no hay scripts duplicados

### 🚀 **Optimizaciones**
- Verificar que solo se cargan los scripts necesarios
- Confirmar que no hay requests a archivos eliminados
- Validar que el tiempo de carga es óptimo

---

**Fecha**: 2025-10-06  
**Versión**: 1.0  
**Estado**: Listo para testing
