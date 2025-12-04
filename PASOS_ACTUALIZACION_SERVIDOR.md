# 🚀 ACTUALIZACIÓN SERVIDOR - Fixes de Templates

---

## ⚡ INICIO RÁPIDO (Para el error de clientes)

**Si ves el error `TemplateDoesNotExist` en `/cl/es/clientes/`:**

1. **Descargar:** `egarage_update_clientes_template.zip` (28 archivos, ~50 KB) ✓ Ya generado
2. **Subir al servidor:** Carpeta `cl/` a `/home/atlantareciclajes/apps/egarage/current/templates/`
3. **Reload:** Web app en PythonAnywhere o `touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py`
4. **Verificar:** https://www.egarage.cl/cl/es/clientes/

📖 **Instrucciones detalladas:** Ver archivo `INSTRUCCIONES.txt` dentro del ZIP

---

## 🆕 PROBLEMA ACTUAL: Template Clientes Lista (NUEVO - 3 Dic 2025)

### 📋 Resumen del Problema
**Error:** `TemplateDoesNotExist: common/clientes/cliente_list.html, clientes/cliente_list.html`  
**URL afectada:** https://www.egarage.cl/cl/es/clientes/  
**Causa:** La estructura de templates por país/idioma (`cl/es/clientes/`) no está en el servidor de producción

### ✅ Solución
Copiar la carpeta completa `templates/cl/` al servidor de producción.

**Archivos necesarios:**
- `templates/cl/es/clientes/cliente_list.html` ✓ Ya existe en `deploy_atlantareciclajes/`
- Y toda la estructura de templates de Chile

---

## 📋 PROBLEMA ANTERIOR: Template Otros Servicios

**Error:** `TemplateDoesNotExist: common/servicios/otros_servicios_menu.html`  
**URL afectada:** https://www.egarage.cl/cl/es/servicios/otros-servicios/  
**Causa:** Template faltante en la ubicación que Django esperaba encontrarlo

## ✅ Solución Implementada
Se creó el template `templates/common/servicios/otros_servicios_menu.html` en la ubicación correcta.

---

## 🔧 FIX RÁPIDO PARA ERROR DE CLIENTES (NUEVO)

### Opción A: Copiar solo el archivo necesario (RÁPIDO)

```bash
# 1. Conectarse al servidor
ssh atlantareciclajes@ssh.pythonanywhere.com

# 2. Ir al directorio de templates
cd /home/atlantareciclajes/apps/egarage/current/templates

# 3. Crear la estructura de directorios para Chile
mkdir -p cl/es/clientes

# 4. Desde tu computadora local, subir el archivo
# Usa FileZilla o SCP para copiar:
# LOCAL:  deploy_atlantareciclajes/templates/cl/es/clientes/cliente_list.html
# REMOTO: /home/atlantareciclajes/apps/egarage/current/templates/cl/es/clientes/cliente_list.html

# 5. Verificar permisos
chmod 644 /home/atlantareciclajes/apps/egarage/current/templates/cl/es/clientes/cliente_list.html

# 6. Reload de la aplicación
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```

### Opción B: Copiar toda la carpeta cl/ (RECOMENDADO)

Esto asegura que todos los templates de Chile estén disponibles:

```bash
# 1. Desde tu computadora, comprimir la carpeta cl/
cd deploy_atlantareciclajes/templates
zip -r cl_templates.zip cl/

# 2. Subir cl_templates.zip al servidor usando FileZilla:
#    LOCAL:  deploy_atlantareciclajes/templates/cl_templates.zip
#    REMOTO: /home/atlantareciclajes/apps/egarage/current/templates/

# 3. En el servidor, descomprimir
cd /home/atlantareciclajes/apps/egarage/current/templates
unzip cl_templates.zip

# 4. Verificar que se creó la estructura
ls -la cl/es/clientes/cliente_list.html

# 5. Ajustar permisos
chmod -R 644 cl/
find cl/ -type d -exec chmod 755 {} \;

# 6. Limpiar
rm cl_templates.zip

# 7. Reload
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```

### ✅ Verificar que funciona

1. Esperar 15-20 segundos después del reload
2. Ir a: https://www.egarage.cl/cl/es/clientes/
3. La página debe cargar sin errores mostrando la lista de clientes

---

## 📦 PASO 1: Preparar la Actualización (Template Otros Servicios)

Ya está listo el archivo:
```
✓ egarage_update_otros_servicios.zip (5.6 KB)
```

Contenido:
- `templates/common/servicios/otros_servicios_menu.html`
- `INSTRUCCIONES.txt`

---

## 🔐 PASO 2: Conectar al Servidor

**Opción A: Usar FileZilla (Recomendado)**
1. Abrir FileZilla
2. Configurar conexión SFTP:
   - **Host:** `atlantareciclajes.pythonanywhere.com`
   - **Puerto:** `22`
   - **Usuario:** `atlantareciclajes`
   - **Contraseña:** [tu contraseña]
3. Conectar

**Opción B: Usar SSH desde terminal**
```bash
ssh atlantareciclajes@atlantareciclajes.pythonanywhere.com
```

