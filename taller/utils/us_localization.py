from decimal import Decimal, ROUND_HALF_UP
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import locale

class USDCurrencyMixin:
    """Mixin para manejo de moneda USD"""
    
    @staticmethod
    def format_usd(amount):
        """Formatear cantidad como USD"""
        if amount is None:
            return "$0.00"
        
        # Redondear a 2 decimales
        amount = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Formatear con comas para miles
        return f"${amount:,.2f}"
    
    @staticmethod
    def parse_usd_string(amount_str):
        """Convertir string USD a Decimal"""
        if not amount_str:
            return Decimal('0.00')
        
        # Remover símbolos y espacios
        clean_str = amount_str.replace('$', '').replace(',', '').strip()
        try:
            return Decimal(clean_str).quantize(Decimal('0.01'))
        except:
            return Decimal('0.00')

class USTaxCalculator:
    """Calculadora de impuestos para el mercado estadounidense"""
    
    def __init__(self, estado=None, ciudad=None):
        self.estado = estado
        self.ciudad = ciudad
    
    def calcular_sales_tax(self, subtotal):
        """Calcular sales tax basado en ubicación"""
        if not subtotal:
            return Decimal('0.00')
        
        subtotal = Decimal(str(subtotal))
        tax_rate = self.get_tax_rate()
        
        tax_amount = subtotal * tax_rate / 100
        return tax_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def get_tax_rate(self):
        """Obtener tasa de impuesto por ubicación"""
        # Importar aquí para evitar circular imports
        from taller.models.ubicacion import Estado, Ciudad
        
        try:
            if self.ciudad:
                ciudad_obj = Ciudad.objects.get(id=self.ciudad)
                # Usar sales_tax_total que incluye estado + local
                return ciudad_obj.sales_tax_total
            
            if self.estado:
                estado_obj = Estado.objects.get(id=self.estado)
                if estado_obj.sales_tax:
                    return estado_obj.sales_tax
                    
        except (Estado.DoesNotExist, Ciudad.DoesNotExist):
            pass
        
        # Tasa por defecto para Georgia (Atlanta)
        return Decimal('8.90')  # 4% estado + 4.9% local promedio Atlanta
    
    def calcular_total_con_tax(self, subtotal):
        """Calcular total incluyendo sales tax"""
        if not subtotal:
            return {
                'subtotal': Decimal('0.00'),
                'tax': Decimal('0.00'),
                'total': Decimal('0.00'),
                'tax_rate': self.get_tax_rate()
            }
        
        subtotal = Decimal(str(subtotal))
        tax = self.calcular_sales_tax(subtotal)
        total = subtotal + tax
        
        return {
            'subtotal': subtotal.quantize(Decimal('0.01')),
            'tax': tax,
            'total': total.quantize(Decimal('0.01')),
            'tax_rate': self.get_tax_rate()
        }

class USServiceTranslator:
    """Traductor de servicios al inglés americano"""
    
    SERVICIOS_EN = {
        'Cambio de aceite': 'Oil Change',
        'Rotación de llantas': 'Tire Rotation', 
        'Frenos': 'Brake Service',
        'Batería': 'Battery Service',
        'Transmisión': 'Transmission Service',
        'Aire acondicionado': 'AC Service',
        'Alineación': 'Wheel Alignment',
        'Suspensión': 'Suspension Service',
        'Escape': 'Exhaust Service',
        'Motor': 'Engine Service',
        'Filtros': 'Filter Replacement',
        'Bujías': 'Spark Plugs',
        'Radiador': 'Radiator Service',
        'Diagnóstico': 'Diagnostic',
        'Inspección': 'Inspection',
        'Mantenimiento preventivo': 'Preventive Maintenance',
        'Reparación general': 'General Repair',
        'Sistema eléctrico': 'Electrical System',
        'Sistema de combustible': 'Fuel System',
        'Embrague': 'Clutch Service'
    }
    
    REPUESTOS_EN = {
        'Aceite': 'Motor Oil',
        'Filtro de aceite': 'Oil Filter',
        'Filtro de aire': 'Air Filter',
        'Pastillas de freno': 'Brake Pads',
        'Discos de freno': 'Brake Rotors',
        'Batería': 'Battery',
        'Bujías': 'Spark Plugs',
        'Cables de bujía': 'Spark Plug Wires',
        'Correa de distribución': 'Timing Belt',
        'Correa del alternador': 'Alternator Belt',
        'Termostato': 'Thermostat',
        'Bomba de agua': 'Water Pump',
        'Radiador': 'Radiator',
        'Mangueras': 'Hoses',
        'Amortiguadores': 'Shock Absorbers',
        'Resortes': 'Springs',
        'Neumáticos': 'Tires',
        'Llantas': 'Wheels',
        'Escape': 'Exhaust System'
    }
    
    @classmethod
    def traducir_servicio(cls, servicio_es):
        """Traducir nombre de servicio al inglés"""
        return cls.SERVICIOS_EN.get(servicio_es, servicio_es)
    
    @classmethod
    def traducir_repuesto(cls, repuesto_es):
        """Traducir nombre de repuesto al inglés"""
        return cls.REPUESTOS_EN.get(repuesto_es, repuesto_es)
    
    @classmethod
    def get_servicios_bilingue(cls):
        """Obtener lista de servicios en ambos idiomas"""
        return [
            {'es': es, 'en': en} 
            for es, en in cls.SERVICIOS_EN.items()
        ]

class USDateTimeHelper:
    """Helper para manejo de fechas y zonas horarias USA"""
    
    TIMEZONES_USA = {
        'Eastern': 'America/New_York',
        'Central': 'America/Chicago', 
        'Mountain': 'America/Denver',
        'Pacific': 'America/Los_Angeles',
        'Alaska': 'America/Anchorage',
        'Hawaii': 'Pacific/Honolulu'
    }
    
    @staticmethod
    def get_timezone_by_state(estado_nombre):
        """Obtener timezone por estado"""
        # Mapeo de estados a timezones
        STATE_TIMEZONES = {
            'Georgia': 'America/New_York',
            'Florida': 'America/New_York', 
            'New York': 'America/New_York',
            'California': 'America/Los_Angeles',
            'Texas': 'America/Chicago',
            'Illinois': 'America/Chicago',
            'Arizona': 'America/Phoenix',  # No observa DST
            'Nevada': 'America/Los_Angeles',
            'Washington': 'America/Los_Angeles',
            'Colorado': 'America/Denver',
            'Alaska': 'America/Anchorage',
            'Hawaii': 'Pacific/Honolulu',
        }
        
        return STATE_TIMEZONES.get(estado_nombre, 'America/New_York')  # Default Eastern
    
    @staticmethod
    def format_us_date(date_obj):
        """Formatear fecha al estilo estadounidense MM/DD/YYYY"""
        if not date_obj:
            return ""
        return date_obj.strftime("%m/%d/%Y")
    
    @staticmethod  
    def format_us_datetime(datetime_obj):
        """Formatear fecha y hora al estilo estadounidense"""
        if not datetime_obj:
            return ""
        return datetime_obj.strftime("%m/%d/%Y %I:%M %p")  # 12-hour format with AM/PM
