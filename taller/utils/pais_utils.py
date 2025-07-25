"""
Utilidades para manejo de países y localización
"""

def get_marcas_por_pais(user):
    """
    Retorna las marcas de vehículos según el país del usuario
    """
    if hasattr(user, 'empresa') and user.empresa.pais == 'US':
        from taller.models.marcas_usa import MarcaVehiculo
        return MarcaVehiculo.objects.filter(pais_origen='USA', activa=True)
    else:
        from taller.models.marca import Marca
        return Marca.objects.all()

def get_configuracion_pais(empresa):
    """
    Retorna configuración específica según el país de la empresa
    """
    if empresa.pais == 'US':
        return {
            'moneda': 'USD',
            'simbolo_moneda': '$',
            'decimales': 2,
            'idioma_default': 'en',
            'formato_fecha': '%m/%d/%Y',
            'zona_horaria_default': 'America/New_York',
            'validacion_patente': r'^[A-Z0-9]{2,7}$',  # Formato USA más flexible
            'impuesto_default': 0.08,  # 8% promedio sales tax USA
        }
    else:  # Chile
        return {
            'moneda': 'CLP',
            'simbolo_moneda': '$',
            'decimales': 0,
            'idioma_default': 'es',
            'formato_fecha': '%d/%m/%Y',
            'zona_horaria_default': 'America/Santiago',
            'validacion_patente': r'^[A-Z]{2}\d{4}$',  # Formato Chile: AA1234
            'impuesto_default': 0.19,  # 19% IVA Chile
        }

def formatear_precio(precio, empresa):
    """
    Formatea el precio según el país de la empresa
    """
    config = get_configuracion_pais(empresa)
    
    if config['decimales'] > 0:
        return f"{config['simbolo_moneda']}{precio:.{config['decimales']}f} {config['moneda']}"
    else:
        return f"{config['simbolo_moneda']}{precio:,.0f} {config['moneda']}"

def get_modelos_por_marca_y_pais(marca_id, user):
    """
    Retorna modelos filtrados por marca y país del usuario
    """
    if hasattr(user, 'empresa') and user.empresa.pais == 'US':
        # Para USA, usar el sistema de MarcaVehiculo (si existe ModeloVehiculo)
        try:
            from taller.models.marcas_usa import ModeloVehiculo
            return ModeloVehiculo.objects.filter(marca_id=marca_id, activo=True)
        except ImportError:
            # Si no existe ModeloVehiculo, usar el sistema tradicional
            from taller.models.modelo import Modelo
            return Modelo.objects.filter(marca_id=marca_id)
    else:
        # Para Chile, usar el sistema tradicional
        from taller.models.modelo import Modelo
        return Modelo.objects.filter(marca_id=marca_id)

def validar_patente_por_pais(patente, pais):
    """
    Valida formato de patente según el país
    """
    import re
    
    if pais == 'US':
        # USA: formatos variados por estado, más flexible
        return bool(re.match(r'^[A-Z0-9]{2,8}$', patente.upper()))
    else:
        # Chile: formato AA1234 o ABCD12
        return bool(re.match(r'^[A-Z]{2,4}\d{2,4}$', patente.upper()))

def get_regiones_por_pais(pais):
    """
    Retorna regiones/estados según el país
    """
    if pais == 'US':
        # Estados de USA
        return [
            ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'),
            ('CA', 'California'), ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'),
            ('FL', 'Florida'), ('GA', 'Georgia'), ('HI', 'Hawaii'), ('ID', 'Idaho'),
            ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'), ('KS', 'Kansas'),
            ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'), ('MD', 'Maryland'),
            ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'),
            ('MO', 'Missouri'), ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'),
            ('NH', 'New Hampshire'), ('NJ', 'New Jersey'), ('NM', 'New Mexico'), ('NY', 'New York'),
            ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'), ('OK', 'Oklahoma'),
            ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'),
            ('SD', 'South Dakota'), ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'),
            ('VT', 'Vermont'), ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'),
            ('WI', 'Wisconsin'), ('WY', 'Wyoming')
        ]
    else:
        # Regiones de Chile
        from taller.models.region_ciudad import TallerRegion
        return [(str(r.pk), r.nombre) for r in TallerRegion.objects.all()]

def validar_telefono_por_pais(telefono, pais):
    """
    Valida formato de teléfono según el país
    """
    import re
    
    if pais == 'US':
        # USA: (123) 456-7890 o 123-456-7890 o 1234567890
        patron = r'^(\+1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$'
        return bool(re.match(patron, telefono))
    else:
        # Chile: +56912345678 o 912345678 o 22345678
        patron = r'^(\+56)?[0-9]{8,9}$'
        return bool(re.match(patron, telefono.replace(' ', '').replace('-', '')))
