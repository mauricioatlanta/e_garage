from copy import deepcopy
from django.db import transaction

from taller.servicios.models import (
    CategoriaServicio,
    CategoriaServicioName,
    SubcategoriaServicio,
    SubcategoriaServicioName,
)

COUNTRY_LANG = {
    "CL": "es",
    "MX": "es",
    "PE": "es",
    "VE": "es",
    "US": "en",
    "BR": "pt",
}

BASE_CATEGORIES = {
    "HVAC_CLIMATE": {
        "label": "Aire acondicionado y climatización",
        "aliases": ["climatizador", "ac"],
        "subservices": {
            "HVAC_REFRIGERANT_CHARGE": {
                "label": "Carga de gas refrigerante",
                "aliases": ["recarga de gas"],
            },
            "HVAC_COMPRESSOR_SERVICE": {
                "label": "Reparación o reemplazo de compresor",
                "aliases": ["compresor"],
            },
            "HVAC_EVAP_COND_INSPECTION": {
                "label": "Revisión de evaporador y condensador",
                "aliases": ["evaporador", "condensador"],
            },
            "HVAC_CABIN_FILTER": {
                "label": "Cambio de filtro de cabina",
                "aliases": ["filtro de habitáculo"],
            },
            "HVAC_ELECTRONIC_DIAG": {
                "label": "Diagnóstico de climatizador electrónico",
                "aliases": ["diagnóstico clima"],
            },
            "HVAC_HEATER_SERVICE": {
                "label": "Sistema calefactor",
                "aliases": ["calefacción"],
            },
        },
    },
    "BODYSHOP": {
        "label": "Carrocería y pintura",
        "aliases": ["bodyshop"],
        "subservices": {
            "BODY_DENT_REPAIR": {
                "label": "Reparación de abolladuras",
                "aliases": ["golpe"],
            },
            "BODY_FRAME_STRAIGHTEN": {
                "label": "Enderezado estructural y chasis",
                "aliases": ["alineación de chasis"],
            },
            "BODY_PAINT": {
                "label": "Pintura completa o parcial",
                "aliases": ["pintura"],
            },
            "BODY_POLISH_DETAIL": {
                "label": "Pulido, abrillantado y detailing",
                "aliases": ["detailing"],
            },
            "BODY_PANEL_REPLACEMENT": {
                "label": "Reemplazo de parachoques, puertas o guardafangos",
                "aliases": ["cambio de piezas"],
            },
            "BODY_COLOR_MATCH": {
                "label": "Emparejamiento de color y retoques",
                "aliases": ["retoque de pintura"],
            },
            "BODY_CLASSIC_RESTO": {
                "label": "Restauración de vehículos clásicos",
                "aliases": ["restauración"],
            },
        },
    },
    "FUEL_ADMISSION": {
        "label": "Combustible y admisión",
        "aliases": ["alimentación"],
        "subservices": {
            "FUEL_INJECTION_SERVICE": {
                "label": "Inyección electrónica (limpieza y calibración)",
                "aliases": ["inyección"],
            },
            "FUEL_PUMP_FILTER": {
                "label": "Revisión de bomba y filtro de combustible",
                "aliases": ["bomba de bencina"],
            },
            "FUEL_INJECTOR_CLEAN": {
                "label": "Limpieza de inyectores",
                "aliases": ["inyectores"],
            },
            "FUEL_THROTTLE_SENSORS": {
                "label": "Cuerpo de aceleración y sensores asociados",
                "aliases": ["cuerpo mariposa"],
            },
            "FUEL_AIR_ADMISSION": {
                "label": "Sistema de admisión de aire",
                "aliases": ["admisión"],
            },
            "FUEL_TURBO_SERVICE": {
                "label": "Turbo y sobrealimentación",
                "aliases": ["turbo"],
            },
        },
    },
    "DIAGNOSTICS": {
        "label": "Diagnóstico y programación",
        "aliases": ["scanner"],
        "subservices": {
            "DIAG_SCANNER_OBD": {
                "label": "Scanner OBD-II / OBD2",
                "aliases": ["scanner obd"],
            },
            "DIAG_MULTIBRAND": {
                "label": "Diagnóstico multimarcas",
                "aliases": ["diagnóstico multimarca"],
            },
            "DIAG_ECU_TCU_PROGRAM": {
                "label": "Reprogramación ECU / TCU",
                "aliases": ["reprogramación"],
            },
            "DIAG_CLEAR_CODES": {
                "label": "Borrado de códigos de falla",
                "aliases": ["borrar códigos"],
            },
            "DIAG_SENSOR_CALIB": {
                "label": "Calibración de sensores",
                "aliases": ["calibrar sensores"],
            },
            "DIAG_SYSTEM_SYNC": {
                "label": "Sincronización electrónica de sistemas",
                "aliases": ["sincronización"],
            },
        },
    },
    "DIFFERENTIAL_FINAL_DRIVE": {
        "label": "Diferencial y transmisión final",
        "aliases": ["diferencial"],
        "subservices": {
            "DIFF_OIL_CHANGE": {
                "label": "Cambio de aceite de diferencial",
                "aliases": ["aceite diferencial"],
            },
            "DIFF_GEAR_INSPECTION": {
                "label": "Revisión de piñones, coronas y satélites",
                "aliases": ["piñones"],
            },
            "DIFF_AXLES_CV": {
                "label": "Semiejes y homocinéticas",
                "aliases": ["homocinética"],
            },
            "DIFF_UJOINT_DRIVESHAFT": {
                "label": "Crucetas y cardanes",
                "aliases": ["cardanes"],
            },
            "DIFF_AXLE_SERVICE": {
                "label": "Ejes delanteros y traseros",
                "aliases": ["ejes"],
            },
        },
    },
    "ELECTRICAL_ELECTRONICS": {
        "label": "Electricidad y electrónica automotriz",
        "aliases": ["eléctrico"],
        "subservices": {
            "ELEC_CHARGING_SYSTEM": {
                "label": "Alternador, batería y motor de arranque",
                "aliases": ["sistema de carga"],
            },
            "ELEC_FUSES_RELAYS": {
                "label": "Revisión de fusibles y relés",
                "aliases": ["fusibles"],
            },
            "ELEC_WIRING_REPAIR": {
                "label": "Reparación de cableado",
                "aliases": ["cableado"],
            },
            "ELEC_LIGHTING": {
                "label": "Luces exteriores e interiores",
                "aliases": ["iluminación"],
            },
            "ELEC_SENSORS": {
                "label": "Sensores (MAF, TPS, O2, temperatura, etc.)",
                "aliases": ["sensores"],
            },
            "ELEC_ECU_BCM_TCM": {
                "label": "ECU, BCM, TCM y reprogramaciones",
                "aliases": ["módulos"],
            },
            "ELEC_DIAG_COMPLETE": {
                "label": "Diagnóstico eléctrico completo",
                "aliases": ["diagnóstico eléctrico"],
            },
        },
    },
    "EMISSIONS_EXHAUST": {
        "label": "Emisiones y escape",
        "aliases": ["escape"],
        "subservices": {
            "EMISS_MUFFLER_REPLACE": {
                "label": "Reemplazo de silenciador o caño de escape",
                "aliases": ["silenciador"],
            },
            "EMISS_CATALYST_DPF": {
                "label": "Limpieza o reemplazo de catalizador / DPF",
                "aliases": ["catalizador"],
            },
            "EMISS_O2_SENSORS": {
                "label": "Sensores de oxígeno",
                "aliases": ["sensor oxígeno"],
            },
            "EMISS_EXHAUST_GASKETS": {
                "label": "Revisión de juntas del múltiple",
                "aliases": ["juntas múltiple"],
            },
            "EMISS_PRE_TECH": {
                "label": "Control técnico pre-revisión",
                "aliases": ["pre-revisión"],
            },
        },
    },
    "BRAKES": {
        "label": "Frenos",
        "aliases": ["frenos"],
        "subservices": {
            "BRAKE_DIAG": {
                "label": "Diagnóstico de frenos",
                "aliases": ["diagnóstico frenos"],
            },
            "BRAKE_PAD_CHANGE": {
                "label": "Cambio de pastillas delanteras o traseras",
                "aliases": ["pastillas"],
            },
            "BRAKE_DISK_RESURFACE": {
                "label": "Rectificación de discos",
                "aliases": ["rectificar discos"],
            },
            "BRAKE_DRUM_SERVICE": {
                "label": "Revisión de tambores y zapatas",
                "aliases": ["tambores"],
            },
            "BRAKE_FLUID_BLEED": {
                "label": "Purga y reemplazo de líquido",
                "aliases": ["purga"],
            },
            "BRAKE_ABS_REPAIR": {
                "label": "Reparación de ABS y sensores",
                "aliases": ["abs"],
            },
            "BRAKE_EBD_CALIB": {
                "label": "Calibración del sistema EBD / ESP",
                "aliases": ["ebd", "esp"],
            },
        },
    },
    "INSPECTIONS_CERT": {
        "label": "Inspecciones y certificaciones",
        "aliases": ["inspecciones"],
        "subservices": {
            "INSP_PREPURCHASE": {
                "label": "Inspección precompra o pre-venta",
                "aliases": ["precompra"],
            },
            "INSP_PREVENTIVE": {
                "label": "Control técnico preventivo",
                "aliases": ["control preventivo"],
            },
            "INSP_FULL_REPORT": {
                "label": "Informe mecánico completo",
                "aliases": ["informe"],
            },
            "INSP_MILEAGE_CERT": {
                "label": "Certificado de kilometraje",
                "aliases": ["kilometraje"],
            },
            "INSP_TRAVEL_CHECK": {
                "label": "Revisión previa a viaje",
                "aliases": ["revisión de viaje"],
            },
        },
    },
    "INTERIOR_COMFORT": {
        "label": "Interior y confort",
        "aliases": ["interior"],
        "subservices": {
            "INT_UPHOLSTERY": {
                "label": "Tapicería (asientos, techo, paneles)",
                "aliases": ["tapicería"],
            },
            "INT_LOCKS_HANDLES": {
                "label": "Cerraduras y manillas",
                "aliases": ["cerraduras"],
            },
            "INT_POWER_WINDOWS": {
                "label": "Vidrios eléctricos y pestillos",
                "aliases": ["eleva vidrios"],
            },
            "INT_CABIN_AC": {
                "label": "Aire acondicionado interior",
                "aliases": ["aire interior"],
            },
            "INT_AUDIO_NAV": {
                "label": "Sistema de audio, GPS y multimedia",
                "aliases": ["audio"],
            },
            "INT_STEERING_CONTROLS": {
                "label": "Volante y mandos",
                "aliases": ["volante"],
            },
            "INT_SEATBELTS": {
                "label": "Cinturones de seguridad",
                "aliases": ["cinturones"],
            },
        },
    },
    "PREVENTIVE_MAINT": {
        "label": "Mantenimiento preventivo",
        "aliases": ["mantención"],
        "subservices": {
            "PM_SCHEDULED_CHECKS": {
                "label": "Revisión de 5.000 / 10.000 / 20.000 km",
                "aliases": ["servicio programado"],
            },
            "PM_OIL_FILTER": {
                "label": "Cambio de aceite y filtros",
                "aliases": ["cambio de aceite"],
            },
            "PM_FLUIDS_LEVELS": {
                "label": "Revisión de líquidos y niveles",
                "aliases": ["niveles"],
            },
            "PM_QUICK_SCAN": {
                "label": "Escaneo rápido de diagnóstico",
                "aliases": ["scan rápido"],
            },
            "PM_TRAVEL_CHECK": {
                "label": "Revisión previa a viaje",
                "aliases": ["check viaje"],
            },
        },
    },
    "ENGINE_DRIVETRAIN": {
        "label": "Motor y transmisión",
        "aliases": ["tren motriz"],
        "subservices": {
            "ENGINE_DIAG": {
                "label": "Diagnóstico de motor",
                "aliases": ["diagnóstico motor"],
            },
            "ENGINE_REBUILD": {
                "label": "Reparación o reemplazo completo",
                "aliases": ["rectificado"],
            },
            "ENGINE_SEALS_LUBE": {
                "label": "Lubricación y sellos",
                "aliases": ["sellos"],
            },
            "ENGINE_TIMING_BELT": {
                "label": "Correa de distribución",
                "aliases": ["correa"],
            },
            "ENGINE_HEAD_VALVES": {
                "label": "Culata, válvulas y cigüeñal",
                "aliases": ["culata"],
            },
            "ENGINE_TRANSMISSION_BOX": {
                "label": "Caja de cambios mecánica / automática",
                "aliases": ["caja"],
            },
            "ENGINE_CLUTCH_FLYWHEEL": {
                "label": "Embrague y volante de inercia",
                "aliases": ["embrague"],
            },
            "ENGINE_COOLING_PUMP": {
                "label": "Sistema de refrigeración y bomba de agua",
                "aliases": ["radiador"],
            },
        },
    },
    "TIRES_VULCANIZATION": {
        "label": "Neumáticos y vulcanización",
        "aliases": ["llantas"],
        "subservices": {
            "TIRE_MOUNT": {
                "label": "Montaje y desmontaje",
                "aliases": ["montaje"],
            },
            "TIRE_PUNCTURE_REPAIR": {
                "label": "Reparación de pinchazos",
                "aliases": ["parche"],
            },
            "TIRE_ALIGN_BALANCE": {
                "label": "Alineación y balanceo",
                "aliases": ["alineación"],
            },
            "TIRE_ROTATION": {
                "label": "Rotación de neumáticos",
                "aliases": ["rotación"],
            },
            "TIRE_WHEEL_REPAIR": {
                "label": "Reparación o soldadura de llantas",
                "aliases": ["soldadura llanta"],
            },
            "TIRE_SALES": {
                "label": "Venta de neumáticos y válvulas",
                "aliases": ["venta neumáticos"],
            },
        },
    },
    "CUSTOM_MODS": {
        "label": "Personalización y modificaciones",
        "aliases": ["custom"],
        "subservices": {
            "CUSTOM_LIGHTING": {
                "label": "Luces LED / Xenón",
                "aliases": ["luces"],
            },
            "CUSTOM_BODY_KIT": {
                "label": "Kit deportivo o body kit",
                "aliases": ["body kit"],
            },
            "CUSTOM_TUNING": {
                "label": "Reprogramación chip tuning",
                "aliases": ["chip tuning"],
            },
            "CUSTOM_SPORT_SUSP": {
                "label": "Suspensión deportiva",
                "aliases": ["suspensión sport"],
            },
            "CUSTOM_AUDIO": {
                "label": "Sistema de sonido personalizado",
                "aliases": ["audio"],
            },
            "CUSTOM_ACCESSORIES": {
                "label": "Accesorios estéticos y funcionales",
                "aliases": ["accesorios"],
            },
        },
    },
    "SAFETY_ADAS": {
        "label": "Seguridad y asistencia (ADAS)",
        "aliases": ["adas"],
        "subservices": {
            "SAFETY_AIRBAGS": {
                "label": "Airbags (revisión y reemplazo)",
                "aliases": ["airbag"],
            },
            "SAFETY_COLLISION_SENSORS": {
                "label": "Sensores de colisión",
                "aliases": ["sensores de choque"],
            },
            "SAFETY_TRACTION_CONTROL": {
                "label": "Control de tracción / estabilidad",
                "aliases": ["control estabilidad"],
            },
            "SAFETY_ADAS_CALIB": {
                "label": "Calibración ADAS",
                "aliases": ["calibración adas"],
            },
            "SAFETY_PARKING_SENSORS": {
                "label": "Sensores de estacionamiento y cámaras",
                "aliases": ["sensores de retro"],
            },
            "SAFETY_ALARMS": {
                "label": "Alarmas y cierres centralizados",
                "aliases": ["alarmas"],
            },
        },
    },
    "EMERGENCY_EXTERNAL": {
        "label": "Servicios de emergencia y externos",
        "aliases": ["emergencia"],
        "subservices": {
            "EMERGENCY_TOWING": {
                "label": "Servicio de grúa",
                "aliases": ["grúa"],
            },
            "EMERGENCY_MOBILE_DIAG": {
                "label": "Diagnóstico móvil",
                "aliases": ["diagnóstico a domicilio"],
            },
            "EMERGENCY_ROADSIDE_BATTERY": {
                "label": "Cambio de batería o neumático a domicilio",
                "aliases": ["asistencia batería"],
            },
            "EMERGENCY_ROADSIDE_ASSIST": {
                "label": "Asistencia en ruta",
                "aliases": ["auxilio"],
            },
        },
    },
    "QUICK_SERVICES": {
        "label": "Servicios rápidos",
        "aliases": ["servicio express"],
        "subservices": {
            "QUICK_OIL_FILTER": {
                "label": "Cambio de aceite y filtro",
                "aliases": ["express aceite"],
            },
            "QUICK_BRAKE_CHECK": {
                "label": "Revisión de frenos",
                "aliases": ["check frenos"],
            },
            "QUICK_BATTERY_TEST": {
                "label": "Revisión de batería",
                "aliases": ["test batería"],
            },
            "QUICK_WIPERS": {
                "label": "Cambio de plumillas",
                "aliases": ["escobillas"],
            },
            "QUICK_LIGHTS_LEVELS": {
                "label": "Control de luces y niveles",
                "aliases": ["control luces"],
            },
        },
    },
    "OFFROAD_4X4": {
        "label": "Sistemas 4x4 y off-road",
        "aliases": ["4x4"],
        "subservices": {
            "OFFROAD_TRANSFER_CASE": {
                "label": "Revisión de caja de transferencia",
                "aliases": ["transfer"],
            },
            "OFFROAD_DIFFERENTIALS": {
                "label": "Mantenimiento de diferenciales 4WD",
                "aliases": ["diferenciales 4wd"],
            },
            "OFFROAD_COUPLINGS": {
                "label": "Acoples y tracción total",
                "aliases": ["acoples"],
            },
            "OFFROAD_PREP": {
                "label": "Preparación off-road",
                "aliases": ["preparación offroad"],
            },
            "OFFROAD_WINCH_PROTECTION": {
                "label": "Instalación de winches y protecciones",
                "aliases": ["winche"],
            },
        },
    },
    "SUSPENSION_STEERING": {
        "label": "Suspensión y dirección",
        "aliases": ["suspensión"],
        "subservices": {
            "SUSP_SHOCKS_SPRINGS": {
                "label": "Amortiguadores y resortes",
                "aliases": ["amortiguadores"],
            },
            "SUSP_TIE_RODS": {
                "label": "Terminales y rótulas",
                "aliases": ["terminales"],
            },
            "SUSP_CONTROL_ARMS": {
                "label": "Parrillas y bujes",
                "aliases": ["bujes"],
            },
            "SUSP_STEERING_RACK": {
                "label": "Cremallera de dirección",
                "aliases": ["cremallera"],
            },
            "SUSP_ALIGNMENT": {
                "label": "Alineación",
                "aliases": ["alinear"],
            },
            "SUSP_AIR_SYSTEM": {
                "label": "Suspensión neumática o electrónica",
                "aliases": ["suspensión neumática"],
            },
        },
    },
    "TUNE_UP": {
        "label": "Tune up / afinación",
        "aliases": ["afinación"],
        "subservices": {
            "TUNE_OIL_FILTER": {
                "label": "Cambio de aceite y filtro",
                "aliases": ["cambio aceite"],
            },
            "TUNE_FILTERS_REPLACE": {
                "label": "Reemplazo de filtro de aire, combustible y cabina",
                "aliases": ["filtros"],
            },
            "TUNE_SPARK_IGNITION": {
                "label": "Cambio de bujías, cables y bobinas",
                "aliases": ["bujías"],
            },
            "TUNE_THROTTLE_CLEAN": {
                "label": "Limpieza de cuerpo de aceleración e inyectores",
                "aliases": ["cuerpo aceleración"],
            },
            "TUNE_DISTRIBUTOR_CHECK": {
                "label": "Revisión de tapa y rotor (vehículos antiguos)",
                "aliases": ["distribuidor"],
            },
            "TUNE_MIX_IDLE": {
                "label": "Calibración de mezcla y ralentí",
                "aliases": ["ralentí"],
            },
            "TUNE_SENSOR_CLEAN": {
                "label": "Limpieza de sensores (MAF, TPS, O2)",
                "aliases": ["limpieza sensores"],
            },
            "TUNE_ECU_RESET": {
                "label": "Escaneo y reset de ECU",
                "aliases": ["reset ecu"],
            },
            "TUNE_COOLING_CHECK": {
                "label": "Revisión de sistema de refrigeración",
                "aliases": ["refrigeración"],
            },
            "TUNE_DIESEL_SERVICE": {
                "label": "Afinación diésel (filtros, inyectores, precalentadores, EGR, DPF)",
                "aliases": ["afinación diésel"],
            },
        },
    },
    "GLASS_MIRRORS": {
        "label": "Vidrios y espejos",
        "aliases": ["parabrisas"],
        "subservices": {
            "GLASS_WINDSHIELD_REPLACE": {
                "label": "Reemplazo de parabrisas y vidrios laterales",
                "aliases": ["parabrisas"],
            },
            "GLASS_TINT": {
                "label": "Polarizado",
                "aliases": ["polarizado"],
            },
            "GLASS_LEAK_SEAL": {
                "label": "Sellado de filtraciones",
                "aliases": ["sellado"],
            },
            "GLASS_MIRROR_REPLACE": {
                "label": "Reemplazo de espejos laterales",
                "aliases": ["espejos"],
            },
            "GLASS_WINDOW_LIFTER": {
                "label": "Levantavidrios eléctricos o manuales",
                "aliases": ["levantavidrios"],
            },
            "GLASS_RAIN_SENSOR_CALIB": {
                "label": "Calibración de sensores de lluvia y luz",
                "aliases": ["sensor lluvia"],
            },
        },
    },
}

