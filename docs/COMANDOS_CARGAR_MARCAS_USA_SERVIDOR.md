# 🚗 Cargar Marcas USA en el Servidor

## Ubicación del Proyecto

El proyecto está en: `/home/atlantareciclajes/apps/egarage/`

## Pasos para cargar marcas USA

### 1. Navegar al directorio del proyecto

```bash
# Opción A: Si hay un symlink 'current'
cd ~/apps/egarage/current

# Opción B: Si no hay symlink, usar el release más reciente
cd ~/apps/egarage/releases/2025-11-17_1615_eg
```

### 2. Verificar que estás en el lugar correcto

```bash
ls -la manage.py
pwd
```

### 3. Ejecutar el comando para cargar marcas USA

```bash
python3.10 manage.py cargar_marcas_usa
```

### 4. Verificar que se cargaron las marcas

```bash
python3.10 manage.py shell
```

Luego en el shell de Django:
```python
from taller.models.marca import Marca
total = Marca.objects.filter(country='US').count()
print(f"Total marcas USA: {total}")
Marca.objects.filter(country='US').values_list('nombre', flat=True)[:10]
exit()
```

## Comando completo (todo en uno)

```bash
# Si hay symlink current
cd ~/apps/egarage/current && python3.10 manage.py cargar_marcas_usa

# O si no hay symlink, usar el release más reciente
cd ~/apps/egarage/releases/2025-11-17_1615_eg && python3.10 manage.py cargar_marcas_usa
```

## Verificar symlink 'current'

```bash
ls -la ~/apps/egarage/ | grep current
```

Si existe, será algo como:
```
lrwxrwxrwx 1 atlantareciclajes atlantareciclajes   45 Nov 17 16:15 current -> releases/2025-11-17_1615_eg
```



