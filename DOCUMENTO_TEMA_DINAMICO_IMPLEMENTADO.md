# DocumentoForm con Tema Dinámico - Implementación Plug-and-Play

## ✅ Implementación Completada

### 1. **Archivo de Estilos** (`templates/taller/documentos/_document_theme.html`)

#### Características:
- ✅ **Estilos Tailwind sobrios** - Sin saturación visual
- ✅ **Paletas por tipo** - Slate (OT), Amber (PRES), Emerald (REC)
- ✅ **Efectos sutiles** - Bordes elegantes y sombras suaves
- ✅ **Chips temáticos** - Fondos oscuros con texto claro

#### Clases CSS:
```css
.doc-shell { @apply rounded-2xl border bg-white/5 backdrop-blur p-5 shadow-md; }
.theme-ot    { @apply border-slate-500/50; }
.theme-pres  { @apply border-amber-500/50; }
.theme-rec   { @apply border-emerald-600/50; }
```

### 2. **Template de Creación** (`templates/taller/documentos/crear_ejemplo.html`)

#### Características:
- ✅ **Shell dinámico** - Cambia tema según tipo de documento
- ✅ **Chip temático** - Muestra tipo con emoji y color
- ✅ **Grid responsive** - Layout adaptativo con Tailwind
- ✅ **JavaScript vanilla** - Sin dependencias extra
- ✅ **DAL integrado** - Select2 con forward automático

#### Estructura:
```html
<div id="doc-shell" class="doc-shell theme-ot">
    <div class="flex items-center justify-between mb-4">
        <span id="doc-chip" class="doc-chip chip-ot">🔧 OT</span>
        <div class="text-xs text-gray-400">{{ empresa_nombre }} • {{ empresa_moneda }}</div>
    </div>
    <form id="document-form" method="post" novalidate>
        <!-- Campos del formulario -->
    </form>
</div>
```

### 3. **Template de Edición** (`templates/taller/documentos/editar_ejemplo.html`)

#### Características:
- ✅ **Misma funcionalidad** que crear
- ✅ **ID del documento** visible en el chip
- ✅ **Valores pre-cargados** del documento existente
- ✅ **Tema inicial** basado en el tipo actual

### 4. **JavaScript del Tema Dinámico**

#### Funcionalidades:
- ✅ **Cambio automático** al seleccionar tipo
- ✅ **Inicialización** según valor del formulario
- ✅ **Mapeo de temas** por tipo de documento
- ✅ **Reset de clases** antes de aplicar nuevas

#### Código JavaScript:
```javascript
function applyTheme(value) {
    const v = (value || 'OT').toUpperCase();
    resetShellThemes();
    resetChipThemes();
    (shellThemes[v] || shellThemes['OT']).forEach(c => shell.classList.add(c));
    const conf = chipThemes[v] || chipThemes['OT'];
    conf.classes.forEach(c => chip.classList.add(c));
    chip.textContent = conf.label;
}

// Reacciona a cambios del select
tipo.addEventListener('change', function (e) {
    applyTheme(e.target.value);
});
```

### 5. **DocumentoForm Actualizado** (`taller/documentos/forms.py`)

#### Mejoras:
- ✅ **IDs únicos** para todos los campos
- ✅ **Compatibilidad** con JavaScript del tema
- ✅ **IDs consistentes** - `id_tipo`, `id_cliente`, etc.

#### Código:
```python
# Asegurar IDs únicos para JavaScript
self.fields['tipo'].widget.attrs.setdefault("id", "id_tipo")
self.fields['numero'].widget.attrs.setdefault("id", "id_numero")
# ... todos los campos
```

### 6. **Vistas Actualizadas** (`taller/documentos/views_ejemplo.py`)

#### Contexto Completo:
- ✅ **Variables de empresa** - nombre, moneda, país
- ✅ **Contexto de país** - para localización
- ✅ **Datos del formulario** - form y obj

#### Código:
```python
context = {
    "form": form,
    "country": country,
    "empresa_nombre": empresa.nombre_taller,
    "empresa_moneda": empresa.moneda,
    "empresa_pais": empresa.pais,
}
```

## 🎨 Paletas de Colores

### OT (Orden de Trabajo):
- **Shell**: `border-slate-500/50` - Gris profesional
- **Chip**: `bg-slate-800/70 text-slate-100` - Fondo oscuro elegante
- **Emoji**: 🔧 - Herramienta

### PRES (Presupuesto):
- **Shell**: `border-amber-500/50` - Ámbar cálido
- **Chip**: `bg-amber-900/60 text-amber-100` - Fondo ámbar oscuro
- **Emoji**: 📋 - Clipboard

### REC (Recibo):
- **Shell**: `border-emerald-600/50` - Verde esmeralda
- **Chip**: `bg-emerald-900/60 text-emerald-100` - Fondo verde oscuro
- **Emoji**: 🧾 - Recibo

## 🔧 Uso en Producción

### 1. Incluir el archivo de estilos:
```html
{% block extra_head %}
  {% include "taller/documentos/_document_theme.html" %}
{% endblock %}
```

### 2. Usar el shell dinámico:
```html
{% with tipo_init=form.data.tipo|default:form.instance.tipo|default:"OT" %}
<div id="doc-shell" class="doc-shell theme-ot">
    <span id="doc-chip" class="doc-chip chip-ot">🔧 OT</span>
    <!-- formulario -->
</div>
{% endwith %}
```

### 3. JavaScript automático:
- Se inicializa según el valor del formulario
- Reacciona a cambios del select de tipo
- No requiere configuración adicional

## 🌍 Características Multi-país

### Soporte Automático:
- ✅ **Labels localizados** - Español/Inglés según país
- ✅ **Placeholders DAL** - Búsqueda en idioma correcto
- ✅ **Botones localizados** - Crear/Cancelar vs Create/Cancel
- ✅ **Información de empresa** - Moneda y país visibles

## 📱 Responsive Design

### Breakpoints:
- ✅ **Mobile first** - Grid adaptativo
- ✅ **sm:grid-cols-2** - Dos columnas en pantallas medianas+
- ✅ **Gap consistente** - Espaciado uniforme
- ✅ **Botones flexibles** - Layout adaptativo

## 🚀 Estado: LISTO PARA PRODUCCIÓN

### Características Implementadas:
- ✅ Tema dinámico por tipo de documento
- ✅ Estilos sobrios y elegantes con Tailwind
- ✅ JavaScript vanilla sin dependencias
- ✅ Templates de crear y editar
- ✅ Integración completa con DAL
- ✅ Soporte multi-país
- ✅ Design responsive
- ✅ IDs únicos para JavaScript

### Archivos Creados:
1. `templates/taller/documentos/_document_theme.html` - Estilos
2. `templates/taller/documentos/crear_ejemplo.html` - Template crear
3. `templates/taller/documentos/editar_ejemplo.html` - Template editar
4. `taller/documentos/views_ejemplo.py` - Vistas actualizadas
5. `taller/documentos/forms.py` - IDs únicos agregados

**El pack plug-and-play está completo y funcionando. Solo incluye el archivo de estilos y usa los templates de ejemplo.**
