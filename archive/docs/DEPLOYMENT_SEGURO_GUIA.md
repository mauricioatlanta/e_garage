# 🚀 GUÍA DE DEPLOYMENT SEGURO - eGarage

## 📋 Descripción

Este script actualiza eGarage en el servidor **SIN BORRAR** datos de suscriptores. Preserva:
- ✅ Usuarios (User)
- ✅ Empresas (Empresa)
- ✅ Suscripciones (Suscripcion)
- ✅ RegistroEmbudoSuscriptor
- ✅ Todos los datos relacionados (clientes, vehículos, documentos, etc.)

---

## 🎯 Uso Rápido

### En el Servidor (Linux/SSH):

```bash
# 1. Conectarse al servidor
ssh usuario@servidor

# 2. Ir al directorio del proyecto
cd /ruta/a/egarage

# 3. Dar permisos de ejecución (solo primera vez)
chmod +x scripts/deploy_seguro_suscriptores.sh

# 4. Ejecutar el script
./scripts/deploy_seguro_suscriptores.sh
```

---

## 📦 Qué Hace el Script

### 1. **Backup Completo** 🔒
- Crea backup JSON de todos los datos
- Crea backup SQLite completo
- Cuenta usuarios, empresas y suscripciones antes del deployment

### 2. **Verificación de Estado** 🔍
- Verifica cuántos usuarios/empresas hay actualmente
- Muestra migraciones pendientes

### 3. **Actualización de Código** 📥
- Si hay Git: hace `git pull`
- Si no hay Git: asume que el código ya está actualizado

### 4. **Actualización de Dependencias** 📦
- Actualiza pip
- Instala/actualiza paquetes de `requirements.txt`

### 5. **Migraciones Seguras** ⚡
- Crea nuevas migraciones si hay cambios en modelos
- Aplica migraciones **SIN BORRAR DATOS**
- Si hay errores, intenta con `--fake-initial`

### 6. **Verificación Post-Deployment** ✅
- Verifica que los datos se preservaron
- Compara conteos antes/después
- Alerta si se perdieron datos

### 7. **Archivos Estáticos** 🎨
- Recolecta archivos estáticos
- Limpia cache de estáticos

### 8. **Verificaciones Finales** 🔍
- Ejecuta `python manage.py check --deploy`
- Verifica que todo esté correcto

---

## ⚠️ IMPORTANTE: Antes de Ejecutar

### 1. **Subir Archivos al Servidor**

Si NO usas Git, debes subir los archivos manualmente:

**Opción A: SCP (desde tu PC)**
```bash
# Desde tu PC Windows (PowerShell)
scp -r taller/ usuario@servidor:/ruta/a/egarage/
scp -r templates/ usuario@servidor:/ruta/a/egarage/
scp -r gestion_taller/ usuario@servidor:/ruta/a/egarage/
```

**Opción B: FileZilla/WinSCP**
- Conectar al servidor
- Subir carpetas: `taller/`, `templates/`, `gestion_taller/`
- Asegurarse de mantener la estructura de carpetas

**Opción C: Git (recomendado)**
```bash
# En tu PC local
git add -A
git commit -m "Actualización: [descripción]"
git push origin main

# En el servidor (el script lo hará automáticamente)
./scripts/deploy_seguro_suscriptores.sh
```

### 2. **Verificar Requisitos**

```bash
# Verificar que Python está disponible
python --version  # o python3 --version

# Verificar que Django está instalado
python manage.py --version

# Verificar que requirements.txt existe
ls requirements.txt
```

---

## 🔄 Proceso Paso a Paso

### Paso 1: Preparación Local

```bash
# 1. Asegurarse de que todo funciona localmente
python manage.py check
python manage.py test  # si tienes tests

# 2. Crear migraciones si hay cambios en modelos
python manage.py makemigrations

# 3. Verificar que las migraciones son correctas
python manage.py migrate --plan

# 4. Commit y push (si usas Git)
git add -A
git commit -m "Actualización: [descripción]"
git push origin main
```

### Paso 2: En el Servidor

```bash
# 1. Conectarse al servidor
ssh usuario@servidor

# 2. Ir al directorio del proyecto
cd /ruta/a/egarage

# 3. (Opcional) Ver estado actual
python manage.py showmigrations
python manage.py shell
# >>> from django.contrib.auth.models import User
# >>> User.objects.count()
# >>> exit()

# 4. Ejecutar el script
./scripts/deploy_seguro_suscriptores.sh
```

