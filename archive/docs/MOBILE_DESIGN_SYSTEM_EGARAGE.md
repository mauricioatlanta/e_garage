# 🎨 MOBILE DESIGN SYSTEM - eGarage

**Versión:** 1.0  
**Última actualización:** 2025-01-27  
**Enfoque:** Mobile-first, experiencia app nativa

---

## 📐 TOKENS DE DISEÑO

### Tipografía

#### Títulos de Página
```html
<h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-white">
```
- **Móvil:** `text-2xl` (24px)
- **Desktop:** `text-3xl` (30px)
- **Peso:** `font-bold` (700)
- **Tracking:** `tracking-tight` (letraespaciado ajustado)

#### Subtítulos
```html
<p class="text-sm sm:text-base text-slate-300">
```
- **Móvil:** `text-sm` (14px)
- **Desktop:** `text-base` (16px)
- **Color:** `text-slate-300` (gris claro)

#### Labels de Formulario
```html
<label class="block text-sm sm:text-base text-cyan-200 font-semibold">
```
- **Móvil:** `text-sm` (14px)
- **Desktop:** `text-base` (16px)
- **Color:** `text-cyan-200` (cyan claro)
- **Peso:** `font-semibold` (600)

#### Texto Normal
```html
<p class="text-base text-slate-200">
```
- **Tamaño:** `text-base` (16px)
- **Color:** `text-slate-200` (gris muy claro)

#### Badges / Etiquetas
```html
<span class="text-xs sm:text-sm font-semibold px-2 py-1 rounded-full">
```
- **Móvil:** `text-xs` (12px)
- **Desktop:** `text-sm` (14px)
- **Padding:** `px-2 py-1`
- **Forma:** `rounded-full`

---

### Espaciados

#### Padding de Cards
- **Móvil:** `p-4` (16px)
- **Desktop:** `sm:p-5` (20px) o `sm:p-6` (24px)

#### Gaps entre Elementos
- **Móvil:** `gap-3` (12px) o `gap-4` (16px)
- **Desktop:** `sm:gap-4` (16px) o `sm:gap-6` (24px)

#### Espaciado Vertical en Formularios
- **Móvil:** `space-y-3` (12px)
- **Desktop:** `sm:space-y-4` (16px)

#### Márgenes de Sección
- **Móvil:** `mt-4` (16px) o `mt-6` (24px)
- **Desktop:** `sm:mt-6` (24px) o `sm:mt-8` (32px)

#### Padding Horizontal de Contenedor
- **Móvil:** `px-4` (16px)
- **Desktop:** `sm:px-6` (24px)

---

### Radios de Borde

#### Cards Principales
```html
<div class="rounded-2xl ...">
```
- **Valor:** `rounded-2xl` (16px)

#### Cards Secundarias / Listas
```html
<div class="rounded-xl ...">
```
- **Valor:** `rounded-xl` (12px)

#### Botones
```html
<button class="rounded-xl ...">
```
- **Valor:** `rounded-xl` (12px)

#### Inputs
```html
<input class="rounded-lg ...">
```
- **Valor:** `rounded-lg` (8px)

---

### Sombras

#### Cards Importantes
```html
<div class="shadow-lg ...">
```
- **Clase:** `shadow-lg`
- **Uso:** Cards principales, modales

#### Cards Secundarias
```html
<div class="shadow-md ...">
```
- **Clase:** `shadow-md`
- **Uso:** Cards de lista, elementos secundarios

#### Hover de Cards
```html
<div class="hover:shadow-xl transition-shadow ...">
```
- **Clase:** `hover:shadow-xl`
- **Efecto:** Elevación al hover

---

## 🧩 COMPONENTES BASE

### Botón Primario

**Uso:** Guardar, Crear, Acciones principales

