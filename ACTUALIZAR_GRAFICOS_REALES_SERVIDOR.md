# 🚀 Actualizar Gráficos con Datos Reales en el Servidor

## 📋 Archivos Modificados

Los siguientes archivos fueron actualizados para mostrar datos reales en los gráficos:

1. **`taller/views_extra/dashboard_empresa.py`** - Vista con cálculos de datos reales
2. **`templates/us/en/dashboard/centro_operaciones_espacial.html`** - Template USA
3. **`templates/taller/us/en/dashboard/centro_operaciones_espacial.html`** - Template USA (alternativo)

---

## ⚡ OPCIÓN 1: Usando Git (Recomendado)

### Paso 1: Commit y Push desde tu PC

```powershell
# Desde E:\projecto\e_garage
git status
git add taller/views_extra/dashboard_empresa.py
git add templates/us/en/dashboard/centro_operaciones_espacial.html
git add templates/taller/us/en/dashboard/centro_operaciones_espacial.html

git commit -m "feat: actualizar gráficos del dashboard espacial con datos reales de la base de datos"

git push origin main
```

### Paso 2: Actualizar en el Servidor

```bash
# Conectarte al servidor
ssh atlantareciclajes@ssh.pythonanywhere.com

# Ir al directorio del proyecto
cd /home/atlantareciclajes/apps/egarage/current

# Activar virtual environment
source ~/.virtualenvs/venv_egarage310/bin/activate

# Hacer pull de los cambios
git pull origin main

# Verificar que los archivos se actualizaron
ls -la taller/views_extra/dashboard_empresa.py
ls -la templates/us/en/dashboard/centro_operaciones_espacial.html
ls -la templates/taller/us/en/dashboard/centro_operaciones_espacial.html

# Recargar la aplicación
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```

### Paso 3: Reload en PythonAnywhere

- Ve al Dashboard de PythonAnywhere
- Web → Click en **"Reload"**

---

## 📤 OPCIÓN 2: Copiar Archivos con SCP (Si no usas Git)

### Desde tu PC (PowerShell):

```powershell
# Cambiar al directorio del proyecto
cd E:\projecto\e_garage

# Copiar archivos al servidor
scp taller/views_extra/dashboard_empresa.py atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/views_extra/

scp templates/us/en/dashboard/centro_operaciones_espacial.html atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/templates/us/en/dashboard/

scp templates/taller/us/en/dashboard/centro_operaciones_espacial.html atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/templates/taller/us/en/dashboard/
```

### En el Servidor:

```bash
# Verificar que los archivos se copiaron
cd /home/atlantareciclajes/apps/egarage/current
ls -la taller/views_extra/dashboard_empresa.py
ls -la templates/us/en/dashboard/centro_operaciones_espacial.html
ls -la templates/taller/us/en/dashboard/centro_operaciones_espacial.html

# Recargar la aplicación
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```

---

## 🌐 OPCIÓN 3: Panel de PythonAnywhere (Files)

1. **Ir al Dashboard de PythonAnywhere**
2. **Files → Navegar a:** `/home/atlantareciclajes/apps/egarage/current/`
3. **Subir los archivos:**
   - `taller/views_extra/dashboard_empresa.py`
   - `templates/us/en/dashboard/centro_operaciones_espacial.html`
   - `templates/taller/us/en/dashboard/centro_operaciones_espacial.html`
4. **Web → Click en "Reload"**

---

## ✅ Verificación Post-Actualización

### 1. Verificar que los archivos están actualizados

```bash
# En el servidor
cd /home/atlantareciclajes/apps/egarage/current

# Verificar que el archivo tiene los cambios (debe tener "chart_data_json")
grep -n "chart_data_json" taller/views_extra/dashboard_empresa.py

# Debe mostrar líneas con "chart_data_json"
```

### 2. Verificar que el sitio funciona

- Abrir: `https://www.egarage.cl/us/es/centro-operaciones-espacial/`
- Verificar que los gráficos muestran datos reales (no ejemplos)
- Los gráficos deben mostrar:
  - **Ingresos Operacionales**: Últimos 7 meses con datos reales
  - **Servicios Principales**: Distribución porcentual real
  - **Productividad de Técnicos**: Datos reales de técnicos

### 3. Verificar logs (si hay errores)

- Dashboard de PythonAnywhere → **Web → Error log**
- Verificar que no hay errores nuevos relacionados con `chart_data_json`

---

## 🔍 Cambios Realizados

### En la Vista (`dashboard_empresa.py`):

- ✅ Cálculo de ingresos mensuales (últimos 7 meses)
- ✅ Distribución porcentual de servicios
- ✅ Datos de productividad de técnicos
- ✅ Datos pasados como JSON al template

### En los Templates:

- ✅ JavaScript actualizado para usar `chart_data_json`
- ✅ Manejo de casos sin datos
- ✅ Formato de moneda correcto
- ✅ Gráficos con datos reales en lugar de ejemplos

---

## 🆘 Si Algo Falla

### Error: "chart_data_json is not defined"

**Solución:** Verificar que el archivo `dashboard_empresa.py` tiene el código de cálculo de gráficos y que `chart_data_json` está en el context.

### Error: Los gráficos muestran datos vacíos

**Solución:** 
1. Verificar que hay datos en la base de datos (documentos, servicios, técnicos)
2. Verificar que los filtros por empresa están funcionando
3. Revisar los logs del servidor para errores

### Rollback (si es necesario)

```bash
# En el servidor, hacer rollback del último commit
cd /home/atlantareciclajes/apps/egarage/current
git log --oneline -5  # Ver últimos commits
git reset --hard HEAD~1  # Revertir último commit (CUIDADO: esto elimina cambios)
git pull origin main  # O restaurar desde backup
```

---

## 📝 Notas Importantes

- ⚠️ **Siempre hacer backup antes de actualizar** (si tienes datos importantes)
- ⚠️ **Los gráficos solo mostrarán datos si hay información en la base de datos**
- ⚠️ **Si no hay datos, los gráficos mostrarán mensajes como "No service data"**
- ✅ **Los números en los tiles ya eran reales, ahora los gráficos también lo son**

---

## 🎯 Resultado Esperado

Después de actualizar, cuando visites:
`https://www.egarage.cl/us/es/centro-operaciones-espacial/`

Deberías ver:
- ✅ Gráfico de ingresos con los últimos 7 meses reales
- ✅ Gráfico de servicios con distribución real de tus servicios
- ✅ Gráfico de técnicos con productividad real de tus técnicos
- ✅ Todos los datos reflejan información real de tu empresa

