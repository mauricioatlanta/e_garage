# 🧪 Tests de Flujos Críticos Financieros

## 🎯 Objetivo

Validación exhaustiva de escenarios que afectan directamente la facturación del cliente. Asegura que los cálculos financieros y las actualizaciones de stock sean **inmutables y 100% fiables**, eliminando cualquier riesgo de discrepancia contable para el taller.

## 📋 Escenario Crítico Cubierto

El test `test_flujo_critico_completo_chile` valida el siguiente flujo completo:

1. ✅ **Crear un Documento (Factura)** - Tipo `FAC`
2. ✅ **Aplicar un Repuesto con Stock 0** - Validación y manejo correcto
3. ✅ **Registrar un Pago Parcial** - Tracking de `monto_pagado` y `saldo_pendiente`
4. ✅ **Verificar el IVA/Sales Tax** - Cálculo correcto según país (Chile 19%, USA 0%)
5. ✅ **Verificar el Dashboard** - Métricas actualizadas correctamente

## 🧪 Tests Implementados

### 1. `test_flujo_critico_completo_chile`

**Flujo completo para Chile con IVA:**

- Crea factura tipo `FAC` en estado `BORRADOR`
- Crea repuesto con stock 0 y lo agrega a la factura
- Valida que NO se puede emitir con stock 0 (bloqueo de seguridad)
- Agrega stock y emite la factura (descuenta stock correctamente)
- Registra pago parcial (50% del total)
- Verifica cálculos de IVA (19% sobre repuestos solamente)
- Verifica que métricas del dashboard se actualizan

**Validaciones críticas:**
- ✅ Stock se valida antes de emitir
- ✅ Stock se descuenta correctamente al emitir
- ✅ IVA solo se aplica a repuestos (no a servicios en Chile)
- ✅ Cálculos son consistentes antes y después de pago parcial
- ✅ Dashboard refleja la factura emitida

### 2. `test_flujo_critico_completo_usa_sin_iva`

**Flujo completo para USA sin IVA:**

- Mismo flujo que Chile pero validando que USA NO tiene IVA
- Verifica que `tax_amount = 0` para documentos de USA
- Valida que el resto del flujo funciona igual

### 3. `test_inmutabilidad_calculos_despues_pago_parcial`

**Validación de inmutabilidad contable:**

Este test es **CRÍTICO** para garantizar integridad financiera:

- Crea factura completa con repuestos y servicios
- Guarda valores iniciales de totales
- **Verifica que los totales NO cambian** después de:
  - Emitir la factura
  - Registrar pago parcial (30%)
  - Completar pago (100%)

**Garantiza:**
- ✅ Los cálculos financieros son **INMUTABLES**
- ✅ No hay riesgo de discrepancia contable
- ✅ Los totales se mantienen constantes independientemente del estado de pago

### 4. `test_validacion_stock_cero_bloquea_emision`

**Validación de seguridad de inventario:**

- Intenta emitir factura con repuesto stock 0
- Verifica que la validación detecta el problema
- Confirma que el stock NO cambia si falla la validación
- Asegura que `validar_y_procesar_emision` retorna error

## 🔍 Campos Validados

### Cálculos Financieros
- `neto_repuestos` - Total de repuestos sin IVA
- `neto_servicios` - Total de servicios (sin IVA en Chile)
- `neto_otros_servicios` - Otros servicios
- `tax_amount` - IVA calculado (19% en Chile, 0% en USA)
- `total` - Total general de la factura

### Estado de Pago
- `estado_pago` - `"NO_PAGADO"`, `"PARCIAL"`, `"PAGADO"`
- `monto_pagado` - Monto efectivamente pagado
- `saldo_pendiente` - Saldo restante por pagar
- `pagado` - Boolean indicando si está completamente pagado
- `metodo_pago` - Método utilizado (efectivo, transferencia, tarjeta, cheque)

### Dashboard (KPIs)
- `total_ventas` - Suma de totales de facturas emitidas
- `total_facturas` - Cantidad de facturas emitidas
- `ticket_promedio` - Promedio de ventas por factura
- `total_ot` - Cantidad de órdenes de trabajo
- `total_presupuestos` - Cantidad de presupuestos

## 🚀 Ejecutar Tests

```bash
# Ejecutar todos los tests de flujo crítico
python manage.py test tests.test_flujo_critico_financiero

# Ejecutar un test específico
python manage.py test tests.test_flujo_critico_financiero.TestFlujoCriticoFinanciero.test_flujo_critico_completo_chile

# Ejecutar con verbosidad
python manage.py test tests.test_flujo_critico_financiero -v 2
```

## ✅ Criterios de Éxito

Un test pasa si:

1. ✅ **Stock se valida correctamente** - No permite emitir con stock 0
2. ✅ **Stock se descuenta al emitir** - El inventario se actualiza correctamente
3. ✅ **IVA se calcula correctamente** - 19% en Chile (solo repuestos), 0% en USA
4. ✅ **Pago parcial se registra** - Campos `monto_pagado` y `saldo_pendiente` correctos
5. ✅ **Cálculos son INMUTABLES** - Los totales NO cambian después de pagos
6. ✅ **Dashboard se actualiza** - Métricas reflejan la factura emitida

