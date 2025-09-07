# 🧹 Instrucciones de Limpieza y Despliegue en Render - eGarage

## 📋 Resumen Ejecutivo

Este documento contiene las instrucciones completas para:
1. **Limpiar** el proyecto eliminando archivos temporales y de prueba
2. **Reorganizar** la estructura del proyecto
3. **Desplegar** en Render con configuración optimizada

---

## 🎯 Paso 1: Ejecutar Script de Auditoría

### 1.1 Generar informe de limpieza (modo simulación)
```bash
cd E:/projecto/e_garage
python tools/audit_and_cleanup.py --root E:/projecto/e_garage
```

### 1.2 Revisar el informe generado
- Se creará un archivo `eg_cleanup_report_YYYY-MM-DD_HHMMSS.md`
- Revisa qué archivos se moverán y dónde
- Verifica que no se muevan archivos importantes

### 1.3 Aplicar la limpieza
```bash
python tools/audit_and_cleanup.py --root E:/projecto/e_garage --apply
```

**Resultado esperado:**
- Archivos movidos a `/scripts/` (scripts de carga, debug, etc.)
- Archivos movidos a `/docs/` (todos los .md)
- Archivos movidos a `/_backup/` (backups y versiones finales)
- Raíz del proyecto limpia con solo estructura Django

---

## 🏗️ Paso 2: Preparar para Render

### 2.1 Verificar archivos creados
Asegúrate de que estos archivos estén en la raíz:
- ✅ `render.yaml` - Configuración de Render
- ✅ `requirements.txt` - Actualizado para PostgreSQL
- ✅ `gestion_taller/settings/production.py` - Settings para producción

### 2.2 Crear directorio de logs (opcional)
```bash
mkdir logs
echo "# Logs de producción" > logs/README.md
```

### 2.3 Verificar estructura final
Tu proyecto debería verse así:
```
e_garage/
├── manage.py
├── render.yaml
├── requirements.txt
├── gestion_taller/
│   ├── settings/
│   │   ├── base.py
│   │   ├── production.py  # ← NUEVO
│   │   └── ...
│   └── wsgi.py
├── core/
├── taller/
├── frontend/
├── templates/
├── static/
├── media/
├── scripts/          # ← Archivos movidos aquí
├── docs/             # ← Archivos .md movidos aquí
├── _backup/          # ← Backups movidos aquí
└── tools/
    └── audit_and_cleanup.py
```

---

## 🚀 Paso 3: Desplegar en Render

### 3.1 Preparar repositorio Git
```bash
# Crear rama para limpieza
git checkout -b chore/cleanup-render

# Agregar archivos nuevos
git add render.yaml
git add gestion_taller/settings/production.py
git add requirements.txt
git add tools/audit_and_cleanup.py
git add INSTRUCCIONES_LIMPIEZA_RENDER.md

# Commit de limpieza
git add .
git commit -m "chore: cleanup root; add render.yaml; enable whitenoise; prod settings"

# Push a GitHub
git push origin chore/cleanup-render
```

### 3.2 Crear Pull Request
1. Ve a GitHub
2. Crea PR desde `chore/cleanup-render` a `main`
3. Revisa los cambios
4. Mergea el PR

### 3.3 Configurar Render

#### 3.3.1 Crear cuenta en Render
1. Ve a [render.com](https://render.com)
2. Regístrate con tu cuenta de GitHub
3. Conecta tu repositorio

#### 3.3.2 Desplegar con Blueprint
1. En Render Dashboard → **New** → **Blueprint**
2. Selecciona tu repositorio `e_garage`
3. Render detectará automáticamente `render.yaml`
4. Haz clic en **Apply**

#### 3.3.3 Configuración automática
Render creará automáticamente:
- ✅ **Web Service** (egarage-web)
- ✅ **PostgreSQL Database** (egarage-db)
- ✅ **Persistent Disk** para media files
- ✅ Variables de entorno configuradas

### 3.4 Verificar despliegue

#### 3.4.1 Monitorear build
1. Ve a la pestaña **Logs** del servicio web
2. Verifica que:
   - ✅ `pip install` se ejecute correctamente
   - ✅ `collectstatic` se ejecute sin errores
   - ✅ `migrate` se ejecute en postDeploy
   - ✅ `gunicorn` inicie correctamente

#### 3.4.2 Probar aplicación
1. Ve a la URL del servicio (ej: `https://eggarage-web.onrender.com`)
2. Verifica que:
   - ✅ La página principal cargue
   - ✅ `/admin/` funcione
   - ✅ `/cl/` y `/us/` funcionen
   - ✅ Subir archivos funcione (media files)

---

## 🔧 Paso 4: Configuración Adicional (Opcional)

### 4.1 Dominio personalizado
1. En Render → **Settings** → **Custom Domains**
2. Agrega tu dominio (ej: `egarage.com`)
3. Render maneja SSL automáticamente

### 4.2 Variables de entorno adicionales
Si necesitas configurar email o otros servicios:
```bash
# En Render Dashboard → Environment
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
DEFAULT_FROM_EMAIL=noreply@egarage.com
```

### 4.3 Health Check
1. En Render → **Settings** → **Health Check**
2. Configura **Health Check Path** → `/admin/login/`
3. Esto asegura que Render detecte si la app está funcionando

---

## 🚨 Solución de Problemas Comunes

### Problema: Error en collectstatic
**Solución:**
```bash
# Verificar que WhiteNoise esté en MIDDLEWARE
# En gestion_taller/settings/production.py
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # ← Debe estar aquí
    # ... resto del middleware
]
```

### Problema: Error de base de datos
**Solución:**
```bash
# Verificar que dj-database-url esté instalado
# En requirements.txt debe estar:
psycopg2-binary==2.9.9
dj-database-url==2.1.0
```

### Problema: Media files no persisten
**Solución:**
```bash
# Verificar que el disk esté montado correctamente
# En render.yaml debe estar:
disk:
  name: media
  mountPath: /opt/render/project/src/media
  sizeGB: 2
```

### Problema: Error 500 en producción
**Solución:**
1. Revisar logs en Render Dashboard
2. Verificar que `DEBUG = False` en production.py
3. Verificar que `ALLOWED_HOSTS` incluya tu dominio

---

## ✅ Checklist Final

### Antes del despliegue:
- [ ] Script de limpieza ejecutado
- [ ] Archivos reorganizados correctamente
- [ ] `render.yaml` en la raíz
- [ ] `requirements.txt` actualizado para PostgreSQL
- [ ] `production.py` configurado con WhiteNoise
- [ ] Código commiteado y pusheado a GitHub

### Después del despliegue:
- [ ] Build exitoso en Render
- [ ] Migraciones ejecutadas
- [ ] Página principal carga correctamente
- [ ] Admin funciona
- [ ] Rutas por país funcionan (/cl/, /us/)
- [ ] Subida de archivos funciona
- [ ] Logs sin errores críticos

---

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs en Render Dashboard
2. Verifica la configuración en `render.yaml`
3. Confirma que las variables de entorno estén configuradas
4. Revisa que `production.py` tenga la configuración correcta

---

## 🎉 ¡Listo!

Tu proyecto eGarage ahora está:
- ✅ **Limpio** y organizado
- ✅ **Desplegado** en Render
- ✅ **Escalable** para 500+ suscriptores
- ✅ **Optimizado** para producción

**URL de tu aplicación:** `https://eggarage-web.onrender.com`
