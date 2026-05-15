# 🚀 Guía Completa de Actualización del Servidor eGarage

## 📋 Resumen

Esta guía te llevará paso a paso para actualizar completamente tu servidor eGarage con la versión nueva de tu PC, **SIN PERDER** ningún dato de suscriptores ni información de clientes.

**Tiempo estimado:** 30-60 minutos (dependiendo del tamaño de la base de datos)

---

## ⚠️ IMPORTANTE: ANTES DE EMPEZAR

1. **Asegúrate de tener acceso SSH al servidor** o acceso a la consola de PythonAnywhere
2. **Verifica que tienes permisos de escritura** en el directorio del proyecto
3. **Ten a mano las credenciales** de la base de datos (si es necesario)
4. **Reserva tiempo suficiente** - no interrumpas el proceso una vez iniciado

---

## 📍 CONVENCIÓN DE ESTA GUÍA

A lo largo de esta guía verás etiquetas que indican **DÓNDE** hacer cada acción:

- **[EN TU PC]** = Acción que debes hacer en tu computadora local (Windows)
- **[EN EL SERVIDOR]** = Acción que debes hacer en el servidor (SSH o consola)

---

## 📦 PASO 1: Preparar el Código en tu PC Local

**[EN TU PC]**

Antes de actualizar el servidor, asegúrate de que tu código local esté actualizado y listo.

### 1.1 Abrir PowerShell o Terminal en tu PC

**[EN TU PC]**

1. Abre PowerShell (Windows) o tu terminal preferida
2. Navega al directorio del proyecto:

```powershell
cd E:\projecto\e_garage
```

### 1.2 Verificar cambios locales

**[EN TU PC]**

Verifica si hay cambios que no se han guardado:

```powershell
git status
```

**¿Qué ver?**
- Si ves archivos en rojo/amarillo, hay cambios sin guardar
- Si dice "nothing to commit", todo está guardado

### 1.3 Hacer commit de cambios pendientes (si los hay)

**[EN TU PC]**

Si hay cambios sin guardar, guárdalos:

```powershell
# Agregar todos los cambios
git add .

# Hacer commit con un mensaje descriptivo
git commit -m "Preparación para actualización completa del servidor - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
```

**Espera a que termine** - verás un mensaje confirmando el commit.

### 1.4 Subir cambios a Git (si usas repositorio remoto)

**[EN TU PC]**

Si usas Git con un repositorio remoto (GitHub, GitLab, etc.), sube los cambios:

```powershell
# Ver qué rama estás usando
git branch

# Subir cambios (ajusta 'main' por tu rama si es diferente)
git push origin main
```

**Espera a que termine** - verás mensajes de progreso.

**Si no usas Git remoto**, puedes saltar este paso y subir los archivos directamente al servidor más adelante.

### 1.5 Verificar que los scripts están en el proyecto

**[EN TU PC]**

Verifica que los scripts de actualización están presentes:

```powershell
# Verificar que existe el script de backup
Test-Path scripts_deploy\backup_datos_criticos.py

# Verificar que existe el script de actualización
Test-Path scripts_deploy\actualizar_servidor_completo.sh
```

**Si alguno falta**, asegúrate de que están en el proyecto antes de continuar.

---

## 🛡️ PASO 2: Hacer Backup de Datos Críticos en el Servidor

**[EN EL SERVIDOR]**

**ESTE ES EL PASO MÁS IMPORTANTE** - No lo omitas bajo ninguna circunstancia.

### 2.1 Conectarte al servidor

**[EN EL SERVIDOR]**

**Opción A: Si usas PythonAnywhere:**
1. Ve a tu dashboard de PythonAnywhere en el navegador
2. Haz clic en la pestaña **Consoles**
3. Haz clic en **Bash** para abrir una consola
4. O usa SSH desde tu PC:
   ```powershell
   # [EN TU PC] Abrir PowerShell
   ssh atlantareciclajes@ssh.pythonanywhere.com
   ```

