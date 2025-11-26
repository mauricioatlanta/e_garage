# 📦 Guía de Uso: Servicio de Inventario

## 🎯 Resumen Ejecutivo

El servicio de inventario maneja automáticamente los movimientos de stock cuando cambias el estado de los documentos. **No necesitas hacer nada manual** - todo es automático.

## ⚡ Uso Rápido

### Emitir un Documento

```python
# En tu vista
documento.estado = 'EMITIDO'
documento.save()  # ✅ Stock se descuenta automáticamente
```

### Anular un Documento

```python
# En tu vista
documento.estado = 'ANULADO'
documento.save()  # ✅ Stock se repone automáticamente
```

### Validar Stock (Sin Emitir)

```python
from taller.services.inventory_service import InventoryService

errores = InventoryService.validar_stock_disponible(documento)
if errores:
    # Mostrar errores al usuario
    for error in errores:
        print(error)
```

## 📋 Reglas de Negocio

### ✅ Documentos que MUEVEN Stock

- **OT** (Orden de Trabajo) → SÍ mueve stock
- **FAC** (Factura/Boleta) → SÍ mueve stock

### ❌ Documentos que NO MUEVEN Stock

- **PRES** (Presupuesto) → NO mueve stock

### 🔄 Estados y Acciones

| Estado Anterior | Estado Nuevo | Acción de Stock |
|-----------------|--------------|-----------------|
| BORRADOR | EMITIDO | ✅ Descontar |
| EMITIDO | ANULADO | ✅ Reponer |
| ANULADO | EMITIDO | ✅ Descontar |
| EMITIDO | EMITIDO (edición) | ✅ Ajustar diferencia |

## 🔧 Integración en Vistas

### Vista para Emitir Documento

```python
from taller.services.inventory_service import InventoryService

@login_required
def emitir_documento(request, documento_id):
    documento = get_object_or_404(
        Documento.objects.select_related('empresa').prefetch_related(
            'lineas_repuesto__repuesto'
        ),
        id=documento_id,
        empresa=request.user.empresa  # 🔒 Multi-tenant
    )
    
    # 1. Validar stock ANTES de emitir
    errores = InventoryService.validar_stock_disponible(documento)
    
    if errores:
        messages.error(request, "No se puede emitir el documento:")
        for error in errores:
            messages.error(request, error)
        return redirect('documentos:ver_documento', pk=documento.pk)
    
    # 2. Cambiar estado (la señal procesará el stock automáticamente)
    documento.estado = 'EMITIDO'
    documento.save()  # ✅ Señal descuenta stock
    
    messages.success(request, "Documento emitido. Stock actualizado.")
    return redirect('documentos:ver_documento', pk=documento.pk)
```

### Vista para Anular Documento

```python
@login_required
def anular_documento(request, documento_id):
    documento = get_object_or_404(
        Documento,
        id=documento_id,
        empresa=request.user.empresa  # 🔒 Multi-tenant
    )
    
    # Cambiar estado (la señal procesará la reposición automáticamente)
    documento.estado = 'ANULADO'
    documento.save()  # ✅ Señal repone stock
    
    messages.success(request, "Documento anulado. Stock repuesto.")
    return redirect('documentos:ver_documento', pk=documento.pk)
```

## 🎨 Ejemplo Completo en Template

```html
<!-- templates/taller/documentos/detalle_documento.html -->

{% if documento.estado == 'BORRADOR' %}
    <form method="post" action="{% url 'documentos:emitir_documento' documento.id %}">
        {% csrf_token %}
        <button type="submit" class="btn btn-success">
            📄 Emitir Documento
        </button>
    </form>
{% elif documento.estado == 'EMITIDO' %}
    <form method="post" action="{% url 'documentos:anular_documento' documento.id %}">
        {% csrf_token %}
        <button type="submit" class="btn btn-danger">
            ❌ Anular Documento
        </button>
    </form>
{% endif %}
```

## 🔍 Debugging y Logs

El servicio registra todos los movimientos en los logs:

```python
# Ver logs en consola
# Ejemplo de salida:

[InventoryService] 📦 Inventario: Procesando descontar para Doc WO001 (Tipo: OT)
[InventoryService]   ✅ Filtro de Aceite: Descontado 2 unidades. Stock: 10 → 8
[InventoryService]   ✅ Bujía: Descontado 4 unidades. Stock: 15 → 11
```

