# Arquitectura Desarme – Ajustes aprobados y especificación para implementación

**Fecha:** 2025-03-11  
**Estado:** Aprobado conceptualmente; especificación previa a implementación de código.  
**Relación:** Complementa y ajusta `PROPUESTA_ARQUITECTURA_DESARME.md`.

---

## Resumen de ajustes incorporados

| # | Ajuste | Decisión |
|---|--------|----------|
| 1 | Vehículos – un solo modelo, `cliente` NULL en desarme | Validaciones en `Vehiculo.clean()`: CLIENTE → cliente obligatorio; DESARME → cliente NULL. Revisar todo el proyecto donde se asuma `vehiculo.cliente` existe. |
| 2 | Documento.vehiculo | Selector/autocomplete/filtros limitados a `Vehiculo.tipo_uso = CLIENTE`. Desarme no aparece en documento. |
| 3 | Significado de `origen_repuesto` | EXTERNO / STOCK_BODEGA / DESARME definidos de forma explícita (ver sección 3). |
| 4 | PiezaDesarme vs Repuesto | Repuesto = catálogo/inventario bodega. PiezaDesarme = unidad física de yarda con trazabilidad. PiezaDesarme puede referenciar opcionalmente `repuesto`/`part`. |
| 5 | PiezaDesarme – campos operativos | Agregar `estado_pieza`, `ubicacion_fisica`, `observaciones`; opcionalmente `lado`, `zona`, `posicion`. |
| 6 | Búsqueda unificada en documentos | Diseño de buscador que combine Repuesto + PiezaDesarme con etiqueta de origen (BODEGA / DESARME / EXTERNO). Sin UI completo aún. |
| 7 | InventoryService | Lógica explícita por origen: STOCK_BODEGA → Repuesto; DESARME → PiezaDesarme; EXTERNO → no inventario. Reversión al anular. |
| 8 | Campos adicionales en Vehiculo (desarme) | `ubicacion_fisica`, `fecha_baja_desarme`, `observaciones_desarme`. |
| 9 | Sin UI masiva todavía | Implementar primero: modelos, migraciones, InventoryService, validaciones, CRUD básico PiezaDesarme. Dashboards/reportes/kanban después. |
| 10 | Entregable actual | Este documento: modelos finales, LineaRepuesto, InventoryService, migraciones y análisis de impacto. |

---

## 1. Modelo final de Vehiculo (actualizado)

### 1.1 Cambios respecto al actual

- **`cliente`**: pasar a `null=True, blank=True`. Obligatorio solo cuando `tipo_uso == 'CLIENTE'`.
- **Nuevos campos** (ya en propuesta): `tipo_uso`, `costo_adquisicion`, `fecha_ingreso_desarme`, `estado_desarme`.
- **Campos adicionales para desarme**: `ubicacion_fisica`, `fecha_baja_desarme`, `observaciones_desarme`.

### 1.2 Definición

```python
# taller/models/vehiculos.py

class Vehiculo(TenantScoped):
    TIPO_USO_CLIENTE = "CLIENTE"
    TIPO_USO_DESARME = "DESARME"
    TIPO_USO_CHOICES = [
        (TIPO_USO_CLIENTE, "Cliente"),
        (TIPO_USO_DESARME, "Desarme"),
    ]

    # Nullable cuando tipo_uso == DESARME
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Obligatorio si tipo_uso=CLIENTE; debe ser NULL si tipo_uso=DESARME.",
    )
    tipo_uso = models.CharField(
        max_length=20,
        choices=TIPO_USO_CHOICES,
        default=TIPO_USO_CLIENTE,
        db_index=True,
    )

    # ... (marca, modelo, patente, anio, etc. sin cambio) ...

    # --- Campos solo relevantes para DESARME ---
    costo_adquisicion = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    fecha_ingreso_desarme = models.DateField(null=True, blank=True)
    estado_desarme = models.CharField(
        max_length=20, null=True, blank=True
    )  # EN_YARDA, EN_DESARME, DESARMADO, BAJA
    ubicacion_fisica = models.CharField(
        max_length=120, null=True, blank=True,
        help_text="Ubicación en la yarda (ej: fila 3, posición 12)",
    )
    fecha_baja_desarme = models.DateField(null=True, blank=True)
    observaciones_desarme = models.TextField(blank=True, null=True)

    def clean(self):
        super().clean()
        # 1) Regla cliente ↔ tipo_uso
        if self.tipo_uso == self.TIPO_USO_CLIENTE:
            if not self.cliente_id:
                raise ValidationError(
                    "Si el vehículo es de cliente, debe tener un cliente asignado."
                )
        elif self.tipo_uso == self.TIPO_USO_DESARME:
            if self.cliente_id is not None:
                raise ValidationError(
                    "Un vehículo de desarme no debe tener cliente asignado."
                )
        # 2) Empresa coherente con cliente (solo si hay cliente)
        if self.empresa_id and self.cliente_id and self.cliente.empresa_id != self.empresa_id:
            raise ValidationError(
                "El cliente del vehículo debe pertenecer a la misma empresa."
            )
        # ... resto de validaciones existentes (VIN/patente, marca/modelo, motor/caja) ...
```

