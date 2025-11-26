# 🔧 Resolver Divergencia de Ramas en el Servidor

## Problema

Git indica que hay ramas divergentes entre el servidor y el repositorio remoto.

## Solución Recomendada para el Servidor

En el servidor, generalmente queremos mantener los cambios del repositorio remoto (origin/main). 

### Opción 1: Merge (Recomendado)

```bash
cd ~/apps/egarage/current
git pull origin main --no-rebase
```

O configurar el comportamiento por defecto:

```bash
git config pull.rebase false
git pull origin main
```

### Opción 2: Resetear a origin/main (Si no hay cambios locales importantes)

```bash
cd ~/apps/egarage/current
git fetch origin
git reset --hard origin/main
```

⚠️ **CUIDADO**: Esto eliminará cualquier cambio local que no esté en el repositorio remoto.

### Opción 3: Ver qué cambios locales hay

```bash
cd ~/apps/egarage/current
git log HEAD..origin/main --oneline  # Cambios en remoto que no tienes
git log origin/main..HEAD --oneline  # Cambios locales que no están en remoto
```

## Después de Resolver

1. Reinicia la aplicación web en PythonAnywhere
2. Prueba crear un vehículo con Chevrolet y Camaro
3. Revisa los logs si el error persiste



