# 🔍 Encontrar el Proyecto en el Servidor

Si no encuentras `manage.py`, sigue estos pasos:

## Método 1: Buscar manage.py

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
ls -la ~/egarage 2>/dev/null
ls -la ~/apps/egarage/current 2>/dev/null
ls -la ~/mysite 2>/dev/null
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
cd /home/atlantareciclajes/ruta_encontrada

# Verifica que estás en el lugar correcto
ls -la manage.py
pwd  # Muestra la ruta actual

# Ahora puedes ejecutar comandos Django
python3.10 manage.py cargar_marcas_usa
```

## Ejemplo de rutas comunes:

- `/home/atlantareciclajes/egarage/`
- `/home/atlantareciclajes/apps/egarage/current/`
- `/home/atlantareciclajes/mysite/`
- `/home/atlantareciclajes/webapp/`



