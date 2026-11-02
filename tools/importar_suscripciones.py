#!/usr/bin/env python
"""
Script para importar suscripciones en OceanDigital
Ejecutar en OceanDigital: python importar_suscripciones.py suscripciones_export.json
"""

import os
import sys
import django
import json
from datetime import date

# Agregar el directorio del proyecto al path
# Esto permite que Python encuentre el módulo gestion_taller
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # Subir un nivel desde tools/ al root del proyecto
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.suscripcion import Suscripcion

def importar_suscripciones(archivo_json):
    """Importa suscripciones desde archivo JSON"""
    
    # Leer archivo JSON
    # Si el archivo tiene mensajes de stderr mezclados, extraer solo el JSON
    with open(archivo_json, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Buscar el inicio del JSON (primera línea que comienza con {)
    inicio_json = contenido.find('{')
    if inicio_json == -1:
        print("ERROR: No se encontró JSON válido en el archivo")
        return False
    
    # Extraer solo la parte JSON
    contenido_json = contenido[inicio_json:]
    
    # Intentar parsear el JSON
    try:
        datos = json.loads(contenido_json)
    except json.JSONDecodeError as e:
        print(f"ERROR: El archivo JSON no es válido: {e}")
        print(f"Primeras 200 caracteres del JSON encontrado:")
        print(contenido_json[:200])
        return False
    
    if 'suscripciones' not in datos:
        print("ERROR: El archivo JSON no tiene el formato correcto")
        return False
    
    # Mostrar información del archivo si está disponible
    if 'total_suscriptores_unicos' in datos:
        print(f"Archivo consolidado con {datos['total_suscriptores_unicos']} suscriptores únicos")
        if 'por_pais' in datos:
            print("Distribución por país:")
            for pais, count in sorted(datos['por_pais'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {pais}: {count}")
        print()
    elif 'total' in datos:
        print(f"Archivo con {datos['total']} suscripciones")
        print()
    
    suscripciones_importadas = 0
    suscripciones_actualizadas = 0
    errores = []
    
    for suscripcion_data in datos['suscripciones']:
        try:
            # Buscar usuario por email o username (case-insensitive)
            user = None
            email_buscar = suscripcion_data.get('user_email')
            username_buscar = suscripcion_data.get('user_username')
            
            # Si no hay email ni username, saltar
            if not email_buscar and not username_buscar:
                errores.append(f"Usuario sin email ni username (ID original: {suscripcion_data.get('user_id_original', 'desconocido')})")
                continue
            
            # Buscar por email (case-insensitive)
            if email_buscar:
                try:
                    user = User.objects.get(email__iexact=email_buscar)
                except User.DoesNotExist:
                    pass
                except User.MultipleObjectsReturned:
                    # Si hay múltiples, tomar el primero
                    user = User.objects.filter(email__iexact=email_buscar).first()
            
            # Si no se encontró por email, buscar por username (case-insensitive)
            if not user and username_buscar:
                try:
                    user = User.objects.get(username__iexact=username_buscar)
                except User.DoesNotExist:
                    pass
                except User.MultipleObjectsReturned:
                    user = User.objects.filter(username__iexact=username_buscar).first()
            
            # Si aún no se encontró, intentar buscar si el email del archivo coincide con username del servidor
            # o viceversa (para casos como support@egarage.cl / mauricioatlanta@gmail.com)
            if not user:
                if email_buscar:
                    try:
                        user = User.objects.get(username__iexact=email_buscar)
                    except (User.DoesNotExist, User.MultipleObjectsReturned):
                        pass
                if not user and username_buscar:
                    try:
                        user = User.objects.get(email__iexact=username_buscar)
                    except (User.DoesNotExist, User.MultipleObjectsReturned):
                        pass
            
            if not user:
                errores.append(f"Usuario no encontrado: {suscripcion_data.get('user_email')} o {suscripcion_data.get('user_username')}")
                continue
            
            # Verificar si ya existe suscripción para este usuario
            suscripcion, creada = Suscripcion.objects.get_or_create(
                user=user,
                defaults={
                    'tipo': suscripcion_data.get('tipo', 'trial'),
                    'fecha_inicio': date.fromisoformat(suscripcion_data['fecha_inicio']) if suscripcion_data.get('fecha_inicio') else None,
                    'fecha_fin': date.fromisoformat(suscripcion_data['fecha_fin']) if suscripcion_data.get('fecha_fin') else None,
                    'activa': suscripcion_data.get('activa', False),
                }
            )
            
            if not creada:
                # Actualizar suscripción existente
                suscripcion.tipo = suscripcion_data.get('tipo', suscripcion.tipo)
                if suscripcion_data.get('fecha_inicio'):
                    suscripcion.fecha_inicio = date.fromisoformat(suscripcion_data['fecha_inicio'])
                if suscripcion_data.get('fecha_fin'):
                    suscripcion.fecha_fin = date.fromisoformat(suscripcion_data['fecha_fin'])
                suscripcion.activa = suscripcion_data.get('activa', suscripcion.activa)
                suscripcion.save()
                suscripciones_actualizadas += 1
            else:
                suscripciones_importadas += 1
            
            print(f"✓ {'Importada' if creada else 'Actualizada'}: {user.email} - {suscripcion.tipo}")
            
        except Exception as e:
            error_msg = f"Error procesando suscripción {suscripcion_data.get('user_email', 'desconocido')}: {str(e)}"
            errores.append(error_msg)
            print(f"✗ {error_msg}")
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE IMPORTACIÓN")
    print("="*60)
    total_en_archivo = datos.get('total_suscriptores_unicos') or datos.get('total', len(datos['suscripciones']))
    print(f"Total en archivo: {total_en_archivo}")
    print(f"Importadas: {suscripciones_importadas}")
    print(f"Actualizadas: {suscripciones_actualizadas}")
    print(f"Errores: {len(errores)}")
    
    if errores:
        print("\nErrores encontrados:")
        for error in errores:
            print(f"  - {error}")
    
    return len(errores) == 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python importar_suscripciones.py <archivo_json>")
        sys.exit(1)
    
    archivo_json = sys.argv[1]
    
    if not os.path.exists(archivo_json):
        print(f"ERROR: El archivo {archivo_json} no existe")
        sys.exit(1)
    
    try:
        exito = importar_suscripciones(archivo_json)
        sys.exit(0 if exito else 1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
