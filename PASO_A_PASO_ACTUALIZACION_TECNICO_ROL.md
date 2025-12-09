# 📋 PASO A PASO: Actualización del Campo ROL en Modelo Tecnico

## 🎯 OBJETIVO
Actualizar el servidor con los cambios realizados al campo `rol` del modelo `Tecnico` (cambio de `TextChoices` a `ROL_CHOICES`).

---

## ⚠️ IMPORTANTE
- **[EN TU PC]** = Comandos para ejecutar en PowerShell de Windows
- **[EN EL SERVIDOR]** = Comandos para ejecutar en la terminal del servidor (SSH o consola PythonAnywhere)

---

## 📦 PASO 1: Preparar Código en tu PC (5 minutos)

### 1.1 Abrir PowerShell en tu PC

**[EN TU PC]**

1. Presiona `Windows + X`
2. Selecciona **"Windows PowerShell"** o **"Terminal"**

### 1.2 Navegar al proyecto

**[EN TU PC]**

Copia y pega este comando:

```powershell
cd E:\projecto\e_garage
```

### 1.3 Verificar cambios

**[EN TU PC]**

Copia y pega este comando:

```powershell
git status
```

**Resultado esperado:** Deberías ver archivos modificados como:
- `taller/models/tecnico.py`
- `taller/configuracion/rubros_logic.py`
- `taller/documentos/views_country_aware.py`

### 1.4 Agregar archivos al staging

**[EN TU PC]**

Copia y pega este comando:

```powershell
git add taller/models/tecnico.py taller/configuracion/rubros_logic.py taller/documentos/views_country_aware.py
```

**O si prefieres agregar todos los cambios:**

```powershell
git add .
```

### 1.5 Hacer commit

**[EN TU PC]**

Copia y pega este comando:

```powershell
git commit -m "refactor: Cambiar campo rol de Tecnico de TextChoices a ROL_CHOICES"
```

### 1.6 Verificar estado antes de push

**[EN TU PC]**

Copia y pega este comando:

```powershell
git status
```

**Resultado esperado:** Debería decir `"nothing to commit, working tree clean"`

### 1.7 Subir cambios a Git

**[EN TU PC]**

Copia y pega este comando:

```powershell
git push origin main
```

**Si tu rama se llama diferente (por ejemplo `master`), usa:**

```powershell
git push origin master
```

**Resultado esperado:** Verás mensajes como:
```
Enumerating objects: X, done.
Counting objects: 100% (X/X), done.
Writing objects: 100% (X/X), done.
```

✅ **PASO 1 COMPLETADO** - Los cambios ya están en Git

---

## 🛡️ PASO 2: Conectarse al Servidor (2 minutos)

### 2.1 Opción A: PythonAnywhere (Consola del navegador)

**[EN TU PC]**

1. Abre tu navegador
2. Ve a: https://www.pythonanywhere.com
3. Inicia sesión
4. Haz clic en la pestaña **"Consoles"**
5. Haz clic en **"Bash"** para abrir una consola

**Ya estarás [EN EL SERVIDOR]**

### 2.2 Opción B: SSH desde PowerShell

**[EN TU PC]**

Copia y pega este comando (ajusta el usuario si es diferente):

```powershell
ssh atlantareciclajes@ssh.pythonanywhere.com
```

**Resultado esperado:** Te pedirá la contraseña y luego verás un prompt como:
```
(venv_egarage310) atlantareciclajes@atlantareciclajes:~$
```

---

## 📍 PASO 3: Navegar al Proyecto en el Servidor (1 minuto)

**[EN EL SERVIDOR]**

### 3.1 Ir al directorio del proyecto

Copia y pega este comando:

```bash
cd /home/atlantareciclajes/apps/egarage/current
```

**Si esta ruta no funciona, encuentra tu proyecto:**

```bash
find ~ -name "manage.py" -type f 2>/dev/null
```

**Luego ve a la carpeta que contenga `manage.py`:**

```bash
cd /ruta/que/te/dio/el/comando/anterior
```

### 3.2 Verificar que estás en el lugar correcto

**[EN EL SERVIDOR]**

Copia y pega este comando:

```bash
ls -la | grep manage.py
```

**Resultado esperado:** Debe mostrar `manage.py`

---

## 🔧 PASO 4: Activar Entorno Virtual (1 minuto)

**[EN EL SERVIDOR]**

### 4.1 Activar el entorno virtual

Copia y pega este comando:

```bash
workon venv_egarage310
```

**Si `workon` no funciona, prueba:**

```bash
source ~/.virtualenvs/venv_egarage310/bin/activate
```

### 4.2 Verificar que está activado

**[EN EL SERVIDOR]**

Copia y pega este comando:

```bash
which python
```

**Resultado esperado:** Debe mostrar algo como:
```
/home/atlantareciclajes/.virtualenvs/venv_egarage310/bin/python
```

**También deberías ver `(venv_egarage310)` en tu prompt**

---

## 🔄 PASO 5: Actualizar Código desde Git (3 minutos)

**[EN EL SERVIDOR]**

### 5.1 Verificar estado de Git

Copia y pega este comando:

```bash
git status
```

### 5.2 Ver qué rama estás usando

**[EN EL SERVIDOR]**

Copia y pega este comando:

```bash
git branch
```

**Resultado esperado:** Deberías ver `* main` o `* master` (la `*` indica la rama actual)

### 5.3 Obtener última versión desde Git

**[EN EL SERVIDOR]**

Copia y pega este comando:

```bash
git fetch origin
```

### 5.4 Actualizar código

