# 🔧 SOLUCIÓN: Template `document_edit.html` No Existe

## ❌ Error

```
TemplateDoesNotExist at /cl/documentos/form/2/
taller/common/documentos/document_edit.html
```

## 🔍 Causa

La vista `DocumentoUpdateView` estaba intentando usar el template `documentos/document_edit.html` que no existe en el servidor.

## ✅ Solución Aplicada

Se modificó `DocumentoUpdateView` para usar el mismo template que `DocumentoCreateView` (`document_form.html`), que ya existe y funciona correctamente.

### **Archivo Modificado**

**`taller/documentos/views_migrated.py`**

**Cambio en `DocumentoUpdateView`**:
- **Antes**: `base_template_name = "documentos/document_edit.html"`
- **Después**: `base_template_name = "documentos/document_form.html"`
- **Eliminado**: El método `get_template_names()` personalizado que intentaba buscar múltiples templates

---

## 📋 Archivo a Actualizar en el Servidor

### **taller/documentos/views_migrated.py**
- **Cambio**: `DocumentoUpdateView` ahora usa `document_form.html` en lugar de `document_edit.html`
- **Ubicación en servidor**: `taller/documentos/views_migrated.py`

---

## 🚀 INSTRUCCIONES DE ACTUALIZACIÓN

### **Paso 1: Subir archivo actualizado**
1. **Subir `taller/documentos/views_migrated.py`**
   - Desde tu PC: `taller/documentos/views_migrated.py`
   - Al servidor: `taller/documentos/views_migrated.py`
   - Reemplazar el archivo existente

### **Paso 2: Recargar aplicación**
- PythonAnywhere: Ir a pestaña "Web" → Click "Reload"
- Otro servidor: Reiniciar servicio Django/Gunicorn/uWSGI

### **Paso 3: Verificar**
1. Ir a: `https://www.egarage.cl/cl/documentos/`
2. Hacer clic en "Editar" en cualquier documento
3. Debe cargar el formulario de edición sin errores
4. No debe aparecer el error `TemplateDoesNotExist`

---

## ✅ VERIFICACIÓN

Después de actualizar:
- ✅ `https://www.egarage.cl/cl/documentos/form/2/` carga sin errores
- ✅ `https://www.egarage.cl/us/documentos/form/2/` carga sin errores
- ✅ El formulario de edición se muestra correctamente
- ✅ No aparece el error `TemplateDoesNotExist`

---

## 🔍 Nota Técnica

El template `document_form.html` es usado tanto para crear como para editar documentos. El formulario detecta automáticamente si es creación o edición basándose en si el objeto `documento` tiene un `pk` o no.

---

**Fecha de creación**: 2025-11-25
**Archivos modificados**: 1
**Tiempo estimado de actualización**: 2-3 minutos

