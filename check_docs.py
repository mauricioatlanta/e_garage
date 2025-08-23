import os
import sys
sys.path.append(r'e:\projecto\e_garage')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'garage_project.settings')

import django
django.setup()

from taller.models import Documento

print("=== ESTADO ACTUAL DE DOCUMENTOS ===")
total_docs = Documento.objects.count()
print(f"Total documentos: {total_docs}")

if total_docs > 0:
    print("\nÚltimos 5 documentos:")
    for doc in Documento.objects.order_by('-id')[:5]:
        try:
            rep_count = doc.lineas_repuesto.count()  
            serv_count = doc.lineas_servicio.count()
            otros_count = doc.lineas_otro_servicio.count()
            print(f"Doc {doc.id} ({doc.tipo}): rep={rep_count}, serv={serv_count}, otros={otros_count}, total=${doc.total}")
        except Exception as e:
            print(f"Error con doc {doc.id}: {e}")
else:
    print("No hay documentos en la base de datos")

print("====================================")
