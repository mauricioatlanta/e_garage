                    # ⚡ INICIO RÁPIDO - ACTUALIZACIÓN ATLANTARECICLAJES

**Tu ruta detectada**: `/home/atlantareciclajes/apps/egarage/current`

---

## 🎯 **EJECUTA ESTOS COMANDOS EN ORDEN**

### **Ya estás en la consola, ejecuta:**

```bash
# 1. Dar permisos a scripts CORREGIDOS
cd /home/atlantareciclajes/scripts_deploy/
chmod +x *_FIXED.sh
chmod +x 0_detectar_ruta.sh

# 2. BACKUP COMPLETO
./1_backup_FIXED.sh

# Anota el nombre del backup que te muestre
# Ejemplo: backup_completo_20251106_013500.tar.gz
```

---

## 📥 **AHORA EN TU PC - FILEZILLA**

```
1. Conectar FileZilla:
   Host: atlantareciclajes.pythonanywhere.com
   Puerto: 22 (SFTP)
   Usuario: atlantareciclajes
   Password: [tu password]

2. Descargar backup:
   Navegar a: /home/atlantareciclajes/
   Descargar: backup_completo_20251106_*.tar.gz
   Guardar en: E:\backups_egarage_pythonanywhere\

3. Preparar actualización en tu PC:
   - Ir a: E:\projecto\e_garage\
   - Crear carpeta: deploy_atlantareciclajes\
   - Copiar SOLO estos archivos de tu proyecto:

     deploy_atlantareciclajes\
     ├── templates\
     │   ├── email\          ← Carpeta completa
     │   ├── account\email\  ← Carpeta completa
     │   ├── auth\           ← Carpeta completa
     │   └── public\landing_chile_completa.html
     ├── taller\
     │   ├── views_extra\    ← Todos los archivos nuevos
     │   ├── models\pago.py
     │   ├── forms\
     │   ├── signals.py
     │   ├── apps.py
     │   └── management\     ← Carpeta completa
     └── gestion_taller\
         └── urls.py

4. Comprimir:
   - Seleccionar: deploy_atlantareciclajes\
   - Clic derecho → 7-Zip → Add to archive
   - Nombre: egarage_update_atlantareciclajes.zip

5. Subir a servidor:
   - En FileZilla, crear carpeta: /home/atlantareciclajes/egarage_update/
   - Subir: egarage_update_atlantareciclajes.zip a esa carpeta
   - Esperar que termine (puede tardar 5-10 min)
```

---

## 🚀 **VOLVER A CONSOLA PYTHONANYWHERE**

```bash
# 3. ACTUALIZAR
cd /home/atlantareciclajes/scripts_deploy/
./2_actualizar_FIXED.sh

# El script copiará todos los archivos
# Te pedirá editar settings.py
# Sigue las instrucciones en pantalla
# Ejecutará migraciones
# Recolectará estáticos
```

---

## 🌐 **RELOAD EN NAVEGADOR**

```
1. Ir a: https://www.pythonanywhere.com/user/atlantareciclajes/
2. Pestaña: "Web"
3. Buscar tu app
4. Clic botón verde: "Reload atlantareciclajes.pythonanywhere.com"
5. Esperar 15 segundos
```

---

## ✅ **VERIFICAR**

```bash
# En consola:
cd /home/atlantareciclajes/scripts_deploy/
./3_verificar_FIXED.sh

# Luego probar en navegador:
https://atlantareciclajes.pythonanywhere.com/cl/
```

---

## 🆘 **SI ALGO FALLA**

```bash
cd /home/atlantareciclajes/scripts_deploy/
./4_rollback.sh

# Te pedirá la fecha del backup
# Ingresar: 20251106_013338 (o el que tengas)
# Luego Reload en Web panel
```

---

## 📝 **RESUMEN DE ARCHIVOS A SUBIR**

### **Desde tu PC, necesitas subir:**

**Carpeta 1: scripts_deploy/** (ya está, refresca permisos)
```
0_detectar_ruta.sh
1_backup_FIXED.sh
2_actualizar_FIXED.sh
3_verificar_FIXED.sh
4_rollback.sh
```

**Carpeta 2: egarage_update/** (falta crear)
```
egarage_update_atlantareciclajes.zip
```

---

## ⏱️ **TIEMPO TOTAL**

```
Backup:              3 min
Preparar en PC:     10 min
Subir con FileZilla: 10 min
Actualizar:          7 min
Reload:              1 min
Verificar:           2 min
---
TOTAL:              33 minutos
```

---

## 🎯 **SIGUIENTE ACCIÓN**

En PythonAnywhere Console, ejecuta:

```bash
cd /home/atlantareciclajes/scripts_deploy/
chmod +x *_FIXED.sh
./1_backup_FIXED.sh
```

Luego sigue los pasos de la guía.

**¿Listo?** 🚀
