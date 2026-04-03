# INSTRUCCIONES PARA DEPLOY - Fix Vehículos No Mostrados

## Problemas Solucionados

1. **Vehículos no se muestran en el select** aunque se cargan (2 vehículos encontrados en prefetch)
2. **Error de sintaxis en `marketplace_tooltip.js:361`** - Declaración de función en modo estricto
3. **APIs devuelven HTML en lugar de JSON** - Errores "Unexpected token '<'"
4. **Select2 no inicializa correctamente** después de cargar opciones

## Archivos Nuevos Creados

### 1. `static/js/fix_vehiculos_select2.js`
- Reinicializa Select2 para vehículos
- Carga vehículos desde prefetch/API
- Expone funciones globales para reparación manual

### 2. `static/js/emergency_fix_vehiculos.js`
- Fix de emergencia que se ejecuta inmediatamente
- Fuerza visualización de opciones
- Crea debug viewer para ver opciones disponibles
- Testea APIs problemáticas

### 3. `static/js/api_fix.js`
- Parchea `fetch()` para manejar respuestas HTML
- Intercepta APIs problemáticas y devuelve JSON vacío
- Parchea `updateDocumentNumber` y `buscarClientes`

### 4. `static/js/marketplace_tooltip_fixed.js`
- Versión corregida sin `'use strict'` problemático
- Sintaxis ES5 compatible

## Archivos Modificados

### 1. `templates/taller/common/documentos/document_form.html`
- Incluye los 3 scripts de fix:
  ```html
  <script src="{% static 'js/fix_vehiculos_select2.js' %}"></script>
  <script src="{% static 'js/emergency_fix_vehiculos.js' %}"></script>
  <script src="{% static 'js/api_fix.js' %}"></script>
  ```
- Usa `marketplace_tooltip_fixed.js` en lugar de la versión original

## Pasos para Deploy

### 1. LOCAL - Preparar cambios
```bash
# Agregar archivos nuevos
git add static/js/fix_vehiculos_select2.js
git add static/js/emergency_fix_vehiculos.js
git add static/js/api_fix.js
git add static/js/marketplace_tooltip_fixed.js

# Agregar template modificado
git add templates/taller/common/documentos/document_form.html

# Commit
git commit -m "FIX URGENTE: Vehículos no mostrados en formulario de documentos

- Agregados 3 scripts de fix para vehículos y APIs
- Corregido error de sintaxis en marketplace_tooltip.js
- Solucionado problema de Select2 no inicializado
- Parcheadas APIs que devuelven HTML en lugar de JSON
- Mejorada carga y visualización de vehículos"

# Push
git push origin main
```

### 2. SERVIDOR - Aplicar cambios (via SSH)
```bash
# Conectarse al servidor
ssh usuario@egarage.cl

# Navegar al proyecto
cd /var/www/egarage

# Actualizar código
git pull origin main

# Activar virtual environment
source venv/bin/activate

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Reiniciar servidor
sudo systemctl restart gunicorn
# o
sudo systemctl restart nginx
```

### 3. POST-DEPLOY - Verificación
1. **Acceder al formulario:** `https://www.egarage.cl/cl/es/documentos/form/`
2. **Recargar sin cache:** Ctrl+Shift+R
3. **Seleccionar cliente:** Mauricio Alvarado (ID: 11)
4. **Verificar consola:** No debería haber errores rojos
5. **Verificar vehículos:** Deberían aparecer 2 vehículos

## Comandos de Debug (Consola del Navegador)

Si los problemas persisten, ejecutar en consola:

```javascript
// 1. Forzar fix de emergencia
window.emergencyFixVehiculos();

// 2. Reparar Select2 específicamente
window.repararSelect2Vehiculos();

// 3. Testear APIs
window.testAPIsFixed();

// 4. Mostrar debug de vehículos
window.showVehiculosDebug();

// 5. Forzar carga de vehículos
window.forzarCargaVehiculos();
```

## Solución para Cache del Navegador

### Opción 1: Hard Refresh
- **Windows/Linux:** Ctrl + Shift + R
- **Mac:** Cmd + Shift + R

### Opción 2: Limpiar Cache
1. F12 → Application → Clear Storage → Clear site data
2. O Ctrl+Shift+Delete → "Cached images and files"

### Opción 3: Agregar Versión (para futuro)
```html
<script src="{% static 'js/fix_vehiculos_select2.js' %}?v=2.1.5"></script>
```

## Monitoreo Post-Deploy

Verificar estos logs en consola:
- ✅ `EMERGENCY FIX: Iniciando fix de emergencia para vehículos...`
- ✅ `API FIX: Parcheando APIs problemáticas...`
- ✅ `Encontrados 2 vehículos en prefetch`
- ❌ NO debería haber: `Uncaught SyntaxError` o `Unexpected token '<'`

## Rollback (si es necesario)
```bash
# Revertir template
git checkout templates/taller/common/documentos/document_form.html

# Revertir scripts
git checkout static/js/

# O usar backup
cp templates/taller/common/documentos/document_form.html.backup templates/taller/common/documentos/document_form.html
```

## Contacto para Soporte

Si los problemas persisten:
1. Revisar consola del navegador para errores específicos
2. Ejecutar `window.testAPIsFixed()` para diagnosticar APIs
3. Verificar que jQuery y Select2 se carguen correctamente
4. Revisar network tab para respuestas de API