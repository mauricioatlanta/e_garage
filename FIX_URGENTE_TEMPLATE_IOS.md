# 🚨 Fix Urgente: Template Syntax Error + iOS Password Fix

**Fecha**: 2025-12-08  
**Prioridad**: 🔴 **CRÍTICA**

---

## 🔴 Problema 1: TemplateSyntaxError en document_form.html

### Error
```
Invalid block tag on line 235: 'endblock', expected 'endwith'
```

### Causa
Hay dos bloques `{% with %}` anidados (líneas 187-188) pero solo se está cerrando uno antes del `{% endblock %}`.

### Solución Aplicada
Agregar un segundo `{% endwith %}` antes del `{% endblock %}`:

**Línea 227-235 (ANTES):**
```django
{% endwith %}

<script>
function submitLanguageDoc(lang) {
  document.getElementById('language-input-doc').value = lang;
  document.getElementById('language-form-doc').submit();
}
</script>
{% endblock %}
```

**Línea 227-235 (DESPUÉS):**
```django
{% endwith %}
{% endwith %}

<script>
function submitLanguageDoc(lang) {
  document.getElementById('language-input-doc').value = lang;
  document.getElementById('language-form-doc').submit();
}
</script>
{% endblock documento_title %}
```

---

## 🔴 Problema 2: Fix iOS Password No Funciona

### Síntomas Reportados
- Caracteres no se muestran como puntos
- Cursor salta o deja espacios
- Formulario regresa sin completar la acción

### Diagnóstico

#### ✅ Script está cargado
- El script `ios-password-fix.js` está incluido en `templates/base.html` (línea 23)
- Se carga con `defer` para ejecutarse después del DOM

#### ⚠️ Posibles causas
1. **Script no se ejecuta**: El script puede no estar detectando iOS correctamente
2. **Atributos no se aplican**: Los campos de contraseña pueden no tener los atributos necesarios
3. **Cache del navegador**: El navegador puede estar usando una versión antigua del script

### Soluciones Propuestas

#### A. Verificar que el script se carga
En el iPhone, abrir la consola de Safari (Settings → Safari → Advanced → Web Inspector) y verificar:
```javascript
// Debe mostrar el script
console.log(document.querySelector('script[src*="ios-password-fix"]'));

// Debe mostrar campos con la clase
console.log(document.querySelectorAll('.ios-password-fixed'));
```

#### B. Mejorar detección de iOS
El script actual usa:
```javascript
const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
```

**Mejora sugerida:**
```javascript
const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream ||
              (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
```

#### C. Aplicar atributos directamente en el formulario
Agregar atributos directamente en el campo de contraseña del formulario:

**Archivo**: `taller/forms/custom_login.py`
```python
self.fields['password'].widget.attrs.update({
    'autocapitalize': 'none',
    'autocorrect': 'off',
    'spellcheck': 'false',
    'inputmode': 'text',
    'autocomplete': 'current-password',
})
```

#### D. Forzar recarga del script
1. Cambiar el nombre del archivo o agregar versión:
   ```html
   <script src="{% static 'js/ios-password-fix.js' %}?v=2" defer></script>
   ```

2. Ejecutar `collectstatic` nuevamente:
   ```bash
   python manage.py collectstatic --noinput --clear
   ```

3. Reiniciar aplicación

---

## 📋 Checklist de Acciones

### Inmediatas (Template Error)
- [x] Corregir sintaxis del template (agregar `{% endwith %}` faltante)
- [ ] Verificar que el template carga sin errores
- [ ] Reiniciar aplicación

### iOS Password Fix
- [ ] Verificar que el script se carga en iPhone
- [ ] Verificar que los campos tienen la clase `ios-password-fixed`
- [ ] Mejorar detección de iOS si es necesario
- [ ] Agregar atributos directamente en el formulario
- [ ] Ejecutar `collectstatic --clear` y reiniciar
- [ ] Probar en iPhone 16 real

---

## 🎯 Instrucciones para el Usuario (PWA)

El usuario mencionó que prefiere no escribir la URL. La solución ya está implementada:

### Instalar PWA en iPhone
1. Abrir Safari en iPhone
2. Navegar a `www.egarage.cl`
3. Tocar el botón de compartir (cuadrado con flecha)
4. Seleccionar "Agregar a pantalla de inicio"
5. Confirmar

Una vez instalada, la PWA:
- ✅ Se abre como una app nativa
- ✅ No requiere escribir la URL
- ✅ Funciona offline (páginas cacheadas)
- ✅ Acceso rápido desde la pantalla de inicio

---

## 🔧 Comandos de Verificación

### Verificar archivos estáticos
```bash
ls -la staticfiles/js/ios-password-fix.js
ls -la staticfiles/manifest.json
ls -la staticfiles/sw.js
```

### Forzar recarga
```bash
python manage.py collectstatic --noinput --clear
# Reiniciar aplicación
```

### Verificar en consola del navegador (iPhone)
```javascript
// Verificar script cargado
document.querySelector('script[src*="ios-password-fix"]')

// Verificar campos corregidos
document.querySelectorAll('.ios-password-fixed')

// Verificar atributos
const input = document.querySelector('input[type="password"]');
console.log('autocapitalize:', input.getAttribute('autocapitalize'));
console.log('autocorrect:', input.getAttribute('autocorrect'));
console.log('spellcheck:', input.getAttribute('spellcheck'));
```

---

**Estado**: 🔴 **EN PROGRESO**  
**Próximos pasos**: Corregir template, verificar script iOS, instruir usuario sobre PWA



