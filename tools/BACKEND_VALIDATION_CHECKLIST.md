# 🧪 **CHECKLIST DE VALIDACIONES BACKEND**

## 🎯 **OBJETIVO**
Verificar que al guardar un documento desde el formulario:
- Los cálculos en el backend (modelo + view) son iguales a los del JS
- Los FK están coherentes (empresa, cliente, vehiculo, tecnico_responsable)
- El IVA/sales tax se aplica correctamente según país
- Las líneas (repuestos, servicios, externos) se guardan con sus subtotales correctos
- Los campos de auditoría (created_by, updated_by) se completan

---

## ✅ **1. PRUEBAS UNITARIAS (pytest / Django TestCase)**

### 🧪 **Ejecutar Tests**
```bash
# Ejecutar todas las pruebas
python tools/run_backend_tests.py

# O ejecutar directamente con Django
python manage.py test tests.test_documento_backend
```

### 📋 **Tests Incluidos**
- [ ] **test_totales_chile_con_iva**: Verificar cálculos en Chile con IVA 19%
- [ ] **test_totales_usa_sin_iva**: Verificar cálculos en Estados Unidos sin IVA
- [ ] **test_subtotales_por_linea**: Verificar subtotales individuales por línea
- [ ] **test_coherencia_empresa_cliente_vehiculo**: Verificar coherencia de FK
- [ ] **test_audit_fields**: Verificar campos de auditoría
- [ ] **test_clean_validation**: Verificar validación de Documento.clean()
- [ ] **test_moneda_por_pais**: Verificar moneda por país
- [ ] **test_iva_calculation_edge_cases**: Verificar casos límite de IVA
- [ ] **test_descuentos_en_repuestos**: Verificar aplicación de descuentos
- [ ] **test_multiple_repuestos_con_iva**: Verificar IVA con múltiples repuestos
- [ ] **test_documento_sin_lineas**: Verificar documento sin líneas
- [ ] **test_precios_con_decimales**: Verificar manejo de decimales

### 🎯 **Resultado Esperado**
```
✅ Todas las pruebas pasaron
🎉 El backend está funcionando correctamente
```

---

## ✅ **2. PRUEBA MANUAL (Django Shell)**

### 🧪 **Ejecutar Pruebas Manuales**
```bash
# Ejecutar script de pruebas manuales
python manage.py shell < tools/test_documento_manual.py
```

### 📋 **Validaciones Incluidas**

#### 🇨🇱 **Documento Chile (CLP + IVA 19%)**
- [ ] **Repuestos**: 2 × $10,000 = $20,000
- [ ] **Servicios**: 1 × $5,000 = $5,000
- [ ] **Otros**: 1 × $3,000 = $3,000
- [ ] **IVA**: 19% de $20,000 = $3,800
- [ ] **Total**: $20,000 + $5,000 + $3,000 + $3,800 = $31,800

#### 🇺🇸 **Documento Estados Unidos (USD + Sales Tax 0%)**
- [ ] **Repuestos**: 1 × $100 = $100
- [ ] **Servicios**: 1 × $50 = $50
- [ ] **Otros**: $0
- [ ] **Sales Tax**: 0% = $0
- [ ] **Total**: $100 + $50 + $0 + $0 = $150

### 🎯 **Resultado Esperado**
```
🎉 ¡TODAS LAS PRUEBAS MANUALES PASARON!
   El backend calcula correctamente los totales
   Los cálculos coinciden con el frontend
```

---

## ✅ **3. VALIDACIONES QUE DEBEN PASAR**

| Validación | Resultado |
|------------|-----------|
| `Documento.clean()` verifica que todas las líneas pertenezcan a la misma empresa | ✅ sin error |
| `empresa.moneda` determina moneda del documento | CL → CLP / US → USD |
| `iva = sum(repuestos)*0.19` si `empresa.pais=="CL"` | ✅ |
| `iva = 0` si `empresa.pais=="US"` | ✅ |
| `subtotal_linea = cantidad*precio_unitario` o `precio_cliente` según tipo | ✅ |
| `created_by` / `updated_by` completados | ✅ |

---

## ✅ **4. TEST DE COHERENCIA CON FRONTEND**

### 🧪 **Proceso de Verificación**
1. [ ] **Crear documento en el frontend** (usa JS nuevo)
2. [ ] **Guardar y abrir en el admin**
3. [ ] **Sumar los valores de las líneas manualmente**
4. [ ] **Verificar que los totales, IVA y total general coinciden** con los valores que veías en pantalla
5. [ ] **Repetir en /us/** — el IVA debe ser 0
6. [ ] **(Opcional) exportar ambos documentos a CSV o PDF** y comprobar que los montos impresos coincidan

### 📋 **URLs de Prueba**
- **Chile**: `http://127.0.0.1:8000/cl/es/documentos/form/`
- **Estados Unidos**: `http://127.0.0.1:8000/us/en/documentos/form/`

---

## ✅ **5. MÉTRICAS COMPLEMENTARIAS (REPORTES/DASHBOARD)**

### 📊 **Métricas a Verificar**
| Métrica | Comprobación |
|---------|--------------|
| Ventas por técnico | Agrupa por `documento.tecnico_responsable` |
| Ventas por tipo de línea | Suma por `LineaRepuesto`, `LineaServicio`, `LineaOtroServicio` |
| IVA mensual | Suma `documento.iva` de `empresa.pais="CL"` por `fecha_emision__month` |
| Ganancia (otros servicios) | Suma `precio_cliente - costo_interno` |

---

## ✅ **6. CHECKLIST FINAL DE BACKEND LISTO PARA PRODUCCIÓN**

### 🎯 **Criterios de Aprobación**
- [ ] **Tests de totales CL/US pasan** (pytest = verde)
- [ ] **`Documento.recalcular_totales()` ejecuta los mismos cálculos** que el frontend
- [ ] **`clean()` valida empresa coherente**
- [ ] **AuditMixin graba `created_by` / `updated_by`**
- [ ] **Admin muestra totales con formato monetario**
- [ ] **Reportes mensuales reflejan IVA correcto**

---

## 🚀 **COMANDOS DE EJECUCIÓN**

### 🧪 **Ejecutar Todas las Pruebas**
```bash
# 1. Pruebas unitarias
python tools/run_backend_tests.py

# 2. Pruebas manuales
python manage.py shell < tools/test_documento_manual.py

# 3. Verificar coherencia con frontend
# Abrir navegador y probar manualmente
```

### 📊 **Verificar Resultados**
```bash
# Ver documentos creados
python manage.py shell -c "
from taller.models import Documento
docs = Documento.objects.all()
for doc in docs:
    print(f'ID: {doc.id}, País: {doc.empresa.pais}, Total: {doc.total_general}')
"
```

---

## 🎯 **CRITERIO DE ÉXITO**

**✅ BACKEND PRODUCTION-READY**: Todos los tests pasan sin errores
- Cálculos correctos ✅
- Coherencia de datos ✅
- IVA por país ✅
- Auditoría completa ✅
- Compatibilidad con frontend ✅

---

## 📝 **NOTAS ADICIONALES**

### 🔧 **Debugging**
- Si hay errores, revisar logs de Django
- Verificar que los modelos tengan los métodos `recalcular_totales()`
- Confirmar que los campos de auditoría estén configurados

### 🚀 **Optimizaciones**
- Verificar que las consultas sean eficientes
- Confirmar que no hay N+1 queries
- Validar que los índices estén optimizados

---

**Fecha**: 2025-10-06  
**Versión**: 1.0  
**Estado**: Listo para testing backend
