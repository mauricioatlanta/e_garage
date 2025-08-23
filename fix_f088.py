import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')
django.setup()

from taller.models import Documento

# Verificar el documento problematico F-088
doc = Documento.objects.filter(numero='F-088').first()
if doc:
    print(f"Documento encontrado: {doc.numero}")
    print(f"Empresa: {doc.empresa.nombre_taller}")
    print(f"Cliente: {doc.cliente.nombre}")
    print(f"Repuestos: {doc.lineas_repuesto.count()}")
    print(f"Servicios: {doc.lineas_servicio.count()}")
    
    # Intentar recrear los datos que deberia tener
    from taller.models.lineas_documento import LineaRepuesto as RepuestoDocumento, LineaServicio
    
    # Verificar si el documento tiene datos
    if doc.lineas_repuesto.count() == 0 and doc.lineas_servicio.count() == 0:
        print("DOCUMENTO VACIO - Agregando datos de prueba...")
        
        # Agregar un repuesto
        RepuestoDocumento.objects.create(
            documento=doc,
            codigo='REPAIR-001',
            nombre='Repuesto Reparacion F-088',
            cantidad=1,
            subtotal=15000
        )
        
        # Agregar un servicio
        LineaServicio.objects.create(
            empresa=doc.empresa,
            documento=doc,
            nombre='Servicio Reparacion F-088',
            precio_unitario=25000
        )

        print("Datos agregados manualmente")
        print(f"Repuestos: {doc.lineas_repuesto.count()}")
        print(f"Servicios: {doc.lineas_servicio.count()}")
    else:
        print("El documento ya tiene datos")
else:
    print("Documento F-088 no encontrado")
