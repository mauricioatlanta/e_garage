# 🚀 Variables de Entorno para Render

## Variables Requeridas en Render Dashboard

### Django Core
```
DJANGO_SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-service.onrender.com,localhost,127.0.0.1
```

### Base de Datos
```
DATABASE_URL=postgresql://user:password@host:port/database
```
*Nota: Se genera automáticamente al crear PostgreSQL en Render*

### Configuración Regional
```
LANGUAGE_CODE=es
TIME_ZONE=America/Santiago
```

### Email (Opcional)
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@egarage.com
```

## 🔧 Cómo Configurar en Render

1. **Ir a Dashboard → Environment**
2. **Agregar cada variable** con su valor correspondiente
3. **DATABASE_URL** se configura automáticamente al crear PostgreSQL
4. **SECRET_KEY** generar con: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

## ✅ Verificación

Después del despliegue, verificar que funcionen:
- `/admin/` - Panel de administración
- `/bienvenida/cl/` - Landing Chile
- `/bienvenida/usa/` - Landing USA
