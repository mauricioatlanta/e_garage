# ✨ Feature: Agregar Estados y Ciudades Personalizados

**Fecha:** 10 de Noviembre, 2025
**Template:** `templates/taller/common/documentos/document_form.html`
**Feature:** Opción para agregar estados y ciudades personalizados si no existen en las listas

---

## 🎯 Funcionalidad Implementada

### **1. Agregar Nuevo Estado**

**Ubicación:** Modal de crear cliente → Dropdown "State"

**Cómo funciona:**
1. Al final del dropdown de estados aparece: **"➕ Agregar nuevo estado..."**
2. Al seleccionar esa opción, aparece un campo de texto
3. Usuario escribe el nombre del estado (ej: "Puerto Rico")
4. Presiona **Enter** o hace click fuera del campo
5. El nuevo estado se agrega a la lista con un icono ✨
6. Se selecciona automáticamente
7. Permanece disponible durante toda la sesión

---

### **2. Agregar Nueva Ciudad**

**Ubicación:** Modal de crear cliente → Dropdown "City"

**Cómo funciona:**
1. Al final del dropdown de ciudades aparece: **"➕ Agregar nueva ciudad..."**
2. Al seleccionar esa opción, aparece un campo de texto
3. Usuario escribe el nombre de la ciudad (ej: "Pequeña Ciudad")
4. Presiona **Enter** o hace click fuera del campo
5. La nueva ciudad se agrega a la lista con un icono ✨
6. Se selecciona automáticamente
7. Permanece disponible para ese estado durante toda la sesión

---

## 🎨 Interfaz Visual

### Dropdown de Estado

```
┌────────────────────────────────────┐
│ Seleccione estado...               │
├────────────────────────────────────┤
│ Alabama                            │
│ Alaska                             │
│ Arizona                            │
│ ...                                │
│ Wyoming                            │
│ Mi Estado Nuevo ✨                 │  ← Estado personalizado
│ ➕ Agregar nuevo estado...         │  ← En verde
└────────────────────────────────────┘
```

### Cuando se selecciona "Agregar nuevo estado..."

```
┌────────────────────────────────────┐
│ ➕ Agregar nuevo estado...         │  ← Seleccionado
└────────────────────────────────────┘

┌────────────────────────────────────┐
│ Puerto Rico█                       │  ← Input aparece
└────────────────────────────────────┘
    ↓ Presionar Enter
┌────────────────────────────────────┐
│ Puerto Rico ✨                     │  ← Agregado y seleccionado
└────────────────────────────────────┘
```

### Dropdown de Ciudad (después de seleccionar estado)

```
┌────────────────────────────────────┐
│ Seleccione ciudad...               │
├────────────────────────────────────┤
│ Los Angeles                        │
│ San Francisco                      │
│ San Diego                          │
│ ...                                │
│ Mi Ciudad Nueva ✨                 │  ← Ciudad personalizada
│ ➕ Agregar nueva ciudad...         │  ← En verde
└────────────────────────────────────┘
```

---

## 💾 Almacenamiento

### Variables en Memoria (Sesión Actual)

```javascript
// Estados personalizados
let customStates = [
  {id: 'CUSTOM_PR_1699999999', nombre: 'Puerto Rico'}
];

// Ciudades personalizadas por estado
let customCitiesByState = {
  'CA': ['Mi Ciudad', 'Otra Ciudad'],
  'CUSTOM_PR_1699999999': ['San Juan', 'Ponce']
};
```

**Importante:**
- Los datos se almacenan **solo durante la sesión actual**
- Al recargar la página, se pierden
- Son **específicos de este formulario**
- No se guardan en la base de datos hasta crear el cliente

---

## 🔄 Flujo Completo

### Agregar Estado Personalizado

```
1. Usuario abre modal de cliente
   ↓
2. Dropdown de estados se llena (50 estados + personalizados)
   ↓
3. Usuario selecciona "➕ Agregar nuevo estado..."
   ↓
4. Input de texto aparece debajo del dropdown
   ↓
5. Usuario escribe "Guam" y presiona Enter
   ↓
6. Se ejecuta agregarNuevoEstado('Guam')
   ↓
7. Se agrega a customStates
   ↓
8. Se crea opción en dropdown: "Guam ✨"
   ↓
9. Se selecciona automáticamente
   ↓
10. Input se oculta
   ↓
11. Dropdown de ciudades se reinicia con opción "➕ Agregar nueva ciudad..."
```

### Agregar Ciudad Personalizada

```
1. Usuario selecciona un estado (ej: California)
   ↓
2. Ciudades se cargan (7 ciudades de CA)
   ↓
3. Al final aparece "➕ Agregar nueva ciudad..."
   ↓
4. Usuario selecciona esa opción
   ↓
5. Input de texto aparece debajo del dropdown
   ↓
6. Usuario escribe "Pequeña Ciudad" y presiona Enter
   ↓
7. Se ejecuta agregarNuevaCiudad('Pequeña Ciudad')
   ↓
8. Se agrega a customCitiesByState['CA']
   ↓
9. Se crea opción en dropdown: "Pequeña Ciudad ✨"
   ↓
10. Se selecciona automáticamente
   ↓
11. Input se oculta
```

---

## 🧪 Cómo Probar