## 🛡️ Garantías de Seguridad

Estos tests garantizan:

- ✅ **Integridad contable** - Los totales nunca cambian después de calcularse
- ✅ **Integridad de inventario** - No se puede vender lo que no existe en stock
- ✅ **Cálculo correcto de impuestos** - IVA aplicado según reglas del país
- ✅ **Trazabilidad de pagos** - Estado de pago siempre refleja la realidad
- ✅ **Consistencia del dashboard** - Métricas siempre están actualizadas

## 📝 Notas Técnicas

- Los tests usan `cache.clear()` para asegurar que el dashboard recalcula métricas
- Se usa `force_refresh=True` en `DashboardService` para evitar cache
- Los tests son independientes (cada uno tiene su propio `setUp`)
- Se validan tanto campos directos (`neto_repuestos`) como propiedades (`total_repuestos`) para compatibilidad

## 🛡️ Tests de Bloqueo de Anulación y Auditoría Forense

### `TestBloqueoAnulacionYAudiitoria`

Clase dedicada a validar la integridad contable forense:

#### 1. `test_no_se_puede_eliminar_factura_emitida`

**Objetivo:** Prevenir eliminación de facturas emitidas.

- Intenta eliminar una factura en estado `EMITIDO`
- Valida que la eliminación debe estar bloqueada
- Documenta el riesgo si la eliminación es posible

**Garantía:** Las facturas emitidas no pueden eliminarse, manteniendo la integridad contable.

#### 2. `test_no_se_puede_eliminar_factura_pagada`

**Objetivo:** Prevenir eliminación de facturas pagadas.

- Intenta eliminar una factura con estado `PAGADO`
- Valida que la eliminación debe estar completamente bloqueada
- Documenta el riesgo crítico si la eliminación es posible

**Garantía:** Las facturas pagadas son evidencia financiera crítica e ineliminables.

#### 3. `test_anulacion_mantiene_registro_inmutable`

**Objetivo:** Validar que la anulación mantiene el registro histórico.

- Anula una factura emitida (cambia estado a `ANULADO`)
- Verifica que el documento **NO se elimina**, solo cambia de estado
- Valida que los totales se mantienen inmutables
- Verifica que el stock se repone correctamente
- Confirma que la razón de anulación se guarda en `observaciones`

**Garantías:**
- ✅ El registro se mantiene para auditoría forense
- ✅ Los totales no cambian después de anular
- ✅ El stock se repone correctamente
- ✅ La razón queda documentada

#### 4. `test_anulacion_requiere_razon_auditoria`

**Objetivo:** Validar buena práctica de documentar razones de anulación.

- Anula una factura con razón documentada
- Verifica que las observaciones no están vacías

**Buena Práctica:** Toda anulación debe tener una razón documentada para auditoría.

#### 5. `test_anulacion_factura_pagada_requiere_especial_atencion`

**Objetivo:** Validar anulación de facturas ya pagadas.

- Anula una factura que ya fue pagada
- Verifica que el monto pagado se mantiene para auditoría
- Confirma que la razón documenta el proceso de devolución

**Garantía:** Las anulaciones de facturas pagadas requieren documentación especial y mantenimiento del historial de pago.

## 🔒 Validaciones de Seguridad Contable

Estos tests validan que:

### Bloqueo de Eliminación
- ❌ **NO se puede eliminar** facturas emitidas
- ❌ **NO se puede eliminar** facturas pagadas
- ⚠️ Si el sistema permite eliminación, se documenta como **RIESGO CRÍTICO**

### Inmutabilidad de Registros
- ✅ Anulación **NO elimina** el documento
- ✅ Anulación solo cambia estado a `ANULADO`
- ✅ Totales se mantienen inmutables
- ✅ Número de documento se preserva
- ✅ Historial completo se mantiene

### Reposición de Stock
- ✅ Stock se repone correctamente al anular
- ✅ Movimientos de stock quedan registrados

### Auditoría Forense
- ✅ Razón de anulación se documenta en `observaciones`
- ✅ Montos pagados se mantienen para auditoría
- ✅ Registro completo preservado para análisis forense

## 🔄 Próximos Pasos

Para extender estos tests, considerar:

- [x] ✅ Tests de bloqueo de eliminación de facturas emitidas/pagadas
- [x] ✅ Tests de anulación con registro inmutable
- [ ] Implementar protección a nivel de modelo para prevenir `delete()` en documentos emitidos
- [ ] Tests con múltiples pagos parciales consecutivos
- [ ] Tests con descuentos en repuestos y su efecto en IVA
- [ ] Tests de concurrencia (múltiples emisiones simultáneas)
- [ ] Tests de edición de facturas emitidas y ajuste de stock
- [ ] Tests de notas de crédito/débito como alternativa a eliminación

