# 🚀 DEPLOYMENT - Sistema de Ubicaciones al Servidor

> **Objetivo:** Actualizar servidor con sistema de ubicaciones multi-país  
> **Fecha:** 4 de Diciembre 2024  
> **Archivos modificados:** 21 archivos

---

## 📦 **ARCHIVOS A SUBIR AL SERVIDOR**

### **🆕 Archivos NUEVOS (18 archivos):**

#### **Comandos (3 nuevos):**
```
taller/management/commands/
├── cargar_estados_chile.py
├── cargar_estados_colombia.py
└── cargar_estados_ecuador.py
```

#### **Documentación (13 archivos):**
```
docs/
├── INDICE_UBICACIONES.md
├── README_UBICACIONES.md
├── GUIA_RAPIDA_UBICACIONES.md
├── ARQUITECTURA_UBICACIONES_MULTI_PAIS.md
├── RESUMEN_ARQUITECTURA_UBICACIONES.md
├── COMPARACION_MODELOS_UBICACION.md
├── ESTRATEGIA_MIGRACION_GRADUAL.md
├── FIXTURES_VS_COMANDOS.md
├── AGREGAR_UBICACIONES_ON_THE_FLY.md
└── VERIFICACION_Y_ACTIVACION.md

ARQUITECTURA_UBICACIONES_IMPLEMENTADA.md
INFORME_FINAL_UBICACIONES.md
INFORME_FINAL_SESION_UBICACIONES.md
RESUMEN_FINAL_UBICACIONES.md
DEPLOYMENT_UBICACIONES.md  # Este archivo
```

#### **Scripts (1 archivo):**
```
scripts/
└── setup_ubicaciones.sh
```

### **🔧 Archivos MODIFICADOS (3 archivos):**
```
taller/models/ubicacion.py              # Agregados CO y EC a choices
taller/clientes/forms.py                # Agregados CO y EC a lista
taller/management/commands/
├── cargar_todas_ubicaciones.py         # Quitados emojis (encoding)
└── backfill_addresses.py               # Fix bug NoneType
```

---

## 🚀 **PASOS PARA DEPLOYMENT**

### **OPCIÓN A: Git + SSH (Recomendado)**

#### **Paso 1: Commit y Push desde local**

```bash
# En tu PC (E:\projecto\e_garage)

# 1. Ver archivos modificados
git status

# 2. Agregar archivos nuevos/modificados
git add taller/management/commands/cargar_estados_chile.py
git add taller/management/commands/cargar_estados_colombia.py
git add taller/management/commands/cargar_estados_ecuador.py
git add taller/management/commands/cargar_todas_ubicaciones.py
git add taller/management/commands/backfill_addresses.py
git add taller/models/ubicacion.py
git add taller/clientes/forms.py
git add docs/
git add scripts/setup_ubicaciones.sh
git add *.md

# 3. Commit
git commit -m "feat: Sistema de ubicaciones multi-país completo

- Agregados comandos para Chile, Colombia, Ecuador
- 858 ciudades pre-cargadas para 8 países
- Soporte completo para CO y EC en formularios
- Documentación técnica completa (13 docs)
- Fix bug en backfill_addresses (NoneType)
- Script de setup automatizado

Cobertura: CL(78), US(542), BR(22), MX(53), PE(16), VE(20), CO(81), EC(46)
"

# 4. Push
git push origin main  # o tu rama
```

---

#### **Paso 2: Pull y activar en servidor**

```bash
# SSH al servidor
ssh usuario@tuservidor.com

# Ir al directorio del proyecto
cd /ruta/a/e_garage

# 1. Pull de cambios
git pull origin main

# 2. Activar entorno virtual (si usas)
source venv/bin/activate

# 3. Verificar modelos (NO requiere migración nueva)
python manage.py check

# 4. Cargar ubicaciones
python manage.py cargar_todas_ubicaciones

# 5. Verificar carga
python manage.py verificar_ubicaciones

# 6. Ejecutar backfill (migrar clientes)
python manage.py backfill_addresses --dry-run  # Preview
python manage.py backfill_addresses            # Ejecutar

# 7. Restart del servidor (según tu setup)
sudo systemctl restart gunicorn
# o
sudo supervisorctl restart egarage
# o
touch /path/to/wsgi.py  # Reload
```

