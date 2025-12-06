# ⚡ Resumen Rápido - Actualización Completa del Servidor

## 🎯 Objetivo
Actualizar completamente el servidor eGarage con la versión nueva **SIN PERDER** datos de suscriptores ni clientes.

---

## 📍 CONVENCIÓN

- **[EN TU PC]** = Acción en tu computadora local (Windows)
- **[EN EL SERVIDOR]** = Acción en el servidor (SSH o consola)

---

## 📝 Proceso en 3 Pasos

### 1️⃣ PREPARAR CÓDIGO (5 min) - [EN TU PC]

```powershell
# [EN TU PC] Abrir PowerShell
cd E:\projecto\e_garage

# Guardar cambios
git add .
git commit -m "Preparación para actualización"

# Subir a Git (si usas repositorio remoto)
git push origin main
```

---

### 2️⃣ BACKUP (5-10 min) - [EN EL SERVIDOR]

```bash
# [EN EL SERVIDOR] Conectarse al servidor
# PythonAnywhere: Consola Bash del dashboard
# O SSH: ssh atlantareciclajes@ssh.pythonanywhere.com

# Navegar al proyecto
cd /home/atlantareciclajes/apps/egarage/current

# Activar venv
workon venv_egarage310

# Ejecutar backup
python scripts_deploy/backup_datos_criticos.py
```

**Espera a que termine** - verifica que se crearon archivos en `backups/datos_criticos/`

---

### 3️⃣ ACTUALIZAR (15-30 min) - [EN EL SERVIDOR]

```bash
# [EN EL SERVIDOR] (Ya conectado desde paso anterior)

# Dar permisos
chmod +x scripts_deploy/actualizar_servidor_completo.sh

# Ejecutar actualización
bash scripts_deploy/actualizar_servidor_completo.sh
```

**NO INTERRUMPAS** - el script hace todo automáticamente:
- ✅ Actualiza código desde Git
- ✅ Actualiza dependencias
- ✅ Aplica migraciones (sin borrar datos)
- ✅ Recolecta archivos estáticos
- ✅ Verifica datos críticos

---

### 4️⃣ VERIFICAR (5 min) - [EN TU PC] y [EN EL SERVIDOR]

**[EN TU PC]**
1. Abre el sitio en el navegador
2. Inicia sesión
3. Verifica que los datos están intactos

**[EN EL SERVIDOR]**
```bash
# Reiniciar aplicación
# PythonAnywhere: Reload en dashboard
# Otros: sudo systemctl restart egarage
```

---

## 🆘 Si algo sale mal

Los datos están en: `backups/datos_criticos/backup_completo_*/`

**[EN EL SERVIDOR]** Para restaurar:
```bash
sqlite3 db.sqlite3 < backups/datos_criticos/backup_completo_*/db_completo_*.sql
```

---

## 📚 Documentación Completa

- **Guía detallada:** `GUIA_ACTUALIZACION_COMPLETA_SERVIDOR.md`
- **Checklist:** `CHECKLIST_ACTUALIZACION_COMPLETA.md`

---

## ⏱️ Tiempo Total Estimado

**25-45 minutos** (dependiendo del tamaño de la BD)

---

**¡Listo para empezar!** 🚀
