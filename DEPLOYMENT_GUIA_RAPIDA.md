# ⚡ GUÍA RÁPIDA DE DEPLOYMENT - Ubicaciones

> **Para ejecutar EN EL SERVIDOR** después de subir archivos

---

## 🚀 **OPCIÓN 1: Con Git (Recomendado)**

### **En tu PC:**

```bash
# Commit y push
git add .
git commit -m "feat: Sistema ubicaciones multi-país (8 países, 858 ciudades)"
git push origin main
```

### **En el servidor (SSH):**

```bash
# 1. Pull
cd /ruta/a/e_garage
git pull origin main

# 2. Ejecutar script de deployment
bash scripts/deploy_ubicaciones.sh
```

**¡Listo!** El script hace todo automáticamente.

---

## 🔧 **OPCIÓN 2: Comandos Manuales (Sin script)**

### **En el servidor:**

```bash
cd /ruta/a/e_garage

# 1. Activar entorno (si usas virtualenv)
source venv/bin/activate

# 2. Verificar
python manage.py check

# 3. Cargar ubicaciones
python manage.py cargar_todas_ubicaciones --skip-existing

# 4. Verificar
python manage.py verificar_ubicaciones

# 5. Backfill (opcional)
python manage.py backfill_addresses

# 6. Restart
sudo systemctl restart gunicorn
```

---

## 📦 **OPCIÓN 3: Sin Git (Subir archivos manualmente)**

### **Archivos a subir (21 archivos):**

#### **Comandos (5 archivos):**
```
taller/management/commands/cargar_estados_chile.py
taller/management/commands/cargar_estados_colombia.py
taller/management/commands/cargar_estados_ecuador.py
taller/management/commands/cargar_todas_ubicaciones.py        (actualizado)
taller/management/commands/backfill_addresses.py              (actualizado)
```

#### **Modelos y Forms (2 archivos):**
```
taller/models/ubicacion.py                                    (actualizado)
taller/clientes/forms.py                                      (actualizado)
```

#### **Scripts (2 archivos):**
```
scripts/setup_ubicaciones.sh
scripts/deploy_ubicaciones.sh
```

#### **Documentación (12 archivos - OPCIONAL):**
```
docs/INDICE_UBICACIONES.md
docs/README_UBICACIONES.md
docs/GUIA_RAPIDA_UBICACIONES.md
docs/ARQUITECTURA_UBICACIONES_MULTI_PAIS.md
docs/RESUMEN_ARQUITECTURA_UBICACIONES.md
docs/COMPARACION_MODELOS_UBICACION.md
docs/ESTRATEGIA_MIGRACION_GRADUAL.md
docs/FIXTURES_VS_COMANDOS.md
docs/AGREGAR_UBICACIONES_ON_THE_FLY.md
docs/VERIFICACION_Y_ACTIVACION.md
ARQUITECTURA_UBICACIONES_IMPLEMENTADA.md
INFORME_FINAL_SESION_UBICACIONES.md
```

### **Comandos para subir:**

```bash
# En PowerShell (tu PC)
scp taller/management/commands/cargar_estados_chile.py usuario@servidor:/ruta/a/e_garage/taller/management/commands/
scp taller/management/commands/cargar_estados_colombia.py usuario@servidor:/ruta/a/e_garage/taller/management/commands/
scp taller/management/commands/cargar_estados_ecuador.py usuario@servidor:/ruta/a/e_garage/taller/management/commands/
scp taller/management/commands/cargar_todas_ubicaciones.py usuario@servidor:/ruta/a/e_garage/taller/management/commands/
scp taller/management/commands/backfill_addresses.py usuario@servidor:/ruta/a/e_garage/taller/management/commands/
scp taller/models/ubicacion.py usuario@servidor:/ruta/a/e_garage/taller/models/
scp taller/clientes/forms.py usuario@servidor:/ruta/a/e_garage/taller/clientes/
scp scripts/deploy_ubicaciones.sh usuario@servidor:/ruta/a/e_garage/scripts/

# Luego SSH y ejecutar:
ssh usuario@servidor
cd /ruta/a/e_garage
bash scripts/deploy_ubicaciones.sh
```

---

## ⚡ **COMANDOS RÁPIDOS (COPIAR Y PEGAR)**

### **Para ejecutar EN EL SERVIDOR vía SSH:**

```bash
cd /ruta/a/e_garage
source venv/bin/activate  # Si usas virtualenv
python manage.py cargar_todas_ubicaciones --skip-existing
python manage.py verificar_ubicaciones
python manage.py backfill_addresses --dry-run
python manage.py backfill_addresses
sudo systemctl restart gunicorn  # O tu comando de restart
```

---