### 1.3 Índices recomendados

- `(empresa, tipo_uso)` para listados y filtros.
- Mantener `(empresa, cliente)` para vehiculos-por-cliente (solo tendrán cliente los CLIENTE).

---

## 2. Modelo completo de PiezaDesarme

### 2.1 Rol

- **Repuesto**: catálogo e inventario de bodega (identidad comercial).
- **PiezaDesarme**: unidad física extraída de un vehículo en la yarda; trazabilidad por vehículo; puede opcionalmente vincularse a `Repuesto` o `Part` para reutilizar catálogo.

### 2.2 Multi-tenant y auditoría

**PiezaDesarme** sigue el patrón canónico del proyecto: hereda de **`TenantScoped`** (como `Vehiculo` y `Repuesto`), con `empresa` FK, `created_at` y `updated_at`. No se usa `AuditMixin` en PiezaDesarme para mantener coherencia con Repuesto/Vehiculo.

### 2.3 costo_asignado

**Definición:** Costo **unitario** imputado (por unidad). El costo total de la partida es `costo_asignado * cantidad`. Rentabilidad por línea: `precio_unitario * cantidad - costo_asignado * cantidad`.

### 2.4 Cantidad y estado_pieza (regla final)

- **cantidad**: Número de unidades físicas de esta partida (puede ser > 1).
- **estado_pieza** aplica a la **partida completa** (registro):
  - **DISPONIBLE**: tiene stock (`cantidad > 0`) y está disponible para venta.
  - **RESERVADA**: reservada para un cliente/pedido (no se descuenta hasta confirmar).
  - **VENDIDA**: **todas** las unidades vendidas (`cantidad` llegó a 0). Se marca al descontar la última unidad.
  - **DANADA** / **SCRAP**: baja por daño o chatarra.

Al vender: se descuenta `cantidad`. Cuando `cantidad` pasa a 0, actualizar `estado_pieza = VENDIDA` y `activo = False`. No usar VENDIDA para ventas parciales; solo cuando la partida queda sin stock.

### 2.5 Estados de pieza (choices)

```python
ESTADO_DISPONIBLE = "DISPONIBLE"
ESTADO_RESERVADA = "RESERVADA"
ESTADO_VENDIDA = "VENDIDA"
ESTADO_DANADA = "DANADA"
ESTADO_SCRAP = "SCRAP"
ESTADO_PIEZA_CHOICES = [
    (ESTADO_DISPONIBLE, "Disponible"),
    (ESTADO_RESERVADA, "Reservada"),
    (ESTADO_VENDIDA, "Vendida"),
    (ESTADO_DANADA, "Dañada"),
    (ESTADO_SCRAP, "Scrap"),
]
```

### 2.6 Definición (TenantScoped + clean)