```html
<button class="w-full sm:w-auto inline-flex items-center justify-center px-4 py-3 text-sm sm:text-base font-semibold rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-white shadow-lg hover:shadow-xl transition-all focus:outline-none focus:ring-2 focus:ring-cyan-400/60 focus:ring-offset-2 focus:ring-offset-slate-900">
  💾 Guardar
</button>
```

**Características:**
- `w-full sm:w-auto` - Ancho completo en móvil
- `px-4 py-3` - Padding táctil (44px mínimo de altura)
- `text-sm sm:text-base` - Texto responsive
- `rounded-xl` - Radio estándar
- `focus:ring-2 focus:ring-cyan-400/60` - Focus accesible

---

### Botón Secundario

**Uso:** Volver, Cancelar, Acciones secundarias

```html
<button class="w-full sm:w-auto inline-flex items-center justify-center px-4 py-3 text-sm sm:text-base font-semibold rounded-xl bg-slate-800/60 hover:bg-slate-700/60 border border-slate-600/50 text-slate-200 hover:text-white transition-all focus:outline-none focus:ring-2 focus:ring-slate-400/60 focus:ring-offset-2 focus:ring-offset-slate-900">
  ← Volver
</button>
```

**Características:**
- Mismo padding y tamaño que primario
- Fondo más sutil
- Borde visible
- Hover suave

---

### Card de Lista

**Uso:** Clientes, Vehículos, Documentos en listas

```html
<div class="bg-slate-900/60 border border-slate-700/80 rounded-xl p-4 sm:p-5 shadow-md hover:shadow-lg transition-all space-y-2">
  <div class="flex items-start justify-between">
    <div class="flex-1">
      <h3 class="text-base sm:text-lg font-semibold text-white">Título</h3>
      <p class="text-sm text-slate-400 mt-1">Subtítulo o descripción</p>
    </div>
    <span class="badge-status">Estado</span>
  </div>
  <div class="flex items-center gap-4 text-xs sm:text-sm text-slate-400">
    <span>📅 Fecha</span>
    <span>💰 Total</span>
  </div>
  <div class="flex items-center gap-2 pt-2 border-t border-slate-700/50">
    <a href="#" class="btn-action">Ver</a>
    <a href="#" class="btn-action">Editar</a>
  </div>
</div>
```

**Características:**
- `bg-slate-900/60` - Fondo semitransparente
- `border border-slate-700/80` - Borde sutil
- `rounded-xl` - Radio estándar
- `p-4 sm:p-5` - Padding responsive
- `space-y-2` - Espaciado interno

---

### Header de Página

**Uso:** Todas las páginas principales

```html
<div class="mb-6 sm:mb-8 px-4 sm:px-6">
  <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
    <div class="flex-1">
      <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-2">
        Título de la Página
      </h1>
      <p class="text-sm sm:text-base text-slate-300">
        Subtítulo corto y descriptivo
      </p>
    </div>
    <div class="flex items-center gap-3 w-full sm:w-auto">
      <button class="btn-primary">Acción Principal</button>
    </div>
  </div>
</div>
```

**Características:**
- `flex-col sm:flex-row` - Apila en móvil
- `gap-4` - Espaciado consistente
- `mb-6 sm:mb-8` - Margen inferior responsive
- Título + Subtítulo + Acciones

---

### Sección de Formulario

**Uso:** Agrupación de campos en formularios

```html
<div class="bg-slate-900/60 border border-slate-700/80 rounded-2xl p-4 sm:p-6 shadow-lg mb-6">
  <h3 class="text-lg sm:text-xl font-semibold text-cyan-300 mb-4 flex items-center gap-2">
    <span>🔧</span>
    Título de la Sección
  </h3>
  <div class="space-y-3 sm:space-y-4">
    <!-- Campos del formulario -->
  </div>
</div>
```

**Características:**
- `bg-slate-900/60` - Fondo consistente
- `rounded-2xl` - Radio más grande (card principal)
- `p-4 sm:p-6` - Padding generoso
- `shadow-lg` - Sombra destacada
- Título opcional con icono

---