### Test 1: Agregar Estado Personalizado

1. Ve a `http://127.0.0.1:8000/us/documentos/form/`
2. Click en "➕ New" junto a Cliente
3. Abrir consola (F12)
4. En dropdown "State", scrollear hasta el final
5. Seleccionar **"➕ Agregar nuevo estado..."**
6. Debe aparecer un campo de texto debajo
7. Escribir "Puerto Rico"
8. Presionar **Enter**
9. Verificar en consola: `✅ Nuevo estado agregado: Puerto Rico`
10. Verificar que "Puerto Rico ✨" aparece en el dropdown
11. Verificar que está seleccionado automáticamente

### Test 2: Agregar Ciudad Personalizada

1. Con el modal abierto, seleccionar un estado (ej: California)
2. Esperar a que se carguen las ciudades
3. En dropdown "City", scrollear hasta el final
4. Seleccionar **"➕ Agregar nueva ciudad..."**
5. Debe aparecer un campo de texto debajo
6. Escribir "Mi Ciudad"
7. Presionar **Enter**
8. Verificar en consola: `✅ Nueva ciudad agregada: Mi Ciudad para estado CA`
9. Verificar que "Mi Ciudad ✨" aparece en el dropdown
10. Verificar que está seleccionada automáticamente

### Test 3: Persistencia en la Sesión

1. Agregar estado "Guam"
2. Agregar ciudad "Agana" para Guam
3. Cerrar el modal
4. Volver a abrir el modal
5. Verificar que "Guam ✨" sigue en la lista de estados
6. Seleccionar "Guam"
7. Verificar que "Agana ✨" aparece en ciudades

### Test 4: Crear Cliente con Datos Personalizados

1. Agregar estado "Puerto Rico"
2. Agregar ciudad "San Juan"
3. Completar todos los campos del cliente
4. Click en "✓ Create Client"
5. El cliente debe crearse correctamente con esos datos

---

## 🎨 Características Visuales

### Estados/Ciudades Personalizados

- **Icono:** ✨ (estrella brillante)
- **Color:** Verde (#10b981)
- **Font weight:** Bold
- **Indicador visual claro** de que son personalizados

### Opción "Agregar nuevo..."

- **Icono:** ➕
- **Color:** Verde (#10b981)
- **Font weight:** Bold
- **Siempre al final** de la lista

### Input Inline

- **Placeholder:** "Escriba nuevo estado..." / "Escriba nueva ciudad..."
- **Fondo oscuro** con borde cyan
- **Texto blanco** siempre visible
- **Aparece/desaparece** suavemente

---

## 🔧 Funciones JavaScript Agregadas

```javascript
// Variables globales
let customStates = [];
let customCitiesByState = {};

// Para estados
function mostrarInputNuevoEstado()
function ocultarInputNuevoEstado()
function agregarNuevoEstado(nombre)

// Para ciudades
function mostrarInputNuevaCiudad()
function ocultarInputNuevaCiudad()
function agregarNuevaCiudad(nombre)
function setupClienteCiudadListener()
```

---

## 💡 Casos de Uso

### 1. **Territorios USA**
- Puerto Rico
- Guam
- US Virgin Islands
- American Samoa

### 2. **Ciudades Pequeñas**
- Ciudades no incluidas en la lista hardcodeada
- Pueblos pequeños
- Áreas no incorporadas

### 3. **Ciudades Nuevas**
- Ciudades fundadas recientemente
- Áreas en desarrollo

### 4. **Nombres Alternativos**
- Variaciones de nombres
- Abreviaciones locales

---

## ⚠️ Limitaciones

1. **No persistente:** Los datos personalizados se pierden al recargar la página
2. **Solo en sesión:** No se comparten entre pestañas del navegador
3. **No valida:** No valida si el estado/ciudad realmente existe
4. **No se guarda en BD:** Los estados/ciudades personalizados solo existen en memoria

---

## 🚀 Mejoras Futuras Sugeridas

1. **Persistencia en localStorage:** Guardar en el navegador
2. **Sincronización con BD:** Opción para guardar permanentemente
3. **Validación:** Verificar contra una API de geocodificación
4. **Autocompletado:** Sugerencias mientras escribe
5. **Compartir entre formularios:** Reutilizar en otros modales

---

## ✅ Checklist

- [x] Variable `customStates` declarada
- [x] Variable `customCitiesByState` declarada
- [x] Opción "➕ Agregar nuevo estado..." agregada a dropdown
- [x] Opción "➕ Agregar nueva ciudad..." agregada a dropdown
- [x] Input inline para nuevo estado
- [x] Input inline para nueva ciudad
- [x] Función `mostrarInputNuevoEstado()`
- [x] Función `ocultarInputNuevoEstado()`
- [x] Función `agregarNuevoEstado()`
- [x] Función `mostrarInputNuevaCiudad()`
- [x] Función `ocultarInputNuevaCiudad()`
- [x] Función `agregarNuevaCiudad()`
- [x] Listener para detectar selección de nuevo estado
- [x] Listener para detectar selección de nueva ciudad
- [x] Estados personalizados se muestran con icono ✨
- [x] Ciudades personalizadas se muestran con icono ✨
- [x] Logs de debug implementados

---

**Status:** ✅ COMPLETADO - Listo para usar

