# 🚨 Fix Urgente - Línea 239 document_form.html

**Error**: `VariableDoesNotExist: Failed lookup for key [company_country]`  
**Ubicación**: Línea 239 en servidor de producción  
**Prioridad**: 🔴 **CRÍTICA** - Impide crear documentos

---

## ✅ Estado del Archivo Local

El archivo local **YA ESTÁ CORREGIDO**:
- ✅ Línea 187: `{% with active_country=empresa.pais|default:'CL' %}`
- ✅ Línea 241: `{% with active_country=empresa.pais|default:'CL' %}`

---

## 🔴 Problema en el Servidor

El servidor todavía tiene la versión antigua en la línea 239:
```django
{% with active_country=company_country|default:request.company_country|default:empresa.pais|default:'CL' %}
```

**Debe cambiarse a:**
```django
{% with active_country=empresa.pais|default:'CL' %}
```

---

## 🚀 Solución Rápida: Opción 1 (Script Automático)

### Paso 1: Subir el script al servidor

```bash
# Desde tu máquina local
scp FIX_SERVIDOR_LINEA_239.sh usuario@servidor:/tmp/
```

### Paso 2: Ejecutar en el servidor

```bash
# Conectarse al servidor
ssh usuario@servidor

# Ir al directorio de la aplicación
cd /home/atlantareciclajes/apps/egarage/current

# Dar permisos de ejecución
chmod +x /tmp/FIX_SERVIDOR_LINEA_239.sh

# Ejecutar el script
/tmp/FIX_SERVIDOR_LINEA_239.sh
```

---

## 🚀 Solución Rápida: Opción 2 (Edición Manual)

### Paso 1: Conectarse al servidor

```bash
ssh usuario@servidor
cd /home/atlantareciclajes/apps/egarage/current
```

### Paso 2: Crear backup

```bash
cp templates/taller/common/documentos/document_form.html \
   templates/taller/common/documentos/document_form.html.backup_$(date +%Y%m%d_%H%M%S)
```

### Paso 3: Editar el archivo

```bash
nano templates/taller/common/documentos/document_form.html
```

**Buscar** (Ctrl+W) la línea 239:
```
{% with active_country=company_country|default:request.company_country|default:empresa.pais|default:'CL' %}
```

**Reemplazar por:**
```
{% with active_country=empresa.pais|default:'CL' %}
```

**También buscar** la línea ~186 (en el bloque `documento_title`) y hacer el mismo cambio si existe.

**Guardar**: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## 🚀 Solución Rápida: Opción 3 (Git Pull)

Si los cambios ya están en el repositorio Git:

```bash
# En el servidor
cd /home/atlantareciclajes/apps/egarage/current
workon venv_egarage310  # o el nombre de tu entorno virtual
git pull origin main
```

---

## ✅ Verificación

Después de aplicar el fix, verificar:

```bash
# Verificar que el patrón antiguo NO existe
grep -n "company_country|default:request.company_country" \
  templates/taller/common/documentos/document_form.html

# Debe retornar: (nada, o solo comentarios)

# Verificar que el patrón nuevo SÍ existe
grep -n "active_country=empresa.pais|default:'CL'" \
  templates/taller/common/documentos/document_form.html

# Debe mostrar las líneas 187 y 241 (o 186 y 239 en el servidor)
```

---

## 🔍 Verificación en el Navegador

1. Acceder a: `https://www.egarage.cl/us/documentos/form/`
2. **Resultado esperado**: ✅ Página carga sin errores
3. Si persiste el error, limpiar cache de Python:

```bash
cd /home/atlantareciclajes/apps/egarage/current
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -name "*.pyc" -delete
```

---

## 📋 Comandos Completos (Copia y Pega)

```bash
# 1. Conectarse al servidor
ssh usuario@servidor

# 2. Ir al directorio
cd /home/atlantareciclajes/apps/egarage/current

# 3. Crear backup
cp templates/taller/common/documentos/document_form.html \
   templates/taller/common/documentos/document_form.html.backup

# 4. Editar (usar sed para reemplazo automático)
sed -i "s/{% with active_country=company_country|default:request.company_country|default:empresa.pais|default:'CL' %}/{% with active_country=empresa.pais|default:'CL' %}/g" \
  templates/taller/common/documentos/document_form.html

# 5. Verificar
grep -n "active_country=empresa.pais" \
  templates/taller/common/documentos/document_form.html

# 6. Limpiar cache (opcional)
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -name "*.pyc" -delete
```

---

## ⚠️ IMPORTANTE

- **No es necesario reiniciar** la aplicación (Django recarga templates automáticamente)
- Si el error persiste después del fix, puede ser cache del navegador. Probar en modo incógnito.
- El fix debe aplicarse en **ambas ubicaciones** del archivo:
  - Línea ~186 (bloque `documento_title`)
  - Línea ~239 (bloque `documento_content`)

---

**Prioridad**: 🔴 **CRÍTICA** - Este error impide crear documentos en producción



