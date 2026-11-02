from urllib.parse import quote

from django.conf import settings


COUNTRY_WHATSAPP_COPY = {
    "cl": {
        "button": "📲 Probar demo gratis por WhatsApp",
        "secondary": "Hablar con un asesor al tiro",
        "message": "Hola, me interesa probar eGarage gratis para mi {rubro_local} en Chile.",
        "generic_rubro": "negocio automotriz",
        "rubros": {
            "workshop": "Taller mecánico",
            "salvage": "Desarmaduría",
            "parts": "Casa de repuestos",
            "tire": "Vulcanización",
            "carwash": "Carwash",
            "recycling": "Recicladora",
            "bodyshop": "Bodyshop",
        },
    },
    "br": {
        "button": "📲 Testar demo grátis no WhatsApp",
        "secondary": "Falar com um consultor",
        "message": "Olá! Gostaria de testar o eGarage grátis na minha {rubro_local} no Brasil.",
        "generic_rubro": "empresa automotiva",
        "rubros": {
            "workshop": "Oficina mecânica",
            "salvage": "Desmanche / Ferro-velho",
            "parts": "Autopeças",
            "tire": "Borracharia",
            "carwash": "Lava-jato",
            "recycling": "Recicladora",
            "bodyshop": "Funilaria e pintura",
        },
    },
    "mx": {
        "button": "📲 Probar demo gratis por WhatsApp",
        "secondary": "Pedir acceso sin costo",
        "message": "Hola, me gustaría probar la demo de eGarage para mi {rubro_local} en México.",
        "generic_rubro": "negocio automotriz",
        "rubros": {
            "workshop": "Taller mecánico",
            "salvage": "Yonke / Deshuesadero",
            "parts": "Refaccionaria",
            "tire": "Llantera",
            "carwash": "Autolavado",
            "recycling": "Recicladora",
            "bodyshop": "Hojalatería y pintura",
        },
    },
    "us_en": {
        "button": "📲 Try Free Demo on WhatsApp",
        "secondary": "Get started now",
        "message": "Hi! I want to try eGarage free demo for my {rubro_local} in the US.",
        "generic_rubro": "automotive business",
        "rubros": {
            "workshop": "auto shop",
            "salvage": "salvage yard / junkyard",
            "parts": "auto parts store",
            "tire": "tire shop",
            "carwash": "car wash",
            "recycling": "recycling business",
            "bodyshop": "body shop",
        },
    },
    "us_es": {
        "button": "📲 Probar demo gratis por WhatsApp",
        "secondary": "Pedir acceso ahora",
        "message": "Hola, quiero probar eGarage gratis para mi {rubro_local} en Estados Unidos.",
        "generic_rubro": "negocio automotriz",
        "rubros": {
            "workshop": "Taller mecánico",
            "salvage": "Yonke / Junkyard",
            "parts": "Auto parts",
            "tire": "Tire shop",
            "carwash": "Car wash",
            "recycling": "Recicladora",
            "bodyshop": "Bodyshop",
        },
    },
    "ar": {
        "button": "📲 Probá la demo gratis por WhatsApp",
        "secondary": "Pedí tu acceso sin cargo",
        "message": "Hola, quiero probar eGarage gratis para mi {rubro_local} en Argentina.",
        "generic_rubro": "negocio automotor",
        "rubros": {
            "workshop": "Taller mecánico",
            "salvage": "Desarmadero",
            "parts": "Casa de repuestos",
            "tire": "Gomería",
            "carwash": "Lavadero",
            "recycling": "Recicladora",
            "bodyshop": "Chapa y pintura",
        },
    },
    "co": {
        "button": "📲 Probar demo gratis por WhatsApp",
        "secondary": "Solicitar prueba ya mismo",
        "message": "Hola, me interesa probar eGarage sin costo para mi {rubro_local} en Colombia.",
        "generic_rubro": "negocio automotriz",
        "rubros": {
            "workshop": "Taller mecánico",
            "salvage": "Chivera",
            "parts": "Almacén de repuestos",
            "tire": "Montallantas",
            "carwash": "Lavadero",
            "recycling": "Recicladora",
            "bodyshop": "Latonería y pintura",
        },
    },
    "pe": {
        "button": "📲 Probar demo gratis por WhatsApp",
        "secondary": "Pedir acceso sin costo",
        "message": "Hola, me interesa probar eGarage gratis para mi {rubro_local} en Perú.",
        "generic_rubro": "negocio automotriz",
        "rubros": {
            "workshop": "Taller mecánico",
            "salvage": "Desarmadero",
            "parts": "Casa de repuestos",
            "tire": "Llantería",
            "carwash": "Lavado de autos",
            "recycling": "Recicladora",
            "bodyshop": "Planchado y pintura",
        },
    },
    "ec": {
        "button": "📲 Probar demo gratis por WhatsApp",
        "secondary": "Solicitar prueba gratis",
        "message": "Hola, quiero probar eGarage sin costo para mi {rubro_local} en Ecuador.",
        "generic_rubro": "negocio automotriz",
        "rubros": {
            "workshop": "Taller mecánico",
            "salvage": "Chatarrería",
            "parts": "Almacén de repuestos",
            "tire": "Llantera",
            "carwash": "Lavado de autos",
            "recycling": "Recicladora",
            "bodyshop": "Enderezada y pintura",
        },
    },
    "ve": {
        "button": "📲 Probar demo gratis por WhatsApp",
        "secondary": "Pedir acceso sin costo",
        "message": "Hola, quiero probar eGarage gratis para mi {rubro_local} en Venezuela.",
        "generic_rubro": "negocio automotriz",
        "rubros": {
            "workshop": "Taller mecánico",
            "salvage": "Desarmadero",
            "parts": "Casa de repuestos",
            "tire": "Cauchera",
            "carwash": "Lavado de autos",
            "recycling": "Recicladora",
            "bodyshop": "Latonería y pintura",
        },
    },
}


COUNTRY_ALIASES = {
    "us": "us_en",
    "usa": "us_en",
}


def normalize_country_key(country_key: str) -> str:
    key = (country_key or "cl").lower()
    return COUNTRY_ALIASES.get(key, key)


def get_whatsapp_contact_number() -> str:
    raw = str(getattr(settings, "WHATSAPP_CONTACT_NUMBER", "") or "")
    digits = "".join(ch for ch in raw if ch.isdigit())
    if digits:
        return digits
    fallback = str(getattr(settings, "SUPPORT_WHATSAPP_WA_ME", "56953574683") or "")
    return "".join(ch for ch in fallback if ch.isdigit())


def get_whatsapp_cta_context(country_key: str, vertical_key: str | None = None) -> dict:
    key = normalize_country_key(country_key)
    copy = COUNTRY_WHATSAPP_COPY.get(key, COUNTRY_WHATSAPP_COPY["cl"])
    rubro_local = copy["rubros"].get(vertical_key or "", copy["generic_rubro"])
    message = copy["message"].format(rubro_local=rubro_local)
    number = get_whatsapp_contact_number()
    return {
        "button_label": copy["button"],
        "secondary_label": copy["secondary"],
        "message": message,
        "encoded_message": quote(message, safe=""),
        "number": number,
        "url": f"https://wa.me/{number}?text={quote(message, safe='')}",
        "country_key": key,
        "vertical_key": vertical_key or "hub",
        "rubro_local": rubro_local,
    }