```python
# taller/models/pieza_desarme.py

from core.models import TenantScoped

class PiezaDesarme(TenantScoped):
    vehiculo = models.ForeignKey(
        "taller.Vehiculo",
        on_delete=models.PROTECT,
        related_name="piezas_desarme",
        limit_choices_to={"tipo_uso": "DESARME"},
    )

    # Catálogo opcional
    repuesto = models.ForeignKey(
        "taller.Repuesto",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="piezas_desarme",
    )
    part = models.ForeignKey(
        "taller.Part",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="piezas_desarme",
    )

    codigo = models.CharField(max_length=100, db_index=True)
    nombre = models.CharField(max_length=255)
    cantidad = models.PositiveIntegerField(default=1)
    costo_asignado = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Costo unitario imputado (por unidad).",
    )
    precio_venta_sugerido = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    fecha_extraccion = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    # Campos operativos
    estado_pieza = models.CharField(
        max_length=20,
        choices=ESTADO_PIEZA_CHOICES,
        default=ESTADO_DISPONIBLE,
        db_index=True,
    )
    ubicacion_fisica = models.CharField(max_length=120, null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)
    # Opcionales para mapas / inventario físico
    lado = models.CharField(max_length=50, null=True, blank=True)
    zona = models.CharField(max_length=50, null=True, blank=True)
    posicion = models.CharField(max_length=50, null=True, blank=True)

    # created_at, updated_at, empresa vienen de TenantScoped

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.vehiculo_id and self.vehiculo.tipo_uso != "DESARME":
            raise ValidationError(
                {"vehiculo": "El vehículo debe ser de tipo Desarme."}
            )
        if self.empresa_id and self.vehiculo_id and self.vehiculo.empresa_id != self.empresa_id:
            raise ValidationError(
                "La pieza y el vehículo deben pertenecer a la misma empresa."
            )
        if self.repuesto_id and self.repuesto.empresa_id != self.empresa_id:
            raise ValidationError(
                "El repuesto referenciado debe pertenecer a la misma empresa."
            )
        if getattr(self, "part_id", None) and self.part and self.part.empresa_id not in (None, self.empresa_id):
            raise ValidationError(
                "El part referenciado debe ser de la misma empresa o catálogo global."
            )

    class Meta(TenantScoped.Meta):
        verbose_name = "Pieza de desarme"
        verbose_name_plural = "Piezas de desarme"
        indexes = [
            models.Index(fields=["empresa", "vehiculo"]),
            models.Index(fields=["empresa", "codigo"]),
            models.Index(fields=["empresa", "estado_pieza"]),
        ]
```

---

## 3. Cambios en LineaRepuesto

### 3.1 Significado explícito de origen_repuesto

| Valor | Significado | Inventario |
|-------|-------------|------------|
| **EXTERNO** | Compra directa para este documento (ej. a otro autopart). No ingresa a inventario. | No genera movimiento. |
| **STOCK_BODEGA** | Repuesto existente en bodega (`Repuesto`). | Se descuenta vía `InventoryService` en `Repuesto`. |
| **DESARME** | Pieza extraída de vehículo de desarme. | Se descuenta en `PiezaDesarme`. |

### 3.2 Campos a agregar en LineaRepuesto

```python
# taller/models/lineas_documento.py

ORIGEN_EXTERNO = "EXTERNO"
ORIGEN_STOCK_BODEGA = "STOCK_BODEGA"
ORIGEN_DESARME = "DESARME"
ORIGEN_REPUESTO_CHOICES = [
    (ORIGEN_EXTERNO, "Externo"),
    (ORIGEN_STOCK_BODEGA, "Stock bodega"),
    (ORIGEN_DESARME, "Desarme"),
]

class LineaRepuesto(models.Model):
    # ... campos existentes (documento, repuesto, part, codigo, nombre, cantidad, precio_unitario, descuento, observaciones, tecnico_responsable) ...

    origen_repuesto = models.CharField(
        max_length=20,
        choices=ORIGEN_REPUESTO_CHOICES,
        default=ORIGEN_STOCK_BODEGA,
        db_index=True,
    )
    pieza_desarme = models.ForeignKey(
        "taller.PiezaDesarme",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="lineas_repuesto",
    )
    costo_linea = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Costo para rentabilidad (EXTERNO: costo compra; DESARME: puede venir de PiezaDesarme).",
    )

    def clean(self):
        # ... validaciones country existentes ...
        if self.origen_repuesto == ORIGEN_DESARME:
            if not self.pieza_desarme_id:
                raise ValidationError("Origen Desarme requiere pieza de desarme.")
            if self.pieza_desarme.cantidad < self.cantidad:
                raise ValidationError(
                    f"Stock insuficiente en pieza de desarme. Disponible: {self.pieza_desarme.cantidad}"
                )
        elif self.origen_repuesto == ORIGEN_STOCK_BODEGA:
            if not (self.repuesto_id or getattr(self, "part_id", None)):
                raise ValidationError("Origen Stock bodega requiere repuesto o part.")
        # EXTERNO: sin obligación de repuesto/part; opcional costo_linea.
```