---

### **OPCIÓN B: Subir archivos manualmente (Si no usas Git)**

#### **Paso 1: Comprimir archivos**

```bash
# En PowerShell (tu PC)
cd E:\projecto\e_garage

# Comprimir solo archivos necesarios
Compress-Archive -Path `
    taller/management/commands/cargar_estados_chile.py, `
    taller/management/commands/cargar_estados_colombia.py, `
    taller/management/commands/cargar_estados_ecuador.py, `
    taller/management/commands/cargar_todas_ubicaciones.py, `
    taller/management/commands/backfill_addresses.py, `
    taller/models/ubicacion.py, `
    taller/clientes/forms.py, `
    docs/, `
    scripts/setup_ubicaciones.sh `
    -DestinationPath ubicaciones_update.zip -Force
```

#### **Paso 2: Subir al servidor**

```bash
# Subir vía SCP/SFTP
scp ubicaciones_update.zip usuario@servidor:/tmp/

# SSH al servidor
ssh usuario@servidor

# Descomprimir
cd /ruta/a/e_garage
unzip -o /tmp/ubicaciones_update.zip

# Continuar con pasos 3-7 de Opción A
```

---

## ⚠️ **IMPORTANTE: VERIFICACIONES EN SERVIDOR**

### **Antes de cargar datos:**

```bash
# 1. Verificar que modelos están bien
python manage.py shell
>>> from taller.models import Estado, Ciudad
>>> Estado.objects.count()  # Debería ser 0 o existente
>>> exit()

# 2. Check de Django
python manage.py check

# 3. Ver si ya hay datos
python manage.py verificar_ubicaciones
```

### **Si ya hay datos en producción:**

```bash
# Usar --skip-existing para no duplicar
python manage.py cargar_todas_ubicaciones --skip-existing
```

---

## 🎯 **COMANDOS EN ORDEN (SERVIDOR)**

```bash
# ============================================
# DEPLOYMENT - Sistema de Ubicaciones
# ============================================

# 1. Pull de código (o descomprimir)
git pull origin main

# 2. Activar entorno
source venv/bin/activate  # Si usas virtualenv

# 3. Verificar
python manage.py check

# 4. Cargar ubicaciones
python manage.py cargar_todas_ubicaciones --skip-existing

# 5. Verificar carga
python manage.py verificar_ubicaciones

# 6. Backfill (si hay clientes)
python manage.py backfill_addresses --dry-run
python manage.py backfill_addresses

# 7. Verificar migración
python manage.py verificar_ubicaciones

# 8. Restart servidor
sudo systemctl restart gunicorn
# o el comando que uses
```

---

## 📊 **RESULTADO ESPERADO EN SERVIDOR**

```
Después de ejecutar los comandos:

✅ 230 estados/regiones en BD
✅ 858 ciudades en BD
✅ 8 países con cobertura completa
✅ Formularios funcionando con datos reales
✅ Clientes migrados a billing_address

Verificar en navegador:
  https://tudominio.com/us/en/clientes/crear/
  - Select State → Debe mostrar 50 estados
  - Seleccionar California → Debe cargar ~100 ciudades
  - Botones "+ ADD STATE/CITY" → Deben funcionar
```

---

## 🚨 **TROUBLESHOOTING**

### **Error: "Estado matching query does not exist"**

**Causa:** No se ejecutó `cargar_todas_ubicaciones`

**Solución:**
```bash
python manage.py cargar_todas_ubicaciones
```

---

### **Error: "UnicodeEncodeError" en comandos**

**Causa:** Servidor Linux/Unix con encoding diferente

**Solución:** Ya quitamos emojis de `cargar_todas_ubicaciones.py`

Si aún falla:
```bash
export PYTHONIOENCODING=utf-8
python manage.py cargar_todas_ubicaciones
```

