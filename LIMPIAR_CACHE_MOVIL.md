# 📱 Cómo Limpiar Caché en Móvil

> Después de actualizar el archivo en PythonAnywhere, debes limpiar la caché para ver los cambios

---

## 📱 iPhone / iPad (Safari)

### Método 1: Limpiar Caché Completa
```
1. Abrir "Ajustes" (Settings)
2. Bajar y seleccionar "Safari"
3. Bajar y tocar "Borrar historial y datos de sitios web"
4. Confirmar "Borrar historial y datos"
5. Abrir Safari y volver a cargar la página
```

### Método 2: Recarga Forzada
```
1. Abrir Safari
2. Ir a la página: https://www.egarage.cl/us/clientes/
3. Deslizar hacia abajo para recargar (pull to refresh)
4. Cerrar Safari completamente (deslizar hacia arriba)
5. Volver a abrir Safari y entrar a la página
```

---

## 📱 Android (Chrome)

### Método 1: Limpiar Caché del Sitio
```
1. Abrir Chrome
2. Tocar los 3 puntos (⋮) arriba a la derecha
3. Tocar "Configuración"
4. Tocar "Privacidad y seguridad"
5. Tocar "Borrar datos de navegación"
6. Seleccionar "Imágenes y archivos en caché"
7. Tocar "Borrar datos"
8. Volver a cargar la página
```

### Método 2: Recarga Forzada
```
1. Abrir Chrome
2. Ir a: https://www.egarage.cl/us/clientes/
3. Deslizar hacia abajo para recargar
4. Tocar los 3 puntos (⋮)
5. Tocar el ícono de recargar (↻)
6. Esperar que cargue completamente
```

### Método 3: Modo Incógnito (Prueba rápida)
```
1. Abrir Chrome
2. Tocar los 3 puntos (⋮)
3. Tocar "Nueva pestaña de incógnito"
4. Ir a: https://www.egarage.cl/us/clientes/
5. Si aquí se ve bien, es problema de caché
```

---

## 🌐 Desktop (Para probar)

### Chrome
```
1. Presionar Ctrl + Shift + Del
2. Seleccionar "Imágenes y archivos en caché"
3. Click en "Borrar datos"
```

O simplemente:
```
Ctrl + F5  (recarga forzada)
```

### Firefox
```
1. Presionar Ctrl + Shift + Del
2. Seleccionar "Caché"
3. Click en "Limpiar ahora"
```

---

## ✅ Checklist de Verificación

Después de limpiar caché, en tu celular deberías ver:

### En la página de clientes:

- [ ] ✅ **Botones de navegación** (arriba) tienen texto:
  - SETTINGS, CENTER, CLIENTS, DOCUMENTS, EXTRA
  - PARTS, REPORTS, SERVICES, VEHICLES, LOGOUT

- [ ] ✅ **Cards de clientes** tienen:
  - Bordes brillantes cyan
  - Nombre del cliente en grande (fuente Orbitron)
  - ID en purple (#bc13fe)

- [ ] ✅ **Botones de acción** en cada card:
  - 👁️ VIEW (cyan)
  - ✏️ EDIT (cyan)
  - 🗑️ DELETE (rojo)

- [ ] ✅ **Los botones son grandes**:
  - Mínimo 70-75px de altura
  - Texto visible y legible
  - Iconos grandes (1.6-1.8rem)

---

## 🎯 Si AÚN NO VES LOS CAMBIOS

### 1. Verifica en PythonAnywhere

Vuelve a abrir el archivo en PythonAnywhere Files y verifica que tenga:

```css
/* 🎨 DISEÑO FUTURISTA Y TECNOLÓGICO - OPTIMIZADO PARA MÓVIL */
:root {
    --cyber-blue: #00ffff;
    --cyber-purple: #bc13fe;
    ...
}
```

Y las cards móviles tengan:
```html
<div class="client-card-futuristic">
```

### 2. Verifica que hiciste Reload

En PythonAnywhere webapps:
- Debe decir: "Last reload: hace unos segundos"
- Si no, haz click en "Reload" de nuevo

### 3. Limpia caché AGRESIVAMENTE

```
iPhone:
Ajustes > Safari > Avanzado > Datos del sitio web > Eliminar todos

Android:
Chrome > Configuración > Privacidad > Borrar datos de navegación > TODO
```

### 4. Modo Avión (Truco)

```
1. Activa modo avión en tu celular
2. Espera 5 segundos
3. Desactiva modo avión
4. Abre el navegador
5. Carga la página de nuevo
```

---

## 🔍 Cómo Verificar que el Archivo se Subió

En PythonAnywhere, abre el archivo y busca (Ctrl+F):
- `client-card-futuristic` ✅ Debe encontrarlo
- `btn-futuristic` ✅ Debe encontrarlo
- `--cyber-blue: #00ffff` ✅ Debe encontrarlo

Si NO encuentra estas clases, el archivo NO se actualizó correctamente.

---

## 🎬 GIF Mental de lo que Debes Ver

### Móvil (Correcto) ✅
```
╔═══════════════════════════════════╗
║  ⚡ Borde brillante cyan ⚡        ║
║                                   ║
║  👤 Juan Pérez           #12345   ║  ← Blanco
║                                   ║
║  📧 juan@email.com                ║  ← Cyan
║  📞 +56 9 1234 5678               ║
║  ─────────────────────────────────║
║                                   ║
║  ┌───────┐ ┌───────┐ ┌─────────┐║
║  │  👁️   │ │  ✏️   │ │   🗑️   │║  ← Iconos GRANDES
║  │ VIEW  │ │ EDIT  │ │ DELETE │║  ← Texto VISIBLE
║  └───────┘ └───────┘ └─────────┘║  ← Cyan brillante
╚═══════════════════════════════════╝
```

### Móvil (Incorrecto) ❌
```
┌──────────────────────────────────┐
│ Juan Pérez              #12345   │  ← Sin efectos
│ juan@email.com                   │
│ +56 9 1234 5678                  │
│                                  │
│ [    ] [    ] [    ]             │  ← Botones vacíos
└──────────────────────────────────┘  ← Sin brillo
```

---

## 🚀 Resumen

1. **Pega el nuevo archivo en PythonAnywhere**
2. **Click en "Reload"**
3. **Espera 30 segundos**
4. **Limpia caché del celular**
5. **Recarga la página**

**Si después de todo esto NO ves cambios**, el archivo NO se guardó correctamente en PythonAnywhere.

---

**Tiempo total: 2 minutos** ⚡

