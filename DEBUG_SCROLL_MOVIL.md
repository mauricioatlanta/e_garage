# 🐛 Debug: Problema de Scroll Automático en Móviles

## 📋 Resumen del Problema

En dispositivos móviles, la página hace scroll hacia arriba automáticamente al intentar scrollear, haciendo imposible leer o llenar formularios.

---

## ✅ Lo que YA Sabemos (Descartado)

### **Archivos JS Revisados (todos limpios):**
- ❌ `starfield.js` - Solo dibuja canvas, sin scroll
- ❌ `dynamic_effects.js` - Solo `reload()` al eliminar (no loop)
- ❌ `region_ciudad_handler.js` - Solo maneja selects
- ❌ `documento_form_futurista.js` - Solo focus() al agregar líneas
- ❌ `formulario_vehiculo.js` - Solo focus() en eventos específicos

**Conclusión:** El bug NO está en estos JS externos.

---

## 🎯 Posibles Culpables

### **1. Scripts Inline en Templates**
`.focus()` encontrado en:
- `templates/taller/common/documentos/document_form.html` (6x)
- `templates/taller/common/vehiculos/vehiculo_form.html` (3x)
- `templates/us/en/clientes/crear_cliente.html` (2x)

**Acción:** Verificar con espías si alguno se ejecuta en loop.

### **2. Service Worker**
- Podría estar recargando la página en ciertas condiciones
- Menos probable, pero posible

### **3. Combinación de Layout Móvil + Focus**
- Algún input que recibe focus() repetidamente
- Posiblemente en combinación con eventos de teclado virtual

---

## 🔍 Herramientas de Debug Activadas

### **Espías en `templates/base.html` y `templates/taller/common/base.html`:**

```javascript
// ✅ window.scrollTo() - detecta scrolls programáticos
// ✅ element.scrollIntoView() - detecta scroll a elemento
// ✅ window.scroll() - alternativa a scrollTo
// ✅ element.focus() - detecta cambios de foco ← NUEVO
```

### **Qué verás en consola cuando ocurra el bug:**

```javascript
🎯 *** focus() en: <input id="id_nombre"> - 2025-12-03T...
    at HTMLInputElement.someFunction (crear_cliente.html:856)
    at DOMContentLoaded (crear_cliente.html:901)
```

O:

```javascript
🔍 *** window.scrollTo llamado con: 0 0 2025-12-03T...
    at culpableFunction (archivo.js:123)
    at ...
```

---

## 🧪 Pasos de Prueba

### **1. Probar en PC (Modo Móvil):**
```bash
python manage.py runserver 0.0.0.0:8000
```

**Chrome DevTools:**
1. Abrir: `http://127.0.0.1:8000/us/clientes/crear/`
2. F12 → Modo móvil 📱
3. Console activa
4. Scrollear hasta que ocurra el "salto"
5. **Copiar el stack trace completo**

### **2. Probar en Celular Real:**
```
http://192.168.1.106:8000/us/clientes/crear/
```

**Con Chrome Remote Debugging (Android):**
1. USB debugging activado
2. PC: `chrome://inspect`
3. Ver consola en tiempo real

---

## 📝 Información a Recopilar

Cuando ocurra el bug, necesitamos:

1. **El elemento que recibe focus:**
   ```
   🎯 *** focus() en: <input id="ESTE_ES_EL_CULPABLE">
   ```

2. **El archivo y línea que lo causa:**
   ```
   at nombreFuncion (archivo.html:LINE_NUMBER)
   ```

3. **Stack trace completo** - para ver la cadena de llamadas

---

## 🔧 Posibles Soluciones (una vez identificado)

### **Si es un focus() en loop:**
```javascript
// ANTES (malo):
setInterval(() => {
    input.focus(); // ❌ Se ejecuta constantemente
}, 100);

// DESPUÉS (bueno):
// Solo focus en eventos específicos
button.addEventListener('click', () => {
    input.focus(); // ✅ Solo cuando el usuario hace click
});
```

### **Si es un scrollTo involuntario:**
```javascript
// Agregar condición para evitar en móviles:
if (window.innerWidth > 768) {
    window.scrollTo(0, 0); // Solo en desktop
}
```

### **Si es un autofocus problemático:**
```html
<!-- ANTES: -->
<input autofocus>

<!-- DESPUÉS: -->
<input>
<!-- O agregar solo en desktop con JS -->
```

---

## 📊 Estado Actual

- ✅ Espías de scroll activados
- ✅ Espía de focus activado
- ✅ starfield.js desactivado temporalmente
- ✅ Búsqueda en templates completada
- ⏳ Esperando stack trace del bug en acción

---

## 🎯 Próximo Paso

**Reproducir el bug con los espías activos y copiar el stack trace completo aquí.**

Una vez tengamos eso, tendremos el archivo y línea exacta del problema y podremos arreglarlo en minutos.






