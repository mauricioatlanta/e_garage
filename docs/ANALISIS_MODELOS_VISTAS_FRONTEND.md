# 📊 Análisis: Modelos, Vistas Multi-Tenant y Conversión Frontend

## 1. 📦 Revisión de Modelos: Cálculos en Documento y LineaRepuesto

### 1.1 Modelo `Documento` - Cálculos Centralizados

El modelo `Documento` maneja todos los cálculos financieros de forma centralizada:

```python
# taller/models/documento.py

class Documento(AuditMixin, models.Model):
    empresa = models.ForeignKey("taller.Empresa", ...)  # 🔒 Multi-tenant
    
    # Campos de totales
    neto_repuestos = models.DecimalField(...)
    neto_servicios = models.DecimalField(...)
    neto_otros_servicios = models.DecimalField(...)
    descuento = models.DecimalField(...)
    tax_rate_applied = models.DecimalField(...)
    tax_amount = models.DecimalField(...)
    total = models.DecimalField(...)
    
    def _sum_repuesto(self):
        """Suma repuestos con descuento por línea"""
        qs = getattr(self, "lineas_repuesto", None)
        if not qs:
            return Decimal("0")
        
        # Calcular con descuento porcentual
        expr = ExpressionWrapper(
            F("cantidad") * F("precio_unitario") * (1 - F("descuento") / 100),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
        total = qs.aggregate(s=Sum(expr)).get("s") or Decimal("0")
        return Decimal(total)
    
    def recompute_totals(self, persist=False):
        """
        Recalcula netos, impuesto y total conforme reglas:
        - CL: IVA 19% SOLO sobre repuestos
        - US: 0% por defecto (usa tax_rate_applied si viene)
        """
        rep = self._sum_repuesto()
        srv = self._sum_servicio()
        osrv = self._sum_otro_servicio()
        
        # Quantize según país (US: 2 decimales, CL: 0 decimales)
        rep = self._q(rep)
        srv = self._q(srv)
        osrv = self._q(osrv)
        
        # Descuento a nivel documento
        desc = getattr(self, "descuento", Decimal("0")) or Decimal("0")
        desc = self._q(desc)
        
        # Tasa de impuesto según país
        rate = self._resolve_tax_rate()
        pais = (self.empresa.pais or "CL").upper()
        
        if pais == "CL":
            tax_base = rep  # IVA solo a repuestos
        else:  # US
            if getattr(self, "apply_vat", True):
                tax_base = rep + srv  # Repuestos + servicios
            else:
                tax_base = Decimal("0")
        
        tax_amount = tax_base * rate / Decimal("100.0")
        tax_amount = self._q(tax_amount)
        
        subtotal_general = rep + srv + osrv
        total = subtotal_general - desc + tax_amount
        total = self._q(total)
        
        # Asignar valores
        self.neto_repuestos = rep
        self.neto_servicios = srv
        self.neto_otros_servicios = osrv
        self.tax_rate_applied = rate
        self.tax_amount = tax_amount
        self.total = total
        
        if persist:
            self.save(update_fields=[...])
```

**Puntos clave:**
- ✅ **Cálculos en el backend** (ORM) para precisión
- ✅ **Quantize según país** (US: 2 decimales, CL: 0)
- ✅ **Validación multi-tenant** en `clean()` asegura que cliente/vehículo pertenecen a la empresa
- ✅ **Recálculo automático** en `save()` cuando hay cambios en líneas

### 1.2 Modelo `LineaRepuesto` - Cálculos por Línea

```python
# taller/models/lineas_documento.py

class LineaRepuesto(models.Model):
    documento = models.ForeignKey("taller.Documento", ...)
    repuesto = models.ForeignKey("taller.Repuesto", ...)
    
    codigo = models.CharField(...)
    nombre = models.CharField(...)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(...)
    descuento = models.DecimalField(..., help_text="Descuento en porcentaje")
    
    @property
    def subtotal(self):
        """Calcular subtotal con descuento"""
        subtotal_bruto = self.cantidad * self.precio_unitario
        descuento_valor = subtotal_bruto * (self.descuento / 100)
        return subtotal_bruto - descuento_valor
    
    def clean(self):
        """Validaciones de consistencia multi-tenant"""
        # Validar que repuesto y documento pertenecen al mismo país
        if (hasattr(self, "documento") and self.documento and 
            self.repuesto and hasattr(self.repuesto, "country")):
            ValidacionConsistencia.assert_same_country(
                self.documento, self.repuesto,
                "Repuesto de otro país no puede usarse en este documento"
            )
```

