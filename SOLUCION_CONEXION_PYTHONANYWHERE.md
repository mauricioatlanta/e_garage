# 🔧 SOLUCIÓN: Error de Autenticación en PythonAnywhere

## ❌ Problema
```
Estado: Access denied 
Error: La autenticación falló.
Error: Error crítico: No se pudo conectar al servidor
```

---

## ✅ SOLUCIÓN 1: Usar API Token (Recomendado)

PythonAnywhere requiere un **API Token** en lugar de la contraseña para SFTP.

### Paso 1: Obtener API Token

1. Ir a: https://www.pythonanywhere.com/user/atlantareciclajes/
2. Clic en pestaña **"Account"** (o "Cuenta")
3. Buscar sección **"API Token"**
4. Si no existe, buscar **"API"** o **"Security"**
5. Clic en **"Create API token"** o **"Generar token"**
6. **Copiar el token** (se muestra solo una vez)

### Paso 2: Configurar FileZilla con API Token

**Configuración en FileZilla:**

```
Tipo: SFTP
Host: ssh.pythonanywhere.com
Puerto: 22
Usuario: atlantareciclajes
Contraseña: [PEGAR EL API TOKEN AQUÍ]
```

**O si FileZilla tiene campo "API Token":**
- Usuario: `atlantareciclajes`
- API Token: `[tu token]`

---

## ✅ SOLUCIÓN 2: Subir por Web Panel (Alternativa)

Si SFTP no funciona, puedes subir archivos directamente desde el navegador.

### Paso 1: Acceder al Web Panel

1. Ir a: https://www.pythonanywhere.com/user/atlantareciclajes/
2. Clic en pestaña **"Files"** (o "Archivos")

### Paso 2: Navegar a la carpeta

1. En el explorador de archivos, navegar a:
   ```
   /home/atlantareciclajes/
   ```

2. Si no existe la carpeta `egarage_update`, crearla:
   - Clic en botón **"New directory"** o **"Nuevo directorio"**
   - Nombre: `egarage_update`
   - Clic en **"Create"**

### Paso 3: Subir el archivo ZIP

1. Entrar a la carpeta `egarage_update`
2. Clic en botón **"Upload a file"** o **"Subir archivo"**
3. Seleccionar: `egarage_update_atlantareciclajes.zip`
4. Esperar a que termine la subida
5. Verificar que el archivo aparezca en la lista

**⚠️ NOTA:** El límite de tamaño por archivo en el Web Panel es de 100MB. Si tu ZIP es más grande, necesitarás usar SFTP con API Token.

---

## ✅ SOLUCIÓN 3: Verificar Credenciales

### Verificar Usuario

1. Ir a: https://www.pythonanywhere.com/user/atlantareciclajes/
2. Verificar que el usuario sea correcto: `atlantareciclajes`

### Verificar Contraseña/Token

1. En la pestaña **"Account"**, verificar:
   - Contraseña de la cuenta
   - API Token (si existe)

### Verificar Host y Puerto

**Configuración correcta:**
```
Host: ssh.pythonanywhere.com
Puerto: 22
Protocolo: SFTP (no FTP)
```

---

## ✅ SOLUCIÓN 4: Usar WinSCP (Alternativa a FileZilla)

Si FileZilla sigue dando problemas, prueba WinSCP:

1. Descargar WinSCP: https://winscp.net/
2. Instalar y abrir
3. Configurar:
   ```
   Protocolo: SFTP
   Nombre de host: ssh.pythonanywhere.com
   Puerto: 22
   Nombre de usuario: atlantareciclajes
   Contraseña: [API Token o contraseña]
   ```
4. Clic en **"Conectar"**

---

## 📋 PASO A PASO COMPLETO (Con API Token)

### 1. Obtener API Token

```
1. Ir a: https://www.pythonanywhere.com/user/atlantareciclajes/
2. Pestaña: "Account" o "Security"
3. Buscar: "API Token" o "API"
4. Clic: "Create API token"
5. Copiar el token (ejemplo: abc123xyz789...)
```

### 2. Configurar FileZilla

```
1. Abrir FileZilla
2. Clic en "Archivo" → "Gestor de sitios" (o Ctrl+S)
3. Clic en "Nuevo sitio"
4. Nombre: "PythonAnywhere"
5. Configurar:
   - Protocolo: SFTP - SSH File Transfer Protocol
   - Host: ssh.pythonanywhere.com
   - Puerto: 22
   - Tipo de acceso: Normal
   - Usuario: atlantareciclajes
   - Contraseña: [PEGAR API TOKEN AQUÍ]
6. Clic en "Conectar"
```

### 3. Verificar Conexión

Si conecta correctamente, deberías ver:
- Panel izquierdo: Tu PC (E:\projecto\e_garage)
- Panel derecho: Servidor (/home/atlantareciclajes)

### 4. Navegar en el Servidor

En el panel derecho (servidor):
1. Navegar a: `/home/atlantareciclajes/`
2. Si no existe `egarage_update`, crearla:
   - Clic derecho → "Crear directorio"
   - Nombre: `egarage_update`

### 5. Subir el Archivo ZIP

1. En panel izquierdo (tu PC), navegar a:
   ```
   E:\projecto\e_garage\
   ```

2. Buscar archivo: `egarage_update_atlantareciclajes.zip`

3. Arrastrar el archivo desde panel izquierdo al panel derecho (carpeta `egarage_update`)

4. Esperar a que termine la transferencia (puede tardar 5-10 minutos)

5. Verificar que el archivo aparezca en el servidor

---

## 🔍 VERIFICAR QUE EL ARCHIVO SE SUBIÓ

### Opción 1: En FileZilla
- Ver el archivo en el panel derecho (servidor)
- Verificar tamaño y fecha

### Opción 2: En Web Panel
1. Ir a: https://www.pythonanywhere.com/user/atlantareciclajes/
2. Pestaña: "Files"
3. Navegar a: `/home/atlantareciclajes/egarage_update/`
4. Verificar que `egarage_update_atlantareciclajes.zip` esté ahí

### Opción 3: En Consola
1. Abrir consola Bash en PythonAnywhere
2. Ejecutar:
   ```bash
   ls -lh /home/atlantareciclajes/egarage_update/
   ```
3. Deberías ver el archivo ZIP con su tamaño

---

## 🆘 SI NADA FUNCIONA

### Contactar Soporte de PythonAnywhere

1. Ir a: https://www.pythonanywhere.com/support/
2. Explicar el problema de autenticación
3. Mencionar que intentas usar SFTP con FileZilla
4. Preguntar cómo obtener/generar API Token

### Alternativa Temporal: Usar Consola

Si no puedes subir por SFTP, puedes:

1. **Dividir el ZIP en partes más pequeñas** (usando 7-Zip)
2. **Subir por Web Panel** (límite 100MB por archivo)
3. **Recomprimir en el servidor** usando la consola

---

## ✅ CHECKLIST

- [ ] API Token obtenido de PythonAnywhere
- [ ] FileZilla configurado con API Token
- [ ] Conexión exitosa a servidor
- [ ] Carpeta `egarage_update` creada en servidor
- [ ] Archivo ZIP subido correctamente
- [ ] Archivo verificado en servidor

---

**¿Necesitas ayuda con algún paso específico?** 🚀







