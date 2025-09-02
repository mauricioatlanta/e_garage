#!/usr/bin/env python
"""
Script para crear una sesión de usuario para acceder al documento 45
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.auth import authenticate, login
from django.test import Client

def main():
    print("=== ACCESO AL DOCUMENTO 45 ===")
    
    # El documento 45 pertenece al usuario test_diagnostic
    username = 'test_diagnostic'
    
    try:
        user = User.objects.get(username=username)
        print(f"✓ Usuario encontrado: {user.username}")
        print(f"  - ID: {user.id}")
        print(f"  - Empresa: {user.empresa.nombre_taller}")
        print(f"  - Empresa ID: {user.empresa.id}")
        
        # Crear cliente de prueba
        client = Client()
        
        # Intentar login (necesitamos la contraseña)
        print("\n=== INFORMACIÓN PARA ACCESO ===")
        print(f"Para acceder al documento 45, necesitas:")
        print(f"1. Iniciar sesión como: {username}")
        print(f"2. Visitar la URL: http://127.0.0.1:8000/us/documentos/form/45/")
        print("\nSi no conoces la contraseña, puedes:")
        print("- Cambiar la contraseña del usuario")
        print("- O crear un nuevo documento para tu usuario actual")
        
        print("\n=== DOCUMENTOS DISPONIBLES PARA OTROS USUARIOS ===")
        from taller.documentos.models import Documento
        
        for user in User.objects.all()[:5]:
            try:
                empresa = user.empresa
                docs_count = Documento.objects.filter(empresa=empresa).count()
                if docs_count > 0:
                    docs = list(Documento.objects.filter(empresa=empresa).values_list('id', flat=True)[:3])
                    print(f"- {user.username}: {docs_count} documentos {docs}")
            except:
                continue
                
    except User.DoesNotExist:
        print(f"✗ Usuario {username} no existe")

if __name__ == "__main__":
    main()
