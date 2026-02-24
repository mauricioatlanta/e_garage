#!/usr/bin/env python
"""
Script para crear usuarios faltantes desde el archivo consolidado
Crea usuarios básicos para poder importar sus suscripciones
"""

import os
import sys
import json
import django
from django.contrib.auth.models import User

# Agregar el directorio del proyecto al path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

def crear_usuarios_faltantes(archivo_json, crear_todos=False):
    """Crea usuarios faltantes desde el archivo consolidado"""
    
    # Leer archivo JSON
    with open(archivo_json, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    inicio_json = contenido.find('{')
    if inicio_json == -1:
        print("ERROR: No se encontró JSON válido")
        return False
    
    contenido_json = contenido[inicio_json:]
    datos = json.loads(contenido_json)
    
    if 'suscripciones' not in datos:
        print("ERROR: Formato incorrecto")
        return False
    
    # Obtener usuarios existentes
    usuarios_existentes = {}
    for user in User.objects.all():
        if user.email:
            usuarios_existentes[user.email.lower()] = user
        if user.username:
            usuarios_existentes[user.username.lower()] = user
    
    usuarios_creados = []
    usuarios_ya_existen = []
    errores = []
    
    print("="*80)
    print("CREACIÓN DE USUARIOS FALTANTES")
    print("="*80)
    print()
    
    for suscripcion in datos['suscripciones']:
        email = suscripcion.get('user_email')
        username = suscripcion.get('user_username')
        user_id_original = suscripcion.get('user_id_original')
        
        # Saltar si no tiene email ni username
        if not email and not username:
            continue
        
        # Verificar si ya existe
        existe = False
        if email and email.lower() in usuarios_existentes:
            existe = True
        elif username and username.lower() in usuarios_existentes:
            existe = True
        
        if existe:
            usuarios_ya_existen.append(email or username)
            continue
        
        # Crear usuario
        try:
            # Usar email como username si no hay username, o viceversa
            username_final = username or email.split('@')[0] if email else f"user_{user_id_original}"
            email_final = email or f"{username_final}@egarage.local"
            
            # Asegurar que el username sea único
            username_base = username_final
            counter = 1
            while User.objects.filter(username=username_final).exists():
                username_final = f"{username_base}_{counter}"
                counter += 1
            
            # Crear usuario
            user = User.objects.create_user(
                username=username_final,
                email=email_final if email else None,
                password=None,  # Sin contraseña, el usuario deberá usar "forgot password"
                is_active=True,
            )
            
            usuarios_creados.append({
                'username': username_final,
                'email': email_final,
                'user_id': user.id,
                'tipo_suscripcion': suscripcion.get('tipo'),
            })
            
            print(f"✓ Creado: {email_final or username_final} (ID: {user.id})")
            
        except Exception as e:
            errores.append({
                'email': email,
                'username': username,
                'error': str(e)
            })
            print(f"✗ Error creando {email or username}: {e}")
    
    print()
    print("="*80)
    print("RESUMEN")
    print("="*80)
    print(f"Usuarios creados: {len(usuarios_creados)}")
    print(f"Usuarios que ya existían: {len(usuarios_ya_existen)}")
    print(f"Errores: {len(errores)}")
    
    if usuarios_creados:
        print("\nUsuarios creados:")
        for u in usuarios_creados:
            print(f"  - {u['email'] or u['username']} (ID: {u['user_id']})")
    
    if usuarios_ya_existen:
        print("\nUsuarios que ya existían:")
        for u in usuarios_ya_existen:
            print(f"  - {u}")
    
    if errores:
        print("\nErrores:")
        for e in errores:
            print(f"  - {e['email'] or e['username']}: {e['error']}")
    
    print()
    print("="*80)
    print("PRÓXIMOS PASOS")
    print("="*80)
    if usuarios_creados:
        print("1. Los usuarios fueron creados sin contraseña")
        print("2. Deberán usar 'Olvidé mi contraseña' para establecer una")
        print("3. Ahora puedes importar las suscripciones:")
        print("   python tools/importar_suscripciones.py suscripciones_consolidadas.json")
    else:
        print("No se crearon nuevos usuarios. Todos ya existen o no tienen email/username.")
    
    return len(errores) == 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python crear_usuarios_faltantes.py <archivo_json>")
        print("\nEste script crea usuarios básicos para las suscripciones que tienen email/username")
        print("pero el usuario no existe en el servidor.")
        sys.exit(1)
    
    archivo_json = sys.argv[1]
    if not os.path.exists(archivo_json):
        print(f"ERROR: El archivo {archivo_json} no existe")
        sys.exit(1)
    
    crear_todos = '--todos' in sys.argv
    exito = crear_usuarios_faltantes(archivo_json, crear_todos)
    sys.exit(0 if exito else 1)
