# 📤 PASO 2: SUBIR ARCHIVO AL SERVIDOR - GUÍA DETALLADA

## 🎯 Objetivo
Subir el archivo `egarage_update_atlantareciclajes.zip` al servidor PythonAnywhere.

---

## 📋 PREPARACIÓN

### Verificar que tienes el archivo ZIP

En tu PC, verifica que existe:
```
E:\projecto\e_garage\egarage_update_atlantareciclajes.zip
```

**Tamaño esperado:** Depende de tu proyecto (puede ser 10-50 MB o más)

---

## 🔧 MÉTODO 1: FileZilla con API Token (Recomendado)

### Paso 1: Obtener API Token

1. **Abrir navegador** y ir a:
   ```
   https://www.pythonanywhere.com/user/atlantareciclajes/
   ```

2. **Iniciar sesión** si es necesario

3. **Ir a pestaña "Account"** (o "Cuenta" / "Configuración")

4. **Buscar sección "API Token"** o "API"
   - Si no la ves, buscar en "Security" o "Seguridad"

5. **Clic en "Create API token"** o "Generar token"

6. **⚠️ IMPORTANTE:** Copiar el token inmediatamente (solo se muestra una vez)
   - Ejemplo: `abc123def456ghi789...`

### Paso 2: Configurar FileZilla

1. **Abrir FileZilla**

2. **Clic en "Archivo" → "Gestor de sitios"** (o presionar `Ctrl+S`)

3. **Clic en "Nuevo sitio"**

4. **Configurar:**
   ```
   Nombre: PythonAnywhere
   Protocolo: SFTP - SSH File Transfer Protocol
   Host: ssh.pythonanywhere.com
   Puerto: 22
   Tipo de acceso: Normal
   Usuario: atlantareciclajes
   Contraseña: [PEGAR AQUÍ EL API TOKEN]
   ```

5. **Clic en "Conectar"**

### Paso 3: Verificar Conexión

Si conecta correctamente:
- ✅ Panel izquierdo: Tu PC
- ✅ Panel derecho: Servidor (`/home/atlantareciclajes`)

Si falla:
- ❌ Ver archivo: `SOLUCION_CONEXION_PYTHONANYWHERE.md`

### Paso 4: Crear Carpeta en Servidor

En el panel derecho (servidor):

1. **Navegar a:** `/home/atlantareciclajes/`
   - Si no estás ahí, escribir en la barra de ruta del servidor

2. **Verificar si existe carpeta `egarage_update`:**
   - Si existe: ✅ Listo
   - Si NO existe:
     - Clic derecho en espacio vacío
     - Seleccionar "Crear directorio"
     - Nombre: `egarage_update`
     - Enter

3. **Entrar a la carpeta** `egarage_update` (doble clic)

### Paso 5: Subir el Archivo ZIP

1. **En panel izquierdo (tu PC):**
   - Navegar a: `E:\projecto\e_garage\`
   - Buscar archivo: `egarage_update_atlantareciclajes.zip`

2. **Arrastrar y soltar:**
   - Arrastrar el archivo desde panel izquierdo
   - Soltar en panel derecho (carpeta `egarage_update`)

3. **Esperar transferencia:**
   - Ver progreso en la parte inferior de FileZilla
   - ⏱️ Tiempo estimado: 5-15 minutos (depende del tamaño y velocidad)

4. **Verificar:**
   - El archivo debe aparecer en el panel derecho
   - Verificar tamaño y fecha

---

## 🌐 MÉTODO 2: Web Panel (Alternativa)

Si FileZilla no funciona, usa el navegador:

### Paso 1: Acceder al Web Panel

1. **Ir a:**
   ```
   https://www.pythonanywhere.com/user/atlantareciclajes/
   ```

2. **Clic en pestaña "Files"** (o "Archivos")

### Paso 2: Navegar a la Carpeta

1. **En el explorador de archivos:**
   - Navegar a: `/home/atlantareciclajes/`

2. **Crear carpeta `egarage_update`** (si no existe):
   - Clic en botón **"New directory"** o **"Nuevo directorio"**
   - Nombre: `egarage_update`
   - Clic en **"Create"** o **"Crear"**

3. **Entrar a la carpeta** `egarage_update`

### Paso 3: Subir el Archivo

1. **Clic en botón "Upload a file"** o **"Subir archivo"**

2. **Seleccionar archivo:**
   - Buscar: `E:\projecto\e_garage\egarage_update_atlantareciclajes.zip`
   - Clic en "Abrir"

3. **Esperar subida:**
   - Ver progreso en pantalla
   - ⚠️ **Límite:** 100MB por archivo
   - Si tu ZIP es más grande, necesitas usar FileZilla

4. **Verificar:**
   - El archivo debe aparecer en la lista

---

## ✅ VERIFICACIÓN FINAL

### Verificar en FileZilla:
- Archivo visible en panel derecho
- Tamaño correcto
- Fecha reciente

### Verificar en Web Panel:
1. Ir a: `/home/atlantareciclajes/egarage_update/`
2. Ver archivo: `egarage_update_atlantareciclajes.zip`
3. Verificar tamaño

### Verificar en Consola (Opcional):

1. **Abrir consola Bash** en PythonAnywhere:
   - Ir a: https://www.pythonanywhere.com/user/atlantareciclajes/
   - Pestaña: "Consoles"
   - Clic en "Bash" o crear nueva

2. **Ejecutar:**
   ```bash
   ls -lh /home/atlantareciclajes/egarage_update/
   ```

3. **Deberías ver:**
   ```
   -rw-r--r-- 1 atlantareciclajes atlantareciclajes 15M Nov 23 17:00 egarage_update_atlantareciclajes.zip
   ```
   (El tamaño puede variar)

---

## 🆘 PROBLEMAS COMUNES

### Error: "Access denied"
- ✅ Ver: `SOLUCION_CONEXION_PYTHONANYWHERE.md`
- ✅ Usar API Token en lugar de contraseña

### Error: "Archivo muy grande" (Web Panel)
- ✅ Límite: 100MB
- ✅ Solución: Usar FileZilla con API Token

### Error: "Conexión interrumpida"
- ✅ Verificar conexión a internet
- ✅ Intentar de nuevo
- ✅ FileZilla reanuda automáticamente

### Archivo no aparece en servidor
- ✅ Verificar que subiste a la carpeta correcta
- ✅ Verificar en Web Panel
- ✅ Verificar en consola con `ls -lh`

---

## 📋 CHECKLIST

- [ ] API Token obtenido de PythonAnywhere
- [ ] FileZilla configurado y conectado
- [ ] Carpeta `egarage_update` creada en servidor
- [ ] Archivo ZIP subido correctamente
- [ ] Archivo verificado (tamaño y fecha)
- [ ] Listo para siguiente paso (Paso 3: Actualizar)

---

## ⏭️ SIGUIENTE PASO

Una vez que el archivo esté subido:

**Paso 3: Ejecutar actualización en servidor**

Ver: `COMANDOS_ACTUALIZACION_SERVIDOR.md` - Sección "Paso 4: ACTUALIZAR"

---

**¿Necesitas ayuda?** Revisa `SOLUCION_CONEXION_PYTHONANYWHERE.md` 🚀







