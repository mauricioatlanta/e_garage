#!/usr/bin/env python
"""
Script para poblar datos de ejemplo en el sistema multilenguaje de servicios
Crea categorías, servicios y nombres en español e inglés para ambos países
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')
django.setup()

from taller.servicios.models import (
    CategoriaServicio, CategoriaServicioName,
    SubcategoriaServicio, SubcategoriaServicioName, 
    Servicio, ServicioName
)


def create_categories_and_services():
    """Crea categorías y servicios de ejemplo para ambos países"""
    
    print("🏗️ Creando categorías de servicios...")
    
    # === CATEGORÍAS PARA CHILE ===
    cat_motor_cl = CategoriaServicio.objects.create(
        country='CL',
        code='motor_transmission'
    )
    CategoriaServicioName.objects.create(
        categoria=cat_motor_cl,
        language='es',
        label='Motor y Transmisión',
        aliases=['motor', 'transmision', 'caja de cambios'],
        is_default=True
    )
    CategoriaServicioName.objects.create(
        categoria=cat_motor_cl,
        language='en',
        label='Engine & Transmission',
        aliases=['engine', 'transmission', 'gearbox'],
        is_default=True
    )
    
    cat_frenos_cl = CategoriaServicio.objects.create(
        country='CL',
        code='brakes_suspension'
    )
    CategoriaServicioName.objects.create(
        categoria=cat_frenos_cl,
        language='es',
        label='Frenos y Suspensión',
        aliases=['frenos', 'suspension', 'amortiguadores'],
        is_default=True
    )
    CategoriaServicioName.objects.create(
        categoria=cat_frenos_cl,
        language='en',
        label='Brakes & Suspension',
        aliases=['brakes', 'suspension', 'shocks'],
        is_default=True
    )
    
    # === CATEGORÍAS PARA USA ===
    cat_motor_us = CategoriaServicio.objects.create(
        country='US',
        code='engine_transmission'
    )
    CategoriaServicioName.objects.create(
        categoria=cat_motor_us,
        language='en',
        label='Engine & Transmission',
        aliases=['engine', 'transmission', 'drivetrain'],
        is_default=True
    )
    CategoriaServicioName.objects.create(
        categoria=cat_motor_us,
        language='es',
        label='Motor y Transmisión',
        aliases=['motor', 'transmisión', 'tren motriz'],
        is_default=True
    )
    
    cat_maintenance_us = CategoriaServicio.objects.create(
        country='US',
        code='maintenance_inspection'
    )
    CategoriaServicioName.objects.create(
        categoria=cat_maintenance_us,
        language='en',
        label='Maintenance & Inspection',
        aliases=['maintenance', 'inspection', 'service'],
        is_default=True
    )
    CategoriaServicioName.objects.create(
        categoria=cat_maintenance_us,
        language='es',
        label='Mantenimiento e Inspección',
        aliases=['mantenimiento', 'inspección', 'servicio'],
        is_default=True
    )
    
    print("✅ Categorías creadas")
    
    # === SUBCATEGORÍAS ===
    print("🏗️ Creando subcategorías...")
    
    # Chile - Motor
    subcat_cambio_aceite_cl = SubcategoriaServicio.objects.create(
        categoria=cat_motor_cl,
        country='CL',
        code='oil_change'
    )
    SubcategoriaServicioName.objects.create(
        subcategoria=subcat_cambio_aceite_cl,
        language='es',
        label='Cambio de Aceite',
        aliases=['aceite', 'cambio aceite', 'lubricación'],
        is_default=True
    )
    
    # Chile - Frenos
    subcat_frenos_cl = SubcategoriaServicio.objects.create(
        categoria=cat_frenos_cl,
        country='CL', 
        code='brake_service'
    )
    SubcategoriaServicioName.objects.create(
        subcategoria=subcat_frenos_cl,
        language='es',
        label='Servicio de Frenos',
        aliases=['frenos', 'pastillas', 'discos'],
        is_default=True
    )
    
    # USA - Engine
    subcat_oil_change_us = SubcategoriaServicio.objects.create(
        categoria=cat_motor_us,
        country='US',
        code='oil_change_service'
    )
    SubcategoriaServicioName.objects.create(
        subcategoria=subcat_oil_change_us,
        language='en',
        label='Oil Change Service',
        aliases=['oil change', 'lube', 'oil service'],
        is_default=True
    )
    SubcategoriaServicioName.objects.create(
        subcategoria=subcat_oil_change_us,
        language='es',
        label='Cambio de Aceite',
        aliases=['cambio de aceite', 'lubricación', 'aceite'],
        is_default=True
    )
    
    print("✅ Subcategorías creadas")
    
    # === SERVICIOS ===
    print("🏗️ Creando servicios...")
    
    # Chile - Cambio de aceite
    servicio_aceite_cl = Servicio.objects.create(
        subcategoria=subcat_cambio_aceite_cl,
        country='CL',
        code='cambio_aceite_motor',
        precio_base=25000,
        activo=True
    )
    ServicioName.objects.create(
        servicio=servicio_aceite_cl,
        language='es',
        label='Cambio de aceite de motor',
        aliases=['cambio aceite', 'aceite motor', 'lubricación motor'],
        is_default=True
    )
    
    # Chile - Pastillas de freno
    servicio_pastillas_cl = Servicio.objects.create(
        subcategoria=subcat_frenos_cl,
        country='CL',
        code='cambio_pastillas_freno',
        precio_base=45000,
        activo=True
    )
    ServicioName.objects.create(
        servicio=servicio_pastillas_cl,
        language='es',
        label='Cambio de pastillas de freno',
        aliases=['pastillas', 'pastillas freno', 'balatas'],
        is_default=True
    )
    
    # USA - Oil change
    servicio_oil_us = Servicio.objects.create(
        subcategoria=subcat_oil_change_us,
        country='US',
        code='engine_oil_change',
        precio_base=35.00,
        activo=True
    )
    ServicioName.objects.create(
        servicio=servicio_oil_us,
        language='en',
        label='Engine Oil Change',
        aliases=['oil change', 'lube service', 'oil service'],
        is_default=True
    )
    ServicioName.objects.create(
        servicio=servicio_oil_us,
        language='es',
        label='Cambio de aceite del motor',
        aliases=['cambio de aceite', 'servicio de aceite', 'lubricación'],
        is_default=True
    )
    
    # USA - Transmission service
    servicio_trans_us = Servicio.objects.create(
        subcategoria=subcat_oil_change_us,
        country='US',
        code='transmission_service',
        precio_base=120.00,
        activo=True
    )
    ServicioName.objects.create(
        servicio=servicio_trans_us,
        language='en',
        label='Transmission Service',
        aliases=['transmission', 'trans service', 'gear service'],
        is_default=True
    )
    ServicioName.objects.create(
        servicio=servicio_trans_us,
        language='es',
        label='Servicio de transmisión',
        aliases=['transmisión', 'servicio transmisión', 'caja de cambios'],
        is_default=True
    )
    
    print("✅ Servicios creados")
    
    # === RESUMEN ===
    print("\n📊 RESUMEN DE DATOS CREADOS:")
    print(f"  Categorías CL: {CategoriaServicio.objects.filter(country='CL').count()}")
    print(f"  Categorías US: {CategoriaServicio.objects.filter(country='US').count()}")
    print(f"  Subcategorías CL: {SubcategoriaServicio.objects.filter(country='CL').count()}")
    print(f"  Subcategorías US: {SubcategoriaServicio.objects.filter(country='US').count()}")
    print(f"  Servicios CL: {Servicio.objects.filter(country='CL').count()}")
    print(f"  Servicios US: {Servicio.objects.filter(country='US').count()}")
    print(f"  Nombres de servicios: {ServicioName.objects.count()}")


def test_search_functionality():
    """Prueba la funcionalidad de búsqueda"""
    print("\n🔍 PRUEBAS DE BÚSQUEDA:")
    
    from taller.utils.service_search import ServiceSearchEngine
    
    # Búsqueda en Chile (español)
    engine_cl = ServiceSearchEngine(country='CL', language='es')
    results = engine_cl.search_services('aceite')
    print(f"  Búsqueda 'aceite' en CL: {len(results)} resultados")
    for service in results:
        print(f"    - {service.get_label('es')}")
    
    # Búsqueda en USA (inglés)
    engine_us = ServiceSearchEngine(country='US', language='en')
    results = engine_us.search_services('oil')
    print(f"  Búsqueda 'oil' en US: {len(results)} resultados")
    for service in results:
        print(f"    - {service.get_label('en')}")
    
    # Búsqueda en USA (español - usuarios latinos)
    engine_us_es = ServiceSearchEngine(country='US', language='es')
    results = engine_us_es.search_services('aceite')
    print(f"  Búsqueda 'aceite' en US (español): {len(results)} resultados")
    for service in results:
        print(f"    - {service.get_label('es')}")


if __name__ == '__main__':
    print("🚀 Iniciando población de datos multilenguaje...")
    
    # Limpiar datos existentes
    print("🧹 Limpiando datos existentes...")
    ServicioName.objects.all().delete()
    SubcategoriaServicioName.objects.all().delete()  
    CategoriaServicioName.objects.all().delete()
    Servicio.objects.all().delete()
    SubcategoriaServicio.objects.all().delete()
    CategoriaServicio.objects.all().delete()
    
    # Crear nuevos datos
    create_categories_and_services()
    
    # Probar búsquedas
    test_search_functionality()
    
    print("\n🎉 ¡Datos de ejemplo creados exitosamente!")
    print("💡 Ahora puedes probar el admin en /admin/")
    print("🌍 Datos separados por país: CL vs US")
    print("🗣️ Nombres localizados: ES y EN")
    print("🔍 Búsqueda con aliases funcionando")
