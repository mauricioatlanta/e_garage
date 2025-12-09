# 🔧 SOLUCIÓN: Subir Cambios al Servidor (Sin Git)

## ⚠️ PROBLEMA IDENTIFICADO

El servidor no tiene los cambios porque:
1. No es un repositorio Git en esa ubicación
2. Los cambios no se han subido todavía

## 📋 SOLUCIÓN: Subir Archivos Manualmente

### OPCIÓN 1: Usando SCP desde tu PC (Recomendado)

**[EN TU PC] - PowerShell**

Copia y pega estos comandos **uno por uno**:

```powershell
# 1. Subir el modelo Tecnico
scp E:\projecto\e_garage\taller\models\tecnico.py atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/models/tecnico.py
```

```powershell
# 2. Subir rubros_logic.py
scp E:\projecto\e_garage\taller\configuracion\rubros_logic.py atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/configuracion/rubros_logic.py
```

```powershell
# 3. Subir views_country_aware.py
scp E:\projecto\e_garage\taller\documentos\views_country_aware.py atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/documentos/views_country_aware.py
```

### OPCIÓN 2: Usando la Interfaz Web de PythonAnywhere

**[EN TU PC] - Navegador**

1. Ve a: https://www.pythonanywhere.com
2. Inicia sesión
3. Ve a la pestaña **"Files"**
4. Navega a: `/home/atlantareciclajes/apps/egarage/current/taller/models/`
5. Haz clic en **"tecnico.py"** para editarlo
6. Abre el archivo local `E:\projecto\e_garage\taller\models\tecnico.py` en tu PC
7. Copia TODO el contenido del archivo local
8. Pega en el editor web de PythonAnywhere
9. Haz clic en **"Save"**
10. Repite para:
    - `/home/atlantareciclajes/apps/egarage/current/taller/configuracion/rubros_logic.py`
    - `/home/atlantareciclajes/apps/egarage/current/taller/documentos/views_country_aware.py`

### OPCIÓN 3: Encontrar la Ubicación Correcta del Proyecto

**[EN EL SERVIDOR] - Consola Bash**

Si la ruta `/home/atlantareciclajes/apps/egarage/current` no existe, busca dónde está realmente:

```bash
# Buscar el archivo manage.py
find ~ -name "manage.py" -type f 2>/dev/null

# O buscar el archivo tecnico.py actual
find ~ -name "tecnico.py" -path "*/models/tecnico.py" -type f 2>/dev/null
```

Una vez que encuentres la ruta correcta, ajusta los comandos SCP o usa la interfaz web.

---

## ✅ PASOS DESPUÉS DE SUBIR LOS ARCHIVOS

**[EN EL SERVIDOR] - Consola Bash**

Una vez que hayas subido los 3 archivos, ejecuta estos comandos:

```bash
# 1. Verificar que los archivos se subieron correctamente
grep -n "ROL_CHOICES" /home/atlantareciclajes/apps/egarage/current/taller/models/tecnico.py

# Debe mostrar las líneas con ROL_CHOICES (debería mostrar algo)

# 2. Verificar sintaxis de Python
python -m py_compile /home/atlantareciclajes/apps/egarage/current/taller/models/tecnico.py

# No debe mostrar errores (si no muestra nada, está bien)

# 3. Verificar que Django puede cargar el modelo
python manage.py check

# Debe decir: "System check identified no issues (0 silenced)."

# 4. Verificar que ROL_CHOICES existe
python manage.py shell -c "from taller.models import Tecnico; print('ROL_CHOICES:', Tecnico.ROL_CHOICES)"

# Debe mostrar: ROL_CHOICES: [('TECNICO', 'Técnico'), ('VENDEDOR', 'Vendedor'), ('MIXTO', 'Técnico/Vendedor')]
```

---

## 🔄 REINICIAR LA APLICACIÓN

**[EN TU PC] - Navegador**

1. Ve a: https://www.pythonanywhere.com
2. Inicia sesión
3. Ve a la pestaña **"Web"**
4. Busca tu aplicación web
5. Haz clic en el botón **"Reload"** o **"Reload webapp"**
6. Espera 10-30 segundos

---

## 📝 RESUMEN DE ARCHIVOS A SUBIR

Sube estos 3 archivos al servidor:

1. ✅ `taller/models/tecnico.py`
2. ✅ `taller/configuracion/rubros_logic.py`
3. ✅ `taller/documentos/views_country_aware.py`

---

## 🆘 SI SIGUE HABIENDO ERRORES

### Error: "not a git repository"

**Solución:** No uses `git pull`. Sube los archivos manualmente usando SCP o la interfaz web.

### Error: "ROL_CHOICES no existe"

**Solución:** Verifica que el archivo se subió correctamente:

```bash
# En el servidor
cat /home/atlantareciclajes/apps/egarage/current/taller/models/tecnico.py | grep -A 5 "ROL_CHOICES"
```

Debe mostrar:
```python
ROL_CHOICES = [
    ('TECNICO', 'Técnico'),
    ('VENDEDOR', 'Vendedor'),
    ('MIXTO', 'Técnico/Vendedor'),
]
```

### Error: "choices must be an iterable"

**Solución:** Asegúrate de que ROL_CHOICES está definido como una lista de tuplas, no como una clase.

---

## ⚡ COMANDOS RÁPIDOS (SCP)

**[EN TU PC] - PowerShell (ejecuta uno por uno)**

```powershell
scp E:\projecto\e_garage\taller\models\tecnico.py atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/models/
```

```powershell
scp E:\projecto\e_garage\taller\configuracion\rubros_logic.py atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/configuracion/
```

```powershell
scp E:\projecto\e_garage\taller\documentos\views_country_aware.py atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/documentos/
```

**Nota:** Ajusta la ruta del servidor si tu proyecto está en otro lugar.





