# 🔧 Solución al Error de NumPy/numexpr en el Servidor

## Problema
El comando falla debido a un error de compatibilidad entre NumPy 2.0 y numexpr:
```
AttributeError: _ARRAY_API not found
```

## Soluciones

### Opción 1: Ejecutar con --skip-checks (Recomendado)

```bash
python3.10 manage.py cargar_servicios_produccion --skip-checks
```

Esto evita las validaciones del sistema que causan el error de importación.

### Opción 2: Ejecutar directamente con Python (Si Opción 1 no funciona)

Si el `--skip-checks` no funciona, puedes ejecutar el código directamente:

```bash
python3.10 -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models import Empresa
from taller.servicios.models import (
    CategoriaServicio, CategoriaServicioName,
    Servicio, ServicioName,
    SubcategoriaServicio, SubcategoriaServicioName
)

# Datos básicos de servicios
categorias = [
    {
        'code': 'motor',
        'es': 'Sistema de Motor',
        'en': 'Engine System',
        'subcategorias': [
            {
                'code': 'diagnostico',
                'es': 'Diagnóstico computarizado de motor',
                'en': 'Engine Computer Diagnostics',
                'servicios': [
                    {'es': 'Diagnóstico computarizado de motor (OBD-II / fabricante)', 'en': 'OBD-II/Manufacturer Engine Scan'},
                    {'es': 'Lectura y borrado de códigos de error', 'en': 'Read and Clear Error Codes'},
                ],
            },
            {
                'code': 'aceite',
                'es': 'Cambio de aceite y filtros',
                'en': 'Oil & Filter Change',
                'servicios': [
                    {'es': 'Cambio de aceite de motor y filtros (aceite, aire, combustible, habitáculo)', 'en': 'Engine Oil & Filter Change (oil, air, fuel, cabin)'},
                    {'es': 'Cambio de aceite sintético', 'en': 'Synthetic Oil Change'},
                ],
            },
        ],
    },
    {
        'code': 'frenos',
        'es': 'Sistema de Frenos',
        'en': 'Brake System',
        'subcategorias': [
            {
                'code': 'revision',
                'es': 'Revisión de frenos',
                'en': 'Brake Inspection',
                'servicios': [
                    {'es': 'Revisión completa del sistema de frenos', 'en': 'Complete Brake System Inspection'},
                ],
            },
            {
                'code': 'reparacion',
                'es': 'Reparación de frenos',
                'en': 'Brake Repair',
                'servicios': [
                    {'es': 'Cambio de pastillas de freno', 'en': 'Brake Pad Replacement'},
                    {'es': 'Cambio de discos de freno', 'en': 'Brake Rotor Replacement'},
                ],
            },
        ],
    },
]

empresas = Empresa.objects.all()
print(f'Encontradas {empresas.count()} empresa(s)')

for country, lang, label_key in [('CL', 'es', 'es'), ('US', 'en', 'en')]:
    print(f'Poblando servicios para {country} ({lang})')
    for cat in categorias:
        cat_obj, _ = CategoriaServicio.objects.get_or_create(country=country, code=cat['code'])
        CategoriaServicioName.objects.get_or_create(
            categoria=cat_obj, language=lang, is_default=True,
            defaults={'label': cat[label_key]}
        )
        for sub in cat['subcategorias']:
            sub_obj, _ = SubcategoriaServicio.objects.get_or_create(
                categoria=cat_obj, code=sub['code'], country=country
            )
            SubcategoriaServicioName.objects.get_or_create(
                subcategoria=sub_obj, language=lang, is_default=True,
                defaults={'label': sub[label_key]}
            )
            for serv in sub['servicios']:
                for empresa in empresas:
                    if empresa.pais == country:
                        servicio, _ = Servicio.objects.get_or_create(
                            empresa=empresa, categoria=cat_obj, subcategoria=sub_obj,
                            nombre=serv[label_key]
                        )
                        ServicioName.objects.get_or_create(
                            servicio=servicio, language=lang, is_default=True,
                            defaults={'label': serv[label_key]}
                        )

print(f'Total servicios: {Servicio.objects.count()}')
"
```

### Opción 3: Downgrade de NumPy (Solo si es necesario)

Si las opciones anteriores no funcionan, puedes hacer downgrade de NumPy:

```bash
pip3.10 install --user "numpy<2"
```

**⚠️ ADVERTENCIA:** Esto puede afectar otras dependencias. Úsalo solo como último recurso.

## Verificar que funcionó

Después de ejecutar cualquiera de las opciones:

```bash
python3.10 manage.py shell --skip-checks
```

En el shell:
```python
from taller.servicios.models import Servicio
print(f"Total servicios: {Servicio.objects.count()}")
exit()
```

