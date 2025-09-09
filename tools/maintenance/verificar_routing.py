#!/usr/bin/env python
import os
import sys

import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.urls import resolve

# Verificar a qué vista está yendo realmente la URL
try:
    r = resolve('/taller/vehiculos/crear/')
    print('=== VERIFICACIÓN DE ROUTING ===')
    print('URL:', '/taller/vehiculos/crear/')
    print('MODULE:', r.func.__module__)
    print('VIEW NAME:', getattr(r.func, '__name__', r.func.__class__.__name__))
    print('NAMESPACE:', r.namespace)
    print('URL_NAME:', r.url_name)
    print('===============================')
    
    # También verificar la ruta sin /taller/
    try:
        r2 = resolve('/vehiculos/crear/')
        print('URL alternativa:', '/vehiculos/crear/')
        print('MODULE:', r2.func.__module__)
        print('VIEW NAME:', getattr(r2.func, '__name__', r2.func.__class__.__name__))
        print('NAMESPACE:', r2.namespace)
        print('URL_NAME:', r2.url_name)
    except:
        print('URL /vehiculos/crear/ no existe')
        
except Exception as e:
    print('ERROR al resolver URL:', e)
