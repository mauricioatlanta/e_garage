# ✅ Checklist de Actualización Completa del Servidor

Usa este checklist para asegurarte de que no olvidas ningún paso importante.

**Convención:**
- **[EN TU PC]** = Acción en tu computadora local (Windows)
- **[EN EL SERVIDOR]** = Acción en el servidor (SSH o consola)

---

## 📋 PREPARACIÓN (En tu PC)

### Paso 1: Preparar Código Local

- [ ] **[EN TU PC]** Abrir PowerShell
- [ ] **[EN TU PC]** Navegar al proyecto: `cd E:\projecto\e_garage`
- [ ] **[EN TU PC]** Verificar cambios: `git status`
- [ ] **[EN TU PC]** Hacer commit de cambios pendientes (si los hay): `git add . && git commit -m "Preparación para actualización"`
- [ ] **[EN TU PC]** Subir cambios a Git (si usas repositorio remoto): `git push origin main`
- [ ] **[EN TU PC]** Verificar que los scripts existen:
  - [ ] `scripts_deploy\backup_datos_criticos.py` existe
  - [ ] `scripts_deploy\actualizar_servidor_completo.sh` existe

---

## 🛡️ BACKUP (En el servidor)

### Paso 2: Conectarse al Servidor

- [ ] **[EN EL SERVIDOR]** Conectarse al servidor:
  - [ ] PythonAnywhere: Abrir consola Bash desde dashboard
  - [ ] O SSH: `ssh atlantareciclajes@ssh.pythonanywhere.com`
- [ ] **[EN EL SERVIDOR]** Navegar al proyecto: `cd /home/atlantareciclajes/apps/egarage/current`
- [ ] **[EN EL SERVIDOR]** Verificar que estoy en el lugar correcto: `ls -la | grep manage.py`

### Paso 3: Activar Entorno Virtual

- [ ] **[EN EL SERVIDOR]** Activar entorno virtual:
  - [ ] PythonAnywhere: `workon venv_egarage310`
  - [ ] O local: `source venv/bin/activate`
- [ ] **[EN EL SERVIDOR]** Verificar que está activado: `which python`

### Paso 4: Ejecutar Backup

- [ ] **[EN EL SERVIDOR]** Verificar que el script existe: `ls -la scripts_deploy/backup_datos_criticos.py`
- [ ] **[EN EL SERVIDOR]** Si NO existe, subirlo desde PC (o usar Git)
- [ ] **[EN EL SERVIDOR]** Ejecutar backup: `python scripts_deploy/backup_datos_criticos.py`
- [ ] **[EN EL SERVIDOR]** Esperar a que termine completamente (puede tardar varios minutos)
- [ ] **[EN EL SERVIDOR]** Verificar que se crearon los archivos:
  - [ ] Archivos JSON en `backups/datos_criticos/backup_completo_*/`
  - [ ] Archivo `RESUMEN_BACKUP.json` existe
  - [ ] Archivo `db_completo_*.sql` existe
- [ ] **[EN EL SERVIDOR]** Anotar la ubicación del backup: `_________________________`

---

## 🔄 ACTUALIZACIÓN (En el servidor)

### Paso 5: Preparar Script de Actualización

- [ ] **[EN EL SERVIDOR]** Verificar que el script existe: `ls -la scripts_deploy/actualizar_servidor_completo.sh`
- [ ] **[EN EL SERVIDOR]** Si NO existe, subirlo desde PC (o usar Git)
- [ ] **[EN EL SERVIDOR]** Dar permisos de ejecución: `chmod +x scripts_deploy/actualizar_servidor_completo.sh`
- [ ] **[EN EL SERVIDOR]** Verificar permisos: `ls -la scripts_deploy/actualizar_servidor_completo.sh`

### Paso 6: Actualizar Código

- [ ] **[EN EL SERVIDOR]** Si usas Git:
  - [ ] Ver rama actual: `git branch`
  - [ ] Obtener última versión: `git fetch origin`
  - [ ] Guardar cambios locales: `git stash save "Cambios locales"`
  - [ ] Actualizar: `git pull origin main`
- [ ] **[EN EL SERVIDOR]** Si NO usas Git:
  - [ ] Subir archivos desde PC usando SCP o rsync

### Paso 7: Ejecutar Actualización

