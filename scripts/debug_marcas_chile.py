#!/usr/bin/env python
"""
Script para debug - verificar marcas en contexto de crear vehículo
"""
import os

import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth import get_user_model

from taller.models.marca import Marca

User = get_user_model()

def main():
    print("🔍 DEBUG: Verificando marcas para Chile\n")
    
    # Obtener marcas de Chile
    marcas_chile = Marca.objects.filter(country='CL').order_by('nombre')
    
    print(f"📊 Total marcas Chile: {marcas_chile.count()}")
    print("📋 Lista de marcas:")
    for i, marca in enumerate(marcas_chile[:10], 1):
        print(f"  {i}. {marca.nombre} (ID: {marca.id})")
    
    if marcas_chile.count() > 10:
        print(f"  ... y {marcas_chile.count() - 10} más")
    
    # Verificar usuarios de Chile
    print("\n🔍 Verificando usuarios de Chile:")
    usuarios_chile = User.objects.filter(empresa__pais='CL')
    for user in usuarios_chile[:3]:
        print(f"  👤 {user.username} - Empresa: {user.empresa.nombre if user.empresa else 'N/A'}")

if __name__ == '__main__':
    main()
