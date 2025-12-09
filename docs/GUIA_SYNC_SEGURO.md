# 🔒 GUÍA: Sincronización Segura Servidor → PC

## 🎯 Objetivo
Sincronizar el código del servidor a tu PC **SIN tocar**:
- ❌ Usuarios registrados
- ❌ Credenciales y passwords
- ❌ Base de datos local
- ❌ Archivos subidos por usuarios

---

## ⚡ USO RÁPIDO

```powershell
# Desde la raíz del proyecto:
cd E:\projecto\e_garage
.\scripts\sync_servidor_pc_seguro.ps1
```

El script:
1. ✅ Hace backup de archivos sensibles
2. ✅ Sincroniza código del servidor
3. ✅ Restaura archivos protegidos
4. ✅ Verifica que usuarios no se tocaron

---

## 🛡️ ARCHIVOS PROTEGIDOS

El script **NO sobrescribe** estos archivos:

| Archivo/Carpeta | Razón |
|----------------|-------|
| `db.sqlite3` | Base de datos con usuarios y empresas |
| `.env` | Variables de entorno (credenciales, API keys) |
| `gestion_taller/settings.py` | Configuración (puede tener credenciales) |
| `gestion_taller/settings/*.py` | Settings locales/producción |
| `media/` | Archivos subidos por usuarios |
| `logs/` | Logs locales |

---

## 📋 PROCESO PASO A PASO

### 1. Ejecutar Script

```powershell
.\scripts\sync_servidor_pc_seguro.ps1
```

### 2. Seleccionar Método

El script ofrece 3 opciones:

**Opción 1: FileZilla (Recomendado)**
- Más control visual
- Puedes elegir qué descargar
- El script te guía paso a paso

**Opción 2: rsync (WSL/Git Bash)**
- Más rápido
- Sincronización inteligente
- Excluye automáticamente archivos sensibles

**Opción 3: SCP (PowerShell)**
- Simple pero descarga todo
- El script restaura archivos protegidos después

### 3. Verificación Automática

Después de sincronizar, el script:
- ✅ Restaura archivos protegidos
- ✅ Verifica que usuarios no cambiaron
- ✅ Muestra cambios en Git
- ✅ Genera resumen

---

## 🔍 VERIFICACIÓN MANUAL

### Verificar Usuarios

```powershell
# Verificar que usuarios no cambiaron
python manage.py shell
```

```python
from django.contrib.auth.models import User
from taller.models.empresa import Empresa

print(f"Usuarios: {User.objects.count()}")
print(f"Empresas: {Empresa.objects.count()}")
```

### Verificar Archivos Protegidos

```powershell
# Verificar que db.sqlite3 es el local (no del servidor)
Get-Item db.sqlite3 | Select-Object LastWriteTime, Length

# Verificar que .env existe y es local
Test-Path .env
```

### Ver Cambios Sincronizados

```powershell
# Ver qué archivos cambiaron
git status

# Ver resumen de cambios
git diff --stat

# Ver cambios en un archivo específico
git diff gestion_taller/urls.py
```

---

## ✅ CHECKLIST POST-SINCRONIZACIÓN

Después de sincronizar, verifica:

- [ ] `db.sqlite3` existe y es el local (no sobrescrito)
- [ ] `.env` existe y tiene tus credenciales locales
- [ ] Usuarios locales intactos: `python manage.py shell` → `User.objects.count()`
- [ ] Archivos de código actualizados: `git status` muestra cambios
- [ ] Proyecto funciona: `python manage.py runserver`
- [ ] No hay errores de importación
- [ ] Templates actualizados

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### Problema: Usuarios desaparecieron

**Solución:**
```powershell
# El script guarda backup automático en:
# .sync_protected_YYYYMMDD_HHMMSS/db.sqlite3

# Restaurar:
$backupDir = Get-ChildItem -Path . -Filter ".sync_protected_*" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Copy-Item "$backupDir\db.sqlite3" -Destination "db.sqlite3" -Force
```

### Problema: .env fue sobrescrito

**Solución:**
```powershell
# Restaurar desde backup:
$backupDir = Get-ChildItem -Path . -Filter ".sync_protected_*" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Copy-Item "$backupDir\.env" -Destination ".env" -Force
```

### Problema: Archivos no se sincronizaron

**Solución:**
1. Verifica conexión al servidor
2. Verifica permisos de escritura en carpeta local
3. Cierra editores que tengan archivos abiertos
4. Intenta de nuevo con FileZilla (más control)

### Problema: Conflicto en Git

**Solución:**
```powershell
# Ver conflictos
git status

# Si hay conflictos, resolver manualmente:
# 1. Abrir archivo con conflicto
# 2. Buscar marcadores: <<<<<<< HEAD
# 3. Resolver conflicto
# 4. git add archivo_resuelto.py
# 5. git commit
```

---

## 📊 INFORMACIÓN DEL SERVIDOR

```
Usuario: atlantareciclajes
Host: atlantareciclajes.pythonanywhere.com
Puerto: 22 (SFTP)
Ruta: /home/atlantareciclajes/apps/egarage/current
     o: /home/atlantareciclajes/egarage/
```

---

## 🔄 FLUJO COMPLETO

```
1. Ejecutar script
   ↓
2. Script hace backup de archivos sensibles
   ↓
3. Seleccionar método de sincronización
   ↓
4. Descargar código del servidor
   ↓
5. Script restaura archivos protegidos
   ↓
6. Script verifica usuarios no cambiaron
   ↓
7. Revisar cambios en Git
   ↓
8. Commit cambios (opcional)
   ↓
9. Eliminar backup temporal (opcional)
```

---

## 💡 CONSEJOS

1. **Siempre ejecuta el script** antes de hacer cambios grandes
2. **Revisa los cambios** con `git diff` antes de commitear
3. **Mantén backups** de `.sync_protected_*` por unos días
4. **Verifica usuarios** después de cada sincronización
5. **No sincronices** si tienes cambios locales importantes sin commitear

---

## ⚙️ PARÁMETROS AVANZADOS

```powershell
# Especificar ruta del servidor diferente
.\scripts\sync_servidor_pc_seguro.ps1 -ServerPath "/home/atlantareciclajes/egarage"

# Saltar backup (no recomendado)
.\scripts\sync_servidor_pc_seguro.ps1 -SkipBackup

# Especificar ruta local diferente
.\scripts\sync_servidor_pc_seguro.ps1 -LocalPath "D:\proyectos\e_garage"
```

---

## ✅ RESUMEN

Este script garantiza que:
- ✅ Código se sincroniza desde servidor
- ✅ Usuarios y credenciales NO se tocan
- ✅ Base de datos local se preserva
- ✅ Archivos sensibles se restauran automáticamente
- ✅ Verificación automática de integridad

**¡Sincronización segura garantizada!** 🔒