### 3.3 Compatibilidad

- Líneas existentes: migración con `origen_repuesto='STOCK_BODEGA'`, `pieza_desarme=None`, `costo_linea=None`.

---

## 4. Cambios necesarios en InventoryService

### 4.1 Reglas explícitas

```text
if origen_repuesto == STOCK_BODEGA:
    usar lógica actual (descontar/reponer en Repuesto)
if origen_repuesto == DESARME:
    descontar/reponer en PiezaDesarme (por pieza_desarme_id)
if origen_repuesto == EXTERNO:
    no mover inventario
```

### 4.2 Procesar movimiento (procesar_movimiento_stock)

- Filtrar líneas según `origen_repuesto`:
  - **STOCK_BODEGA**: líneas con `repuesto_id` (o `part` si se usa para stock); descontar/reponer en `Repuesto` como hoy.
  - **DESARME**: líneas con `pieza_desarme_id`; descontar/reponer `PiezaDesarme.cantidad`; si cantidad llega a 0, marcar `activo=False` y/o `estado_pieza=VENDIDA` según regla de negocio.
  - **EXTERNO**: no tocar inventario.
- Reversión al anular: mismo criterio por origen; para DESARME, reponer cantidad en `PiezaDesarme` y revertir estado si aplica.

### 4.3 Validar stock (validar_stock_disponible)

- **STOCK_BODEGA**: como hoy (`Repuesto.cantidad_stock >= linea.cantidad`).
- **DESARME**: `linea.pieza_desarme.cantidad >= linea.cantidad` y pieza activa.
- **EXTERNO**: no validar stock.

### 4.4 Procesar edición (procesar_edicion)

- Por cada línea, según `origen_repuesto`: aplicar diferencias en `Repuesto` o en `PiezaDesarme`; EXTERNO sin movimiento.

### 4.5 Resumen de firma sugerida

- `procesar_movimiento_stock(documento, accion)`:
  - Itera `documento.lineas_repuesto`.
  - Por cada línea: lee `origen_repuesto`; si STOCK_BODEGA y tiene repuesto → actualiza Repuesto; si DESARME y tiene pieza_desarme → actualiza PiezaDesarme; si EXTERNO → skip.
- `validar_stock_disponible(documento)`: incluir validación para líneas DESARME (y STOCK_BODEGA como hoy).
- Al anular: llamar `procesar_movimiento_stock(documento, "reponer")` con la misma lógica por origen.

---

## 5. Búsqueda unificada en creación de documentos (diseño)

### 5.1 Objetivo

Al agregar una línea de repuesto, el usuario debe poder encontrar:

- Repuestos de bodega (`Repuesto`).
- Piezas de desarme (`PiezaDesarme`).

Y ver claramente el origen en los resultados.

### 5.2 Enfoque a nivel de consultas

- **Opción A – Endpoint único**: Un endpoint (ej. `GET /api/repuestos-busqueda/?q=alternador`) que:
  - Busca en `Repuesto` (por nombre/código) filtrado por empresa.
  - Busca en `PiezaDesarme` (por nombre/código, activo, estado DISPONIBLE) filtrado por empresa.
  - Devuelve una lista unificada con un campo `origen`: `"STOCK_BODEGA"` o `"DESARME"`, y para DESARME un identificador de vehículo (patente/VIN) para mostrar en UI.
