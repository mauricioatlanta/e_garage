# 📦 Lista de Archivos para Actualizar en el Servidor

## 🎯 Resumen
Esta lista incluye todos los archivos modificados o creados durante la sesión de mejoras de "Capa de Inteligencia" y optimización del formulario de documentos.

---

## 📁 ARCHIVOS MODIFICADOS (Actualizar)

### 1. Formularios (Backend)
```
taller/forms/documento_form.py
```
**Cambios principales:**
- ✅ Validación blindada en `clean_kilometraje()` (valores negativos, conversión millas/km)
- ✅ Validación de kilometraje creciente en `clean()` (no menor al anterior)
- ✅ Configuración de `payment_status` como ChoiceField con traducciones
- ✅ Método `_configure_widget_attrs()` para inputmode="numeric" y placeholders
- ✅ Configuración de widgets con atributos optimizados

### 2. Templates (Frontend)
```
templates/taller/common/documentos/document_form.html
```
**Cambios principales:**
- ✅ Eliminados todos los `if is_cl` → Reemplazados por `{% trans %}`
- ✅ Eliminados todos los `!important` del CSS (de 172 a 0)
- ✅ Refactorizado CSS: bordes de 2.5px/3px → 1px
- ✅ Eliminada animación `pulse-glow infinite` (mejor rendimiento)
- ✅ Cambiado `text-transform: uppercase` → `none` (menos fatiga visual)
- ✅ Optimizados box-shadows (más ligeros)
- ✅ Uso correcto de Django Forms (`{{ form.kilometraje }}`, `{{ form.tipo }}`, etc.)
- ✅ Errores mostrados elegantemente
- ✅ Campos calculados marcados con `data-calculated="true"`
- ✅ Script `document_engine.js` agregado al final

```
templates/taller/common/documentos/fragments/_tax_id.html
```
**Cambios principales:**
- ✅ Eliminados `if is_cl` → Usa `{% trans %}`

```
templates/taller/common/documentos/fragments/_address.html
```
**Cambios principales:**
- ✅ Eliminados `if is_cl` → Usa `{% trans %}`
- ✅ Agregado `inputmode="numeric"` a campo ZIP
- ✅ Uso de Django Forms donde es posible

### 3. Configuración Tailwind
```
static/js/tailwind.config.js
```
**Cambios principales:**
- ✅ Agregados colores personalizados (neon-cyan, cyber-dark, etc.)
- ✅ Agregados box-shadows personalizados
- ✅ Agregado `text-neon-cyan` para uso directo

---

## 🆕 ARCHIVOS NUEVOS (Crear en el servidor)

### 1. JavaScript - Capa de Inteligencia
```
static/js/document_engine.js
```
**Funcionalidad:**
- ✅ Forzar teclado numérico en móviles (`inputmode="numeric"`)
- ✅ Blindar campos calculados (readonly)
- ✅ Mejoras de UX móvil
- ✅ Prevenir edición de totales

### 2. Scripts de Deployment
```
scripts/compile_translations.sh
```
**Funcionalidad:**
- ✅ Script Linux/Mac para compilar traducciones
- ✅ Verifica que los archivos `.mo` se generaron correctamente

```
scripts/compile_translations.ps1
```
**Funcionalidad:**
- ✅ Script Windows para compilar traducciones
- ✅ Verifica que los archivos `.mo` se generaron correctamente

### 3. Documentación
```
docs/DEPLOYMENT_TRANSLATIONS.md
```
**Contenido:**
- ✅ Guía completa de deployment de traducciones
- ✅ Checklist de deployment
- ✅ Troubleshooting

```
docs/MEJORAS_FINALES_SAAS.md
```
**Contenido:**
- ✅ Documentación de validación de kilometraje creciente
- ✅ Documentación de compilación de traducciones
- ✅ Impacto en el negocio

```
docs/CAPA_INTELIGENCIA_IMPLEMENTADA.md
```
**Contenido:**
- ✅ Documentación completa de la capa de inteligencia
- ✅ Los tres niveles implementados
- ✅ Casos de prueba

---

## 🚀 COMANDOS DE DEPLOYMENT

### 📍 NOTA IMPORTANTE
Los comandos siguientes son para el **SERVIDOR LINUX**. Si estás en **Windows local**, solo necesitas:
- ✅ `python manage.py compilemessages` (ya lo hiciste ✅)
- ✅ `python manage.py collectstatic --noinput` (ya lo hiciste ✅)
- ✅ Reiniciar el servidor de desarrollo (`python manage.py runserver`) si está corriendo

---

### 🐧 PARA EL SERVIDOR LINUX (Producción)

