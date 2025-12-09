# 🚨 Fix Urgente - Servidor de Producción

**Fecha**: 2025-12-08  
**Error**: `VariableDoesNotExist` en `/us/documentos/form/`  
**Causa**: El servidor tiene versión antigua del template con referencia a `company_country`

---

## 🔴 Problema Identificado

El servidor de producción tiene una versión antigua del archivo `document_form.html` que intenta acceder a `company_country` directamente, causando el error:

```
VariableDoesNotExist: Failed lookup for key [company_country]
```

**Línea problemática en servidor (antigua)**:
```django
{% with active_country=company_country|default:request.company_country|default:empresa.pais|default:'CL' %}
```

**Línea correcta (local)**:
```django
{% with active_country=empresa.pais|default:'CL' %}
```

---

## ✅ Solución: Actualizar Archivo en Servidor

### Opción 1: Via Git (Recomendada)

```bash
# En el servidor
cd /home/atlantareciclajes/apps/egarage/current
workon venv_egarage310
git pull origin main
```

### Opción 2: Editar Directamente en el Servidor

```bash
# En el servidor
cd /home/atlantareciclajes/apps/egarage/current
nano templates/taller/common/documentos/document_form.html
```

**Buscar línea 186** (o buscar `company_country|default:request.company_country`):

**Cambiar de:**
```django
{% with active_country=company_country|default:request.company_country|default:empresa.pais|default:'CL' %}
```

**A:**
```django
{% with active_country=empresa.pais|default:'CL' %}
```

**Guardar**: `Ctrl+O`, `Enter`, `Ctrl+X`

**También verificar línea 240** (en bloque `documento_content`) y hacer el mismo cambio si es necesario.

---

## 🔍 Verificación Rápida

### Verificar que el cambio se aplicó:

```bash
# En el servidor
grep -n "company_country|default" templates/taller/common/documentos/document_form.html
```

**Resultado esperado**: No debe encontrar ninguna línea (o solo comentarios)

### Verificar sintaxis correcta:

```bash
# En el servidor
grep -n "active_country=empresa.pais" templates/taller/common/documentos/document_form.html
```

**Resultado esperado**: Debe encontrar las líneas 187 y 241

---

## ⚠️ IMPORTANTE: Verificar Ambas Ubicaciones

El error puede estar en dos lugares del mismo archivo:

1. **Línea ~186** (bloque `documento_title`)
2. **Línea ~240** (bloque `documento_content`)

**Ambas deben corregirse**:

```django
# ANTES (INCORRECTO):
{% with active_country=company_country|default:request.company_country|default:empresa.pais|default:'CL' %}

# DESPUÉS (CORRECTO):
{% with active_country=empresa.pais|default:'CL' %}
```

---

## 🚀 Después de Corregir

1. **No es necesario reiniciar** (templates se recargan automáticamente)
2. **Verificar inmediatamente**: Acceder a `https://www.egarage.cl/us/documentos/form/`
3. **Si persiste el error**: Limpiar cache de Python:
   ```bash
   find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
   find . -name "*.pyc" -delete
   ```

---

## 📋 Comandos Completos (Copia y Pega)

```bash
# 1. Ir al directorio
cd /home/atlantareciclajes/apps/egarage/current

# 2. Activar entorno virtual
workon venv_egarage310

# 3. Opción A: Actualizar via Git
git pull origin main

# O Opción B: Editar manualmente
nano templates/taller/common/documentos/document_form.html
# Buscar y reemplazar las líneas problemáticas

# 4. Verificar cambios
grep -n "active_country=empresa.pais" templates/taller/common/documentos/document_form.html

# 5. Limpiar cache (opcional pero recomendado)
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -name "*.pyc" -delete
```

---

## ✅ Verificación Final

Después de aplicar el fix, acceder a:
- `https://www.egarage.cl/us/documentos/form/`
- `https://www.egarage.cl/cl/documentos/form/`

**Resultado esperado**: ✅ Página carga sin errores

---

**Prioridad**: 🔴 **CRÍTICA** - Este error impide crear documentos en producción