## 📱 PATRONES MÓVILES

### Lista: Tabla en Desktop, Cards en Móvil

```html
<!-- Desktop: Tabla -->
<div class="hidden md:block overflow-x-auto">
  <table class="w-full">
    <!-- Tabla completa -->
  </table>
</div>

<!-- Móvil: Cards -->
<div class="md:hidden space-y-3">
  {% for item in items %}
  <div class="bg-slate-900/60 border border-slate-700/80 rounded-xl p-4 shadow-md">
    <!-- Contenido de la card -->
  </div>
  {% endfor %}
</div>
```

---

### Empty State

```html
<div class="text-center py-12 sm:py-16 px-4">
  <div class="text-6xl mb-4 opacity-50">📄</div>
  <h3 class="text-xl sm:text-2xl font-semibold text-slate-200 mb-2">
    Aún no tienes documentos
  </h3>
  <p class="text-sm sm:text-base text-slate-400 mb-6 max-w-md mx-auto">
    Crea tu primer documento para comenzar a gestionar el taller.
  </p>
  <a href="#" class="btn-primary inline-block">
    ➕ Crear Primer Documento
  </a>
</div>
```

**Características:**
- Icono grande y opaco
- Título descriptivo
- Descripción amigable
- Botón de acción claro

---

### Feedback Visual (Mensajes)

```html
<!-- Éxito -->
<div class="bg-green-900/30 border border-green-500/50 rounded-xl p-4 mb-4 flex items-center gap-3">
  <span class="text-2xl">✅</span>
  <p class="text-sm sm:text-base text-green-200">Operación realizada con éxito</p>
</div>

<!-- Error -->
<div class="bg-red-900/30 border border-red-500/50 rounded-xl p-4 mb-4 flex items-center gap-3">
  <span class="text-2xl">❌</span>
  <p class="text-sm sm:text-base text-red-200">Error al procesar la solicitud</p>
</div>

<!-- Info -->
<div class="bg-blue-900/30 border border-blue-500/50 rounded-xl p-4 mb-4 flex items-center gap-3">
  <span class="text-2xl">ℹ️</span>
  <p class="text-sm sm:text-base text-blue-200">Información importante</p>
</div>
```

---

## 🎯 REGLAS DE ORO

### Zonas Táctiles
- **Mínimo:** 44x44px (`h-11` o `py-2.5`/`py-3`)
- **Recomendado:** 48x48px (`h-12` o `py-3`)

### Colores Principales
- **Primario:** Cyan (`cyan-400`, `cyan-500`, `cyan-600`)
- **Secundario:** Blue (`blue-500`, `blue-600`)
- **Acento:** Purple (`purple-500`, `purple-600`)
- **Fondo:** Slate oscuro (`slate-900`, `slate-800`)
- **Texto:** Blanco/Gris claro (`white`, `slate-200`, `slate-300`)

### Transiciones
- **Estándar:** `transition-all` o `transition-colors`
- **Duración:** Por defecto de Tailwind (150ms-300ms)

### Focus States
- **Siempre incluir:** `focus:outline-none focus:ring-2 focus:ring-cyan-400/60`
- **Offset:** `focus:ring-offset-2 focus:ring-offset-slate-900`

---

## 📋 CHECKLIST DE APLICACIÓN

Al crear o modificar componentes, verificar:

- [ ] Usa tokens de tipografía del design system
- [ ] Espaciados consistentes (`p-4 sm:p-5`, `gap-3 sm:gap-4`)
- [ ] Radios de borde estándar (`rounded-xl`, `rounded-2xl`)
- [ ] Zonas táctiles mínimas (44px)
- [ ] Focus states accesibles
- [ ] Responsive (móvil primero, luego desktop)
- [ ] Mantiene estilo futurista (neones, fondos oscuros)
- [ ] Transiciones suaves

---

**Este design system debe aplicarse consistentemente en toda la aplicación móvil para lograr una experiencia unificada y profesional.**

