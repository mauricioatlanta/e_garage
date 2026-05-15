# eGarage - Sistema de Gestión de Taller

Sistema completo de gestión para talleres mecánicos con funcionalidades avanzadas de IA, multi-país (Chile 🇨🇱 / USA 🇺🇸), y gestión de suscripciones.

## 🚀 Características Principales

- ✅ Gestión de talleres multi-empresa
- ✅ Sistema de órdenes de trabajo
- ✅ Control de inventario y repuestos
- ✅ Gestión de clientes y vehículos
- ✅ Sugerencias inteligentes con IA
- ✅ Soporte multi-país (Chile/USA)
- ✅ Sistema de suscripciones
- ✅ Reportes y estadísticas
- ✅ Autenticación con django-allauth
- ✅ API REST integrada

## 📋 Requisitos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)
- Entorno virtual (recomendado)

## 🔧 Instalación

### 1. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd e_garage
```

### 2. Crear Entorno Virtual

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Copia el archivo de ejemplo y edita con tus valores:

```bash
cp env.example .env
```

Edita el archivo `.env` y configura al menos:
- `DJANGO_SECRET_KEY` - Genera una con: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DJANGO_DEBUG=True` (para desarrollo)
- `EMAIL_PASSWORD` (si necesitas funcionalidad de email)

### 5. Aplicar Migraciones

```bash
python manage.py migrate
```

### 6. Cargar Datos Iniciales (Opcional)

```bash
# Ubicaciones de Chile y USA
python manage.py loaddata fixtures/ubicacion_cl.json
python manage.py loaddata fixtures/ubicacion_us.json

# Marcas y modelos de vehículos
python manage.py loaddata fixtures/marcas_modelos.json

# Precios de suscripción
python manage.py loaddata fixtures/precios_suscripcion_iniciales.json
```

### 7. Crear Superusuario

```bash
python manage.py createsuperuser
```

### 8. Ejecutar Servidor de Desarrollo

```bash
python manage.py runserver
```

Accede a: http://127.0.0.1:8000

## 🌐 Despliegue en Producción

### PythonAnywhere

1. Usa el archivo `WSGI_CORRECTO_PYTHONANYWHERE.py` como referencia
2. Configura las variables de entorno en el servidor
3. Instala dependencias: `pip install -r requirements.txt`
4. Ejecuta migraciones: `python manage.py migrate`
5. Recolecta archivos estáticos: `python manage.py collectstatic`

### Variables de Entorno de Producción

Asegúrate de configurar:
```bash
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<clave-segura-y-aleatoria>
DJANGO_ALLOWED_HOSTS=egarage.cl,www.egarage.cl
DJANGO_CSRF_TRUSTED_ORIGINS=https://egarage.cl,https://www.egarage.cl
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
EMAIL_PASSWORD=<tu-password-real>
SENTRY_DSN=<tu-dsn-de-sentry>  # Opcional pero recomendado
```

## 📦 Estructura del Proyecto

```
e_garage/
├── gestion_taller/      # Configuración principal de Django
├── taller/              # App principal de gestión de taller
├── ubicacion/           # Manejo de ubicaciones (países, regiones, ciudades)
├── templates/           # Templates HTML
├── static/              # Archivos estáticos (CSS, JS, imágenes)
├── fixtures/            # Datos iniciales
├── tests/               # Tests unitarios y E2E
├── manage.py            # Comando principal de Django
├── requirements.txt     # Dependencias del proyecto
└── env.example          # Ejemplo de variables de entorno
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=taller --cov=ubicacion

# Tests específicos
pytest tests/unit/
pytest tests/smoke/
```

## 🔐 Seguridad

- **NUNCA** commitear el archivo `.env` al repositorio
- Usar `DJANGO_DEBUG=False` en producción
- Configurar correctamente `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS`
- Usar HTTPS en producción (`SECURE_SSL_REDIRECT=True`)
- Configurar Sentry para monitoreo de errores

## 📝 Comandos Útiles

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recolectar archivos estáticos
python manage.py collectstatic

# Ejecutar shell de Django
python manage.py shell

# Ver rutas disponibles
python manage.py show_urls  # Requiere django-extensions
```

## 🌍 Multi-País

El sistema soporta dos países:
- 🇨🇱 Chile (CLP - Pesos Chilenos)
- 🇺🇸 USA (USD - Dólares)

El middleware `SimpleCountryRedirectMiddleware` detecta automáticamente el país del usuario y lo redirige a la versión correspondiente.

## 📧 Configuración de Email

El sistema usa `EgarageEmailBackend` personalizado que:
- Maneja errores de SMTP gracefully
- Soporta SSL/TLS
- Configurable vía variables de entorno

## 🤖 Funcionalidades de IA

El sistema incluye sugerencias inteligentes basadas en:
- Historial de vehículos
- Patrones de mantenimiento
- Marcas y modelos específicos
- Análisis predictivo

Ver `taller/ia_views.py` para más detalles.

## 📄 Licencia

[Tu licencia aquí]

## 👥 Contribuir

[Instrucciones para contribuir]

## 📞 Soporte

[Información de contacto o issues]

---

**Desarrollado con ❤️ usando Django**











