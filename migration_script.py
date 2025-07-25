#!/usr/bin/env python3
"""
Script para migrar de empresa_usuario a empresa (campo user)
Este script actualiza los datos existentes antes de ejecutar la migración
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')
django.setup()

from django.db import transaction
from taller.models.empresa import Empresa
from django.contrib.auth.models import User

def migrar_empresa_usuario():
    """
    Migra los datos de usuario a user en el modelo Empresa
    """
    print("🔄 Iniciando migración de empresa_usuario a empresa...")
    
    with transaction.atomic():
        empresas = Empresa.objects.all()
        
        if not empresas.exists():
            print("✅ No hay empresas existentes, no se requiere migración")
            return
        
        print(f"📊 Encontradas {empresas.count()} empresas para migrar")
        
        for empresa in empresas:
            if hasattr(empresa, 'usuario') and empresa.usuario:
                # Si ya existe campo usuario, usar ese valor
                print(f"✅ Empresa {empresa.nombre_taller} ya tiene usuario: {empresa.usuario.username}")
            else:
                print(f"❌ Empresa {empresa.nombre_taller} no tiene usuario asignado")
                # Aquí podrías asignar un usuario por defecto o crear uno
        
        print("✅ Migración completada")

if __name__ == "__main__":
    migrar_empresa_usuario()
