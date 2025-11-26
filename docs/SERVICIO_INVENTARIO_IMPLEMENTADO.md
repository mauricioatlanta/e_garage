# 📦 Servicio de Inventario (Inventory Service) - Implementación Completa

## 📋 Resumen

Implementación completa del servicio de gestión de inventario que maneja movimientos de stock automáticamente según cambios de estado de documentos.

**Reglas de Negocio:**
- ✅ Los Presupuestos (PRES) NUNCA mueven stock
- ✅ Las Órdenes de Trabajo (OT) y Facturas (FAC) SÍ mueven stock
- ✅ Las ediciones ajustan diferencia correctamente
- ✅ Las anulaciones devuelven el stock
- ✅ Usa F() expressions para evitar race conditions

## 🎯 Problema Resuelto

**Antes:**
- ❌ Stock no se actualizaba al emitir documentos
- ❌ No se validaba stock disponible antes de emitir
- ❌ Anulaciones no devolvían stock
- ❌ Ediciones no ajustaban stock correctamente

**Ahora:**
- ✅ Stock se actualiza automáticamente al emitir
- ✅ Validación de stock antes de emitir
- ✅ Anulaciones devuelven stock automáticamente
- ✅ Ediciones ajustan diferencia correctamente
- ✅ Thread-safe con F() expressions

## 📁 Archivos Creados

### 1. Servicio de Inventario
**Archivo**: `taller/services/inventory_service.py`

Servicio dedicado que maneja toda la lógica de inventario:

```python
class InventoryService:
    @staticmethod
    def procesar_movimiento_stock(documento, accion, cantidades_anteriores=None):
        """Procesa movimiento de stock según acción"""
    
    @staticmethod
    def validar_stock_disponible(documento):
        """Valida que hay stock suficiente"""
    
    @staticmethod
    def procesar_edicion(documento_anterior, documento_nuevo):
        """Maneja cambios de stock en ediciones"""
```

### 2. Señales de Inventario
**Archivo**: `taller/documentos/signals_inventory.py`

Señales Django que detectan cambios de estado y actualizan stock automáticamente:

```python
@receiver(pre_save, sender=Documento)
def controlar_stock_al_cambiar_estado(sender, instance, **kwargs):
    """Detecta cambios de estado y actualiza stock"""
```

**Casos manejados:**
- BORRADOR → EMITIDO: Descontar stock
- EMITIDO → ANULADO: Reponer stock
- ANULADO → EMITIDO: Descontar stock nuevamente
- Edición de documento emitido: Ajustar diferencia

### 3. Vistas de Inventario
**Archivo**: `taller/documentos/views_inventory.py`

Vistas para emitir y anular documentos con validación:

- `emitir_documento()` - Emite documento validando stock
- `anular_documento()` - Anula documento reponiendo stock
- `validar_stock_documento()` - Valida stock sin emitir

## 🔧 Configuración

### 1. Agregar Señales

Ya está configurado en `taller/documentos/apps.py`:

```python
def ready(self):
    from . import signals  # noqa
    from . import signals_inventory  # ✅ Señales de inventario
```

### 2. URLs Agregadas

Ya agregadas en `taller/documentos/urls.py`:

```python
path("emitir/<int:documento_id>/", views_inventory.emitir_documento, name="emitir_documento"),
path("anular/<int:documento_id>/", views_inventory.anular_documento, name="anular_documento"),
path("validar-stock/<int:documento_id>/", views_inventory.validar_stock_documento, name="validar_stock_documento"),
```

## 🎨 Flujo de Trabajo

### 1. Crear Documento (Borrador)

```
Usuario crea documento con repuestos
    ↓
Documento se guarda con estado BORRADOR
    ↓
Stock NO se mueve (está en borrador)
```

### 2. Emitir Documento

```
Usuario hace clic en "Emitir"
    ↓
Vista valida stock disponible
    ↓
Si hay stock suficiente:
    - Cambia estado a EMITIDO
    - Señal pre_save detecta cambio
    - Servicio descuenta stock automáticamente
    ↓
Si NO hay stock suficiente:
    - Muestra errores
    - NO cambia estado
    - NO descuenta stock
```

### 3. Anular Documento

```
Usuario hace clic en "Anular"
    ↓
Vista cambia estado a ANULADO
    ↓
Señal pre_save detecta cambio
    ↓
Servicio repone stock automáticamente
```

### 4. Editar Documento Emitido

```
Usuario edita documento emitido
    - Cambia cantidad de 2 a 3 → Descuenta 1 extra
    - Cambia cantidad de 3 a 2 → Repone 1 unidad
    - Elimina línea → Repone cantidad eliminada
    - Agrega línea → Descuenta cantidad nueva
    ↓
Servicio procesa edición y ajusta diferencia
```