COUNTRY_OVERRIDES = {
    "MX": {
        "categories": {
            "HVAC_CLIMATE": {
                "label": "Clima automotriz y aire acondicionado",
                "aliases": ["clima", "aire acondicionado"],
            },
            "BODYSHOP": {
                "label": "Hojalatería y pintura",
                "aliases": ["hojalatería", "body shop"],
            },
            "INTERIOR_COMFORT": {
                "label": "Interior y confort",
                "aliases": ["interior", "detalles"],
            },
            "TIRES_VULCANIZATION": {
                "label": "Llantas y vulcanizadora",
                "aliases": ["llantas", "vulcanizadora"],
            },
            "QUICK_SERVICES": {
                "label": "Servicios express",
                "aliases": ["servicios rápidos", "express"],
            },
        },
    },
    "PE": {
        "categories": {
            "BODYSHOP": {
                "label": "Plancha y pintura",
                "aliases": ["plancha"],
            },
        },
    },
    "VE": {
        "categories": {
            "BODYSHOP": {
                "label": "Latonería y pintura",
                "aliases": ["latonería"],
            },
        },
    },
    "US": {
        "categories": {
            "HVAC_CLIMATE": {
                "label": "HVAC & climate control",
                "aliases": ["air conditioning", "hvac"],
            },
            "BODYSHOP": {
                "label": "Bodywork & paint",
                "aliases": ["collision repair", "body shop"],
            },
            "FUEL_ADMISSION": {
                "label": "Fuel & intake systems",
                "aliases": ["fuel system"],
            },
            "DIAGNOSTICS": {
                "label": "Diagnostics & programming",
                "aliases": ["diagnostics"],
            },
            "DIFFERENTIAL_FINAL_DRIVE": {
                "label": "Differential & final drive",
                "aliases": ["final drive"],
            },
            "ELECTRICAL_ELECTRONICS": {
                "label": "Electrical & electronics",
                "aliases": ["electrical"],
            },
            "EMISSIONS_EXHAUST": {
                "label": "Emissions & exhaust",
                "aliases": ["emissions"],
            },
            "BRAKES": {
                "label": "Brake system",
                "aliases": ["brakes"],
            },
            "INSPECTIONS_CERT": {
                "label": "Inspections & certifications",
                "aliases": ["inspections"],
            },
            "INTERIOR_COMFORT": {
                "label": "Interior & comfort",
                "aliases": ["interior"],
            },
            "PREVENTIVE_MAINT": {
                "label": "Preventive maintenance",
                "aliases": ["maintenance"],
            },
            "ENGINE_DRIVETRAIN": {
                "label": "Engine & drivetrain",
                "aliases": ["drivetrain"],
            },
            "TIRES_VULCANIZATION": {
                "label": "Tires & tire care",
                "aliases": ["tires"],
            },
            "CUSTOM_MODS": {
                "label": "Customization & upgrades",
                "aliases": ["custom"],
            },
            "SAFETY_ADAS": {
                "label": "Safety & ADAS",
                "aliases": ["adas"],
            },
            "EMERGENCY_EXTERNAL": {
                "label": "Emergency & mobile services",
                "aliases": ["roadside"],
            },
            "QUICK_SERVICES": {
                "label": "Quick services",
                "aliases": ["express"],
            },
            "OFFROAD_4X4": {
                "label": "4x4 & off-road",
                "aliases": ["off-road"],
            },
            "SUSPENSION_STEERING": {
                "label": "Suspension & steering",
                "aliases": ["suspension"],
            },
            "TUNE_UP": {
                "label": "Tune-up",
                "aliases": ["tune up"],
            },
            "GLASS_MIRRORS": {
                "label": "Glass & mirrors",
                "aliases": ["glass"],
            },
        },
        "subservices": {
            "HVAC_REFRIGERANT_CHARGE": {
                "label": "Refrigerant recharge",
                "aliases": ["ac recharge"],
            },
            "HVAC_COMPRESSOR_SERVICE": {
                "label": "Compressor repair or replacement",
                "aliases": ["compressor"],
            },
            "HVAC_EVAP_COND_INSPECTION": {
                "label": "Evaporator and condenser inspection",
                "aliases": ["evaporator"],
            },
            "HVAC_CABIN_FILTER": {"label": "Cabin filter replacement", "aliases": ["cabin filter"]},
            "HVAC_ELECTRONIC_DIAG": {
                "label": "Electronic climate diagnostics",
                "aliases": ["climate diagnostics"],
            },
            "HVAC_HEATER_SERVICE": {"label": "Heater core service", "aliases": ["heater"]},
            "BODY_DENT_REPAIR": {"label": "Dent repair", "aliases": ["dent removal"]},
            "BODY_FRAME_STRAIGHTEN": {
                "label": "Frame and unibody straightening",
                "aliases": ["frame straightening"],
            },
            "BODY_PAINT": {"label": "Full or spot painting", "aliases": ["paint"]},
            "BODY_POLISH_DETAIL": {"label": "Polishing & detailing", "aliases": ["detailing"]},
            "BODY_PANEL_REPLACEMENT": {
                "label": "Bumper, door or fender replacement",
                "aliases": ["panel replacement"],
            },
            "BODY_COLOR_MATCH": {"label": "Color matching & touch-ups", "aliases": ["color match"]},
            "BODY_CLASSIC_RESTO": {"label": "Classic car restoration", "aliases": ["restoration"]},
            "FUEL_INJECTION_SERVICE": {
                "label": "Electronic injection service",
                "aliases": ["fuel injection"],
            },
            "FUEL_PUMP_FILTER": {
                "label": "Fuel pump and filter inspection",
                "aliases": ["fuel pump"],
            },
            "FUEL_INJECTOR_CLEAN": {"label": "Injector cleaning", "aliases": ["injector cleaning"]},
            "FUEL_THROTTLE_SENSORS": {
                "label": "Throttle body and sensor service",
                "aliases": ["throttle body"],
            },
            "FUEL_AIR_ADMISSION": {"label": "Air intake system service", "aliases": ["intake"]},
            "FUEL_TURBO_SERVICE": {"label": "Turbocharger and boost systems", "aliases": ["turbo"]},
            "DIAG_SCANNER_OBD": {"label": "OBD-II scan", "aliases": ["obd scan"]},
            "DIAG_MULTIBRAND": {"label": "Multibrand diagnostics", "aliases": ["multi-brand"]},
            "DIAG_ECU_TCU_PROGRAM": {
                "label": "ECU / TCU programming",
                "aliases": ["ecu programming"],
            },
            "DIAG_CLEAR_CODES": {"label": "Fault code clearing", "aliases": ["clear codes"]},
            "DIAG_SENSOR_CALIB": {"label": "Sensor calibration", "aliases": ["sensor calibration"]},
            "DIAG_SYSTEM_SYNC": {
                "label": "Electronic system synchronization",
                "aliases": ["system sync"],
            },
            "DIFF_OIL_CHANGE": {"label": "Differential fluid change", "aliases": ["diff fluid"]},
            "DIFF_GEAR_INSPECTION": {
                "label": "Ring and pinion inspection",
                "aliases": ["gear inspection"],
            },
            "DIFF_AXLES_CV": {"label": "Axle shafts and CV joints", "aliases": ["cv joints"]},
            "DIFF_UJOINT_DRIVESHAFT": {
                "label": "U-joints and driveshaft service",
                "aliases": ["driveshaft"],
            },
            "DIFF_AXLE_SERVICE": {
                "label": "Front and rear axle service",
                "aliases": ["axle service"],
            },
            "ELEC_CHARGING_SYSTEM": {"label": "Charging system repair", "aliases": ["alternator"]},
            "ELEC_FUSES_RELAYS": {"label": "Fuse and relay inspection", "aliases": ["fuses"]},
            "ELEC_WIRING_REPAIR": {"label": "Wiring repair", "aliases": ["wiring"]},
            "ELEC_LIGHTING": {"label": "Exterior and interior lighting", "aliases": ["lighting"]},
            "ELEC_SENSORS": {"label": "Sensor diagnostics", "aliases": ["sensors"]},
            "ELEC_ECU_BCM_TCM": {
                "label": "Module repair & reprogramming",
                "aliases": ["control modules"],
            },
            "ELEC_DIAG_COMPLETE": {
                "label": "Complete electrical diagnostic",
                "aliases": ["electrical diagnostic"],
            },
            "EMISS_MUFFLER_REPLACE": {
                "label": "Muffler and exhaust replacement",
                "aliases": ["muffler"],
            },
            "EMISS_CATALYST_DPF": {
                "label": "Catalytic converter / DPF service",
                "aliases": ["catalytic converter"],
            },
            "EMISS_O2_SENSORS": {"label": "Oxygen sensor replacement", "aliases": ["o2 sensor"]},
            "EMISS_EXHAUST_GASKETS": {
                "label": "Exhaust manifold gaskets",
                "aliases": ["exhaust gasket"],
            },
            "EMISS_PRE_TECH": {
                "label": "Pre-inspection emissions check",
                "aliases": ["emissions check"],
            },
            "BRAKE_DIAG": {"label": "Brake diagnosis", "aliases": ["brake inspection"]},
            "BRAKE_PAD_CHANGE": {
                "label": "Front or rear pad replacement",
                "aliases": ["pad replacement"],
            },
            "BRAKE_DISK_RESURFACE": {"label": "Rotor resurfacing", "aliases": ["rotor service"]},
            "BRAKE_DRUM_SERVICE": {"label": "Drum and shoe service", "aliases": ["drum service"]},
            "BRAKE_FLUID_BLEED": {"label": "Brake fluid flush", "aliases": ["fluid flush"]},
            "BRAKE_ABS_REPAIR": {"label": "ABS repair and sensors", "aliases": ["abs repair"]},
            "BRAKE_EBD_CALIB": {"label": "EBD / ESP calibration", "aliases": ["esp calibration"]},
            "INSP_PREPURCHASE": {"label": "Pre-purchase inspection", "aliases": ["ppi"]},
            "INSP_PREVENTIVE": {
                "label": "Preventive technical check",
                "aliases": ["preventive check"],
            },
            "INSP_FULL_REPORT": {
                "label": "Comprehensive mechanical report",
                "aliases": ["inspection report"],
            },
            "INSP_MILEAGE_CERT": {"label": "Mileage certification", "aliases": ["mileage check"]},
            "INSP_TRAVEL_CHECK": {"label": "Trip-readiness inspection", "aliases": ["trip check"]},
            "INT_UPHOLSTERY": {"label": "Upholstery repair", "aliases": ["upholstery"]},
            "INT_LOCKS_HANDLES": {"label": "Locks and handles", "aliases": ["locks"]},
            "INT_POWER_WINDOWS": {"label": "Power window repair", "aliases": ["power windows"]},
            "INT_CABIN_AC": {"label": "Cabin HVAC service", "aliases": ["cabin hvac"]},
            "INT_AUDIO_NAV": {"label": "Audio, GPS & multimedia", "aliases": ["audio"]},
            "INT_STEERING_CONTROLS": {
                "label": "Steering wheel controls",
                "aliases": ["steering wheel"],
            },
            "INT_SEATBELTS": {"label": "Seat belt service", "aliases": ["seat belts"]},
            "PM_SCHEDULED_CHECKS": {
                "label": "Scheduled maintenance (5k/10k/20k)",
                "aliases": ["scheduled service"],
            },
            "PM_OIL_FILTER": {"label": "Oil & filter change", "aliases": ["oil change"]},
            "PM_FLUIDS_LEVELS": {"label": "Fluids and levels check", "aliases": ["fluid check"]},
            "PM_QUICK_SCAN": {"label": "Quick diagnostic scan", "aliases": ["quick scan"]},
            "PM_TRAVEL_CHECK": {"label": "Pre-trip check", "aliases": ["trip check"]},
            "ENGINE_DIAG": {"label": "Engine diagnostics", "aliases": ["engine diagnostic"]},
            "ENGINE_REBUILD": {"label": "Engine repair or rebuild", "aliases": ["engine rebuild"]},
            "ENGINE_SEALS_LUBE": {
                "label": "Seals & lubrication service",
                "aliases": ["engine seals"],
            },
            "ENGINE_TIMING_BELT": {"label": "Timing belt service", "aliases": ["timing belt"]},
            "ENGINE_HEAD_VALVES": {
                "label": "Cylinder head, valves & crank",
                "aliases": ["cylinder head"],
            },
            "ENGINE_TRANSMISSION_BOX": {
                "label": "Manual / automatic transmission service",
                "aliases": ["transmission"],
            },
            "ENGINE_CLUTCH_FLYWHEEL": {"label": "Clutch & flywheel service", "aliases": ["clutch"]},
            "ENGINE_COOLING_PUMP": {
                "label": "Cooling system & water pump",
                "aliases": ["cooling system"],
            },
            "TIRE_MOUNT": {"label": "Mounting and dismounting", "aliases": ["tire mounting"]},
            "TIRE_PUNCTURE_REPAIR": {"label": "Flat tire repair", "aliases": ["tire repair"]},
            "TIRE_ALIGN_BALANCE": {"label": "Alignment & balancing", "aliases": ["alignment"]},
            "TIRE_ROTATION": {"label": "Tire rotation", "aliases": ["rotation"]},
            "TIRE_WHEEL_REPAIR": {"label": "Wheel repair or welding", "aliases": ["wheel repair"]},
            "TIRE_SALES": {"label": "Tire and valve sales", "aliases": ["tire sales"]},
            "CUSTOM_LIGHTING": {
                "label": "LED / HID lighting upgrades",
                "aliases": ["lighting upgrade"],
            },
            "CUSTOM_BODY_KIT": {"label": "Sport kit or body kit", "aliases": ["body kit"]},
            "CUSTOM_TUNING": {"label": "Chip tuning / remap", "aliases": ["tuning"]},
            "CUSTOM_SPORT_SUSP": {
                "label": "Performance suspension",
                "aliases": ["sport suspension"],
            },
            "CUSTOM_AUDIO": {"label": "Custom audio system", "aliases": ["custom audio"]},
            "CUSTOM_ACCESSORIES": {
                "label": "Aesthetic & functional accessories",
                "aliases": ["accessories"],
            },
            "SAFETY_AIRBAGS": {
                "label": "Airbag inspection & replacement",
                "aliases": ["airbag service"],
            },
            "SAFETY_COLLISION_SENSORS": {
                "label": "Collision sensor service",
                "aliases": ["collision sensors"],
            },
            "SAFETY_TRACTION_CONTROL": {
                "label": "Traction/Stability control service",
                "aliases": ["traction control"],
            },
            "SAFETY_ADAS_CALIB": {"label": "ADAS calibration", "aliases": ["adas calibration"]},
            "SAFETY_PARKING_SENSORS": {
                "label": "Parking sensors & cameras",
                "aliases": ["parking sensors"],
            },
            "SAFETY_ALARMS": {"label": "Alarms & central locking", "aliases": ["alarms"]},
            "EMERGENCY_TOWING": {"label": "Towing service", "aliases": ["towing"]},
            "EMERGENCY_MOBILE_DIAG": {
                "label": "Mobile diagnostics",
                "aliases": ["mobile diagnostic"],
            },
            "EMERGENCY_ROADSIDE_BATTERY": {
                "label": "On-site battery or tire change",
                "aliases": ["roadside battery"],
            },
            "EMERGENCY_ROADSIDE_ASSIST": {
                "label": "Roadside assistance",
                "aliases": ["roadside assist"],
            },
            "QUICK_OIL_FILTER": {"label": "Quick oil & filter change", "aliases": ["quick oil"]},
            "QUICK_BRAKE_CHECK": {"label": "Quick brake check", "aliases": ["brake check"]},
            "QUICK_BATTERY_TEST": {"label": "Battery test", "aliases": ["battery test"]},
            "QUICK_WIPERS": {"label": "Wiper blade replacement", "aliases": ["wipers"]},
            "QUICK_LIGHTS_LEVELS": {
                "label": "Lights and fluid levels check",
                "aliases": ["lights check"],
            },
            "OFFROAD_TRANSFER_CASE": {
                "label": "Transfer case inspection",
                "aliases": ["transfer case"],
            },
            "OFFROAD_DIFFERENTIALS": {
                "label": "4WD differential service",
                "aliases": ["4wd differential"],
            },
            "OFFROAD_COUPLINGS": {"label": "Couplings & AWD systems", "aliases": ["awd"]},
            "OFFROAD_PREP": {"label": "Off-road preparation", "aliases": ["off-road prep"]},
            "OFFROAD_WINCH_PROTECTION": {
                "label": "Winch & armor installation",
                "aliases": ["winch"],
            },
            "SUSP_SHOCKS_SPRINGS": {"label": "Shocks and springs", "aliases": ["shocks"]},
            "SUSP_TIE_RODS": {"label": "Tie rods and ball joints", "aliases": ["tie rods"]},
            "SUSP_CONTROL_ARMS": {
                "label": "Control arms and bushings",
                "aliases": ["control arms"],
            },
            "SUSP_STEERING_RACK": {"label": "Steering rack service", "aliases": ["steering rack"]},
            "SUSP_ALIGNMENT": {"label": "Alignment", "aliases": ["alignment"]},
            "SUSP_AIR_SYSTEM": {
                "label": "Air or electronic suspension",
                "aliases": ["air suspension"],
            },
            "TUNE_OIL_FILTER": {"label": "Oil & filter change", "aliases": ["oil change"]},
            "TUNE_FILTERS_REPLACE": {
                "label": "Air, fuel & cabin filter replacement",
                "aliases": ["filter replacement"],
            },
            "TUNE_SPARK_IGNITION": {
                "label": "Spark plugs, wires and coils",
                "aliases": ["spark plug replacement"],
            },
            "TUNE_THROTTLE_CLEAN": {
                "label": "Throttle body & injector cleaning",
                "aliases": ["throttle cleaning"],
            },
            "TUNE_DISTRIBUTOR_CHECK": {
                "label": "Distributor cap and rotor",
                "aliases": ["distributor"],
            },
            "TUNE_MIX_IDLE": {
                "label": "Mixture and idle adjustment",
                "aliases": ["idle adjustment"],
            },
            "TUNE_SENSOR_CLEAN": {
                "label": "Sensor cleaning (MAF, TPS, O2)",
                "aliases": ["sensor cleaning"],
            },
            "TUNE_ECU_RESET": {"label": "ECU scan & reset", "aliases": ["ecu reset"]},
            "TUNE_COOLING_CHECK": {"label": "Cooling system check", "aliases": ["cooling check"]},
            "TUNE_DIESEL_SERVICE": {
                "label": "Diesel tune-up (filters, injectors, glow plugs, EGR, DPF)",
                "aliases": ["diesel tune"],
            },
            "GLASS_WINDSHIELD_REPLACE": {
                "label": "Windshield and side glass replacement",
                "aliases": ["windshield"],
            },
            "GLASS_TINT": {"label": "Window tinting", "aliases": ["tint"]},
            "GLASS_LEAK_SEAL": {"label": "Leak sealing", "aliases": ["leak seal"]},
            "GLASS_MIRROR_REPLACE": {
                "label": "Side mirror replacement",
                "aliases": ["mirror replacement"],
            },
            "GLASS_WINDOW_LIFTER": {
                "label": "Window regulator service",
                "aliases": ["window regulator"],
            },
            "GLASS_RAIN_SENSOR_CALIB": {
                "label": "Rain/light sensor calibration",
                "aliases": ["rain sensor"],
            },
        },
    },
    "BR": {
        "categories": {
            "HVAC_CLIMATE": {
                "label": "Ar-condicionado e climatização",
                "aliases": ["ar condicionado", "climatização"],
            },
            "BODYSHOP": {
                "label": "Funilaria e pintura",
                "aliases": ["funilaria"],
            },
            "FUEL_ADMISSION": {
                "label": "Combustível e admissão",
                "aliases": ["combustível"],
            },
            "DIAGNOSTICS": {
                "label": "Diagnóstico e programação",
                "aliases": ["diagnóstico"],
            },
            "DIFFERENTIAL_FINAL_DRIVE": {
                "label": "Diferencial e conjunto final",
                "aliases": ["diferencial"],
            },
            "ELECTRICAL_ELECTRONICS": {
                "label": "Elétrica e eletrônica automotiva",
                "aliases": ["elétrica"],
            },
            "EMISSIONS_EXHAUST": {
                "label": "Emissões e escapamento",
                "aliases": ["escapamento"],
            },
            "BRAKES": {
                "label": "Freios",
                "aliases": ["freios"],
            },
            "INSPECTIONS_CERT": {
                "label": "Vistorias e certificações",
                "aliases": ["vistorias"],
            },
            "INTERIOR_COMFORT": {
                "label": "Interior e conforto",
                "aliases": ["interior"],
            },
            "PREVENTIVE_MAINT": {
                "label": "Manutenção preventiva",
                "aliases": ["manutenção"],
            },
            "ENGINE_DRIVETRAIN": {
                "label": "Motor e transmissão",
                "aliases": ["motor"],
            },
            "TIRES_VULCANIZATION": {
                "label": "Pneus e borracharia",
                "aliases": ["pneus"],
            },
            "CUSTOM_MODS": {
                "label": "Personalização e upgrades",
                "aliases": ["personalização"],
            },
            "SAFETY_ADAS": {
                "label": "Segurança e ADAS",
                "aliases": ["adas"],
            },
            "EMERGENCY_EXTERNAL": {
                "label": "Serviços de emergência e externos",
                "aliases": ["guincho", "emergência"],
            },
            "QUICK_SERVICES": {
                "label": "Serviços rápidos",
                "aliases": ["rápidos"],
            },
            "OFFROAD_4X4": {
                "label": "Sistemas 4x4 e off-road",
                "aliases": ["4x4"],
            },
            "SUSPENSION_STEERING": {
                "label": "Suspensão e direção",
                "aliases": ["suspensão"],
            },
            "TUNE_UP": {
                "label": "Tune-up / regulagem",
                "aliases": ["regulagem"],
            },
            "GLASS_MIRRORS": {
                "label": "Vidros e espelhos",
                "aliases": ["vidros"],
            },
        },
        "subservices": {
            "HVAC_REFRIGERANT_CHARGE": {
                "label": "Recarga de gás refrigerante",
                "aliases": ["recarga de ar"],
            },
            "HVAC_COMPRESSOR_SERVICE": {
                "label": "Reparo ou troca do compressor",
                "aliases": ["compressor"],
            },
            "HVAC_EVAP_COND_INSPECTION": {
                "label": "Revisão de evaporador e condensador",
                "aliases": ["evaporador"],
            },
            "HVAC_CABIN_FILTER": {
                "label": "Troca do filtro de cabine",
                "aliases": ["filtro de cabine"],
            },
            "HVAC_ELECTRONIC_DIAG": {
                "label": "Diagnóstico eletrônico do ar",
                "aliases": ["diagnóstico ar"],
            },
            "HVAC_HEATER_SERVICE": {"label": "Sistema de calefação", "aliases": ["aquecedor"]},
            "BODY_DENT_REPAIR": {"label": "Remoção de amassados", "aliases": ["martelinho"]},
            "BODY_FRAME_STRAIGHTEN": {
                "label": "Alinhamento de estrutura e chassi",
                "aliases": ["chassi"],
            },
            "BODY_PAINT": {"label": "Pintura total ou parcial", "aliases": ["pintura"]},
            "BODY_POLISH_DETAIL": {
                "label": "Polimento, brilho e detailing",
                "aliases": ["polimento"],
            },
            "BODY_PANEL_REPLACEMENT": {
                "label": "Troca de para-choque, portas ou para-lamas",
                "aliases": ["troca de peça"],
            },
            "BODY_COLOR_MATCH": {"label": "Acerto de cor e retoques", "aliases": ["retoque"]},
            "BODY_CLASSIC_RESTO": {
                "label": "Restauração de carros clássicos",
                "aliases": ["restauração"],
            },
            "FUEL_INJECTION_SERVICE": {
                "label": "Limpeza e calibração da injeção",
                "aliases": ["injeção"],
            },
            "FUEL_PUMP_FILTER": {
                "label": "Revisão da bomba e filtro de combustível",
                "aliases": ["bomba de combustível"],
            },
            "FUEL_INJECTOR_CLEAN": {"label": "Limpeza de injetores", "aliases": ["injetores"]},
            "FUEL_THROTTLE_SENSORS": {
                "label": "Corpo de borboleta e sensores",
                "aliases": ["corpo de borboleta"],
            },
            "FUEL_AIR_ADMISSION": {"label": "Sistema de admissão de ar", "aliases": ["admissão"]},
            "FUEL_TURBO_SERVICE": {"label": "Turbo e sobrealimentação", "aliases": ["turbo"]},
            "DIAG_SCANNER_OBD": {"label": "Scanner OBD-II", "aliases": ["scanner"]},
            "DIAG_MULTIBRAND": {"label": "Diagnóstico multimarcas", "aliases": ["multimarcas"]},
            "DIAG_ECU_TCU_PROGRAM": {
                "label": "Reprogramação ECU / TCU",
                "aliases": ["reprogramação"],
            },
            "DIAG_CLEAR_CODES": {"label": "Apagar códigos de falha", "aliases": ["apagar códigos"]},
            "DIAG_SENSOR_CALIB": {"label": "Calibração de sensores", "aliases": ["calibração"]},
            "DIAG_SYSTEM_SYNC": {"label": "Sincronização eletrônica", "aliases": ["sincronização"]},
            "DIFF_OIL_CHANGE": {
                "label": "Troca de óleo do diferencial",
                "aliases": ["óleo diferencial"],
            },
            "DIFF_GEAR_INSPECTION": {"label": "Revisão de engrenagens", "aliases": ["engrenagens"]},
            "DIFF_AXLES_CV": {
                "label": "Semieixos e juntas homocinéticas",
                "aliases": ["homocinética"],
            },
            "DIFF_UJOINT_DRIVESHAFT": {"label": "Cruzetas e cardãs", "aliases": ["cardã"]},
            "DIFF_AXLE_SERVICE": {"label": "Eixos dianteiros e traseiros", "aliases": ["eixos"]},
            "ELEC_CHARGING_SYSTEM": {
                "label": "Alternador, bateria e motor de arranque",
                "aliases": ["alternador"],
            },
            "ELEC_FUSES_RELAYS": {"label": "Revisão de fusíveis e relés", "aliases": ["fusíveis"]},
            "ELEC_WIRING_REPAIR": {"label": "Reparo de chicote elétrico", "aliases": ["chicote"]},
            "ELEC_LIGHTING": {"label": "Iluminação externa e interna", "aliases": ["iluminação"]},
            "ELEC_SENSORS": {
                "label": "Sensores (MAF, TPS, O2, temperatura)",
                "aliases": ["sensores"],
            },
            "ELEC_ECU_BCM_TCM": {
                "label": "Módulos ECU, BCM, TCM e reprogramações",
                "aliases": ["módulos"],
            },
            "ELEC_DIAG_COMPLETE": {
                "label": "Diagnóstico elétrico completo",
                "aliases": ["diagnóstico elétrico"],
            },
            "EMISS_MUFFLER_REPLACE": {
                "label": "Troca de silenciador ou escapamento",
                "aliases": ["silenciador"],
            },
            "EMISS_CATALYST_DPF": {
                "label": "Limpeza ou troca de catalisador / DPF",
                "aliases": ["catalisador"],
            },
            "EMISS_O2_SENSORS": {"label": "Sensores de oxigênio", "aliases": ["sensor o2"]},
            "EMISS_EXHAUST_GASKETS": {
                "label": "Revisão de juntas do coletor",
                "aliases": ["junta coletor"],
            },
            "EMISS_PRE_TECH": {
                "label": "Controle técnico pré-vistoria",
                "aliases": ["pré-vistoria"],
            },
            "BRAKE_DIAG": {"label": "Diagnóstico de freios", "aliases": ["diagnóstico freio"]},
            "BRAKE_PAD_CHANGE": {
                "label": "Troca de pastilhas dianteiras ou traseiras",
                "aliases": ["pastilhas"],
            },
            "BRAKE_DISK_RESURFACE": {"label": "Retífica de discos", "aliases": ["retífica"]},
            "BRAKE_DRUM_SERVICE": {"label": "Revisão de tambores e lonas", "aliases": ["tambores"]},
            "BRAKE_FLUID_BLEED": {"label": "Sangria e troca de fluido", "aliases": ["sangria"]},
            "BRAKE_ABS_REPAIR": {"label": "Reparo de ABS e sensores", "aliases": ["abs"]},
            "BRAKE_EBD_CALIB": {"label": "Calibração EBD / ESP", "aliases": ["ebd"]},
            "INSP_PREPURCHASE": {
                "label": "Vistoria pré-compra ou venda",
                "aliases": ["pré-compra"],
            },
            "INSP_PREVENTIVE": {"label": "Controle técnico preventivo", "aliases": ["preventivo"]},
            "INSP_FULL_REPORT": {"label": "Relatório mecânico completo", "aliases": ["relatório"]},
            "INSP_MILEAGE_CERT": {
                "label": "Certificado de quilometragem",
                "aliases": ["quilometragem"],
            },
            "INSP_TRAVEL_CHECK": {"label": "Revisão antes da viagem", "aliases": ["viagem"]},
            "INT_UPHOLSTERY": {
                "label": "Tapeçaria (bancos, teto, painéis)",
                "aliases": ["tapeçaria"],
            },
            "INT_LOCKS_HANDLES": {"label": "Fechaduras e maçanetas", "aliases": ["fechaduras"]},
            "INT_POWER_WINDOWS": {
                "label": "Vidros elétricos e travas",
                "aliases": ["vidros elétricos"],
            },
            "INT_CABIN_AC": {"label": "Ar-condicionado interno", "aliases": ["ar interno"]},
            "INT_AUDIO_NAV": {"label": "Som, GPS e multimídia", "aliases": ["multimídia"]},
            "INT_STEERING_CONTROLS": {"label": "Volante e comandos", "aliases": ["volante"]},
            "INT_SEATBELTS": {"label": "Cintos de segurança", "aliases": ["cintos"]},
            "PM_SCHEDULED_CHECKS": {
                "label": "Revisão de 5.000 / 10.000 / 20.000 km",
                "aliases": ["revisão programada"],
            },
            "PM_OIL_FILTER": {"label": "Troca de óleo e filtros", "aliases": ["troca de óleo"]},
            "PM_FLUIDS_LEVELS": {
                "label": "Verificação de fluidos e níveis",
                "aliases": ["fluidos"],
            },
            "PM_QUICK_SCAN": {"label": "Scanner rápido", "aliases": ["scanner rápido"]},
            "PM_TRAVEL_CHECK": {"label": "Check antes da viagem", "aliases": ["check viagem"]},
            "ENGINE_DIAG": {"label": "Diagnóstico de motor", "aliases": ["diagnóstico motor"]},
            "ENGINE_REBUILD": {"label": "Reparo ou retífica completa", "aliases": ["retífica"]},
            "ENGINE_SEALS_LUBE": {"label": "Lubrificação e retentores", "aliases": ["retentores"]},
            "ENGINE_TIMING_BELT": {"label": "Correia dentada", "aliases": ["correia"]},
            "ENGINE_HEAD_VALVES": {
                "label": "Cabeçote, válvulas e virabrequim",
                "aliases": ["cabeçote"],
            },
            "ENGINE_TRANSMISSION_BOX": {
                "label": "Caixa de câmbio manual/automática",
                "aliases": ["caixa de câmbio"],
            },
            "ENGINE_CLUTCH_FLYWHEEL": {"label": "Embreagem e volante", "aliases": ["embreagem"]},
            "ENGINE_COOLING_PUMP": {
                "label": "Sistema de arrefecimento e bomba d'água",
                "aliases": ["arrefecimento"],
            },
            "TIRE_MOUNT": {"label": "Montagem e desmontagem", "aliases": ["montagem"]},
            "TIRE_PUNCTURE_REPAIR": {"label": "Reparo de furos", "aliases": ["furo"]},
            "TIRE_ALIGN_BALANCE": {
                "label": "Alinhamento e balanceamento",
                "aliases": ["alinhamento"],
            },
            "TIRE_ROTATION": {"label": "Rodízio de pneus", "aliases": ["rodízio"]},
            "TIRE_WHEEL_REPAIR": {"label": "Reparo ou solda de rodas", "aliases": ["roda"]},
            "TIRE_SALES": {"label": "Venda de pneus e válvulas", "aliases": ["venda pneus"]},
            "CUSTOM_LIGHTING": {"label": "Iluminação LED / Xenon", "aliases": ["iluminação"]},
            "CUSTOM_BODY_KIT": {"label": "Kit esportivo ou body kit", "aliases": ["body kit"]},
            "CUSTOM_TUNING": {"label": "Chip tuning / remapeamento", "aliases": ["remap"]},
            "CUSTOM_SPORT_SUSP": {
                "label": "Suspensão esportiva",
                "aliases": ["suspensão esportiva"],
            },
            "CUSTOM_AUDIO": {"label": "Som personalizado", "aliases": ["som"]},
            "CUSTOM_ACCESSORIES": {
                "label": "Acessórios estéticos e funcionais",
                "aliases": ["acessórios"],
            },
            "SAFETY_AIRBAGS": {"label": "Airbags (revisão e troca)", "aliases": ["airbag"]},
            "SAFETY_COLLISION_SENSORS": {
                "label": "Sensores de colisão",
                "aliases": ["sensor colisão"],
            },
            "SAFETY_TRACTION_CONTROL": {
                "label": "Controle de tração / estabilidade",
                "aliases": ["controle de tração"],
            },
            "SAFETY_ADAS_CALIB": {"label": "Calibração ADAS", "aliases": ["adas"]},
            "SAFETY_PARKING_SENSORS": {
                "label": "Sensores de estacionamento e câmeras",
                "aliases": ["sensores de estacionamento"],
            },
            "SAFETY_ALARMS": {"label": "Alarmes e travamento central", "aliases": ["alarmes"]},
            "EMERGENCY_TOWING": {"label": "Serviço de guincho", "aliases": ["guincho"]},
            "EMERGENCY_MOBILE_DIAG": {"label": "Diagnóstico móvel", "aliases": ["móvel"]},
            "EMERGENCY_ROADSIDE_BATTERY": {
                "label": "Troca de bateria ou pneu no local",
                "aliases": ["bateria no local"],
            },
            "EMERGENCY_ROADSIDE_ASSIST": {
                "label": "Assistência na estrada",
                "aliases": ["assistência"],
            },
            "QUICK_OIL_FILTER": {
                "label": "Troca rápida de óleo e filtro",
                "aliases": ["troca rápida"],
            },
            "QUICK_BRAKE_CHECK": {"label": "Check rápido de freios", "aliases": ["check freios"]},
            "QUICK_BATTERY_TEST": {"label": "Teste de bateria", "aliases": ["teste bateria"]},
            "QUICK_WIPERS": {"label": "Troca de palhetas", "aliases": ["palhetas"]},
            "QUICK_LIGHTS_LEVELS": {"label": "Verificação de luzes e níveis", "aliases": ["luzes"]},
            "OFFROAD_TRANSFER_CASE": {
                "label": "Revisão da caixa de transferência",
                "aliases": ["transferência"],
            },
            "OFFROAD_DIFFERENTIALS": {
                "label": "Manutenção de diferenciais 4WD",
                "aliases": ["4wd"],
            },
            "OFFROAD_COUPLINGS": {
                "label": "Acoplamentos e tração total",
                "aliases": ["acoplamentos"],
            },
            "OFFROAD_PREP": {"label": "Preparação off-road", "aliases": ["off-road"]},
            "OFFROAD_WINCH_PROTECTION": {
                "label": "Instalação de guinchos e proteções",
                "aliases": ["guincho"],
            },
            "SUSP_SHOCKS_SPRINGS": {"label": "Amortecedores e molas", "aliases": ["amortecedores"]},
            "SUSP_TIE_RODS": {"label": "Terminais e pivôs", "aliases": ["terminais"]},
            "SUSP_CONTROL_ARMS": {"label": "Bandejas e buchas", "aliases": ["buchas"]},
            "SUSP_STEERING_RACK": {"label": "Caixa de direção", "aliases": ["caixa direção"]},
            "SUSP_ALIGNMENT": {"label": "Alinhamento", "aliases": ["alinhamento"]},
            "SUSP_AIR_SYSTEM": {
                "label": "Suspensão pneumática ou eletrônica",
                "aliases": ["suspensão pneumática"],
            },
            "TUNE_OIL_FILTER": {"label": "Troca de óleo e filtro", "aliases": ["troca de óleo"]},
            "TUNE_FILTERS_REPLACE": {
                "label": "Troca dos filtros de ar, combustível e cabine",
                "aliases": ["filtros"],
            },
            "TUNE_SPARK_IGNITION": {
                "label": "Troca de velas, cabos e bobinas",
                "aliases": ["velas"],
            },
            "TUNE_THROTTLE_CLEAN": {
                "label": "Limpeza de corpo de borboleta e injetores",
                "aliases": ["limpeza corpo"],
            },
            "TUNE_DISTRIBUTOR_CHECK": {
                "label": "Revisão de distribuidor (veículos antigos)",
                "aliases": ["distribuidor"],
            },
            "TUNE_MIX_IDLE": {
                "label": "Acerto de mistura e marcha lenta",
                "aliases": ["marcha lenta"],
            },
            "TUNE_SENSOR_CLEAN": {
                "label": "Limpeza de sensores (MAF, TPS, O2)",
                "aliases": ["limpeza sensores"],
            },
            "TUNE_ECU_RESET": {"label": "Scanner e reset da ECU", "aliases": ["reset ecu"]},
            "TUNE_COOLING_CHECK": {
                "label": "Revisão do sistema de arrefecimento",
                "aliases": ["arrefecimento"],
            },
            "TUNE_DIESEL_SERVICE": {
                "label": "Regulagem diesel (filtros, injetores, velas aquecedoras, EGR, DPF)",
                "aliases": ["diesel"],
            },
            "GLASS_WINDSHIELD_REPLACE": {
                "label": "Troca de para-brisa e vidros laterais",
                "aliases": ["para-brisa"],
            },
            "GLASS_TINT": {"label": "Insulfilm / polarização", "aliases": ["insulfilm"]},
            "GLASS_LEAK_SEAL": {"label": "Vedação de infiltrações", "aliases": ["vedação"]},
            "GLASS_MIRROR_REPLACE": {"label": "Troca de retrovisores", "aliases": ["retrovisor"]},
            "GLASS_WINDOW_LIFTER": {
                "label": "Vidro elétrico / manual",
                "aliases": ["mecanismo vidro"],
            },
            "GLASS_RAIN_SENSOR_CALIB": {
                "label": "Calibração de sensores de chuva e luz",
                "aliases": ["sensor chuva"],
            },
        },
    },
}


