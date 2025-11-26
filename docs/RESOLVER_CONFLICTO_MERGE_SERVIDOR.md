# 🔧 Resolver Conflicto de Merge en el Servidor

## Problema

El archivo `taller/documentos/views.py` tiene marcadores de conflicto de Git sin resolver:
```
<<<<<<< Updated upstream
```

## Solución: Resetear a origin/main

En el servidor, ejecuta estos comandos para obtener la versión limpia del repositorio:

```bash
cd ~/apps/egarage/current

# 1. Ver qué cambios locales hay (opcional, para referencia)
git status

# 2. Mover archivos no rastreados que entran en conflicto
mkdir -p ~/backup_servidor_$(date +%Y%m%d)
mv taller/urls_extra/colombia.py ~/backup_servidor_$(date +%Y%m%d)/ 2>/dev/null || true
mv taller/urls_extra/ecuador.py ~/backup_servidor_$(date +%Y%m%d)/ 2>/dev/null || true
mv templates/onboarding/bienvenida_colombia.html ~/backup_servidor_$(date +%Y%m%d)/ 2>/dev/null || true
mv templates/onboarding/bienvenida_ecuador.html ~/backup_servidor_$(date +%Y%m%d)/ 2>/dev/null || true

# 3. Resetear completamente a origin/main (elimina todos los cambios locales)
git fetch origin
git reset --hard origin/main

# 4. Limpiar archivos no rastreados
git clean -fd
```

## Después de Resolver

1. Reinicia la aplicación web en PythonAnywhere (botón "Reload" en la pestaña Web)
2. Prueba crear un vehículo con Chevrolet y Camaro
3. Si el error persiste, revisa los logs:
   ```bash
   tail -f logs/django.log | grep -i "clean\|coherencia\|marca\|modelo"
   ```

## Nota

⚠️ **CUIDADO**: `git reset --hard origin/main` eliminará TODOS los cambios locales que no estén en el repositorio remoto. Si necesitas conservar algún cambio local, hazlo antes de ejecutar este comando.