**Puntos clave:**
- ✅ **Property `subtotal`** para cálculos reactivos
- ✅ **Validación multi-tenant** en `clean()` asegura consistencia
- ✅ **Descuento porcentual** aplicado por línea

---

## 2. 🔒 Lógica de Vistas Multi-Tenant

### 2.1 Mixin Base: `TenantViewMixin`

```python
# core/views.py

class TenantViewMixin:
    """Mixin base para CBVs que asegura aislamiento multi-tenant"""
    
    def get_queryset(self):
        # BLINDAJE MULTI-TENANT: SIEMPRE filtrar por empresa del usuario
        if not self.request.user.is_authenticated:
            return self.model.objects.none()
        
        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            return self.model.objects.none()
        
        # Usar manager for_tenant si existe
        if hasattr(self.model.objects, "for_tenant"):
            qs = self.model.objects.for_tenant(empresa)
        else:
            # Fallback: filtrar directamente por empresa
            if hasattr(self.model, "empresa"):
                qs = self.model.objects.filter(empresa=empresa)
            else:
                qs = self.model.objects.none()  # Seguridad por defecto
        
        return qs
    
    def form_valid(self, form):
        # BLINDAJE MULTI-TENANT: SIEMPRE asignar empresa del usuario
        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            raise PermissionDenied("Usuario sin empresa asignada")
        
        if not getattr(form.instance, "empresa_id", None):
            form.instance.empresa = empresa
        return super().form_valid(form)
```

### 2.2 FBV Multi-Tenant: Ejemplo con `editar_documento`

```python
# taller/documentos/views.py

@login_required
def editar_documento(request, documento_id):
    # 🔒 FILTRO OBLIGATORIO POR EMPRESA
    try:
        empresa = request.user.empresa
        documento = get_object_or_404(
            Documento.objects.select_related(
                "cliente", "vehiculo", "tecnico_responsable"
            ).prefetch_related(
                "lineas_repuesto", "lineas_servicio", "lineas_otro_servicio"
            ),
            id=documento_id,
            empresa=empresa,  # 🔒 CLAVE: Filtro por empresa
        )
    except AttributeError:
        raise Http404("Documento no encontrado")
    
    # ... resto de la lógica
```

### 2.3 Autocomplete Multi-Tenant

```python
# taller/views_extra/views_autocomplete.py

class ClienteAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Cliente.objects.none()
        
        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            return Cliente.objects.none()
        
        qs = Cliente.objects.filter(empresa=empresa)  # 🔒 FILTRO EMPRESA
        
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        
        return qs.order_by("nombre")
```

**Patrón de seguridad:**
1. ✅ **Verificar autenticación** siempre
2. ✅ **Obtener empresa del usuario** (`request.user.empresa`)
3. ✅ **Filtrar queryset por empresa** siempre
4. ✅ **Fallback seguro** (`objects.none()` si no hay empresa)

---

## 3. 🎨 Conversión Frontend: jQuery → Alpine.js

### 3.1 Código Actual con jQuery

```javascript
// static/js/formulario_documento.js

function actualizarTotalRepuestos() {
    let total = 0;
    document.querySelectorAll('#tabla-repuestos tbody tr').forEach((row) => {
        let cantidad = row.querySelector('.cantidad-input')?.value || '1';
        let precio = row.querySelector('.precio-input')?.value || '0';
        
        // Limpiar valores
        cantidad = parseInt(cantidad.toString().replace(/[^\d]/g, '')) || 1;
        precio = parseInt(precio.toString().replace(/[^\d]/g, '')) || 0;
        
        const subtotal = cantidad * precio;
        const subtotalElement = row.querySelector('.subtotal-repuesto');
        if (subtotalElement) {
            subtotalElement.textContent = money(subtotal);
        }
        total += subtotal;
    });
    
    // Actualizar total
    const totalElement = document.getElementById('total-repuestos');
    if (totalElement) {
        totalElement.textContent = money(total > 0 ? total : 0);
    }
    
    actualizarTotalesDocumento();
}

// Event listeners manuales
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.cantidad-input, .precio-input').forEach(input => {
        input.addEventListener('change', actualizarTotalRepuestos);
    });
});
```

**Problemas con jQuery:**
- ❌ **Manipulación manual del DOM**
- ❌ **Event listeners manuales** (fácil olvidar al agregar filas dinámicamente)
- ❌ **Lógica dispersa** en múltiples funciones
- ❌ **Estado no reactivo** (necesitas llamar funciones manualmente)

