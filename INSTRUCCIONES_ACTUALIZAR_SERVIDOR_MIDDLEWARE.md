# Instrucciones para Actualizar el Servidor y Eliminar AccountMiddleware

## Problema
El servidor está intentando cargar `allauth.account.middleware.AccountMiddleware` que no existe en la versión instalada de `django-allauth`.

## Solución
Se han eliminado completamente todos los intentos de agregar este middleware en los archivos de configuración.

## Pasos para Actualizar el Servidor

### Opción 1: Usar el Script Automático (Recomendado)

1. **Subir el script al servidor:**
   ```bash
   scp actualizar_servidor_middleware.sh atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/
   ```

2. **Conectarse al servidor:**
   ```bash
   ssh atlantareciclajes@ssh.pythonanywhere.com
   ```

3. **Ejecutar el script:**
   ```bash
   chmod +x ~/actualizar_servidor_middleware.sh
   cd /home/atlantareciclajes/apps/egarage/current
   ~/actualizar_servidor_middleware.sh
   ```

### Opción 2: Comandos Manuales

1. **Conectarse al servidor:**
   ```bash
   ssh atlantareciclajes@ssh.pythonanywhere.com
   ```

2. **Ir al directorio del proyecto:**
   ```bash
   cd /home/atlantareciclajes/apps/egarage/current
   ```

3. **Actualizar código desde Git:**
   ```bash
   git pull origin main --no-rebase
   ```

4. **Verificar que no queden referencias:**
   ```bash
   grep -n "AccountMiddleware" gestion_taller/settings.py gestion_taller/settings/base.py gestion_taller/compacto/settings.py
   ```

5. **Si aún hay referencias, eliminarlas manualmente:**
   ```bash
   sed -i '/AccountMiddleware/d' gestion_taller/settings.py
   sed -i '/AccountMiddleware/d' gestion_taller/settings/base.py
   sed -i '/AccountMiddleware/d' gestion_taller/compacto/settings.py
   ```

6. **Reiniciar el servidor WSGI:**
   ```bash
   touch /var/www/www_egarage_cl_wsgi.py
   ```

## Verificación

Después de actualizar, verifica que el servidor esté funcionando correctamente:

1. Visita `https://www.egarage.cl/`
2. Revisa los logs de error en PythonAnywhere
3. Si hay errores, verifica que no queden referencias a `AccountMiddleware`:
   ```bash
   grep -r "AccountMiddleware" gestion_taller/
   ```

## Nota

Los cambios ya están en el repositorio Git. El servidor solo necesita hacer `git pull` para obtenerlos.

