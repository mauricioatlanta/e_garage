#!/usr/bin/env python
"""
Script para completar traducciones faltantes
Corrección de la advertencia encontrada en validaciones
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.servicios.models import Servicio, ServicioName

def completar_traducciones_faltantes():
    """Completar traducciones al inglés que falten"""
    print("🔍 Identificando servicios sin traducción al inglés...")
    
    # Servicios sin traducción en inglés
    servicios_sin_en = Servicio.objects.exclude(
        names__language='en'
    ).distinct()
    
    print(f"📋 Encontrados {servicios_sin_en.count()} servicios sin traducción")
    
    for servicio in servicios_sin_en:
        print(f"\n🔧 Procesando servicio: {servicio.code}")
        
        # Obtener traducción en español si existe
        traduccion_es = servicio.names.filter(language='es').first()
        
        if traduccion_es:
            # Mapeo de traducciones comunes
            traducciones_comunes = {
                'Cambio de Aceite': 'Oil Change',
                'Reparación de Frenos': 'Brake Repair',
                'Diagnóstico de Motor': 'Engine Diagnosis',
                'Reparación Transmisión': 'Transmission Repair',
                'Alineación': 'Wheel Alignment',
                'Balanceado': 'Wheel Balancing',
                'Remolque': 'Towing',
                'Grúa': 'Towing Service',
                'Auxilio Mecánico': 'Roadside Assistance',
                'Lavado': 'Car Wash',
                'Encerado': 'Car Wax',
                'Detailing': 'Car Detailing'
            }
            
            # Buscar traducción automática
            label_en = traducciones_comunes.get(traduccion_es.label, traduccion_es.label)
            
            # Crear traducción al inglés
            ServicioName.objects.create(
                servicio=servicio,
                language='en',
                label=label_en,
                aliases=traduccion_es.aliases,  # Mantener mismos aliases
                is_default=True
            )
            
            print(f"   ✅ Creada traducción: '{traduccion_es.label}' → '{label_en}'")
        else:
            # Si no hay traducción en español, crear una genérica
            label_generico = f"Service {servicio.code}"
            ServicioName.objects.create(
                servicio=servicio,
                language='en', 
                label=label_generico,
                aliases=[],
                is_default=True
            )
            print(f"   ✅ Creada traducción genérica: '{label_generico}'")
    
    print(f"\n🎉 Traducciones completadas exitosamente")

if __name__ == "__main__":
    completar_traducciones_faltantes()
