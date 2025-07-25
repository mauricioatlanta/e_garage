#!/usr/bin/env python3
import struct
import array

# Simplified .mo file creation without gettext
def create_mo_file():
    # Simple binary format for .mo files
    # This is a minimal implementation
    
    # Messages mapping (msgid -> msgstr)
    messages = {
        "Iniciar sesión": "Sign In",
        "¿Olvidaste tu contraseña?": "Forgot your password?", 
        "¿No tienes cuenta?": "Don't have an account?",
        "Regístrate aquí": "Sign up here",
        "Email": "Email",
        "Contraseña": "Password", 
        "Recordarme": "Remember me",
        "ACCESO RESTRINGIDO": "ACCESS RESTRICTED",
        "Esta cuenta ya tiene un usuario asignado.": "This account already has a user assigned.",
        "No es posible registrar otro usuario para esta suscripción.": "It is not possible to register another user for this subscription.",
        "Cada taller/empresa puede tener únicamente": "Each workshop/company can only have",
        "UN USUARIO ACTIVO": "ONE ACTIVE USER",
        "Si necesitas cambiar el usuario principal, contacta al administrador del sistema.": "If you need to change the main user, contact the system administrator.",
        "Volver al Registro": "Back to Registration"
    }
    
    # Create simple binary data
    magic_number = 0x950412de
    version = 0
    num_strings = len(messages)
    
    # Build strings and offsets
    msgids = []
    msgstrs = []
    
    for msgid, msgstr in messages.items():
        msgids.append(msgid.encode('utf-8'))
        msgstrs.append(msgstr.encode('utf-8'))
    
    # Create binary data
    with open('locale/en/LC_MESSAGES/django.mo', 'wb') as f:
        # Write header
        f.write(struct.pack('<I', magic_number))
        f.write(struct.pack('<I', version))
        f.write(struct.pack('<I', num_strings))
        
        # Calculate offsets
        offset_msgids = 28  # After header
        offset_msgstrs = offset_msgids + (num_strings * 8)
        
        f.write(struct.pack('<I', offset_msgids))
        f.write(struct.pack('<I', offset_msgstrs))
        f.write(struct.pack('<I', 0))  # hash table offset
        f.write(struct.pack('<I', 0))  # hash table size
        
        # Write msgid offsets and lengths
        data_offset = offset_msgstrs + (num_strings * 8)
        for msgid in msgids:
            f.write(struct.pack('<I', len(msgid)))
            f.write(struct.pack('<I', data_offset))
            data_offset += len(msgid) + 1
            
        # Write msgstr offsets and lengths
        for msgstr in msgstrs:
            f.write(struct.pack('<I', len(msgstr)))
            f.write(struct.pack('<I', data_offset))
            data_offset += len(msgstr) + 1
            
        # Write msgids
        for msgid in msgids:
            f.write(msgid)
            f.write(b'\x00')
            
        # Write msgstrs
        for msgstr in msgstrs:
            f.write(msgstr)
            f.write(b'\x00')

if __name__ == '__main__':
    create_mo_file()
    print("django.mo created successfully!")