### Paso 3: Verificación Post-Deployment

```bash
# 1. Verificar que el sitio carga
curl http://localhost:8000/  # o la URL de tu servidor

# 2. Verificar que los datos están intactos
python manage.py shell
# >>> from django.contrib.auth.models import User
# >>> from taller.models.empresa import Empresa
# >>> print(f"Usuarios: {User.objects.count()}")
# >>> print(f"Empresas: {Empresa.objects.count()}")
# >>> exit()

# 3. Probar login con una cuenta existente
# Abrir navegador y hacer login
```

---

## 🆘 Solución de Problemas

### Error: "No such table"

```bash
# Si aparece "no such table", aplicar migraciones con fake-initial
python manage.py migrate --fake-initial

# Luego aplicar migraciones normales
python manage.py migrate
```

### Error: "Table already exists"

```bash
# Marcar migración como aplicada (fake)
python manage.py migrate taller 0001_initial --fake

# O usar fake-initial para todas
python manage.py migrate --fake-initial
```

### Error: "Datos perdidos"

```bash
# RESTAURAR desde backup
cp backups/deployments/db_backup_YYYYMMDD_HHMMSS.sqlite3 db.sqlite3

# O restaurar desde JSON
python manage.py loaddata backups/deployments/backup_pre_deploy_YYYYMMDD_HHMMSS.json
```

### Error: "Permission denied"

```bash
# Dar permisos de ejecución
chmod +x scripts/deploy_seguro_suscriptores.sh

# O ejecutar con bash explícitamente
bash scripts/deploy_seguro_suscriptores.sh
```

---

## 📊 Verificación de Datos

### Antes del Deployment

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.suscripcion import Suscripcion

print(f"Usuarios: {User.objects.count()}")
print(f"Empresas: {Empresa.objects.count()}")
print(f"Suscripciones: {Suscripcion.objects.count()}")

# Listar algunos usuarios
for user in User.objects.all()[:5]:
    print(f"  - {user.email} ({user.username})")
```

### Después del Deployment

```bash
# El script ya verifica esto automáticamente
# Pero puedes verificar manualmente:

python manage.py shell
```

```python
from django.contrib.auth.models import User
from taller.models.empresa import Empresa

# Los números deben ser iguales o mayores que antes
print(f"Usuarios: {User.objects.count()}")
print(f"Empresas: {Empresa.objects.count()}")
```

---

## 🔒 Seguridad

### Backups Automáticos

El script crea backups automáticamente en:
- `backups/deployments/backup_pre_deploy_YYYYMMDD_HHMMSS.json`
- `backups/deployments/db_backup_YYYYMMDD_HHMMSS.sqlite3`

### Recomendación

**Mantén los últimos 5-10 backups** antes de eliminar los antiguos:

```bash
# Ver backups
ls -lh backups/deployments/

# Eliminar backups muy antiguos (más de 30 días)
find backups/deployments/ -name "*.json" -mtime +30 -delete
find backups/deployments/ -name "*.sqlite3" -mtime +30 -delete
```

---

## ✅ Checklist Pre-Deployment

- [ ] Código probado localmente
- [ ] Migraciones creadas y probadas localmente
- [ ] Archivos subidos al servidor (o Git push hecho)
- [ ] Backup manual adicional (opcional pero recomendado)
- [ ] Servidor accesible vía SSH
- [ ] Permisos correctos en el servidor
- [ ] Virtual environment configurado

---

## 📝 Notas Importantes

1. **Las migraciones NO borran datos**: Django solo agrega/modifica columnas, no elimina datos existentes.

2. **Backups automáticos**: El script siempre crea backups antes de hacer cambios.

3. **Verificación automática**: El script verifica que los datos se preservaron después del deployment.

4. **Rollback fácil**: Si algo falla, puedes restaurar desde el backup SQLite.

5. **Sin downtime**: El deployment no requiere detener el servidor (a menos que uses Gunicorn/Nginx, que se reinician automáticamente).

---

## 🎉 ¡Listo!

Después de ejecutar el script, tu eGarage estará actualizado con todos los cambios, y **todos los datos de suscriptores estarán intactos**.

Si tienes problemas, revisa la sección "Solución de Problemas" o restaura desde el backup.

