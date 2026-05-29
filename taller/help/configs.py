"""
Configuraciones para el sistema de ayuda de eGarage
Contenido estático organizado para fácil ampliación futura
"""

# FAQs organizadas por módulo
FAQS = {
    "general": [
        {
            "pregunta": "¿Cómo acceder al sistema?",
            "respuesta": "Inicia sesión con tu usuario y contraseña en la página principal.",
            "categoria": "general",
        },
        {
            "pregunta": "¿Cómo cambiar mi contraseña?",
            "respuesta": "Ve a Configuración > Perfil y selecciona 'Cambiar contraseña'.",
            "categoria": "general",
        },
    ],
    "clientes": [
        {
            "pregunta": "¿Cómo agregar un nuevo cliente?",
            "respuesta": "En el módulo Clientes, haz clic en 'Nuevo Cliente' y completa el formulario.",
            "categoria": "clientes",
        },
        {
            "pregunta": "¿Cómo buscar un cliente existente?",
            "respuesta": "Usa la barra de búsqueda en el módulo Clientes o filtra por nombre, teléfono, etc.",
            "categoria": "clientes",
        },
    ],
    "vehiculos": [
        {
            "pregunta": "¿Cómo registrar un nuevo vehículo?",
            "respuesta": "En el módulo Vehículos, selecciona 'Nuevo Vehículo' y ingresa los datos del cliente y vehículo.",
            "categoria": "vehiculos",
        }
    ],
    "taller": [
        {
            "pregunta": "¿Cómo crear una nueva orden de trabajo?",
            "respuesta": "En el módulo Taller, haz clic en 'Nueva Orden' y selecciona el cliente y vehículo.",
            "categoria": "taller",
        }
    ],
}

# Pasos recomendados por módulo
PASOS_RECOMENDADOS = {
    "clientes": [
        {
            "titulo": "Registro de nuevo cliente",
            "pasos": [
                "Accede al módulo Clientes",
                "Haz clic en 'Nuevo Cliente'",
                "Completa los campos obligatorios (nombre, teléfono, email)",
                "Guarda el registro",
            ],
        },
        {
            "titulo": "Búsqueda de cliente",
            "pasos": [
                "Ve al módulo Clientes",
                "Usa la barra de búsqueda superior",
                "Filtra por nombre, teléfono o email",
                "Selecciona el cliente deseado",
            ],
        },
    ],
    "vehiculos": [
        {
            "titulo": "Registro de vehículo",
            "pasos": [
                "Accede al módulo Vehículos",
                "Haz clic en 'Nuevo Vehículo'",
                "Selecciona o registra el cliente propietario",
                "Ingresa placa, marca, modelo y año",
                "Guarda el registro",
            ],
        }
    ],
    "taller": [
        {
            "titulo": "Creación de orden de trabajo",
            "pasos": [
                "Ve al módulo Taller",
                "Haz clic en 'Nueva Orden'",
                "Selecciona cliente y vehículo",
                "Agrega servicios y repuestos necesarios",
                "Guarda y confirma la orden",
            ],
        },
        {
            "titulo": "Cierre de orden de trabajo",
            "pasos": [
                "Abre la orden de trabajo",
                "Verifica que todos los trabajos estén completados",
                "Ingresa costos finales",
                "Cambia el estado a 'Completada'",
                "Imprime o envía la factura",
            ],
        },
    ],
}

# Configuración del panel de ayuda
PANEL_AYUDA_CONFIG = {
    "secciones": [
        {
            "titulo": "Artículos de Ayuda",
            "tipo": "articulos",
            "descripcion": "Encuentra guías detalladas sobre funcionalidades del sistema",
        },
        {
            "titulo": "Preguntas Frecuentes",
            "tipo": "faqs",
            "descripcion": "Respuestas rápidas a las preguntas más comunes",
        },
        {
            "titulo": "Pasos Recomendados",
            "tipo": "pasos",
            "descripcion": "Guías paso a paso para tareas comunes por módulo",
        },
    ],
    "modulos_disponibles": ["clientes", "vehiculos", "taller", "repuestos", "reportes"],
}
