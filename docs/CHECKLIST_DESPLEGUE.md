# ✅ Checklist de Despliegue - eGarage

**Fecha:** Diciembre 2024  
**Versión:** 1.0  
**Estado:** Listo para Producción

---

## 🎯 Checklist Rápido

### Pre-Despliegue

- [ ] Cuenta de PythonAnywhere creada
- [ ] Base de datos MySQL creada en PythonAnywhere
- [ ] Base de datos configurada con `utf8mb4` (ver SQL abajo)
- [ ] Archivo `.env` preparado con todas las variables
- [ ] SSL/HTTPS activado en PythonAnywhere

### Despliegue

- [ ] Clonar repositorio: `git clone <repo> egarage`
- [ ] Crear archivo `.env` en `/home/tu_usuario/egarage/.env`
- [ ] Configurar archivo WSGI: `/var/www/tu_usuario_pythonanywhere_com_wsgi.py`
  - [ ] Incluir `load_dotenv()` ANTES de `get_wsgi_application()`
- [ ] Instalar dependencias: `pip3.10 install -r requirements.txt`
- [ ] Ejecutar migraciones: `python3.10 manage.py migrate`
- [ ] Recolectar estáticos: `python3.10 manage.py collectstatic --noinput`
- [ ] Crear superusuario: `python3.10 manage.py createsuperuser`
- [ ] Configurar web app en PythonAnywhere (pestaña "Web")
  - [ ] Source code: `/home/tu_usuario/egarage`
  - [ ] Working directory: `/home/tu_usuario/egarage`
  - [ ] WSGI file: `/var/www/tu_usuario_pythonanywhere_com_wsgi.py`
  - [ ] Static files: `/static/` → `/home/tu_usuario/egarage/staticfiles`
  - [ ] Media files: `/media/` → `/home/tu_usuario/egarage/media`
- [ ] Reiniciar web app

### Post-Despliegue

- [ ] Verificar que el sitio carga: `https://tu-dominio.com`
- [ ] Verificar archivos estáticos: `https://tu-dominio.com/static/admin/css/base.css`
- [ ] Verificar HTTPS: `http://tu-dominio.com` → redirige a `https://`
- [ ] Verificar registro desde diferentes países
- [ ] Verificar que emails se envían correctamente
- [ ] Verificar logs de errores (si hay errores 500)

---

## 🔧 Comandos SQL para Base de Datos

### Verificar codificación actual

```sql
SHOW CREATE DATABASE tu_nombre_de_db;
```

### Configurar utf8mb4

```sql
ALTER DATABASE tu_nombre_de_db 
    CHARACTER SET = utf8mb4 
    COLLATE = utf8mb4_unicode_ci;
```

### Verificar que se aplicó

```sql
SHOW CREATE DATABASE tu_nombre_de_db;
-- Debe mostrar: DEFAULT CHARACTER SET utf8mb4
```

---

## 📝 Template de Archivo WSGI

Copia a: `/var/www/tu_usuario_pythonanywhere_com_wsgi.py`

```python
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

project_home = '/home/tu_usuario/egarage'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# ✅ CRÍTICO: Cargar .env ANTES de Django
env_path = Path(project_home) / '.env'
load_dotenv(env_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

---

## 🐛 Troubleshooting Rápido

### Error 500

1. Ver logs: `/var/log/tu_usuario.pythonanywhere.com.error.log`
2. Verificar que WSGI carga `.env` antes de Django
3. Verificar variables en `.env`

### Archivos estáticos 404

1. Ejecutar: `python3.10 manage.py collectstatic --noinput`
2. Verificar ruta en PythonAnywhere: `/home/tu_usuario/egarage/staticfiles`
3. Reiniciar web app

### Error de conexión MySQL

1. Verificar host: `tu_usuario.mysql.pythonanywhere-services.com`
2. Verificar nombre DB: `tu_usuario$egarage_db`
3. Verificar credenciales en pestaña "Databases"

---

**📌 Para más detalles, consulta:** [`DESPLEGUE_PYTHONANYWHERE.md`](./DESPLEGUE_PYTHONANYWHERE.md)