- **Opción B – Dos endpoints**: Uno para repuestos bodega y otro para piezas desarme; el frontend los llama en paralelo y muestra dos bloques o una lista mezclada con etiqueta de origen.

Formato de ítem sugerido para respuesta unificada:

```json
{
  "origen": "DESARME",
  "id": 123,
  "tipo_id": "pieza_desarme",
  "codigo": "ALT-001",
  "nombre": "Alternador Bosch",
  "cantidad_disponible": 2,
  "vehiculo_origen": "ABC123 - Toyota Yaris 2015",
  "precio_sugerido": 150000
}
```

```json
{
  "origen": "STOCK_BODEGA",
  "id": 456,
  "tipo_id": "repuesto",
  "codigo": "ALT-BOSCH",
  "nombre": "Alternador Bosch",
  "cantidad_disponible": 5,
  "vehiculo_origen": null,
  "precio_sugerido": 120000
}
```

- No implementar aún el UI completo; solo dejar definido el contrato de la API y la lógica de consultas (y que EXTERNO sea opción manual sin búsqueda de inventario).

---

## 6. InventoryService canónico y paths del proyecto

### 6.1 Servicio de inventario canónico

**Única implementación:** `taller/services/inventory_service.py`.  
El módulo `taller/reportes/services/inventory_service.py` es una copia duplicada; debe **re-exportar** desde `taller.services.inventory_service` para no mantener dos implementaciones. Quienes importen desde `taller.reportes.services` seguirán funcionando; la lógica se modifica solo en `taller/services/inventory_service.py`.

### 6.2 Paths y nombres reales (confirmados)

| Concepto | Path / nombre |
|---------|----------------|
| Modelo Vehiculo | `taller/models/vehiculos.py` → `class Vehiculo(TenantScoped)` |
| Modelo LineaRepuesto | `taller/models/lineas_documento.py` → `class LineaRepuesto(models.Model)` |
| Modelo Documento | `taller/models/documento.py` → `class Documento(AuditMixin, models.Model)` |
| Formularios de documento | `taller/forms/documento_form.py` (DocumentoForm), `taller/documentos/forms.py` (form con DAL) |
| Autocomplete vehículo | `taller/views_autocomplete.py` → `VehiculoAutocomplete`; `taller/autocomplete.py` (legacy) |
| Servicio de inventario | `taller/services/inventory_service.py` → `InventoryService` |
| Señales inventario | `taller/documentos/signals_inventory.py` (importa desde `taller.services.inventory_service`) |

---

## 7. Migraciones propuestas

### 7.1 Orden sugerido

1. **Vehiculo**
   - Añadir `tipo_uso` (default `'CLIENTE'`).
   - Hacer `cliente` nullable (`null=True, blank=True`).
   - Añadir `costo_adquisicion`, `fecha_ingreso_desarme`, `estado_desarme`, `ubicacion_fisica`, `fecha_baja_desarme`, `observaciones_desarme`.
   - Añadir índice `(empresa, tipo_uso)`.
   - Datos: los vehículos existentes quedan con `tipo_uso='CLIENTE'` y su `cliente` actual (sin cambios).

2. **PiezaDesarme**
   - Crear modelo completo (tabla nueva).

3. **LineaRepuesto**
   - Añadir `origen_repuesto` (default `'STOCK_BODEGA'`).
   - Añadir `pieza_desarme` (FK, null, blank).
   - Añadir `costo_linea` (null, blank).
   - Datos: todas las líneas existentes con `origen_repuesto='STOCK_BODEGA'`, `pieza_desarme=None`.

### 7.2 Consideraciones

- No eliminar columnas ni FKs existentes salvo que se decida explícitamente.
- Las migraciones de datos deben ser reversibles en la medida de lo posible (por ejemplo, no borrar datos al hacer `ReverseMigrate`).

---

## 8. Análisis de impacto en el proyecto actual

### 8.1 Vehiculo.cliente nullable – puntos a revisar/corregir