- [ ] **[EN EL SERVIDOR]** Ejecutar script: `bash scripts_deploy/actualizar_servidor_completo.sh`
- [ ] **[EN EL SERVIDOR]** Esperar a que termine completamente (NO interrumpir)
- [ ] **[EN EL SERVIDOR]** Verificar que terminó correctamente:
  - [ ] Ver mensaje "✅ ACTUALIZACIÓN COMPLETADA"
  - [ ] No hay errores críticos en la salida

---

## 🔍 VERIFICACIÓN POST-ACTUALIZACIÓN

### Verificación del Sitio Web

- [ ] **[EN TU PC]** Abrir el sitio en el navegador
- [ ] **[EN TU PC]** Verificar que la página principal carga
- [ ] **[EN TU PC]** No hay errores 500 en la página principal
- [ ] **[EN TU PC]** El login funciona correctamente
- [ ] **[EN TU PC]** El logout funciona correctamente

### Verificación de Datos

- [ ] **[EN EL SERVIDOR]** Abrir shell de Django: `python manage.py shell`
- [ ] **[EN EL SERVIDOR]** Ejecutar verificación de datos (ver guía completa)
- [ ] **[EN EL SERVIDOR]** Número de empresas/suscriptores es correcto
  - Antes: `_____` | Después: `_____`
- [ ] **[EN EL SERVIDOR]** Número de usuarios es correcto
  - Antes: `_____` | Después: `_____`
- [ ] **[EN EL SERVIDOR]** Número de clientes es correcto
  - Antes: `_____` | Después: `_____`
- [ ] **[EN TU PC]** Puedo ver la lista de clientes
- [ ] **[EN TU PC]** Puedo ver un cliente específico con todos sus datos
- [ ] **[EN TU PC]** Puedo crear un nuevo cliente (prueba opcional)

### Verificación de Funcionalidades

- [ ] **[EN TU PC]** Dashboard carga correctamente
- [ ] **[EN TU PC]** Navegación entre secciones funciona
- [ ] **[EN TU PC]** Formularios cargan correctamente
- [ ] **[EN TU PC]** No hay errores en la consola del navegador (F12)

### Verificación de Logs

- [ ] **[EN EL SERVIDOR]** Revisar logs de errores del servidor
- [ ] **[EN EL SERVIDOR]** No hay errores críticos relacionados con:
  - [ ] Base de datos
  - [ ] Importaciones de módulos
  - [ ] Archivos estáticos
  - [ ] Permisos

---

## 🔄 REINICIO

- [ ] **[EN TU PC]** PythonAnywhere: Ir al dashboard y hacer Reload
- [ ] **[EN EL SERVIDOR]** Otros servidores: `sudo systemctl restart egarage`
- [ ] **[EN TU PC]** Verificar que el sitio sigue funcionando después del reinicio

---

## 📊 RESUMEN FINAL

**Fecha de actualización:** `____/____/____`  
**Hora de inicio:** `____:____`  
**Hora de finalización:** `____:____`  
**Duración total:** `____ minutos`

**Ubicación del backup:**
```
_________________________________________________
_________________________________________________
```

**Problemas encontrados:**
```
_________________________________________________
_________________________________________________
_________________________________________________
```

**Soluciones aplicadas:**
```
_________________________________________________
_________________________________________________
_________________________________________________
```

**Estado final:** 
- [ ] ✅ Actualización exitosa - Todo funciona correctamente
- [ ] ⚠️ Actualización con advertencias menores - Funciona pero hay detalles a revisar
- [ ] ❌ Actualización con problemas - Requiere atención

**Firma/Confirmación:** `_________________________`

---

## 🆘 SI ALGO SALE MAL

- [ ] **[EN EL SERVIDOR]** NO ENTRAR EN PÁNICO - Los datos están en el backup
- [ ] **[EN EL SERVIDOR]** Verificar ubicación del backup: `_________________________`
- [ ] **[EN EL SERVIDOR]** Revisar sección "SOLUCIÓN DE PROBLEMAS" en la guía
- [ ] **[EN EL SERVIDOR]** Si es necesario, proceder con restauración desde backup

---

## 📝 NOTAS ADICIONALES

```
_________________________________________________
_________________________________________________
_________________________________________________
_________________________________________________
```

---

**¡Actualización completada!** 🎉
