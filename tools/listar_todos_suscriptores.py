#!/usr/bin/env python
"""
Script para listar todos los suscriptores/usuarios con sus datos
Ejecutar en PythonAnywhere para ver todos los usuarios y sus empresas
"""

import os
import sys
import django
from collections import defaultdict

sys.path.insert(0, '/home/atlantareciclajes/apps/egarage/current')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.suscripcion import Suscripcion
from taller.models.empresa import Empresa

def listar_todos_suscriptores():
    """Lista todos los usuarios con sus empresas y suscripciones"""
    
    # Obtener todos los usuarios
    usuarios = User.objects.all().order_by('date_joined')
    
    # Agrupar por país
    por_pais = defaultdict(list)
    usuarios_sin_empresa = []
    
    print("="*80)
    print("LISTADO COMPLETO DE USUARIOS/SUSCRIPTORES")
    print("="*80)
    print()
    
    for user in usuarios:
        try:
            # Buscar empresa asociada
            empresa = None
            try:
                empresa = Empresa.objects.get(user=user)
            except Empresa.DoesNotExist:
                try:
                    empresa = Empresa.objects.filter(usuario=user).first()
                except:
                    pass
            
            # Buscar suscripción
            suscripcion = None
            try:
                suscripcion = user.suscripcion
            except:
                pass
            
            # Obtener país
            pais = empresa.pais if empresa else "SIN_PAIS"
            
            datos_usuario = {
                'user': user,
                'email': user.email,
                'username': user.username,
                'fecha_registro': user.date_joined,
                'empresa': empresa,
                'nombre_empresa': empresa.nombre_taller if empresa else None,
                'pais': pais,
                'suscripcion': suscripcion,
                'tipo_suscripcion': suscripcion.tipo if suscripcion else None,
                'suscripcion_activa': suscripcion.activa if suscripcion else False,
                'fecha_fin': suscripcion.fecha_fin if suscripcion else None,
            }
            
            if empresa:
                por_pais[pais].append(datos_usuario)
            else:
                usuarios_sin_empresa.append(datos_usuario)
                
        except Exception as e:
            print(f"Error procesando usuario {user.id}: {e}")
            usuarios_sin_empresa.append({
                'user': user,
                'email': user.email,
                'error': str(e)
            })
    
    # Mostrar resumen por país
    print("RESUMEN POR PAÍS:")
    print("-"*80)
    for pais in sorted(por_pais.keys()):
        count = len(por_pais[pais])
        print(f"{pais}: {count} usuarios")
    print(f"SIN_PAIS: {len(usuarios_sin_empresa)} usuarios")
    print()
    
    # Mostrar detalle por país
    for pais in sorted(por_pais.keys()):
        usuarios_pais = por_pais[pais]
        print("="*80)
        print(f"PAÍS: {pais} ({len(usuarios_pais)} usuarios)")
        print("="*80)
        
        for datos in usuarios_pais:
            user = datos['user']
            empresa = datos['empresa']
            suscripcion = datos['suscripcion']
            
            print(f"\nUsuario ID: {user.id}")
            print(f"  Email: {datos['email']}")
            print(f"  Username: {datos['username']}")
            print(f"  Fecha registro: {datos['fecha_registro']}")
            
            if empresa:
                print(f"  Empresa: {datos['nombre_empresa']} (ID: {empresa.id})")
                print(f"  País: {pais}")
            else:
                print(f"  Empresa: NO TIENE")
            
            if suscripcion:
                print(f"  Suscripción: {datos['tipo_suscripcion']} - Activa: {datos['suscripcion_activa']}")
                if datos['fecha_fin']:
                    print(f"  Fecha fin: {datos['fecha_fin']}")
            else:
                print(f"  Suscripción: NO TIENE")
    
    # Mostrar usuarios sin empresa
    if usuarios_sin_empresa:
        print("\n" + "="*80)
        print(f"USUARIOS SIN EMPRESA ({len(usuarios_sin_empresa)})")
        print("="*80)
        for datos in usuarios_sin_empresa:
            user = datos['user']
            print(f"  - {datos.get('email', 'Sin email')} ({datos.get('username', 'Sin username')}) - ID: {user.id}")
    
    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN FINAL")
    print("="*80)
    print(f"Total usuarios: {User.objects.count()}")
    print(f"Total empresas: {Empresa.objects.count()}")
    print(f"Total suscripciones: {Suscripcion.objects.count()}")
    print(f"\nPor país:")
    for pais in sorted(por_pais.keys()):
        print(f"  {pais}: {len(por_pais[pais])} usuarios")
    
    # Países con más usuarios
    print(f"\nPaíses con más usuarios:")
    paises_ordenados = sorted(por_pais.items(), key=lambda x: len(x[1]), reverse=True)
    for pais, usuarios_list in paises_ordenados:
        print(f"  {pais}: {len(usuarios_list)} usuarios")

if __name__ == '__main__':
    listar_todos_suscriptores()
