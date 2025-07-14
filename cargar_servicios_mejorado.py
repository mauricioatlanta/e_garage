from taller.models import CategoriaServicio, SubcategoriaServicio, Servicio

servicios_por_categoria = {
    "1. Mantenimiento Preventivo y Servicios Periódicos": [
        "Afinamiento completo (bujías, filtros, inyectores, sensores)",
        "Alineación y balanceo computarizado de ruedas",
        "Cambio de aceite y filtro (motor)",
        "Cambio de correas (distribución, alternador, accesorios)",
        "Cambio de filtro de aire",
        "Cambio de filtro de combustible",
        "Cambio de filtro de cabina (habitáculo)",
        "Chequeo y cambio de líquidos (refrigerante, frenos, hidráulico, transmisión)",
        "Diagnóstico computarizado con escáner OBD-II",
        "Inspección de suspensión, rótulas y amortiguadores",
        "Lubricación de bisagras, cerraduras y componentes móviles",
        "Revisión y ajuste del sistema de frenos",
        "Revisión de presión y estado de neumáticos",
        "Revisión del sistema de escape y catalizador",
        "Rotación cruzada de neumáticos",
        "Test de batería y sistema de carga eléctrica"
    ],
    "2. Reparaciones Mecánicas Generales": [
        "Ajuste y sincronización electrónica del motor",
        "Cambio de alternador",
        "Cambio de bomba de agua",
        "Cambio de cadena o correa de distribución",
        "Cambio de empaquetadura de culata",
        "Cambio de empaquetaduras y retenes generales",
        "Cambio de motor de arranque",
        "Cambio de pistones, anillos y metales",
        "Cambio de radiador y componentes de refrigeración",
        "Cambio de sensores (MAP, MAF, O2, temperatura, cigüeñal, etc.)",
        "Cambio de soportes de motor",
        "Diagnóstico y reparación de fallas de motor",
        "Limpieza ultrasónica de inyectores",
        "Rectificación de culata y prueba hidráulica",
        "Reparación de fugas de aceite y refrigerante",
        "Reparación de sistema de inyección (common rail, TBI)",
        "Revisión y reparación de sistema de escape (flexibles, catalizador)"
    ],
    "3. Sistema de Frenos": [
        "Cambio de cilindro maestro de frenos",
        "Cambio de discos ventilados o sólidos",
        "Cambio y purgado de líquido de frenos",
        "Cambio de mangueras y líneas de freno",
        "Cambio de pastillas de freno",
        "Cambio de tambores y zapatas",
        "Purgado y sangrado del sistema de frenos",
        "Diagnóstico y reparación de ABS",
        "Revisión y ajuste del freno de mano"
    ],
    "4. Sistema de Transmisión y Embrague": [
        "Cambio de aceite de transmisión automática (ATF)",
        "Cambio de aceite de caja mecánica",
        "Cambio de cardán y crucetas",
        "Cambio de convertidor de par",
        "Cambio de kit de embrague (disco, prensa y rodamiento)",
        "Cambio de homocinéticas internas y externas",
        "Cambio de retenes de transmisión",
        "Cambio de volante de inercia (bimasa o sólido)",
        "Reparación o reemplazo de caja de cambios"
    ],
    "5. Sistema de Suspensión y Dirección": [
        "Ajuste y calibración de dirección hidráulica o EPS",
        "Cambio de amortiguadores (gas o aceite)",
        "Cambio de axiales y terminales de dirección",
        "Cambio de bieletas estabilizadoras",
        "Cambio de brazos de suspensión (trapecios)",
        "Cambio de bujes de suspensión",
        "Cambio de cremallera o caja de dirección",
        "Cambio de espirales o resortes",
        "Reparación de sistema de dirección asistida",
        "Revisión general de alineación y geometría"
    ],
    "6. Sistema Eléctrico y Electrónico": [
        "Cambio de focos, ampolletas halógenas y LED",
        "Cambio de batería y limpieza de bornes",
        "Reparación o cambio de cableado eléctrico",
        "Cambio de fusibles, relés y cajas eléctricas",
        "Cambio de motor de partida (starter)",
        "Cambio de sensores de ABS, velocidad, reversa",
        "Diagnóstico y reparación de alternador",
        "Diagnóstico y reparación de ECU o módulos electrónicos",
        "Instalación de alarma, cierre centralizado y GPS",
        "Instalación de cámara de retroceso y sensores",
        "Instalación de luces LED o xenón",
        "Instalación de pantallas, radios y multimedia",
        "Reparación de alzavidrios eléctricos",
        "Detección y solución de cortocircuitos"
    ],
    "7. Aire Acondicionado y Climatización": [
        "Cambio de compresor de aire acondicionado",
        "Cambio de condensador y válvula de expansión",
        "Cambio de evaporador",
        "Cambio de filtro de cabina (polen)",
        "Carga y reciclado de gas refrigerante R134a o R1234yf",
        "Detección de fugas con nitrógeno o UV",
        "Limpieza interna del sistema de climatización",
        "Revisión y cambio de ventiladores interiores o radiador"
    ],
    "8. Desabolladura y Pintura": [
        "Eliminación de rayones y microarañazos",
        "Pintura completa profesional con horno",
        "Pintura de calipers y detalles deportivos",
        "Pintura y restauración de llantas",
        "Pintura parcial de piezas (capó, parachoques, puertas)",
        "Aplicación de cerámico o film PPF",
        "Pulido, abrillantado y encerado profesional",
        "Reparación de golpes leves y abolladuras",
        "Reparación y pintura de parachoques plásticos",
        "Cambio o reparación de molduras externas"
    ],
    "9. Vidrios y Accesorios": [
        "Cambio de luneta trasera con desempañador",
        "Cambio de parabrisas con instalación profesional",
        "Cambio de vidrios laterales (manuales o eléctricos)",
        "Instalación de barras de techo y portaequipajes",
        "Instalación de estribos y accesorios exteriores",
        "Cambio de plumillas y sistema de limpiaparabrisas",
        "Polarizado de vidrios con lámina certificada",
        "Reparación y mantenimiento de sunroof",
        "Reparación de trizaduras con resina"
    ],
    "10. Inspecciones y Certificaciones": [
        "Certificación de conversión a gas vehicular (GLP/GNC)",
        "Medición y certificación de gases contaminantes",
        "Inspección de frenos en banco dinamométrico",
        "Inspección de seguridad (airbags, cinturones, ISOFIX)",
        "Chequeo completo de suspensión y dirección",
        "Inspección de sistema eléctrico y luces",
        "Inspección pre-compra para autos usados",
        "Pre-chequeo técnico para Revisión Técnica",
        "Revisión de sistema de emisiones y catalizador"
    ]
}

categoria_padre, _ = CategoriaServicio.objects.get_or_create(nombre="Servicios Automotrices")

contador_categorias = 1
contador_subcategorias = 0
contador_servicios = 0

for nombre_subcat, lista_servicios in servicios_por_categoria.items():
    subcategoria, creada = SubcategoriaServicio.objects.get_or_create(
        nombre=nombre_subcat,
        categoria=categoria_padre
    )
    if creada:
        contador_subcategorias += 1
    for servicio in lista_servicios:
        _, creado = Servicio.objects.get_or_create(nombre=servicio, subcategoria=subcategoria)
        if creado:
            contador_servicios += 1

print(f"✅ Se cargaron {contador_categorias} categoría general, {contador_subcategorias} subcategorías y {contador_servicios} servicios.")