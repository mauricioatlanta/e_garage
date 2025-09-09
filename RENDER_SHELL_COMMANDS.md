# 🚀 Comandos para Render Shell

## 📋 Comandos a ejecutar después del primer despliegue

### 1. Migraciones
```bash
python manage.py migrate
```

### 2. Crear Superusuario
```bash
python manage.py createsuperuser
```
*Seguir las instrucciones para crear usuario admin*

### 3. Collectstatic (si no se ejecutó automáticamente)
```bash
python manage.py collectstatic --noinput
```

### 4. Verificar configuración
```bash
python manage.py check --settings=gestion_taller.settings.production
```

## 🔍 Smoke Test - URLs a verificar

Después del despliegue, verificar que funcionen:

- **Admin**: `https://your-service.onrender.com/admin/`
- **Chile**: `https://your-service.onrender.com/bienvenida/cl/`
- **USA**: `https://your-service.onrender.com/bienvenida/usa/`

## 📊 Monitoreo

- **Logs**: Render Dashboard → Logs
- **Métricas**: Render Dashboard → Metrics
- **Base de datos**: Render Dashboard → PostgreSQL

## 🚨 Troubleshooting

Si algo falla:
1. Revisar logs en Render Dashboard
2. Verificar variables de entorno
3. Ejecutar `python manage.py check` en Shell
4. Verificar que DATABASE_URL esté configurado
