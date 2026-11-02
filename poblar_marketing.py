import os
import django

# Inicializar entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.empresa import Empresa
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.pieza_desarme import PiezaDesarme
from taller.models.compatibility import PartApplication

print("--- Iniciando población de datos de marketing para Interchange ---")

# Tomamos directamente la primera empresa disponible en la base de datos
empresa = Empresa.objects.first()

if not empresa:
    # Si no hay ninguna empresa, creamos una de prueba para la cuenta
    empresa = Empresa.objects.create(
        nombre="Desarmaduría y Repuestos Mauricio",
        rut="76.543.210-k"
    )
    print(f"Empresa de prueba creada: {empresa.nombre}")
else:
    print(f"Empresa seleccionada: {empresa.nombre} (ID: {empresa.id})")

# Crear un vehículo donante base para las piezas de patio/bodega
vehiculo_donante, _ = VehiculoDesarme.objects.get_or_create(
    empresa=empresa,
    defaults={
        "marca_texto": "Vehículo",
        "modelo_texto": "Multimarca Donante",
        "anio": 2018
    }
)

# Definir los 5 repuestos
repuestos_data = [
    {
        "codigo": "BOM-001",
        "nombre": "Bomba de Combustible Eléctrica Universal",
        "precio": 35000,
        "ubicacion": "Estante B-1, Repisa 3",
        "compatibilidades": [
            ("Chevrolet", "Sail", 2012, 2020),
            ("Hyundai", "Accent", 2011, 2019),
            ("Kia", "Rio", 2012, 2018)
        ]
    },
    {
        "codigo": "ALT-002",
        "nombre": "Alternador de 90A",
        "precio": 85000,
        "ubicacion": "Estante C-2, Repisa 1",
        "compatibilidades": [
            ("Toyota", "Yaris", 2014, 2021),
            ("Nissan", "Versa", 2015, 2022),
            ("Suzuki", "Swift", 2013, 2020)
        ]
    },
    {
        "codigo": "BOB-003",
        "nombre": "Bobina de Encendido",
        "precio": 28000,
        "ubicacion": "Patio, Fila 2 (Motor Donante)",
        "compatibilidades": [
            ("Peugeot", "206", 2006, 2012),
            ("Citroen", "C3", 2007, 2015),
            ("Renault", "Clio", 2008, 2016)
        ]
    },
    {
        "codigo": "CUE-004",
        "nombre": "Cuerpo de Aceleración Electrónico",
        "precio": 65000,
        "ubicacion": "Estante A-4, Repisa 4",
        "compatibilidades": [
            ("Chevrolet", "Spark GT", 2011, 2018),
            ("Daewoo", "Lanos", 2000, 2005),
            ("Suzuki", "Alto", 2012, 2021)
        ]
    },
    {
        "codigo": "MOT-005",
        "nombre": "Motor de Partida / Burro de Arranque",
        "precio": 75000,
        "ubicacion": "Patio, Fila 5 (Montado en chasis)",
        "compatibilidades": [
            ("Nissan", "Tiida", 2007, 2014),
            ("Renault", "Megane", 2006, 2012),
            ("Nissan", "Sentra", 2008, 2015)
        ]
    }
]

for item in repuestos_data:
    pieza, created = PiezaDesarme.objects.update_or_create(
        empresa=empresa,
        codigo=item["codigo"],
        defaults={
            "vehiculo_desarme": vehiculo_donante,
            "nombre": item["nombre"],
            "precio_venta_sugerido": item["precio"],
            "ubicacion_fisica": item["ubicacion"],
            "estado_pieza": "disponible",
            "activo": True,
            "publicada": True,
            "cantidad": 1
        }
    )
    
    PartApplication.objects.filter(codigo_pieza=item["codigo"]).delete()
    
    for marca, modelo, anio_d, anio_h in item["compatibilidades"]:
        PartApplication.objects.create(
            codigo_pieza=item["codigo"],
            marca=marca,
            modelo=modelo,
            anio_desde=anio_d,
            anio_hasta=anio_h,
            fuente="marketing_interchange",
            nivel_confianza=10,
            activo=True
        )

print("\n--- ¡Población completada con éxito! ---")
print("\nResumen de repuestos listos en tu base de datos:")
for item in repuestos_data:
    print(f" * [{item['codigo']}] {item['nombre']} | Precio: ${item['precio']:,} | Ubicación: {item['ubicacion']}")

print("\nPuedes revisar la vitrina o tu tienda web en las rutas de tu proyecto (ej: /tienda/ o /catalogo/) para ver los precios, ubicaciones y realizar las capturas de pantalla para tu posteo.")
