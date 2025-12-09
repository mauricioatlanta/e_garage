# 🔧 Fix: Botones de Repuestos/Servicios Desaparecidos

**Fecha**: 2025-12-08  
**Problema**: Después del fix del template, desaparecieron los botones para agregar repuestos, servicios y otros servicios  
**Causa**: `ui_config` no estaba siendo pasado al contexto en `DocumentoCreateView`

---

## ✅ Solución Aplicada

Se agregó `ui_config` al contexto en `DocumentoCreateView.get_context_data()` en `taller/documentos/views_migrated.py`.

### Cambio Realizado

**Archivo**: `taller/documentos/views_migrated.py`  
**Línea**: ~737

**Antes**:
```python
context.update(
    {
        "clientes_prefetch": clientes_prefetch,
        "vehiculos_prefetch": vehiculos_prefetch,
        "repuestos_prefetch": repuestos_prefetch,
        "servicios_prefetch": servicios_prefetch,
        "otros_servicios_prefetch": otros_servicios_prefetch,
    }
)
return context
```

**Después**:
```python
# Obtener ui_config de la empresa
ui_config = {}
try:
    from taller.configuracion.rubros_logic import get_ui_config
    config = getattr(empresa, "config", None)
    if config:
        ui_config = get_ui_config(config)
except Exception:
    pass

# Si no hay configuración, usar valores por defecto
if not ui_config:
    ui_config = {
        "show_repuestos": True,
        "show_services": True,
        "show_otros_servicios": True,
        "show_kilometraje": True,
        "show_vehicle": True,
    }

context.update(
    {
        "clientes_prefetch": clientes_prefetch,
        "vehiculos_prefetch": vehiculos_prefetch,
        "repuestos_prefetch": repuestos_prefetch,
        "servicios_prefetch": servicios_prefetch,
        "otros_servicios_prefetch": otros_servicios_prefetch,
        "ui_config": ui_config,  # ✅ Agregar ui_config al contexto
    }
)
return context
```

---

## 🔍 Explicación

El template `document_form.html` usa `{% if ui_config.show_repuestos %}`, `{% if ui_config.show_services %}`, etc. para mostrar/ocultar los botones y secciones.

- ✅ `DocumentoUpdateView` ya tenía `ui_config` en el contexto (línea 1078)
- ❌ `DocumentoCreateView` **NO** tenía `ui_config` en el contexto

Esto causaba que los botones no se mostraran al crear un nuevo documento.

---

## 🚀 Despliegue

Este fix debe subirse junto con el fix del template (`document_form.html`).

### Opción 1: Git (Recomendado)

```bash
# Commit y push
git add taller/documentos/views_migrated.py
git commit -m "fix: Agregar ui_config al contexto de DocumentoCreateView"
git push origin main

# En el servidor
cd /home/atlantareciclajes/apps/egarage/current
git pull origin main
```

### Opción 2: Edición Directa en Servidor

```bash
# En el servidor
cd /home/atlantareciclajes/apps/egarage/current
nano taller/documentos/views_migrated.py
```

Buscar la línea ~737 y agregar el código de `ui_config` antes del `context.update()` final.

---

## ✅ Verificación

Después del despliegue:

1. Acceder a: `https://www.egarage.cl/us/documentos/form/`
2. **Verificar que aparezcan**:
   - ✅ Botón "+ Agregar repuesto"
   - ✅ Botón "+ Agregar servicio"
   - ✅ Botón "+ Agregar servicio externo"
3. **Verificar que funcionen**:
   - ✅ Al hacer clic en los botones, se agregan filas al formulario
   - ✅ Los contenedores `repuestos-container`, `servicios-container`, `otros-container` están visibles

---

## 📋 Archivos Modificados

1. ✅ `taller/documentos/views_migrated.py` - Agregado `ui_config` al contexto
2. ✅ `templates/taller/common/documentos/document_form.html` - Fix de `VariableDoesNotExist`

---

**Prioridad**: 🔴 **CRÍTICA** - Sin estos botones, no se pueden crear documentos con repuestos/servicios



