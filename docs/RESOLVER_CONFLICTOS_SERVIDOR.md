# 🔧 Resolver Conflictos en el Servidor

## Problema

Hay cambios locales en el servidor que entran en conflicto con los cambios remotos.

## Solución Recomendada

En el servidor, generalmente queremos mantener los cambios del repositorio remoto. 

### Opción 1: Stash de cambios locales (Recomendado)

```bash
cd ~/apps/egarage/current

# Guardar cambios locales en stash
git stash push -m "Cambios locales del servidor antes de pull"

# Hacer pull
git pull origin main --no-rebase

# Si necesitas recuperar los cambios locales después:
# git stash pop
```

### Opción 2: Resetear a origin/main (Si no necesitas los cambios locales)

⚠️ **CUIDADO**: Esto eliminará todos los cambios locales.

```bash
cd ~/apps/egarage/current

# Ver qué cambios se perderán
git status

# Resetear a origin/main
git fetch origin
git reset --hard origin/main
```

### Opción 3: Mover archivos no rastreados

Si hay archivos no rastreados que entran en conflicto:

```bash
cd ~/apps/egarage/current

# Mover archivos no rastreados a un backup
mkdir -p ~/backup_servidor_$(date +%Y%m%d)
mv taller/urls_extra/colombia.py ~/backup_servidor_$(date +%Y%m%d)/
mv taller/urls_extra/ecuador.py ~/backup_servidor_$(date +%Y%m%d)/
mv templates/onboarding/bienvenida_colombia.html ~/backup_servidor_$(date +%Y%m%d)/
mv templates/onboarding/bienvenida_ecuador.html ~/backup_servidor_$(date +%Y%m%d)/

# Luego hacer stash y pull
git stash push -m "Cambios locales del servidor"
git pull origin main --no-rebase
```

## Después de Resolver

1. Reinicia la aplicación web en PythonAnywhere
2. Prueba crear un vehículo con Chevrolet y Camaro
3. Revisa los logs si el error persiste