## ✅ **VERIFICACIÓN POST-DEPLOYMENT**

### **1. Verificar datos:**

```bash
python manage.py shell
```

```python
from taller.models import Estado, Ciudad

print("Estados:", Estado.objects.count())  # Esperado: 230
print("Ciudades:", Ciudad.objects.count())  # Esperado: 858

# Por país
print("Chile:", Estado.objects.filter(pais="CL").count())  # 16
print("Colombia:", Estado.objects.filter(pais="CO").count())  # 32
print("Ecuador:", Estado.objects.filter(pais="EC").count())  # 24
```

### **2. Verificar en navegador:**

```
https://tudominio.com/us/en/clientes/crear/
  ✅ Select State debe mostrar 50 estados
  ✅ Seleccionar California → Ciudades se cargan
  ✅ Botón "+ ADD CITY" funciona
```

### **3. Verificar logs:**

```bash
# Ver últimos logs
tail -f /var/log/gunicorn/error.log
# o
journalctl -u gunicorn -f
```

---

## 🚨 **TROUBLESHOOTING**

### **Error: "ModuleNotFoundError"**

```bash
# Verificar que archivos se subieron
ls taller/management/commands/cargar_estados_chile.py
ls taller/management/commands/cargar_estados_colombia.py
ls taller/management/commands/cargar_estados_ecuador.py
```

### **Error: "No module named ubicacion"**

```bash
# Verificar estructura de apps
python manage.py check
python manage.py showmigrations
```

### **Error: "UnicodeEncodeError"**

```bash
# Set encoding
export PYTHONIOENCODING=utf-8
python manage.py cargar_todas_ubicaciones
```

### **Selects vacíos en formulario:**

```bash
# Verificar datos
python manage.py verificar_ubicaciones

# Si muestra 0 estados/ciudades:
python manage.py cargar_todas_ubicaciones
```

---

## ⏱️ **TIEMPO ESTIMADO**

```
Git pull:           1 min
Verificar modelos:  1 min
Cargar datos:       2-5 min
Verificar:          1 min
Backfill:           1-2 min
Restart:            1 min
Verificación:       2 min
─────────────────────────
TOTAL:             9-13 min
```

---

## 🎯 **CHECKLIST**

```
PRE-DEPLOYMENT:
  ✅ Código commiteado y pusheado
  ✅ Backup de BD creado
  ✅ Plan de rollback preparado

DEPLOYMENT:
  ⏳ SSH al servidor
  ⏳ cd /ruta/a/e_garage
  ⏳ git pull origin main
  ⏳ source venv/bin/activate
  ⏳ python manage.py check
  ⏳ python manage.py cargar_todas_ubicaciones --skip-existing
  ⏳ python manage.py verificar_ubicaciones
  ⏳ python manage.py backfill_addresses
  ⏳ sudo systemctl restart gunicorn

POST-DEPLOYMENT:
  ⏳ Verificar en navegador
  ⏳ Probar crear cliente
  ⏳ Verificar logs
  ⏳ Monitorear errores (15 min)

ROLLBACK (si falla):
  git checkout HEAD~1
  sudo systemctl restart gunicorn
```

---

## 📝 **NOTAS DE RELEASE**

```
VERSIÓN: Sistema de Ubicaciones v1.0
FECHA: 4 de Diciembre 2024

NUEVAS FUNCIONALIDADES:
  ✅ Sistema completo de ubicaciones multi-país
  ✅ 858 ciudades pre-cargadas (8 países)
  ✅ Soporte para Colombia y Ecuador
  ✅ Modales para agregar ubicaciones on-the-fly
  ✅ Migración automática de clientes legacy

ARCHIVOS MODIFICADOS:
  • 3 comandos nuevos (Chile, Colombia, Ecuador)
  • 3 archivos actualizados (modelos, forms, comandos)
  • 13 documentos técnicos

COMANDOS DISPONIBLES:
  • python manage.py cargar_todas_ubicaciones
  • python manage.py verificar_ubicaciones
  • python manage.py backfill_addresses

COBERTURA:
  CL: 16 regiones, 78 ciudades
  US: 50 estados, 542 ciudades
  BR: 27 estados, 22 ciudades
  MX: 32 estados, 53 ciudades
  PE: 25 departamentos, 16 ciudades
  VE: 24 estados, 20 ciudades
  CO: 32 departamentos, 81 ciudades
  EC: 24 provincias, 46 ciudades

IMPACTO:
  • Formularios con datos reales (antes: vacíos)
  • Selects dinámicos con AJAX (antes: estáticos)
  • Agregar ubicaciones on-the-fly (antes: imposible)
```

---

**🚀 ¡Listo para deployment!**