**Opción B: Si usas otro servidor (VPS, Cloud, etc.):**
```powershell
# [EN TU PC] Abrir PowerShell
ssh usuario@tu-servidor.com
# Ejemplo: ssh root@192.168.1.100
```

**Después de conectarte, estarás [EN EL SERVIDOR]**

### 2.2 Navegar al directorio del proyecto

**[EN EL SERVIDOR]**

Una vez conectado al servidor, navega al directorio del proyecto:

```bash
# PythonAnywhere (ajusta según tu configuración)
cd /home/atlantareciclajes/apps/egarage/current

# Otros servidores (ajusta según tu configuración)
# cd /opt/egarage
# cd /var/www/egarage
# etc.
```

**Verifica que estás en el lugar correcto:**

```bash
# Debe mostrar manage.py y otros archivos del proyecto
ls -la | grep manage.py
```

Si no ves `manage.py`, ajusta la ruta según tu configuración.

### 2.3 Activar entorno virtual

**[EN EL SERVIDOR]**

Si usas un entorno virtual (recomendado), actívalo:

```bash
# PythonAnywhere
workon venv_egarage310

# O si tienes venv local en el proyecto
source venv/bin/activate

# O si está en otra ubicación
source ~/.virtualenvs/venv_egarage310/bin/activate
```

**Verifica que está activado:**

```bash
# Debe mostrar la ruta del venv
which python
# Debe mostrar algo como: /home/atlantareciclajes/.virtualenvs/venv_egarage310/bin/python
```

### 2.4 Verificar que el script de backup existe

**[EN EL SERVIDOR]**

Antes de ejecutar, verifica que el script está presente:

```bash
# Verificar que existe
ls -la scripts_deploy/backup_datos_criticos.py
```

**Si NO existe**, necesitas subirlo desde tu PC:

**[EN TU PC]**

```powershell
# Desde tu PC, subir el script al servidor
scp scripts_deploy\backup_datos_criticos.py atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/scripts_deploy/
```

O si usas Git, asegúrate de que el código esté actualizado (ver PASO 3).

### 2.5 Ejecutar script de backup

**[EN EL SERVIDOR]**

Ahora ejecuta el script de backup:

```bash
python scripts_deploy/backup_datos_criticos.py
```

**¿Qué hace este script?**
- ✅ Hace backup de todas las tablas críticas (usuarios, empresas, clientes, etc.)
- ✅ Crea archivos JSON estructurados con todos los datos
- ✅ Crea un backup SQL completo de la base de datos
- ✅ Guarda todo en `backups/datos_criticos/`

**Espera a que termine completamente** - puede tardar varios minutos si hay muchos datos.

**Verás mensajes como:**
```
✅ auth_user: 15 registros guardados
✅ taller_empresa: 8 registros guardados
✅ taller_cliente: 245 registros guardados
...
✅ BACKUP COMPLETADO
```

### 2.6 Verificar que el backup se creó correctamente

**[EN EL SERVIDOR]**

Después de que termine, verifica que se crearon los archivos:

```bash
# Ver el directorio de backups más reciente
ls -lh backups/datos_criticos/backup_completo_*/

# Ver el resumen del backup
cat backups/datos_criticos/backup_completo_*/RESUMEN_BACKUP.json
```

**Debes ver:**
- ✅ Archivos JSON por cada tabla (ej: `auth_user_20250101_120000.json`)
- ✅ Un archivo `RESUMEN_BACKUP.json`
- ✅ Un archivo `db_completo_*.sql`

**Anota la ubicación del backup** (la necesitarás si algo sale mal):
```bash
# Copiar la ruta completa
echo $(ls -td backups/datos_criticos/backup_completo_* | head -1)
```

---

## 🔄 PASO 3: Actualizar el Código en el Servidor

**[EN EL SERVIDOR]**