**[EN EL SERVIDOR]**

**Si estás en la rama `main`:**

```bash
git pull origin main
```

**Si estás en la rama `master`:**

```bash
git pull origin master
```

**Resultado esperado:** Verás mensajes como:
```
Updating abc1234..def5678
Fast-forward
 taller/models/tecnico.py              | 25 +++++----
 taller/configuracion/rubros_logic.py | 12 +++--
 ...
```

### 5.5 Verificar que los archivos se actualizaron

**[EN EL SERVIDOR]**

Copia y pega este comando:

```bash
grep -n "ROL_CHOICES" taller/models/tecnico.py
```

**Resultado esperado:** Debe mostrar las líneas con `ROL_CHOICES`

---

## 🔍 PASO 6: Verificar Cambios (2 minutos)

**[EN EL SERVIDOR]**

### 6.1 Verificar que el modelo se actualizó correctamente

Copia y pega este comando:

```bash
python manage.py check
```

**Resultado esperado:** Debe mostrar:
```
System check identified no issues (0 silenced).
```

**Si hay errores, anótalos antes de continuar**

### 6.2 Verificar sintaxis de Python

**[EN EL SERVIDOR]**

Copia y pega este comando:

```bash
python -m py_compile taller/models/tecnico.py taller/configuracion/rubros_logic.py taller/documentos/views_country_aware.py
```

**Resultado esperado:** No debe mostrar ningún error (comando exitoso sin salida)

---

## ✅ PASO 7: Verificación Final y Reinicio (2 minutos)

**[EN EL SERVIDOR]**

### 7.1 Verificar que todo está correcto

Copia y pega este comando para verificar que los cambios se aplicaron:

```bash
python manage.py shell -c "from taller.models import Tecnico; print('ROL_CHOICES:', Tecnico.ROL_CHOICES)"
```

**Resultado esperado:** Debe mostrar:
```
ROL_CHOICES: [('TECNICO', 'Técnico'), ('VENDEDOR', 'Vendedor'), ('MIXTO', 'Técnico/Vendedor')]
```

### 7.2 Reiniciar la aplicación

**[EN TU PC] - Si usas PythonAnywhere:**

1. Ve a tu dashboard de PythonAnywhere en el navegador
2. Haz clic en la pestaña **"Web"**
3. Busca tu aplicación web
4. Haz clic en el botón **"Reload"** o **"Reload webapp"**
5. Espera 10-30 segundos

**O desde la consola del servidor:**

```bash
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```

**(Ajusta el nombre del archivo WSGI según tu configuración)**

---

## 🧪 PASO 8: Verificar en el Navegador (3 minutos)

**[EN TU PC]**

### 8.1 Abrir el sitio web

1. Abre tu navegador
2. Ve a tu sitio web (ejemplo: `https://egarage.pythonanywhere.com` o tu dominio)
3. Verifica que carga correctamente

### 8.2 Verificar funcionalidad

1. **Inicia sesión** con una cuenta de prueba
2. Ve a la sección donde se usen técnicos (documentos, configuraciones, etc.)
3. Verifica que los campos de rol funcionan correctamente
4. Verifica que no hay errores en la página

---

## 📋 RESUMEN DE COMANDOS (Copia Rápida)

### [EN TU PC] - PowerShell

```powershell
cd E:\projecto\e_garage
git status
git add taller/models/tecnico.py taller/configuracion/rubros_logic.py taller/documentos/views_country_aware.py
git commit -m "refactor: Cambiar campo rol de Tecnico de TextChoices a ROL_CHOICES"
git push origin main
```

### [EN EL SERVIDOR] - Bash

```bash
cd /home/atlantareciclajes/apps/egarage/current
workon venv_egarage310
git status
git pull origin main
python manage.py check
python manage.py shell -c "from taller.models import Tecnico; print('ROL_CHOICES:', Tecnico.ROL_CHOICES)"
```

---

## 🆘 SI ALGO SALE MAL

### Problema: "No se encuentra el archivo"

**Solución:**
```bash
# [EN EL SERVIDOR] Encontrar la ubicación del proyecto
find ~ -name "manage.py" -type f 2>/dev/null
```

### Problema: "Git dice que hay conflictos"

**Solución:**
```bash
# [EN EL SERVIDOR] Ver los conflictos
git status

# Si quieres descartar cambios locales y usar solo los de Git:
git stash
git pull origin main

# O si quieres guardar cambios locales primero:
git stash save "Cambios locales antes de pull"
git pull origin main
```

### Problema: "No puedo conectarme al servidor"

**Solución:**
- Usa la consola de PythonAnywhere desde el navegador
- O verifica tus credenciales SSH

### Problema: "Error al importar el modelo"

**Solución:**
```bash
# [EN EL SERVIDOR] Verificar sintaxis
python -m py_compile taller/models/tecnico.py

# Ver errores detallados
python manage.py check --verbosity=2
```

---

## ✅ CHECKLIST FINAL

- [ ] **[EN TU PC]** Código commiteado y pusheado a Git
- [ ] **[EN EL SERVIDOR]** Código actualizado desde Git
- [ ] **[EN EL SERVIDOR]** `python manage.py check` sin errores
- [ ] **[EN EL SERVIDOR]** ROL_CHOICES verificado correctamente
- [ ] **[EN TU PC]** Aplicación reiniciada
- [ ] **[EN TU PC]** Sitio web funciona correctamente
- [ ] **[EN TU PC]** No hay errores en el navegador

---

**¡Actualización completada!** 🎉

**Tiempo estimado total:** 15-20 minutos





