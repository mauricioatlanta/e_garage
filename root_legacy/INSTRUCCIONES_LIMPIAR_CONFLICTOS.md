# Instrucciones para Limpiar Conflictos en el Servidor

## Problema
El archivo `taller/documentos/views.py` en el servidor tiene marcadores de conflicto de merge en la línea 336:
```
<<<<<<< Updated upstream
```

## Solución Rápida (Comando de una línea)

Ejecuta este comando completo en el servidor:

```bash
cd /home/atlantareciclajes/apps/egarage/current && sed -i '/^<<<<<<</d; /^=======$/d; /^>>>>>>>/d' taller/documentos/views.py && python3 -m py_compile taller/documentos/views.py && touch /var/www/www_egarage_cl_wsgi.py && echo "✅ Listo"
```

## Solución con Script Python (Más Segura)

1. **Subir el script al servidor:**
   ```bash
   scp limpiar_conflictos.py atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/
   ```

2. **Conectarse al servidor:**
   ```bash
   ssh atlantareciclajes@ssh.pythonanywhere.com
   ```

3. **Ejecutar el script:**
   ```bash
   cd /home/atlantareciclajes/apps/egarage/current
   python3 ~/limpiar_conflictos.py
   touch /var/www/www_egarage_cl_wsgi.py
   ```

## Solución Restaurando desde Git

Si las soluciones anteriores no funcionan, restaura el archivo desde Git:

```bash
cd /home/atlantareciclajes/apps/egarage/current
git checkout HEAD -- taller/documentos/views.py
touch /var/www/www_egarage_cl_wsgi.py
```

## Verificación

Después de ejecutar cualquiera de las soluciones, verifica que el servidor esté funcionando:
- Visita `https://www.egarage.cl/`
- Revisa los logs de error en PythonAnywhere
- Verifica que no haya más errores de sintaxis