def get_category_data(country, code):
    base = deepcopy(BASE_CATEGORIES[code])
    overrides = COUNTRY_OVERRIDES.get(country, {}).get("categories", {})
    if code in overrides:
        base.update({k: deepcopy(v) for k, v in overrides[code].items()})
    return base


def get_subservice_data(country, sub_code, base_data):
    overrides = COUNTRY_OVERRIDES.get(country, {}).get("subservices", {})
    if sub_code in overrides:
        merged = deepcopy(base_data)
        merged.update(overrides[sub_code])
        return merged
    return base_data


def normalize_aliases(value):
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def ensure_category(country, code, language, label, aliases):
    cat, created = CategoriaServicio.objects.get_or_create(
        country=country,
        code=code,
        defaults={},
    )
    CategoriaServicioName.objects.update_or_create(
        categoria=cat,
        language=language,
        is_default=True,
        defaults={"label": label, "aliases": normalize_aliases(aliases)},
    )
    return cat, created


def ensure_subcategory(category, country, code, language, label, aliases):
    sub, created = SubcategoriaServicio.objects.get_or_create(
        categoria=category,
        code=code,
        defaults={"country": country},
    )
    sub.country = country
    sub.save(update_fields=["country"])
    SubcategoriaServicioName.objects.update_or_create(
        subcategoria=sub,
        language=language,
        is_default=True,
        defaults={"label": label, "aliases": normalize_aliases(aliases)},
    )
    return sub, created


@transaction.atomic
def run():
    summary = []
    for country, language in COUNTRY_LANG.items():
        cat_created = 0
        sub_created = 0
        for code, cat_data in BASE_CATEGORIES.items():
            resolved = get_category_data(country, code)
            cat, created = ensure_category(
                country,
                code,
                language,
                resolved["label"],
                resolved.get("aliases", []),
            )
            if created:
                cat_created += 1
            for sub_code, sub_data in cat_data["subservices"].items():
                resolved_sub = get_subservice_data(country, sub_code, sub_data)
                _, sub_created_flag = ensure_subcategory(
                    cat,
                    country,
                    sub_code,
                    language,
                    resolved_sub["label"],
                    resolved_sub.get("aliases", []),
                )
                if sub_created_flag:
                    sub_created += 1
        summary.append((country, cat_created, sub_created))

    print("✅ Categorías de servicios actualizadas")
    for country, cats, subs in summary:
        print(f"  • {country}: {cats} categorías nuevas, {subs} subcategorías nuevas")


if __name__ == "__main__":
    run()
