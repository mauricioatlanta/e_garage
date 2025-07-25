#!/usr/bin/env python3
"""
Sistema de backup simplificado
"""
import os
import django
import json
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from taller.models.empresa import Empresa
from taller.models.documento import Documento

print("💾 === SISTEMA BACKUP SIMPLE ===")

# Crear directorio de backups
backup_dir = os.path.join(os.getcwd(), 'backups')
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)
    print(f"📁 Directorio creado: {backup_dir}")

# Backup básico por empresa
empresas = Empresa.objects.all()
print(f"🏢 Empresas encontradas: {empresas.count()}")

for empresa in empresas:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_archivo = f"backup_{empresa.nombre_taller.replace(' ', '_')}_{timestamp}.json"
    ruta_archivo = os.path.join(backup_dir, nombre_archivo)
    
    # Obtener documentos de la empresa
    documentos = Documento.objects.filter(empresa=empresa)
    
    # Crear backup data
    backup_data = {
        'empresa': {
            'nombre_taller': empresa.nombre_taller,
            'direccion': empresa.direccion,
            'telefono': empresa.telefono,
            'email': empresa.email
        },
        'estadisticas': {
            'total_documentos': documentos.count(),
        },
        'fecha_backup': timestamp,
        'documentos': []
    }
    
    # Agregar documentos básicos
    for doc in documentos:
        doc_data = {
            'numero_documento': doc.numero_documento,
            'tipo_documento': doc.tipo_documento,
            'fecha': str(doc.fecha) if doc.fecha else None,
            'observaciones': doc.observaciones
        }
        backup_data['documentos'].append(doc_data)
    
    # Guardar backup
    with open(ruta_archivo, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Backup creado: {nombre_archivo}")
    print(f"   - Documentos: {documentos.count()}")

print("\n🏁 === BACKUP COMPLETADO ===")

# Mostrar archivos creados
print("\n📄 Archivos de backup creados:")
for archivo in os.listdir(backup_dir):
    if archivo.startswith('backup_'):
        tamaño = os.path.getsize(os.path.join(backup_dir, archivo))
        print(f"   {archivo} ({tamaño} bytes)")
