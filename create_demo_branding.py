# Crear usuario y configuración de empresa de prueba
from django.contrib.auth.models import User
from taller.models import CompanySettings

# Crear usuario de prueba
user, created = User.objects.get_or_create(
    username='demo_taller',
    defaults={
        'email': 'demo@tallerdemo.cl',
        'first_name': 'Juan',
        'last_name': 'Pérez'
    }
)

if created:
    print(f"✅ Usuario {user.username} creado")
else:
    print(f"ℹ️ Usuario {user.username} ya existía")

# Crear configuración de empresa
settings, created = CompanySettings.objects.get_or_create(
    user=user,
    defaults={
        'company_name': 'Taller Pérez & Asociados',
        'tagline': 'Expertos en reparación automotriz',
        'primary_color': '#e74c3c',  # Rojo elegante
        'secondary_color': '#3498db',  # Azul
        'address': 'Av. Los Leones 1234, Las Condes, Santiago',
        'phone': '+56 2 2345 6789',
        'email': 'contacto@tallerperez.cl',
        'website': 'https://www.tallerperez.cl',
        'tax_id': '76.123.456-7',
        'business_license': 'LIC-AUTO-2024-001',
        'currency': 'CLP',
        'invoice_prefix': 'FACT',
        'quote_prefix': 'COT',
        'work_order_prefix': 'OT',
        'about_text': 'Somos un taller especializado con más de 20 años de experiencia en reparación y mantención de vehículos. Contamos con tecnología de punta y personal altamente calificado.',
        'terms_and_conditions': 'Los trabajos realizados tienen garantía de 30 días. Los repuestos mantienen la garantía del fabricante. El cliente debe retirar el vehículo en un plazo máximo de 30 días.',
    }
)

if created:
    print(f"✅ Configuración para {settings.company_name} creada")
else:
    print(f"ℹ️ Configuración para {settings.company_name} ya existía")

# Mostrar información
print(f"\n📋 Configuración de empresa:")
print(f"   • Nombre: {settings.company_name}")
print(f"   • Eslogan: {settings.tagline}")
print(f"   • Color primario: {settings.primary_color}")
print(f"   • Email: {settings.email}")
print(f"   • Teléfono: {settings.phone}")

# Probar métodos del modelo
print(f"\n🧪 Pruebas de métodos:")
print(f"   • get_company_name(): {settings.get_company_name()}")
print(f"   • get_logo_url(): {settings.get_logo_url()}")
print(f"   • get_primary_color(): {settings.get_primary_color()}")
print(f"   • get_secondary_color(): {settings.get_secondary_color()}")

print(f"\n✅ Sistema de branding configurado correctamente!")
print(f"🔗 Puedes acceder a la configuración en: /settings/")
