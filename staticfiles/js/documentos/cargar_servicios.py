from taller.models import CategoriaServicio, SubcategoriaServicio, Servicio

data = {
    "Mecánica General": [
        "Cambio de aceite y filtro",
        "Revisión y cambio de bujías",
        "Cambio de correas (alternador, distribución)",
        "Alineación y balanceo",
        "Revisión y reparación de suspensión",
        "Revisión de tren delantero",
        "Cambio de amortiguadores",
        "Afinamiento mayor y menor",
        "Cambio de filtro de aire y cabina",
        "Limpieza de inyectores"
    ],
    "Frenos": [
        "Revisión de sistema de frenos",
        "Cambio de pastillas de freno",
        "Rectificación de discos",
        "Cambio de líquido de frenos",
        "Revisión de calipers y mangueras",
        "Cambio de zapatas y campanas"
    ],
    "Sistema de Refrigeración": [
        "Cambio de líquido refrigerante",
        "Reparación de radiador",
        "Cambio de termostato",
        "Revisión y cambio de bomba de agua",
        "Lavado del sistema de refrigeración"
    ],
    "Transmisión": [
        "Cambio de aceite de transmisión",
        "Reparación de caja automática",
        "Cambio de embrague",
        "Diagnóstico de caja de cambios"
    ],
    "Sistema de Escape": [
        "Reparación o reemplazo de silenciador",
        "Cambio de catalizador",
        "Instalación de cañerías de escape"
    ],
    "Eléctrico y Electrónico": [
        "Diagnóstico computarizado OBD2",
        "Revisión de alternador y arranque",
        "Cambio de batería",
        "Instalación de alarmas y cierre centralizado",
        "Revisión de fusibles y relés",
        "Reparación de luces",
        "Reparación de sistema de encendido"
    ],
    "Aire Acondicionado y Climatización": [
        "Carga de gas refrigerante",
        "Diagnóstico de climatización",
        "Cambio de filtro de habitáculo",
        "Reparación de compresor de aire"
    ],
    "Dirección y Suspensión": [
        "Revisión y cambio de rótulas",
        "Cambio de terminales de dirección",
        "Revisión de cremallera",
        "Cambio de brazos oscilantes"
    ],
    "Neumáticos": [
        "Cambio de neumáticos",
        "Parche o reparación",
        "Rotación de neumáticos",
        "Revisión de presión y desgaste"
    ],
    "Hojalatería": [
        "Desabolladura sin pintura (DSP)",
        "Reparación estructural de chasis",
        "Soldadura y reparación de carrocería",
        "Sustitución de paneles dañados",
        "Reparación de guardabarros y puertas"
    ],
    "Pintura": [
        "Pintura completa de vehículo",
        "Pintura de piezas específicas",
        "Pulido y abrillantado",
        "Pintura con cabina presurizada",
        "Tratamientos anti-rayas y cerámicos"
    ],
    "Cristales y Accesorios": [
        "Cambio de parabrisas",
        "Instalación de láminas de seguridad",
        "Cambio de plumillas",
        "Reparación de alza vidrios",
        "Instalación de accesorios (portaequipajes, sensores, cámaras)"
    ],
    "Inspección y Diagnóstico": [
        "Revisión técnica preventiva",
        "Revisión pre-compra",
        "Informe técnico digitalizado",
        "Chequeo de 40 puntos"
    ],
    "Otros Servicios": [
        "Retiro y entrega a domicilio",
        "Lavado interior y exterior",
        "Sanitización con ozono",
        "Gestión de seguro automotriz",
        "Tramitación de siniestros"
    ]
}

for categoria_nombre, servicios in data.items():
    categoria, _ = CategoriaServicio.objects.get_or_create(nombre=categoria_nombre)
    for servicio_nombre in servicios:
        subcat, _ = SubcategoriaServicio.objects.get_or_create(categoria=categoria, nombre=servicio_nombre)
        Servicio.objects.get_or_create(nombre=servicio_nombre, subcategoria=subcat)

print("✅ Categorías, subcategorías y servicios creados correctamente.")