Ahora vamos a actualizar el código del servidor con la versión nueva de tu PC.

### 3.1 Verificar que el script de actualización existe

**[EN EL SERVIDOR]**

Verifica que el script de actualización está presente:

```bash
ls -la scripts_deploy/actualizar_servidor_completo.sh
```

**Si NO existe**, súbelo desde tu PC:

**[EN TU PC]**

```powershell
# Subir el script al servidor
scp scripts_deploy\actualizar_servidor_completo.sh atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/scripts_deploy/
```

O si usas Git, el script se actualizará en el siguiente paso.

### 3.2 Dar permisos de ejecución al script

**[EN EL SERVIDOR]**

Antes de ejecutar, da permisos de ejecución:

```bash
chmod +x scripts_deploy/actualizar_servidor_completo.sh
```

**Verifica los permisos:**

```bash
ls -la scripts_deploy/actualizar_servidor_completo.sh
# Debe mostrar algo como: -rwxr-xr-x (la 'x' indica que es ejecutable)
```

### 3.3 Actualizar código desde Git (si usas Git)

**[EN EL SERVIDOR]**

Si tu proyecto usa Git, actualiza el código:

```bash
# Ver qué rama estás usando
git branch

# Obtener última versión desde el repositorio remoto
git fetch origin

# Ver qué cambios hay
git status

# Si hay cambios locales, guardarlos primero
git stash save "Cambios locales antes de actualización $(date +%Y%m%d_%H%M%S)"

# Actualizar código (ajusta 'main' por tu rama)
git pull origin main
```

**Si NO usas Git**, necesitas subir los archivos manualmente:

**[EN TU PC]**

```powershell
# Opción 1: Usar SCP para subir archivos específicos
# (Esto puede tardar mucho si hay muchos archivos)

# Opción 2: Usar rsync (más eficiente)
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' --exclude 'db.sqlite3' E:\projecto\e_garage\ atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/

# Opción 3: Crear un ZIP y subirlo
# (Comprimir, subir, descomprimir en el servidor)
```

### 3.4 Ejecutar el script de actualización

**[EN EL SERVIDOR]**

Ahora ejecuta el script de actualización completo:

```bash
bash scripts_deploy/actualizar_servidor_completo.sh
```

**Este script hará automáticamente:**
1. ✅ Verificar que existe el backup
2. ✅ Crear backup adicional de la base de datos
3. ✅ Actualizar código desde Git (si aplica)
4. ✅ Actualizar dependencias Python
5. ✅ Aplicar migraciones de base de datos (sin borrar datos)
6. ✅ Recolectar archivos estáticos
7. ✅ Limpiar caché
8. ✅ Verificar configuración
9. ✅ Verificar que los datos críticos estén intactos

**El proceso puede tardar 10-30 minutos** dependiendo de:
- Velocidad de conexión
- Tamaño de la base de datos
- Cantidad de archivos estáticos

**NO INTERRUMPAS EL PROCESO** - espera a que termine completamente.

**Verás mensajes como:**
```
📋 PASO 1: Verificando backup de datos críticos...
✅ Backup encontrado: /home/.../backup_completo_20250101_120000

📋 PASO 2: Creando backup adicional de base de datos...
✅ Backup de base de datos creado

📋 PASO 3: Activando entorno virtual...
✅ Entorno virtual activado

📋 PASO 4: Actualizando código desde Git...
✅ Código actualizado

...
```

### 3.5 Verificar que la actualización terminó correctamente

**[EN EL SERVIDOR]**

Al final del script, verás un resumen. Verifica que dice:

```
✅ ACTUALIZACIÓN COMPLETADA
```

Si ves errores críticos, **NO CONTINÚES** - revisa la sección "Solución de Problemas" más abajo.

---

## 🔍 PASO 4: Verificación Post-Actualización

### 4.1 Verificar que el sitio carga

**[EN TU PC]**