## ⚠️ Casos Especiales

### 1. Ediciones de Documentos Emitidos

Si editas un documento emitido, el servicio ajusta automáticamente:

```python
# Ejemplo: Cambiar cantidad de 2 a 3
# Antes: Stock = 10
# Después: Stock = 9 (descuenta 1 extra)
```

### 2. Líneas Sin Repuesto Vinculado

Las líneas escritas manualmente (sin `repuesto_id`) **NO** mueven stock:

```python
# Solo se procesan líneas con repuesto vinculado
lineas = documento.lineas_repuesto.filter(repuesto__isnull=False)
```

### 3. Presupuestos

Los presupuestos **NUNCA** mueven stock, incluso si están emitidos:

```python
if documento.tipo == 'PRES':
    return  # No procesar
```

## ✅ Testing Manual

### Test 1: Crear y Emitir Documento

```python
# 1. Crear documento en borrador
documento = Documento.objects.create(
    empresa=empresa,
    cliente=cliente,
    tipo='OT',
    estado='BORRADOR'
)

# 2. Agregar línea con repuesto
LineaRepuesto.objects.create(
    documento=documento,
    repuesto=repuesto,  # ✅ Vinculado con inventario
    nombre='Filtro de Aceite',
    cantidad=2,
    precio_unitario=10000,
)

# 3. Verificar stock inicial
print(f"Stock inicial: {repuesto.cantidad_stock}")  # Ej: 10

# 4. Emitir documento
documento.estado = 'EMITIDO'
documento.save()

# 5. Verificar stock después
repuesto.refresh_from_db()
print(f"Stock después: {repuesto.cantidad_stock}")  # Ej: 8 (10 - 2)
```

### Test 2: Anular Documento

```python
# 1. Documento emitido (stock ya descontado)
documento.estado = 'EMITIDO'
documento.save()

# 2. Verificar stock
print(f"Stock después de emitir: {repuesto.cantidad_stock}")  # Ej: 8

# 3. Anular documento
documento.estado = 'ANULADO'
documento.save()

# 4. Verificar stock repuesto
repuesto.refresh_from_db()
print(f"Stock después de anular: {repuesto.cantidad_stock}")  # Ej: 10 (8 + 2)
```

## 🚨 Troubleshooting

### Problema: Stock no se actualiza

**Posibles causas:**
1. Documento es tipo PRES (presupuesto) → No mueve stock (normal)
2. Línea no tiene `repuesto_id` → Solo se procesan líneas vinculadas
3. Señales no están registradas → Verificar `apps.py`

### Problema: Error al emitir

**Verificar:**
1. Stock suficiente para todas las líneas
2. Documento no está anulado
3. Todas las líneas tienen repuesto válido

### Verificar Señales

```python
# En Django shell
from django.db.models.signals import pre_save
from taller.models.documento import Documento

# Verificar que la señal está registrada
receiver_list = pre_save._live_receivers(sender=Documento)
print(f"Señales registradas: {len(receiver_list)}")
```

## 📊 Ejemplo de Flujo Completo

```
1. Usuario crea documento con repuestos
   → Estado: BORRADOR
   → Stock: NO se mueve

2. Usuario hace clic en "Emitir"
   → Vista valida stock
   → Si hay stock: cambia estado a EMITIDO
   → Señal detecta cambio
   → Servicio descuenta stock automáticamente

3. Usuario edita documento emitido
   → Cambia cantidad de 2 a 3
   → Señal detecta edición
   → Servicio ajusta diferencia (descuenta 1 extra)

4. Usuario anula documento
   → Vista cambia estado a ANULADO
   → Señal detecta cambio
   → Servicio repone todo el stock
```

## ✅ Checklist de Verificación

- [x] Servicio de inventario creado
- [x] Señales configuradas en `apps.py`
- [x] URLs agregadas
- [x] Vistas creadas
- [x] Validación de stock implementada
- [x] Thread-safety con F() expressions
- [x] Multi-tenant seguro
- [x] Logging configurado

¡Todo listo! El inventario funciona automáticamente. 🎉