## 🔒 Seguridad y Thread-Safety

### F() Expressions

Usa F() expressions para evitar race conditions:

```python
# ❌ MAL (puede tener race condition)
repuesto.cantidad_stock = repuesto.cantidad_stock - cantidad
repuesto.save()

# ✅ BIEN (atómico en BD)
Repuesto.objects.filter(id=repuesto.id).update(
    cantidad_stock=F('cantidad_stock') + (-cantidad)
)
```

### Multi-Tenant

```python
# ✅ Siempre filtrar por empresa
Repuesto.objects.filter(
    id=repuesto.id,
    empresa=documento.empresa  # 🔒 Multi-tenant
).update(...)
```

## 📊 Ejemplos de Uso

### Emitir Documento

```python
# Desde la vista
@login_required
def emitir_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id, empresa=request.user.empresa)
    
    # Validar stock
    errores = InventoryService.validar_stock_disponible(documento)
    if errores:
        # Mostrar errores al usuario
        return
    
    # Cambiar estado (la señal procesará el stock)
    documento.estado = 'EMITIDO'
    documento.save()  # ✅ Señal descuenta stock automáticamente
```

### Anular Documento

```python
# Desde la vista
@login_required
def anular_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id, empresa=request.user.empresa)
    
    # Cambiar estado (la señal procesará la reposición)
    documento.estado = 'ANULADO'
    documento.save()  # ✅ Señal repone stock automáticamente
```

### Validar Stock (Sin Emitir)

```python
# Desde la vista o API
errores = InventoryService.validar_stock_disponible(documento)
if errores:
    for error in errores:
        print(error)  # "❌ Stock insuficiente para 'Filtro de Aceite'. Requerido: 5, Disponible: 2"
```

## ⚠️ Casos Especiales

### 1. Presupuestos
Los presupuestos (tipo 'PRES') **NUNCA** mueven stock:
```python
if documento.tipo == 'PRES':
    return  # No procesar
```

### 2. Líneas Manuales vs Vinculadas
Solo se procesan líneas con `repuesto_id` (vinculadas con inventario):
```python
lineas = documento.lineas_repuesto.filter(repuesto__isnull=False)
```

### 3. Ediciones Completas
El método `procesar_edicion()` maneja:
- Cambios de cantidad → Ajusta diferencia
- Líneas agregadas → Descuenta cantidad nueva
- Líneas eliminadas → Repone cantidad eliminada

## ✅ Ventajas vs Implementación Manual

| Aspecto | Manual en save() | InventoryService |
|---------|-----------------|------------------|
| **Organización** | Código mezclado | Servicio dedicado |
| **Thread-Safety** | Riesgo de race conditions | F() expressions (atómico) |
| **Validación** | Difícil validar antes | Método dedicado |
| **Ediciones** | Lógica compleja | Método dedicado |
| **Mantenibilidad** | Media | Alta |
| **Testing** | Difícil | Fácil (servicio aislado) |

## 📝 Logging

El servicio registra todos los movimientos:

```
[InventoryService] 📦 Inventario: Procesando descontar para Doc WO001 (Tipo: OT)
[InventoryService]   ✅ Filtro de Aceite: Descontado 2 unidades. Stock: 10 → 8
[InventoryService]   ✅ Bujía: Descontado 4 unidades. Stock: 15 → 11
```

## 🚀 Próximos Pasos Opcionales

1. **Kardex/Historial de Movimientos**
   - Registrar cada movimiento en tabla de historial
   - Permite auditoría completa

2. **Notificaciones de Stock Bajo**
   - Alertar cuando stock < mínimo configurado

3. **Stock Reservado**
   - Reservar stock en presupuestos (opcional)

4. **API de Stock**
   - Endpoint para consultar stock disponible

## ✅ Checklist de Implementación

- [x] Servicio de inventario creado
- [x] Señales de inventario configuradas
- [x] Vistas de emitir/anular creadas
- [x] Validación de stock implementada
- [x] Manejo de ediciones implementado
- [x] Thread-safety con F() expressions
- [x] Multi-tenant seguro
- [x] Logging de movimientos
- [ ] Kardex/Historial (opcional)
- [ ] Notificaciones de stock bajo (opcional)

## 🎉 Resultado

Con este servicio, tu sistema ahora:
- ✅ Actualiza stock automáticamente al emitir documentos
- ✅ Valida stock antes de permitir emisión
- ✅ Devuelve stock al anular documentos
- ✅ Ajusta stock correctamente en ediciones
- ✅ Es thread-safe y multi-tenant seguro

**¡Inventario completo implementado!** 🎊