Abre tu navegador y verifica:

1. Abre tu sitio web (ej: `https://egarage.cl` o tu dominio)
2. Verifica que la página principal carga correctamente
3. Intenta iniciar sesión con una cuenta de prueba

**Si el sitio NO carga:**
- Espera 1-2 minutos (puede estar reiniciando)
- Revisa los logs (ver PASO 4.4)
- Verifica que la aplicación está corriendo

### 4.2 Verificar datos críticos

**[EN EL SERVIDOR]**

Conectado al servidor, verifica que los datos están intactos:

```bash
# Abrir shell de Django
python manage.py shell
```

**Dentro del shell de Django, ejecuta:**

```python
from taller.models import Empresa, Cliente
from django.contrib.auth.models import User

# Verificar empresas/suscriptores
print("=" * 50)
print("VERIFICACIÓN DE DATOS CRÍTICOS")
print("=" * 50)

empresas_count = Empresa.objects.count()
print(f"\n✅ Empresas/Suscriptores: {empresas_count}")

if empresas_count > 0:
    print("\nPrimeras 5 empresas:")
    for emp in Empresa.objects.all()[:5]:
        print(f"  - {emp.nombre_taller} (Usuario: {emp.user.username})")

# Verificar usuarios
usuarios_count = User.objects.count()
print(f"\n✅ Usuarios: {usuarios_count}")

# Verificar clientes
clientes_count = Cliente.objects.count()
print(f"\n✅ Clientes: {clientes_count}")

if clientes_count > 0:
    print("\nPrimeros 5 clientes:")
    for cli in Cliente.objects.all()[:5]:
        print(f"  - {cli.nombre} (Empresa: {cli.empresa.nombre_taller})")

print("\n" + "=" * 50)
print("Si los números coinciden con lo que tenías antes, ¡perfecto!")
print("=" * 50)

exit()
```

**Anota los números** y compáralos con lo que tenías antes de la actualización.

### 4.3 Verificar funcionalidades principales

**[EN TU PC]**

Abre tu navegador y prueba:

1. **Login/Logout**
   - Inicia sesión con una cuenta
   - Verifica que funciona
   - Cierra sesión
   - Verifica que funciona

2. **Lista de clientes**
   - Ve a la sección de clientes
   - Verifica que muestra todos los clientes
   - Verifica que los números coinciden

3. **Ver un cliente específico**
   - Haz clic en un cliente
   - Verifica que muestra toda su información
   - Verifica que los datos están completos

4. **Crear nuevo cliente** (prueba opcional)
   - Intenta crear un cliente de prueba
   - Verifica que funciona
   - Puedes eliminarlo después

5. **Dashboard**
   - Ve al dashboard principal
   - Verifica que carga sin errores
   - Verifica que muestra datos correctos

### 4.4 Revisar logs de errores

**[EN EL SERVIDOR]**

Revisa los logs para ver si hay errores:

**PythonAnywhere:**
- Ve a tu dashboard
- Haz clic en la pestaña **Web**
- Haz clic en **Error log**
- Revisa los últimos mensajes

**Otros servidores:**

```bash
# Ver últimos errores
tail -n 50 /var/log/egarage/error.log

# O si usas systemd
journalctl -u egarage -n 50 --no-pager

# O logs de Django
tail -n 50 logs/django.log
```

**Busca errores relacionados con:**
- ❌ Base de datos (Database errors)
- ❌ Importaciones de módulos (Import errors)
- ❌ Archivos estáticos faltantes (Static files)
- ❌ Permisos (Permission denied)

**Si encuentras errores**, anótalos y consulta la sección "Solución de Problemas".

---

## 🔄 PASO 5: Reiniciar la Aplicación

### 5.1 PythonAnywhere

**[EN TU PC]**

