from django.shortcuts import render
from django.utils.translation import gettext as _

def landing_usa(request):
    """
    Landing page optimizada para USA (bilingüe ES/EN)
    """
    context = {
        'hero_title_en': "America's #1 AI-Powered Auto Shop Platform",
        'hero_title_es': "La plataforma #1 de talleres con IA en USA",
        'hero_subtitle_en': "Grow your shop with real-time AI, smart quotes, and local tax compliance.",
        'hero_subtitle_es': "Haz crecer tu taller con IA, cotizaciones inteligentes y cumplimiento fiscal local.",
        'benefits': [
            {
                'icon': 'fas fa-robot',
                'en': 'AI-powered recommendations for every job',
                'es': 'Recomendaciones de IA para cada servicio'
            },
            {
                'icon': 'fas fa-dollar-sign',
                'en': 'Automatic sales tax calculation (all 50 states)',
                'es': 'Cálculo automático de impuestos en los 50 estados'
            },
            {
                'icon': 'fas fa-car',
                'en': 'US vehicle database: 1980-2025',
                'es': 'Base de datos de vehículos USA: 1980-2025'
            },
            {
                'icon': 'fas fa-globe-americas',
                'en': 'Bilingual interface (English/Español)',
                'es': 'Interfaz bilingüe (English/Español)'
            },
            {
                'icon': 'fas fa-bolt',
                'en': 'Lightning-fast quotes & invoices',
                'es': 'Cotizaciones y facturas instantáneas'
            },
        ],
        'demo_gif': '/static/img/demo_usa.gif',
        'register_url': '/registro/?utm_source=landing_usa',
        'seo_title': "eGarage USA | AI Auto Shop Software | TallerPro USA",
        'seo_description': "Try eGarage, the #1 AI-powered auto shop management system for the US. Bilingual, tax-compliant, and ready for your shop. Free trial.",
        'og_image': '/static/img/og_usa_landing.png',
    }
    return render(request, 'landing/usa_landing.html', context)