Se asume en varios puntos que `vehiculo.cliente` existe. Ajustes necesarios:

| Ubicación | Uso actual | Ajuste |
|-----------|------------|--------|
| **Templates** (detalle/detalle vehículo) | `vehiculo.cliente.nombre`, etc. | Envolver en `{% if vehiculo.cliente %}`; si no, mostrar "—" o "Vehículo de desarme". |
| **taller/models/documento.py** `clean()` | `self.vehiculo.cliente_id != self.cliente_id` | Ya usa `hasattr(self.vehiculo, "cliente_id")`; añadir que solo se exija coincidencia si `vehiculo.cliente_id` no es None (si documento.vehiculo es solo CLIENTE, en la práctica siempre habrá cliente). |
| **taller/forms/documento_form.py** (DocumentoForm.clean) | `vehiculo.cliente != cliente` | Solo validar si `vehiculo.cliente_id` no es None. |
| **taller/documentos/forms.py** (forms_dal) | `vehiculo.cliente_id != cliente.id` | Idem. |
| **taller/forms/documento_form.py** __init__ | `Vehiculo.objects.filter(empresa=self.empresa)` para vehiculo | Restringir a `tipo_uso=CLIENTE` (y opcionalmente por cliente cuando haya cliente). |
| **taller/documentos/forms.py** __init__ | `qs_veh = Vehiculo.objects.filter(empresa=empresa)` y filtro por cliente_id | Restringir base a `tipo_uso=CLIENTE`; filtro por cliente sigue igual. |
| **taller/views_autocomplete.py** VehiculoAutocomplete | `qs = Vehiculo.objects...filter(empresa=empresa)` y filtro por cliente_id | Restringir a `Vehiculo.objects.filter(empresa=empresa, tipo_uso=Vehiculo.TIPO_USO_CLIENTE)`. |
| **taller/autocomplete.py** (legacy) | `Vehiculo.objects.filter(empresa=...)` | Añadir filtro `tipo_uso=CLIENTE`. |
| **taller/api/views.py** | `vehiculos_cliente_api`: `Vehiculo.objects.filter(cliente_id=..., cliente__empresa=...)` | Ya filtra por cliente; vehículos de desarme no tienen cliente, no aparecerán. Sin cambio estricto; opcionalmente documentar. |
| **taller/documentos/api.py** `api_vehiculos_por_cliente` | `Vehiculo.objects.filter(cliente_id=cid, empresa=...)` | Idem. |
| **taller/vehiculos/views_ingreso.py** | `cliente = vehiculo.cliente` | Si la vista es solo para vehículos de cliente, validar `vehiculo.cliente`; si no existe, redirigir o mensaje "Vehículo de desarme". |
| **taller/reportes/views.py** | `vehiculo.cliente.nombre if vehiculo.cliente else "N/A"` | Ya contempla None. |
| **taller/reportes/kilometraje_reportes.py** | `vehiculo.cliente.nombre if vehiculo.cliente else "N/A"` | Ya contempla None. |
| **taller/utils/garantias.py** | `documento.vehiculo` y uso posterior | Si se usa para garantía de cliente, documento.vehiculo ya será de cliente (por restricción en formulario). Aún así, comprobar que no se acceda a `.cliente` sin comprobar. |
| **scripts/validaciones_consistencia_extendidas.py** | `self.vehiculo.cliente != self.cliente` | Solo si `vehiculo.cliente_id` no es None. |
| **management/commands/audit_tenant_isolation.py** | Asigna `vehiculo.empresa` desde `vehiculo.cliente.empresa` | Si `vehiculo.cliente` es None (desarme), no asignar empresa desde cliente; usar otra regla o dejar empresa ya definida. |

### 8.2 Documento.vehiculo – solo vehículos CLIENTE

