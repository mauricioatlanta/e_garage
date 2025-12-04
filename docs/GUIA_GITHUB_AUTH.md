# 🔐 GUÍA: Autenticación con GitHub

## 🚨 Problema

GitHub **ya no acepta contraseñas** para operaciones Git. Debes usar un **Personal Access Token (PAT)**.

**Error común:**
```
remote: Invalid username or token. Password authentication is not supported for Git operations.
fatal: Authentication failed
```

---

## ✅ SOLUCIÓN: Crear y Usar Personal Access Token

### Paso 1: Crear Personal Access Token en GitHub

1. Ve a GitHub.com e inicia sesión
2. Haz clic en tu **avatar** (arriba derecha) → **Settings**
3. En el menú lateral izquierdo, baja hasta **Developer settings**
4. Haz clic en **Personal access tokens** → **Tokens (classic)** o **Fine-grained tokens**
5. Haz clic en **Generate new token** → **Generate new token (classic)**
6. Configura el token:
   - **Note**: `egarage-desarrollo` (o el nombre que quieras)
   - **Expiration**: Elige un tiempo (ej: 90 días, 1 año, o sin expiración)
   - **Select scopes**: Marca estos permisos:
     - ✅ `repo` (acceso completo a repositorios)
     - ✅ `workflow` (si usas GitHub Actions)
7. Haz clic en **Generate token** (abajo)
8. ⚠️ **IMPORTANTE**: **Copia el token inmediatamente**. Se muestra una sola vez.
   - Tiene este formato: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### Paso 2: Configurar Git para Usar el Token

Ya está configurado el **Windows Credential Manager**. Cuando Git pida credenciales:

1. **Username**: `mauricioatlanta` (tu usuario de GitHub)
2. **Password**: **Pega el Personal Access Token** (no tu contraseña de GitHub)

---

### Paso 3: Probar la Autenticación

```powershell
# Intentar una operación Git (ej: fetch)
cd E:\projecto\e_garage
git fetch origin

# O hacer un pull
git pull origin main
```

Cuando te pida credenciales:
- **Username**: `mauricioatlanta`
- **Password**: Pega tu **Personal Access Token**

El token se guardará automáticamente en Windows Credential Manager.

---

## 🔄 Actualizar Credenciales Existentes

Si ya intentaste autenticarte y falló, limpia las credenciales guardadas:

### Opción 1: Usar Git Credential Manager (Recomendado)

```powershell
# Ver credenciales guardadas
git credential-manager list

# Eliminar credenciales de GitHub
git credential-manager erase https://github.com
```

### Opción 2: Usar Windows Credential Manager

1. Presiona `Windows + R`
2. Escribe: `cmdkey /list`
3. Busca entradas relacionadas con `git:https://github.com`
4. Elimina las entradas:
   ```powershell
   cmdkey /delete:git:https://github.com
   ```

### Opción 3: Actualizar URL del Remote (Alternativa)

Si prefieres, puedes actualizar la URL para incluir tu usuario:

```powershell
git remote set-url origin https://mauricioatlanta@github.com/mauricioatlanta/e_garage.git
```

Luego, cuando Git pida la contraseña, usa el **Personal Access Token**.

---

## 🎯 AUTENTICACIÓN AUTOMÁTICA

Una vez que ingreses el token correctamente, Windows Credential Manager lo guardará y no tendrás que ingresarlo cada vez.

**Para verificar que está guardado:**
```powershell
cmdkey /list | Select-String -Pattern "github"
```

---

## 🔒 ALTERNATIVA: Usar SSH (Más Seguro)

Si prefieres no usar tokens, puedes configurar autenticación SSH:

### 1. Generar Clave SSH

```powershell
# Verificar si ya tienes una clave SSH
ls ~/.ssh

# Si no existe, generar una nueva
ssh-keygen -t ed25519 -C "tu_email@ejemplo.com"
# Presiona Enter para usar ubicación por defecto
# Opcional: agrega una frase de contraseña
```

### 2. Copiar Clave Pública

```powershell
# Mostrar la clave pública
cat ~/.ssh/id_ed25519.pub
# Copia todo el contenido
```

### 3. Agregar Clave a GitHub

1. GitHub.com → **Settings** → **SSH and GPG keys**
2. **New SSH key**
3. **Title**: `PC Desarrollo` (o el nombre que quieras)
4. **Key**: Pega la clave pública que copiaste
5. **Add SSH key**

### 4. Cambiar Remote a SSH

```powershell
git remote set-url origin git@github.com:mauricioatlanta/e_garage.git
```

### 5. Probar

```powershell
git fetch origin
```

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### Error: "Authentication failed"

- ✅ Verifica que el token tiene permisos `repo`
- ✅ Verifica que el token no expiró
- ✅ Asegúrate de usar el **token**, no tu contraseña
- ✅ Limpia credenciales guardadas y vuelve a intentar

### Error: "Token revoked" o "Invalid token"

- El token fue revocado o expiró
- Crea un nuevo token en GitHub
- Actualiza las credenciales en Windows Credential Manager

### El token no se guarda

```powershell
# Verificar que Git Credential Manager está configurado
git config --global credential.helper

# Si está vacío, configurarlo:
git config --global credential.helper manager
```

### Quiero cambiar el token

1. Crea un nuevo token en GitHub
2. Elimina credenciales antiguas:
   ```powershell
   cmdkey /delete:git:https://github.com
   ```
3. Intenta una operación Git (se pedirá el nuevo token)

---

## 📝 RESUMEN RÁPIDO

1. ✅ Crear PAT en GitHub: Settings → Developer settings → Personal access tokens
2. ✅ Copiar el token (formato: `ghp_xxxxx...`)
3. ✅ Configurar Git: `git config --global credential.helper manager` (ya hecho)
4. ✅ Intentar operación Git (ej: `git fetch`)
5. ✅ Username: `mauricioatlanta`
6. ✅ Password: **Pega el token** (no tu contraseña)
7. ✅ El token se guarda automáticamente

---

## 🔗 ENLACES ÚTILES

- GitHub: Crear token: https://github.com/settings/tokens
- GitHub Docs: Autenticación: https://docs.github.com/en/authentication
- Git Credential Manager: https://github.com/GitCredentialManager/git-credential-manager

---

**¿Problemas?** Ejecuta con verbose para ver más detalles:
```powershell
git -c credential.helper=manager fetch origin -v
```