### 3.2 Versión con Alpine.js ✨

```html
<!-- templates/taller/common/documentos/document_form_alpine.html -->

<div x-data="documentoForm()" class="space-y-6">
    
    <!-- Tabla de Repuestos -->
    <div class="bg-gray-900/50 rounded-lg p-4">
        <h3 class="text-lg font-semibold mb-4">Repuestos</h3>
        
        <table class="w-full">
            <thead>
                <tr class="border-b border-gray-700">
                    <th class="text-left p-2">Código</th>
                    <th class="text-left p-2">Nombre</th>
                    <th class="text-right p-2">Cantidad</th>
                    <th class="text-right p-2">Precio Unitario</th>
                    <th class="text-right p-2">Descuento %</th>
                    <th class="text-right p-2">Subtotal</th>
                    <th class="p-2"></th>
                </tr>
            </thead>
            <tbody>
                <template x-for="(linea, index) in repuestos" :key="index">
                    <tr class="border-b border-gray-800">
                        <td class="p-2">
                            <input 
                                type="text" 
                                x-model="linea.codigo"
                                class="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1"
                                placeholder="Código"
                            >
                        </td>
                        <td class="p-2">
                            <input 
                                type="text" 
                                x-model="linea.nombre"
                                class="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1"
                                placeholder="Nombre"
                            >
                        </td>
                        <td class="p-2">
                            <input 
                                type="number" 
                                x-model.number="linea.cantidad"
                                @input="actualizarSubtotal(index)"
                                min="1"
                                step="1"
                                class="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-right"
                            >
                        </td>
                        <td class="p-2">
                            <input 
                                type="number" 
                                x-model.number="linea.precio_unitario"
                                @input="actualizarSubtotal(index)"
                                min="0"
                                step="0.01"
                                class="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-right"
                            >
                        </td>
                        <td class="p-2">
                            <input 
                                type="number" 
                                x-model.number="linea.descuento"
                                @input="actualizarSubtotal(index)"
                                min="0"
                                max="100"
                                step="0.01"
                                class="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-right"
                            >
                        </td>
                        <td class="p-2 text-right font-semibold">
                            <span x-text="formatMoney(calcularSubtotal(linea))"></span>
                        </td>
                        <td class="p-2">
                            <button 
                                type="button"
                                @click="eliminarRepuesto(index)"
                                class="text-red-400 hover:text-red-300"
                            >
                                🗑️
                            </button>
                        </td>
                    </tr>
                </template>
            </tbody>
            <tfoot>
                <tr class="border-t-2 border-gray-700">
                    <td colspan="5" class="p-2 text-right font-bold">Total Repuestos:</td>
                    <td class="p-2 text-right font-bold text-lg">
                        <span x-text="formatMoney(totalRepuestos)"></span>
                    </td>
                    <td></td>
                </tr>
            </tfoot>
        </table>
        
        <button 
            type="button"
            @click="agregarRepuesto()"
            class="mt-4 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 rounded"
        >
            + Agregar Repuesto
        </button>
    </div>
    
    <!-- Resumen de Totales -->
    <div class="bg-gray-900/50 rounded-lg p-4">
        <h3 class="text-lg font-semibold mb-4">Resumen</h3>
        <div class="space-y-2">
            <div class="flex justify-between">
                <span>Subtotal Repuestos:</span>
                <span x-text="formatMoney(totalRepuestos)"></span>
            </div>
            <div class="flex justify-between">
                <span>Subtotal Servicios:</span>
                <span x-text="formatMoney(totalServicios)"></span>
            </div>
            <div class="flex justify-between">
                <span>Descuento:</span>
                <span x-text="formatMoney(descuento)"></span>
            </div>
            <div class="flex justify-between">
                <span>Impuesto (<span x-text="taxRate"></span>%):</span>
                <span x-text="formatMoney(taxAmount)"></span>
            </div>
            <div class="flex justify-between border-t-2 border-gray-700 pt-2 font-bold text-lg">
                <span>TOTAL:</span>
                <span x-text="formatMoney(total)"></span>
            </div>
        </div>
    </div>
</div>

<script>
function documentoForm() {
    return {
        // Estado reactivo
        repuestos: [],
        servicios: [],
        otrosServicios: [],
        
        // Configuración
        country: '{{ country|default:"CL" }}',
        taxRate: 0,
        descuento: 0,
        
        // Inicialización
        init() {
            // Cargar datos iniciales si existen (modo edición)
            if (window.documentoData) {
                this.repuestos = window.documentoData.repuestos || [];
                this.servicios = window.documentoData.servicios || [];
                this.otrosServicios = window.documentoData.otrosServicios || [];
                this.descuento = window.documentoData.descuento || 0;
                this.taxRate = window.documentoData.taxRate || 0;
            } else {
                // Agregar primera línea vacía
                this.agregarRepuesto();
            }
            
            // Determinar tasa de impuesto según país
            this.taxRate = this.country === 'CL' ? 19 : 0;
        },
        
        // Computed properties (reactivos)
        totalRepuestos() {
            return this.repuestos.reduce((sum, linea) => {
                return sum + this.calcularSubtotal(linea);
            }, 0);
        },
        
        totalServicios() {
            return this.servicios.reduce((sum, linea) => {
                return sum + this.calcularSubtotal(linea);
            }, 0);
        },
        
        subtotalGeneral() {
            return this.totalRepuestos + this.totalServicios + this.totalOtrosServicios;
        },
        
        taxAmount() {
            // CL: IVA solo sobre repuestos
            // US: IVA sobre repuestos + servicios (si apply_vat)
            const taxBase = this.country === 'CL' 
                ? this.totalRepuestos 
                : (this.totalRepuestos + this.totalServicios);
            return taxBase * (this.taxRate / 100);
        },
        
        total() {
            return this.subtotalGeneral - this.descuento + this.taxAmount;
        },
        
        // Métodos
        agregarRepuesto() {
            this.repuestos.push({
                codigo: '',
                nombre: '',
                cantidad: 1,
                precio_unitario: 0,
                descuento: 0,
            });
        },
        
        eliminarRepuesto(index) {
            this.repuestos.splice(index, 1);
        },
        
        calcularSubtotal(linea) {
            const subtotalBruto = (linea.cantidad || 0) * (linea.precio_unitario || 0);
            const descuentoValor = subtotalBruto * ((linea.descuento || 0) / 100);
            return Math.max(0, subtotalBruto - descuentoValor);
        },
        
        actualizarSubtotal(index) {
            // Alpine.js actualiza automáticamente, pero podemos forzar recálculo si es necesario
            this.$nextTick(() => {
                // Los computed properties se actualizan automáticamente
            });
        },
        
        formatMoney(value) {
            const num = parseFloat(value) || 0;
            const locale = this.country === 'CL' ? 'es-CL' : 'en-US';
            const currency = this.country === 'CL' ? 'CLP' : 'USD';
            const decimals = this.country === 'CL' ? 0 : 2;
            
            return new Intl.NumberFormat(locale, {
                style: 'currency',
                currency: currency,
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals,
            }).format(num);
        },
        
        // Serializar para enviar al servidor
        serializar() {
            return {
                repuestos: this.repuestos,
                servicios: this.servicios,
                otrosServicios: this.otrosServicios,
                descuento: this.descuento,
                taxRate: this.taxRate,
                total: this.total,
            };
        },
    };
}
</script>
```