1. Abre tu navegador
2. Ve a tu dashboard de PythonAnywhere
3. Haz clic en la pestaña **Web**
4. Busca tu aplicación web
5. Haz clic en el botón **Reload** (o **Reload webapp**)
6. Espera 10-30 segundos
7. Verifica que el sitio carga correctamente

### 5.2 Otros servidores

**[EN EL SERVIDOR]**

```bash
# Si usas systemd
sudo systemctl restart egarage

# Verificar que está corriendo
sudo systemctl status egarage

# Si usas supervisor
sudo supervisorctl restart egarage

# Si usas gunicorn directamente
pkill -HUP gunicorn

# O reiniciar manualmente
# (depende de tu configuración)
```

**Después de reiniciar**, espera 10-30 segundos y verifica que el sitio carga.

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### Problema: "No se encuentra el backup"

**[EN EL SERVIDOR]**

**Solución:**
```bash
# Volver a ejecutar el backup
python scripts_deploy/backup_datos_criticos.py

# Verificar que se creó
ls -lh backups/datos_criticos/backup_completo_*/
```

### Problema: "Error en migraciones"

**[EN EL SERVIDOR]**

**Solución:**
```bash
# Ver qué migraciones están pendientes
python manage.py showmigrations

# Intentar con --fake-initial (si las tablas ya existen)
python manage.py migrate --fake-initial

# Si persiste, verificar el error específico
python manage.py migrate --verbosity=3

# Ver logs detallados
python manage.py migrate 2>&1 | tee migration_errors.log
```

### Problema: "El sitio no carga después de actualizar"

**[EN EL SERVIDOR]**

**Solución:**
1. Verificar que el servidor web está corriendo:
   ```bash
   # PythonAnywhere: Ver en dashboard
   # Otros: 
   sudo systemctl status nginx
   sudo systemctl status gunicorn
   ```

2. Verificar logs de errores (ver PASO 4.4)

3. Verificar permisos de archivos:
   ```bash
   chmod -R 755 .
   chmod -R 775 media/
   chmod -R 775 staticfiles/
   ```

4. Verificar que la aplicación está corriendo:
   ```bash
   ps aux | grep gunicorn
   ps aux | grep python
   ```

### Problema: "Faltan datos después de actualizar"

**[EN EL SERVIDOR]**

**Solución:**
1. **NO ENTRES EN PÁNICO** - Los datos están en el backup
2. Verificar el backup:
   ```bash
   ls -lh backups/datos_criticos/backup_completo_*/
   cat backups/datos_criticos/backup_completo_*/RESUMEN_BACKUP.json
   ```
3. Si es necesario restaurar, ver sección "Restaurar desde Backup" abajo

### Problema: "Error al actualizar dependencias"

**[EN EL SERVIDOR]**

**Solución:**
```bash
# Actualizar pip primero
pip install --upgrade pip

# Limpiar caché de pip
pip cache purge

# Luego instalar dependencias
pip install -r requirements.txt

# Si hay conflictos, instalar una por una
pip install -r requirements.txt --no-deps
pip install -r requirements.txt
```

### Problema: "Script no tiene permisos de ejecución"

**[EN EL SERVIDOR]**

**Solución:**
```bash
# Dar permisos
chmod +x scripts_deploy/actualizar_servidor_completo.sh

# Verificar
ls -la scripts_deploy/actualizar_servidor_completo.sh
```

### Problema: "No puedo conectarme al servidor"

**[EN TU PC]**

**Solución:**
1. Verificar conexión a internet
2. Verificar credenciales SSH
3. Verificar que el servidor está accesible:
   ```powershell
   ping tu-servidor.com
   ```
4. Para PythonAnywhere, usar la consola del dashboard en lugar de SSH

---

## 🔙 RESTAURAR DESDE BACKUP (Si algo sale mal)

### Opción 1: Restaurar desde backup SQL (Más rápido)

**[EN EL SERVIDOR]**

