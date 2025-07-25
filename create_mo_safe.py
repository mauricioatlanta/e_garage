#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import struct

def create_mo_file():
    """
    Crea un archivo .mo simple para traducciones en inglés
    """
    # Definir las traducciones básicas sin acentos
    translations = {
        'Iniciar sesion': 'Sign In',
        'Email': 'Email',
        'Contrasena': 'Password', 
        'Recordarme': 'Remember me',
        'Olvidaste tu contrasena?': 'Forgot your password?',
        'No tienes cuenta?': "Don't have an account?",
        'Registrate aqui': 'Sign up here',
        'ACCESO RESTRINGIDO': 'ACCESS RESTRICTED',
        'Esta cuenta ya tiene un usuario asignado.': 'This account already has a user assigned.',
        'No es posible registrar otro usuario para esta suscripcion.': 'It is not possible to register another user for this subscription.',
        'Cada taller/empresa puede tener unicamente': 'Each workshop/company can only have',
        'UN USUARIO ACTIVO': 'ONE ACTIVE USER',
        'Si necesitas cambiar el usuario principal, contacta al administrador del sistema.': 'If you need to change the main user, contact the system administrator.',
        'Volver al Registro': 'Back to Registration'
    }
    
    # Crear directorio si no existe
    locale_dir = os.path.join('locale', 'en', 'LC_MESSAGES')
    os.makedirs(locale_dir, exist_ok=True)
    
    # Crear archivo .mo
    mo_file = os.path.join(locale_dir, 'django.mo')
    
    # Crear contenido del archivo .mo (formato binario simplificado)
    keys = list(translations.keys())
    values = list(translations.values())
    
    # Formato del archivo .mo (simplificado)
    # Header: magic number + version + num_entries + offset_keys + offset_values
    magic = 0x950412de
    version = 0
    num_entries = len(translations)
    
    # Construir las cadenas
    key_data = b'\x00'.join(k.encode('utf-8') for k in keys) + b'\x00'
    value_data = b'\x00'.join(v.encode('utf-8') for v in values) + b'\x00'
    
    # Calcular offsets
    header_size = 28
    offset_keys = header_size
    offset_values = offset_keys + len(key_data)
    
    # Escribir archivo .mo
    with open(mo_file, 'wb') as f:
        # Header
        f.write(struct.pack('<I', magic))      # Magic number
        f.write(struct.pack('<I', version))    # Version
        f.write(struct.pack('<I', num_entries)) # Number of entries
        f.write(struct.pack('<I', offset_keys)) # Offset to key table
        f.write(struct.pack('<I', offset_values)) # Offset to value table
        f.write(struct.pack('<I', 0))          # Hash table offset (not used)
        f.write(struct.pack('<I', 0))          # Hash table size (not used)
        
        # Key data
        f.write(key_data)
        
        # Value data  
        f.write(value_data)
    
    print(f"✅ Archivo .mo creado exitosamente en: {mo_file}")
    return True

if __name__ == "__main__":
    try:
        create_mo_file()
        print("🎉 Compilación de traducciones completada!")
    except Exception as e:
        print(f"❌ Error al crear archivo .mo: {e}")
        sys.exit(1)