- **Formularios de documento**: queryset de `vehiculo` = `Vehiculo.objects.filter(empresa=..., tipo_uso=Vehiculo.TIPO_USO_CLIENTE)` (y por cliente cuando corresponda).
- **Autocompletes de vehículo para documento**: mismo filtro `tipo_uso=CLIENTE`.
- **APIs que devuelven vehículos para selector de documento**: aplicar el mismo filtro.
- No cambiar el significado de `Documento.vehiculo`: sigue siendo el vehículo del cliente al que se le hace el servicio; los de desarme no se seleccionan ahí.

### 8.3 Reportes y listados de vehículos

- Donde se listen vehículos: opcionalmente filtro por `tipo_uso` (pestaña "Desarme" vs "Clientes").
- Donde se muestre `vehiculo.cliente`: usar `vehiculo.cliente` con fallback "—" o "N/A" cuando sea None.

### 8.4 InventoryService

- Todas las rutas que hoy asumen "línea con repuesto" deben considerar `origen_repuesto` y reparto entre Repuesto y PiezaDesarme; EXTERNO sin movimiento.
- Tests existentes que dan por hecho que toda línea tiene `repuesto`: adaptar a líneas con `origen_repuesto=STOCK_BODEGA` y repuesto; añadir tests para DESARME y EXTERNO.

### 8.5 Resumen de archivos a tocar (implementación fase 1)

- **Modelos**: `taller/models/vehiculos.py`, nuevo `taller/models/pieza_desarme.py`, `taller/models/lineas_documento.py`.
- **Migraciones**: una por modelo (Vehiculo, PiezaDesarme, LineaRepuesto).
- **Servicios**: `taller/services/inventory_service.py` (y si existe copia en `taller/reportes/services/inventory_service.py`, unificar o mantener misma lógica).
- **Formularios**: `taller/forms/documento_form.py`, `taller/documentos/forms.py` (queryset vehículo + validación cliente).
- **Autocomplete**: `taller/views_autocomplete.py` (VehiculoAutocomplete), `taller/autocomplete.py` si se usa.
- **Validación documento**: `taller/models/documento.py` `clean()` (cliente/vehiculo solo cuando vehiculo tenga cliente).
- **Templates**: todos los que usen `vehiculo.cliente` sin comprobación: añadir `{% if vehiculo.cliente %}` o equivalente (ver lista en 7.1).
- **Reportes/scripts**: los que usen `vehiculo.cliente` sin comprobación: añadir `if vehiculo.cliente` o equivalente.

---

## 9. Orden de implementación recomendado (sin UI masiva)

1. **Modelos y migraciones**: Vehiculo (incl. validación clean cliente/tipo_uso), PiezaDesarme, LineaRepuesto.
2. **InventoryService**: extender por `origen_repuesto` (STOCK_BODEGA / DESARME / EXTERNO), validación de stock y reversión al anular.
3. **Validaciones de línea**: `LineaRepuesto.clean()` según origen (DESARME → pieza_desarme y stock; STOCK_BODEGA → repuesto/part).
4. **Ajustes por cliente NULL**: formularios documento, autocomplete vehículo (filtrar tipo_uso=CLIENTE), Documento.clean(), templates y reportes que usen vehiculo.cliente.
5. **CRUD básico PiezaDesarme**: vistas/forms/admin mínimos para alta/baja/consulta de piezas por vehículo de desarme.
6. **Búsqueda unificada**: diseño de API y consultas (sin UI completo); opcionalmente endpoint o dos endpoints documentados.

Después de esto: reportes, dashboards, kanban y gráficos de desarme.

---

## 10. Resultado esperado tras estos ajustes

El sistema podrá manejar de forma coherente:

- Vehículos de **cliente** y vehículos de **desarme** (un solo modelo `Vehiculo`).
- Inventario de **bodega** (`Repuesto`) e inventario de **yarda** (`PiezaDesarme`).
- **Compras externas** (origen EXTERNO) sin movimiento de inventario.
- **Venta unificada** en documentos con líneas de los tres orígenes.
- **Trazabilidad** por vehículo de desarme vía `PiezaDesarme.vehiculo`.
- **Cálculo de recuperación y utilidad** por vehículo desarmado y por origen de repuesto.

Todo ello con la arquitectura de datos definida en este documento y sin implementar todavía reportes ni dashboards complejos.
