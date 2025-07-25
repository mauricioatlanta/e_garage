from taller.models.documento import Documento
from taller.models.empresa import Empresa
from django.contrib.auth.models import User

print("=== DIAGNÓSTICO DE DOCUMENTOS ===")
print(f"Total documentos: {Documento.objects.count()}")
print(f"Total empresas: {Empresa.objects.count()}")  
print(f"Total usuarios: {User.objects.count()}")

print("\n=== DOCUMENTOS POR ID ===")
for doc in Documento.objects.all()[:10]:  # Primeros 10
    print(f"ID: {doc.pk}, Tipo: {doc.tipo_documento}, Empresa: {doc.empresa.pk if doc.empresa else 'None'}")
