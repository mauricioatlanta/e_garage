# 🔧 SOLUCIÓN: Totales en $0.00 en Lista de Documentos

## ❌ Problema

En la página `https://www.egarage.cl/us/documentos/`, las fichas de cada documento muestran todos los valores en **$0.00**:
- Total: $0.00
- Repuestos: $0.00
- Servicios: $0.00
- Otros Servicios: $0.00
- IVA / Impuestos: $0.00

Aunque el documento tiene información (cliente, vehículo, técnico, etc.).

## 🔍 Causa

La vista `DocumentoListView` calcula los totales usando anotaciones (`rep_sum`, `serv_sum`, `otros_sum`, `iva_calc`, `total_display`), pero el template está intentando acceder a los campos del modelo directamente (`documento.neto_repuestos`, `documento.neto_servicios`, etc.).

Los campos en la base de datos están en 0 porque no se están asignando los valores calculados.

## ✅ Solución Aplicada

Se modificó `taller/documentos/views_migrated.py` para asignar los valores calculados en las anotaciones a los campos que el template espera.

### **Archivo Modificado**

**`taller/documentos/views_migrated.py`**

**Cambio en `get_context_data`**:
- Asigna `rep_sum` → `documento.neto_repuestos`
- Asigna `serv_sum` → `documento.neto_servicios`
- Asigna `otros_sum` → `documento.neto_otros_servicios`
- Asigna `iva_calc` → `documento.tax_amount`
- Asigna `total_display` → `documento.total`

---

## 📋 Archivo a Actualizar en el Servidor

### **taller/documentos/views_migrated.py**
- **Cambio**: Asignación de valores calculados a campos del modelo para mostrar en el template
- **Ubicación en servidor**: `taller/documentos/views_migrated.py`

---

## 🚀 INSTRUCCIONES DE ACTUALIZACIÓN

### **Paso 1: Subir archivo actualizado**
1. **Subir `taller/documentos/views_migrated.py`**
   - Desde tu PC: `taller/documentos/views_migrated.py`
   - Al servidor: `taller/documentos/views_migrated.py`
   - Reemplazar el archivo existente

### **Paso 2: Recargar aplicación**
- PythonAnywhere: Ir a pestaña "Web" → Click "Reload"
- Otro servidor: Reiniciar servicio Django/Gunicorn/uWSGI

### **Paso 3: Verificar**
1. Ir a: `https://www.egarage.cl/us/documentos/`
2. Verificar que los totales se muestran correctamente:
   - ✅ Total: Debe mostrar el monto correcto (no $0.00)
   - ✅ Repuestos: Debe mostrar el total de repuestos
   - ✅ Servicios: Debe mostrar el total de servicios
   - ✅ Otros Servicios: Debe mostrar el total de otros servicios
   - ✅ IVA / Impuestos: Debe mostrar el impuesto calculado

---

## ✅ VERIFICACIÓN

Después de actualizar:
- ✅ Los totales se calculan correctamente desde las líneas de repuestos/servicios
- ✅ Los valores se muestran en el formato correcto con el símbolo de moneda
- ✅ Los documentos con líneas muestran los totales correctos
- ✅ Los documentos sin líneas muestran $0.00 (comportamiento esperado)

---

## 🔍 Nota Técnica

Los valores se calculan usando anotaciones de Django:
- `rep_sum`: Suma de `cantidad * precio_unitario` de `lineas_repuesto`
- `serv_sum`: Suma de `cantidad * precio_unitario` de `lineas_servicio`
- `otros_sum`: Suma de `cantidad * precio_cliente` de `lineas_otro_servicio`
- `iva_calc`: Calculado según el país (19% para Chile, 0% para USA)
- `total_display`: Suma de todos los subtotales + IVA

Estos valores se asignan temporalmente a los campos del modelo para que el template pueda accederlos.

---

**Fecha de creación**: 2025-11-25
**Archivos modificados**: 1
**Tiempo estimado de actualización**: 2-3 minutos

