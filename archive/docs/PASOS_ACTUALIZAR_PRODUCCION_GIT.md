# Pasos Detallados: Actualizar Archivos en Producción con Git

## 📋 Pre-requisitos

1. Tienes un repositorio Git configurado (GitHub, GitLab, Bitbucket, etc.)
2. Los cambios ya están en tu repositorio remoto
3. Tienes acceso SSH o Bash a PythonAnywhere

---

## 🚀 Paso a Paso

### Paso 1: Verificar que los Cambios Están en Git

**En tu máquina local (Cursor/IDE):**

```bash
# Verificar el estado
git status

# Si hay cambios sin commit, hacer commit
git add whatsapp/admin.py whatsapp/apps.py gestion_taller/urls.py
git commit -m "Fix: Hacer admin más robusto para evitar error 500 con WhatsApp"

# Subir al repositorio remoto
git push origin main
# O si usas otra rama: git push origin master
```

**Verifica que el push fue exitoso:**
- Ve a tu repositorio en GitHub/GitLab
- Confirma que los 3 archivos tienen los cambios recientes

---

### Paso 2: Conectar a PythonAnywhere

**Opción A: Usando la Consola Bash de PythonAnywhere**

1. Ve a **https://www.pythonanywhere.com**
2. Inicia sesión
3. Haz clic en **"Consoles"** en el menú superior
4. Haz clic en **"Bash"** (o abre una consola Bash existente)

**Opción B: Usando SSH (si está habilitado)**

```bash
ssh tuusuario@ssh.pythonanywhere.com
```

---

### Paso 3: Navegar al Directorio del Proyecto

En la consola de PythonAnywhere, ejecuta:

```bash
# Ver dónde estás
pwd

# Navegar a tu proyecto (ajusta la ruta según tu configuración)
cd /home/tuusuario/mi_proyecto
# O podría ser:
# cd /home/tuusuario/e_garage
# cd /home/tuusuario/egarage

# Verificar que estás en el lugar correcto
ls -la
# Deberías ver: manage.py, gestion_taller/, whatsapp/, etc.
```

**💡 Tip:** Si no sabes la ruta exacta, busca tu archivo `manage.py`:
```bash
find ~ -name "manage.py" -type f 2>/dev/null
```

---

### Paso 4: Verificar el Estado de Git

```bash
# Verificar que estás en un repositorio Git
git status

# Si dice "not a git repository", necesitas inicializar Git o clonar el repo
# Si ya es un repo, continúa al siguiente paso
```

**Si NO es un repositorio Git:**

Tienes dos opciones:

**A) Si el proyecto ya está en Git pero no está inicializado aquí:**
```bash
# Agregar el remote
git remote add origin https://github.com/tuusuario/tu-repo.git
# O si ya existe:
git remote -v  # Verificar que está configurado
```

**B) Si prefieres no usar Git aquí:**
- Ve a la **Opción B** (Subir archivos manualmente) o **Opción C** (Copiar y pegar)

---

### Paso 5: Obtener los Cambios del Repositorio

```bash
# Ver qué rama estás usando
git branch

# Si estás en la rama correcta (main o master), hacer pull
git pull origin main
# O si usas master:
# git pull origin master

# Si hay conflictos, Git te lo dirá
# Si todo está bien, verás algo como:
# "Updating abc1234..def5678"
# "Fast-forward"
# " whatsapp/admin.py | 45 +++++++++++++++++++++++"
# " whatsapp/apps.py  | 12 +++++++"
# " gestion_taller/urls.py | 3 ++-"
```

**Si hay cambios locales que no quieres perder:**
```bash
# Guardar cambios locales temporalmente
git stash

# Hacer pull
git pull origin main

# Recuperar cambios locales (si los necesitas)
git stash pop
```

---

### Paso 6: Verificar que los Archivos se Actualizaron

```bash
# Ver la fecha de modificación de los archivos
ls -lh whatsapp/admin.py whatsapp/apps.py gestion_taller/urls.py

# O ver el último commit que afectó estos archivos
git log -1 --stat -- whatsapp/admin.py whatsapp/apps.py gestion_taller/urls.py
```

**Deberías ver que los archivos tienen una fecha reciente.**

---

### Paso 7: Reiniciar el Servidor Web

**IMPORTANTE:** Después de actualizar los archivos, DEBES reiniciar el servidor.

1. Ve a la pestaña **"Web"** en PythonAnywhere
2. Busca tu aplicación web (probablemente `www.egarage.cl`)
3. Haz clic en el botón **"Reload"** o **"Reload web app"**
4. Espera 10-30 segundos mientras se reinicia

**O desde la consola Bash:**
```bash
# Esto también puede funcionar (depende de tu configuración)
touch /var/www/tuusuario_pythonanywhere_com_wsgi.py
# O el archivo WSGI que uses
```

---

### Paso 8: Verificar que Funcionó

1. Abre tu navegador
2. Ve a: `https://www.egarage.cl/admin/`
3. Deberías ver el admin sin error 500
4. Si todo está bien, verás la página de login o el dashboard del admin

---

## 🔍 Solución de Problemas

### Error: "not a git repository"

**Solución:** El proyecto no está inicializado como repositorio Git en PythonAnywhere.

**Opción 1:** Clonar el repositorio completo:
```bash
cd ~
git clone https://github.com/tuusuario/tu-repo.git mi_proyecto
cd mi_proyecto
```

**Opción 2:** Inicializar Git en el proyecto existente:
```bash
cd /home/tuusuario/mi_proyecto
git init
git remote add origin https://github.com/tuusuario/tu-repo.git
git fetch origin
git checkout -b main origin/main  # o master
```

### Error: "Permission denied" al hacer pull

**Solución:** Puede ser un problema de permisos o autenticación.

```bash
# Verificar permisos
ls -la .git

# Si usas HTTPS y pide credenciales, considera usar SSH
git remote set-url origin git@github.com:tuusuario/tu-repo.git
```

### Error: "Your local changes would be overwritten"

**Solución:** Tienes cambios locales que no están en Git.

```bash
# Ver qué archivos tienen cambios
git status

# Opción 1: Guardar cambios locales
git stash
git pull origin main
git stash pop  # Si quieres recuperarlos

# Opción 2: Descartar cambios locales (CUIDADO: perderás cambios)
git checkout -- whatsapp/admin.py whatsapp/apps.py gestion_taller/urls.py
git pull origin main
```

### El admin sigue dando error 500

**Solución:** Verifica los logs de error:

1. Ve a **Web tab** → **Error log**
2. O desde Bash:
   ```bash
   tail -n 50 ~/logs/error.log
   ```
3. Busca el traceback completo y compártelo para diagnóstico

---

## ✅ Checklist Final

- [ ] Cambios están en el repositorio remoto (GitHub/GitLab)
- [ ] Conectado a PythonAnywhere (Bash o SSH)
- [ ] Navegado al directorio correcto del proyecto
- [ ] Ejecutado `git pull origin main` (o master)
- [ ] Verificado que los 3 archivos se actualizaron
- [ ] Reiniciado el servidor web (Web tab → Reload)
- [ ] Probado `https://www.egarage.cl/admin/` - funciona sin error 500

---

## 📞 Si Necesitas Ayuda

Si encuentras algún problema en estos pasos:

1. Comparte el mensaje de error completo
2. Indica en qué paso te quedaste
3. Muestra el output de `git status` y `git log -1`
