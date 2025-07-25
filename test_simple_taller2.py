#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')
django.setup()

from django.contrib.auth import get_user_model
from taller.models import Cliente, Vehiculo, Documento

def test_taller2_simple():
    print("=== Verificacion rapida de taller2 ===")
    
    User = get_user_model()
    user = User.objects.get(username='taller2')
    empresa = user.empresa_usuario
    
    print(f"Usuario: {user.username}")
    print(f"Empresa: {empresa.nombre_taller}")
    
    # Documentos
    docs = Documento.objects.filter(empresa=empresa).order_by('-id')
    print(f"\nDocumentos en {empresa.nombre_taller}: {docs.count()}")
    
    for doc in docs[:3]:  # Solo los 3 mas recientes
        repuestos = doc.repuestodocumento_set.count()
        servicios = doc.serviciodocumento_set.count()
        total_items = repuestos + servicios
        
        estado = "CON DATOS" if total_items > 0 else "VACIO"
        
        print(f"  Doc #{doc.id}: {doc.numero}")
        print(f"    Repuestos: {repuestos}, Servicios: {servicios}")
        print(f"    Estado: {estado}")
        print(f"    Fecha: {doc.fecha_creacion.strftime('%Y-%m-%d %H:%M')}")
        print()

if __name__ == "__main__":
    test_taller2_simple()