---

### **Problema: "Ciudades no se cargan en select"**

**Causa:** Endpoints AJAX no configurados o cache

**Verificar:**
```bash
# 1. Verificar URL
curl https://tudominio.com/taller/clientes/ajax/ciudades_usa/?estado_id=1

# 2. Verificar en navegador (F12 → Network)
# Debería ver request a /taller/clientes/ajax/ciudades_usa/

# 3. Limpiar cache
python manage.py clear_cache  # Si tienes
# O en navegador: Ctrl+Shift+R (hard reload)
```

---

## ✅ **CHECKLIST DE DEPLOYMENT**

```
PRE-DEPLOYMENT:
  ✅ Código commiteado y pusheado
  ✅ Backup de BD (por si acaso)
  ✅ Notas de release preparadas

DEPLOYMENT:
  ⏳ SSH al servidor
  ⏳ Pull de código (git pull)
  ⏳ Verificar modelos (python manage.py check)
  ⏳ Cargar ubicaciones (cargar_todas_ubicaciones)
  ⏳ Verificar datos (verificar_ubicaciones)
  ⏳ Backfill clientes (backfill_addresses)
  ⏳ Restart servidor (systemctl restart gunicorn)

POST-DEPLOYMENT:
  ⏳ Verificar en navegador (/us/en/clientes/crear/)
  ⏳ Probar crear cliente
  ⏳ Probar selects dinámicos
  ⏳ Probar modal "+ ADD CITY"
  ⏳ Verificar logs de errores

ROLLBACK (si falla):
  ⏳ git checkout HEAD~1
  ⏳ Restart servidor
```

---

## 🎯 **TIEMPO ESTIMADO**

| Paso | Tiempo |
|------|--------|
| Git pull | 1 min |
| Verificar modelos | 1 min |
| Cargar ubicaciones | 2-5 min |
| Backfill | 1-2 min |
| Restart servidor | 1 min |
| Verificación | 2 min |
| **TOTAL** | **8-12 minutos** |

---

## 🎉 **DESPUÉS DEL DEPLOYMENT**

### **Verificar que funciona:**

```
1. Ir a: https://tudominio.com/us/en/clientes/crear/
2. Select State → Debe mostrar 50 estados
3. Seleccionar "California"
4. Select City → Debe cargar ~100 ciudades vía AJAX
5. Seleccionar "Los Angeles"
6. Llenar resto del formulario
7. Guardar

Verificar en admin:
  - Cliente tiene estado_usa = "California"
  - Cliente tiene ciudad_usa = "Los Angeles"
  - Cliente tiene billing_address → Address
```

### **Probar modal "+ ADD CITY":**

```
1. Select State = "California"
2. Click "+ ADD CITY"
3. Modal se abre
4. Escribir "Santa Monica"
5. Submit
6. Modal se cierra
7. "Santa Monica" aparece en select (ya seleccionada)
8. Guardar cliente
```

**Si funciona:** ✅ Deployment exitoso

---

## 📚 **DOCUMENTACIÓN PARA EQUIPO**

Después del deployment, compartir con el equipo:

1. **[README Visual](docs/README_UBICACIONES.md)** - Intro al sistema
2. **[Guía Rápida](docs/GUIA_RAPIDA_UBICACIONES.md)** - Cómo usar

---

## ✅ **RESUMEN**

```
ARCHIVOS A SUBIR:
  • 3 comandos nuevos
  • 13 documentos
  • 1 script
  • 3 actualizaciones

COMANDOS A EJECUTAR:
  1. git pull (o subir archivos)
  2. python manage.py cargar_todas_ubicaciones
  3. python manage.py verificar_ubicaciones
  4. python manage.py backfill_addresses
  5. Restart servidor

TIEMPO TOTAL:
  8-12 minutos

RESULTADO:
  ✅ 858 ciudades disponibles
  ✅ Formularios funcionando
  ✅ Modales on-the-fly
```

---

**¿Listo para deployment?** 🚀