```bash
# 1. Detener la aplicación
# PythonAnywhere: Reload en dashboard (desactivar)
# Otros: sudo systemctl stop egarage

# 2. Hacer backup de la BD actual (por si acaso)
cp db.sqlite3 db.sqlite3.antes_restaurar_$(date +%Y%m%d_%H%M%S)

# 3. Encontrar el backup SQL más reciente
ULTIMO_BACKUP=$(ls -td backups/datos_criticos/backup_completo_* | head -1)
echo "Usando backup: $ULTIMO_BACKUP"

# 4. Restaurar desde backup SQL
sqlite3 db.sqlite3 < "$ULTIMO_BACKUP"/db_completo_*.sql

# 5. Verificar que se restauró
python manage.py shell -c "from taller.models import Empresa; print(f'Empresas: {Empresa.objects.count()}')"

# 6. Reiniciar aplicación
# PythonAnywhere: Reload en dashboard
# Otros: sudo systemctl start egarage
```

### Opción 2: Restaurar desde backups JSON (Más controlado)

Si necesitas restaurar datos específicos, puedes usar los archivos JSON del backup. Esto requiere un script personalizado o hacerlo manualmente desde el shell de Django.

---

## ✅ CHECKLIST FINAL

Antes de considerar la actualización completa, verifica:

### Preparación
- [ ] Código local actualizado y guardado **[EN TU PC]**
- [ ] Cambios subidos a Git (si aplica) **[EN TU PC]**

### Backup
- [ ] Backup de datos críticos creado **[EN EL SERVIDOR]**
- [ ] Backup verificado (archivos JSON y SQL presentes) **[EN EL SERVIDOR]**
- [ ] Ubicación del backup anotada **[EN EL SERVIDOR]**

### Actualización
- [ ] Código actualizado desde Git **[EN EL SERVIDOR]**
- [ ] Dependencias actualizadas **[EN EL SERVIDOR]**
- [ ] Migraciones aplicadas sin errores **[EN EL SERVIDOR]**
- [ ] Archivos estáticos recolectados **[EN EL SERVIDOR]**

### Verificación
- [ ] Sitio web carga correctamente **[EN TU PC]**
- [ ] Login/Logout funciona **[EN TU PC]**
- [ ] Datos de empresas/suscriptores intactos **[EN EL SERVIDOR]**
- [ ] Datos de clientes intactos **[EN EL SERVIDOR]**
- [ ] Funcionalidades principales funcionan **[EN TU PC]**
- [ ] No hay errores en los logs **[EN EL SERVIDOR]**

### Finalización
- [ ] Aplicación reiniciada correctamente **[EN EL SERVIDOR o EN TU PC]**
- [ ] Todo funciona como antes de la actualización **[EN TU PC]**

---

## 📞 SOPORTE

Si encuentras problemas que no puedes resolver:

1. **Revisa los logs** de errores **[EN EL SERVIDOR]**
2. **Verifica el backup** - los datos están seguros **[EN EL SERVIDOR]**
3. **Consulta la documentación** de Django sobre migraciones
4. **Contacta al equipo** si es necesario

---

## 📝 NOTAS IMPORTANTES

- ⏰ **Tiempo de inactividad:** El sitio puede estar inactivo durante 5-15 minutos durante la actualización
- 💾 **Espacio en disco:** Asegúrate de tener suficiente espacio para los backups (pueden ser varios GB) **[EN EL SERVIDOR]**
- 🔒 **Seguridad:** Los backups contienen información sensible - guárdalos de forma segura
- 🔄 **Versiones:** Este proceso funciona mejor si el servidor y tu PC usan la misma versión de Python
- 📍 **Ubicación:** Siempre verifica si estás **[EN TU PC]** o **[EN EL SERVIDOR]** antes de ejecutar comandos

---

## 🎉 ¡LISTO!

Si has completado todos los pasos y el checklist, tu servidor está completamente actualizado con la versión nueva, y todos tus datos están seguros.

**¡Felicidades!** 🚀