---

## 📤 PASO 3: Subir el Archivo

### Con FileZilla:
1. Navega a: `/home/atlantareciclajes/`
2. Crea carpeta si no existe: `egarage_update_otros_servicios/`
3. Arrastra el archivo `egarage_update_otros_servicios.zip`
4. Espera a que termine la subida

### Con SCP (alternativa):
```bash
scp egarage_update_otros_servicios.zip atlantareciclajes@atlantareciclajes.pythonanywhere.com:/home/atlantareciclajes/
```

---

## ⚠️ PASO 4: BACKUP (OBLIGATORIO)

Conectado al servidor por SSH:
```bash
cd /home/atlantareciclajes/scripts_deploy/
./1_backup_FIXED.sh
```

**IMPORTANTE:** Anota el nombre del backup que genera. Lo necesitarás si algo sale mal.

Ejemplo de salida:
```
Backup creado: backup_20251203_223000.tar.gz
```

---

## 📂 PASO 5: Descomprimir e Instalar

```bash
# Navegar al home
cd /home/atlantareciclajes/

# Descomprimir
unzip -o egarage_update_otros_servicios.zip

# Ir a la carpeta descomprimida
cd egarage_update_otros_servicios/

# Crear directorio si no existe
mkdir -p /home/atlantareciclajes/apps/egarage/current/templates/common/servicios

# Copiar el template
cp templates/common/servicios/otros_servicios_menu.html \
   /home/atlantareciclajes/apps/egarage/current/templates/common/servicios/

# Verificar permisos
chmod 644 /home/atlantareciclajes/apps/egarage/current/templates/common/servicios/otros_servicios_menu.html

# Verificar que se copió
ls -la /home/atlantareciclajes/apps/egarage/current/templates/common/servicios/
```

Debes ver:
```
-rw-r--r-- 1 atlantareciclajes atlantareciclajes 8931 Dec  3 22:30 otros_servicios_menu.html
```

---

## 🔄 PASO 6: Reload de la Aplicación

### Opción A: Desde la Interfaz Web (Más Fácil)
1. Ve a: https://www.pythonanywhere.com/user/atlantareciclajes/
2. Click en pestaña **"Web"**
3. Click en el botón verde **"Reload atlantareciclajes.pythonanywhere.com"**
4. Espera 15-20 segundos

### Opción B: Desde la Consola Bash
```bash
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```

---

## ✅ PASO 7: Verificar que Funciona

1. Abre tu navegador
2. Ve a: https://www.egarage.cl/cl/es/servicios/otros-servicios/
3. La página debe cargar sin errores
4. Debes ver:
   - ✓ Interfaz con tema espacial/futurista
   - ✓ Campo de búsqueda de servicios
   - ✓ Estadísticas de servicios
   - ✓ Botón verde "➕ Agregar Servicio"

---

## 🆘 Si Algo Sale Mal

### Ver Logs de Error
```bash
tail -50 /var/log/atlantareciclajes.pythonanywhere.com.error.log
```

### Hacer Rollback
```bash
cd /home/atlantareciclajes/scripts_deploy/
./4_rollback.sh
# Ingresa la fecha del backup que anotaste en el PASO 4
```

### Verificar que el Archivo Existe
```bash
ls -la /home/atlantareciclajes/apps/egarage/current/templates/common/servicios/otros_servicios_menu.html
```

Si el archivo NO existe, repite el PASO 5.

---

## 📝 Comandos Rápidos (Copiar y Pegar)

Para ejecutar todo de una vez (después de subir el zip):

```bash
# BACKUP PRIMERO
cd /home/atlantareciclajes/scripts_deploy/
./1_backup_FIXED.sh
# ANOTA EL NOMBRE DEL BACKUP

# DESCOMPRIMIR E INSTALAR
cd /home/atlantareciclajes/
unzip -o egarage_update_otros_servicios.zip
cd egarage_update_otros_servicios/
mkdir -p /home/atlantareciclajes/apps/egarage/current/templates/common/servicios
cp templates/common/servicios/otros_servicios_menu.html /home/atlantareciclajes/apps/egarage/current/templates/common/servicios/
chmod 644 /home/atlantareciclajes/apps/egarage/current/templates/common/servicios/otros_servicios_menu.html

# VERIFICAR
ls -la /home/atlantareciclajes/apps/egarage/current/templates/common/servicios/

# Luego haz RELOAD desde la interfaz web de PythonAnywhere
```

---

## 🎯 Checklist Final

- [ ] Archivo zip subido al servidor
- [ ] Backup realizado y nombre anotado
- [ ] Template copiado a la ubicación correcta
- [ ] Permisos verificados (644)
- [ ] Aplicación recargada (reload)
- [ ] URL probada y funciona correctamente
- [ ] No hay errores en los logs

---

## 📞 Soporte

Si después de seguir estos pasos sigue sin funcionar:
1. Verifica los logs de error
2. Confirma que la ruta del archivo es exacta
3. Verifica que el reload se completó
4. Revisa que no haya errores de sintaxis en el template

**¡Todo listo! El fix está preparado para subir al servidor.** 🚀

