# 🚀 Cargar Servicios en el Servidor de Producción

## Problema
Los servicios no aparecen en `https://www.egarage.cl/us/servicios/` porque no están cargados en la base de datos del servidor.

## Solución

### Paso 1: Conectarse al servidor PythonAnywhere

1. Accede a tu cuenta de PythonAnywhere
2. Abre una consola Bash (pestaña "Consoles")
3. **Encuentra la ubicación del proyecto:**
   
   Primero, verifica dónde está el proyecto. Puede estar en diferentes ubicaciones:
   ```bash
   # Opción 1: Buscar el archivo manage.py
   find ~ -name "manage.py" -type f 2>/dev/null
   
   # Opción 2: Verificar directorios comunes
   ls -la ~/
   ls -la ~/mysite
   ls -la ~/egarage
   
   # Opción 3: Verificar desde la configuración web
   # Ve a la pestaña "Web" y revisa la ruta del "Source code"
   ```

4. **Navega al directorio del proyecto:**
   
   Si tienes múltiples releases (como `/home/tu_usuario/apps/egarage/releases/...`):
   ```bash
   # Opción A: Si hay un symlink 'current' que apunta a la versión activa
   cd ~/apps/egarage/current
   
   # Opción B: Si no hay symlink, usa la release más reciente
   cd ~/apps/egarage/releases/2025-11-17_1615_eg
   
   # Opción C: Verificar qué release está activa desde la configuración Web
   # Ve a la pestaña "Web" y revisa la ruta del "Source code"
   
   # Verifica que estás en el lugar correcto
   ls -la manage.py
   pwd  # Muestra la ruta actual
   ```

### Paso 2: Ejecutar el comando de carga de servicios

Ejecuta el siguiente comando para cargar servicios básicos para todas las empresas:

```bash
# Si hay errores de validación, usar --skip-checks
python3.10 manage.py cargar_servicios_produccion --skip-checks
```

Este comando:
- ✅ Crea categorías y subcategorías para CL (Chile) y US (USA)
- ✅ Crea servicios básicos para cada empresa según su país
- ✅ Asocia los servicios a las empresas correspondientes

### Paso 3: Verificar la carga

Después de ejecutar el comando, verifica que los servicios se cargaron correctamente:

```bash
python3.10 manage.py shell
```

En el shell de Django:
```python
from taller.servicios.models import Servicio, CategoriaServicio
from taller.models import Empresa

# Ver total de servicios
print(f"Total servicios: {Servicio.objects.count()}")

# Ver servicios por país
print(f"Servicios CL: {Servicio.objects.filter(categoria__country='CL').count()}")
print(f"Servicios US: {Servicio.objects.filter(categoria__country='US').count()}")

# Ver servicios por empresa
for empresa in Empresa.objects.all():
    count = Servicio.objects.filter(empresa=empresa).count()
    print(f"{empresa.nombre} ({empresa.pais}): {count} servicios")

exit()
```

### Paso 4: Reiniciar la aplicación web

Después de cargar los servicios, reinicia la aplicación web en PythonAnywhere:

1. Ve a la pestaña **"Web"**
2. Haz clic en el botón **"Reload"** o **"Restart"**

### Paso 5: Verificar en el navegador

Visita `https://www.egarage.cl/us/servicios/` y verifica que los servicios aparecen correctamente.

## Servicios que se cargan

El comando carga los siguientes servicios básicos:

### Para Chile (CL) y USA (US):

1. **Sistema de Motor**
   - Diagnóstico computarizado
   - Cambio de aceite y filtros
   - Reparación de motor

2. **Sistema de Frenos**
   - Revisión de frenos
   - Reparación de frenos

3. **Transmisión**
   - Mantenimiento de transmisión
   - Reparación de transmisión

4. **Suspensión y Dirección**
   - Alineación
   - Reparación de suspensión

5. **Sistema Eléctrico**
   - Batería y carga
   - Sistema de iluminación

6. **Servicios Especiales**
   - Preparación para revisión técnica
   - Instalación de accesorios
   - Lavado y detallado

7. **Emergencias y Servicios Móviles**
   - Asistencia en ruta
   - Servicio móvil

## Notas Importantes

- ⚠️ El comando crea servicios **solo para empresas que ya existen** en la base de datos
- ⚠️ Los servicios se crean según el país de cada empresa (CL o US)
- ⚠️ Si una empresa no tiene país configurado, no se crearán servicios para ella
- ⚠️ El comando es **idempotente**: puedes ejecutarlo múltiples veces sin duplicar datos

## Troubleshooting

### Error: "No hay empresas en la base de datos"
- Asegúrate de que hay al menos una empresa creada
- Verifica que las empresas tengan el campo `pais` configurado (CL o US)

### Los servicios no aparecen en la página
- Verifica que reiniciaste la aplicación web
- Verifica que la empresa del usuario tiene servicios asociados
- Revisa los logs de errores en PythonAnywhere

### Servicios duplicados
- El comando usa `get_or_create`, por lo que no debería crear duplicados
- Si hay duplicados, puedes limpiarlos manualmente desde el admin de Django

## Comandos Adicionales

### Ver servicios de una empresa específica
```bash
python3.10 manage.py shell
```
```python
from taller.models import Empresa
from taller.servicios.models import Servicio

empresa = Empresa.objects.get(nombre="Nombre de tu empresa")
servicios = Servicio.objects.filter(empresa=empresa)
for s in servicios:
    print(f"- {s.nombre}")
```

### Limpiar servicios (CUIDADO: borra todos los servicios)
```bash
python3.10 manage.py shell
```
```python
from taller.servicios.models import Servicio
Servicio.objects.all().delete()
# Luego ejecuta de nuevo: python3.10 manage.py cargar_servicios_produccion
```