#### Paso 1: Subir archivos
```bash
# Archivos modificados
scp taller/forms/documento_form.py usuario@servidor:/ruta/proyecto/taller/forms/
scp templates/taller/common/documentos/document_form.html usuario@servidor:/ruta/proyecto/templates/taller/common/documentos/
scp templates/taller/common/documentos/fragments/_tax_id.html usuario@servidor:/ruta/proyecto/templates/taller/common/documentos/fragments/
scp templates/taller/common/documentos/fragments/_address.html usuario@servidor:/ruta/proyecto/templates/taller/common/documentos/fragments/
scp static/js/tailwind.config.js usuario@servidor:/ruta/proyecto/static/js/

# Archivos nuevos
scp static/js/document_engine.js usuario@servidor:/ruta/proyecto/static/js/
scp scripts/compile_translations.sh usuario@servidor:/ruta/proyecto/scripts/
scp scripts/compile_translations.ps1 usuario@servidor:/ruta/proyecto/scripts/
```

#### Paso 2: Compilar traducciones (CRÍTICO)
```bash
# En el servidor Linux
cd /ruta/proyecto
python manage.py makemessages -l es
python manage.py makemessages -l en
python manage.py makemessages -l pt_BR
python manage.py compilemessages

# O usar el script
chmod +x scripts/compile_translations.sh
./scripts/compile_translations.sh
```

#### Paso 3: Recolectar archivos estáticos
```bash
python manage.py collectstatic --noinput
```

#### Paso 4: Reiniciar servidor
```bash
# Gunicorn
sudo systemctl restart gunicorn
# o
sudo supervisorctl restart gunicorn

# Nginx (si es necesario)
sudo nginx -t
sudo systemctl reload nginx
```

---

### 🪟 PARA WINDOWS LOCAL (Desarrollo)

#### Ya completado ✅:
```powershell
# ✅ Traducciones compiladas
python manage.py compilemessages

# ✅ Archivos estáticos recolectados
python manage.py collectstatic --noinput
```

#### Si el servidor de desarrollo está corriendo:
```powershell
# Detener: Ctrl+C en la terminal donde corre runserver
# Reiniciar:
python manage.py runserver
```

**Nota**: En Windows local NO necesitas `sudo` ni `systemctl` - esos son comandos de Linux.

---

## ✅ CHECKLIST DE VERIFICACIÓN

Después de actualizar, verificar:

- [ ] El formulario carga sin errores
- [ ] Los campos muestran errores correctamente (probar con kilometraje negativo)
- [ ] La validación de kilometraje creciente funciona (probar con valor menor al anterior)
- [ ] En móvil, el teclado numérico aparece automáticamente
- [ ] Los campos calculados (totales) no se pueden editar
- [ ] Las traducciones funcionan (cambiar idioma)
- [ ] No hay errores en la consola del navegador (F12)
- [ ] El CSS se ve limpio (sin bordes gruesos, sin animaciones infinite)

---

## 📊 RESUMEN DE CAMBIOS

### Archivos Modificados: 5
1. `taller/forms/documento_form.py`
2. `templates/taller/common/documentos/document_form.html`
3. `templates/taller/common/documentos/fragments/_tax_id.html`
4. `templates/taller/common/documentos/fragments/_address.html`
5. `static/js/tailwind.config.js`

### Archivos Nuevos: 6
1. `static/js/document_engine.js`
2. `scripts/compile_translations.sh`
3. `scripts/compile_translations.ps1`
4. `docs/DEPLOYMENT_TRANSLATIONS.md`
5. `docs/MEJORAS_FINALES_SAAS.md`
6. `docs/CAPA_INTELIGENCIA_IMPLEMENTADA.md`

### Total: 11 archivos

---

## 🎯 PRIORIDAD

### 🔴 CRÍTICO (Hacer primero)
1. `taller/forms/documento_form.py` - Validaciones críticas
2. `templates/taller/common/documentos/document_form.html` - Template principal
3. `static/js/document_engine.js` - UX móvil
4. Compilar traducciones (`compilemessages`)

### 🟡 IMPORTANTE (Hacer después)
5. `templates/taller/common/documentos/fragments/_tax_id.html`
6. `templates/taller/common/documentos/fragments/_address.html`
7. `static/js/tailwind.config.js`

### 🟢 OPCIONAL (Puede esperar)
8. Scripts de deployment
9. Documentación

---

## 💡 NOTA FINAL

**IMPORTANTE**: No olvides compilar las traducciones después de subir los archivos. Sin esto, las traducciones pueden ser lentas en producción.

```bash
python manage.py compilemessages
```

¡Listo para deployment! 🚀

