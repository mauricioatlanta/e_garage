# 🔍 Encontrar la Ubicación del Proyecto en PythonAnywhere

Si no estás seguro de dónde está el proyecto en el servidor, sigue estos pasos:

## Método 1: Buscar el archivo manage.py

```bash
find ~ -name "manage.py" -type f 2>/dev/null
```

Este comando buscará el archivo `manage.py` en tu directorio home y mostrará la ruta completa.

## Método 2: Verificar desde la configuración Web

1. Ve a la pestaña **"Web"** en PythonAnywhere
2. Busca la sección **"Source code"** o **"Code"**
3. Ahí verás la ruta del proyecto (por ejemplo: `/home/tu_usuario/mysite` o `/home/tu_usuario/egarage`)

## Método 3: Listar directorios comunes

```bash
# Ver qué hay en el directorio home
ls -la ~/

# Verificar directorios comunes
ls -la ~/mysite 2>/dev/null
ls -la ~/egarage 2>/dev/null
ls -la ~/project 2>/dev/null
```

## Método 4: Verificar desde el archivo WSGI

1. Ve a la pestaña **"Web"** en PythonAnywhere
2. Haz clic en **"WSGI configuration file"** o busca el archivo WSGI
3. Abre el archivo WSGI (generalmente en `/var/www/tu_usuario_pythonanywhere_com_wsgi.py`)
4. Busca la línea que dice `project_home = '/home/tu_usuario/...'`
5. Esa es la ruta de tu proyecto

## Una vez que encuentres la ruta:

```bash
# Navega al directorio
cd /home/tu_usuario/ruta_encontrada

# Verifica que estás en el lugar correcto
ls -la manage.py
pwd  # Muestra la ruta actual

# Ahora puedes ejecutar comandos Django
python3.10 manage.py cargar_servicios_produccion
```

## Ejemplo de rutas comunes:

- `/home/tu_usuario/mysite/`
- `/home/tu_usuario/egarage/`
- `/home/tu_usuario/project/`
- `/home/tu_usuario/webapp/`

## Si el proyecto no existe:

Si no encuentras el proyecto, puede que necesites:

1. **Clonar el repositorio:**
   ```bash
   cd ~
   git clone https://github.com/tu_usuario/egarage.git
   cd egarage
   ```

2. **O subir el proyecto manualmente** usando la pestaña "Files" en PythonAnywhere