### 3.3 Comparación: jQuery vs Alpine.js

| Aspecto | jQuery | Alpine.js |
|---------|--------|-----------|
| **Manipulación DOM** | Manual (`querySelector`, `textContent`) | Reactiva (`x-model`, `x-text`) |
| **Event Listeners** | Manual (fácil olvidar) | Declarativo (`@input`, `@click`) |
| **Estado** | Variables globales | Estado encapsulado (`x-data`) |
| **Cálculos** | Funciones manuales | Computed properties (reactivos) |
| **Filas dinámicas** | Código complejo | `x-for` simple |
| **Formato** | Funciones separadas | Métodos en objeto |
| **Bundle size** | ~30KB | ~15KB |
| **Legibilidad** | Media | Alta |

### 3.4 Ventajas de Alpine.js

✅ **Código más limpio**: Lógica en un solo lugar  
✅ **Reactivo**: Los cambios se propagan automáticamente  
✅ **Sin dependencias**: No necesitas jQuery + plugins  
✅ **Fácil de mantener**: Menos código = menos bugs  
✅ **Mejor rendimiento**: No hay manipulación DOM innecesaria  

---

## 4. 📋 Próximos Pasos Recomendados

1. **Migrar tabla de repuestos** a Alpine.js (ejemplo arriba)
2. **Migrar tabla de servicios** con el mismo patrón
3. **Usar HTMX para agregar filas** (en lugar de JavaScript puro)
4. **Actualizar validaciones** para usar Alpine.js
5. **Eliminar jQuery** una vez migrado todo

¿Quieres que implemente la migración completa de alguna tabla específica?

