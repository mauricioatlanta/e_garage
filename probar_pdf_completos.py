#!/usr/bin/env python
"""
Script para probar PDF con documentos completos de mauricio1 y testuser_usa
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.utils.export_utils import DocumentoPDFExporter

def probar_pdf_cuentas_test():
    """Prueba la generación de PDF para documentos completos"""
    print("=== PROBANDO PDF CON DOCUMENTOS COMPLETOS ===")
    
    # Buscar empresas de test
    empresas_test = Empresa.objects.filter(
        nombre_taller__in=[
            'Taller de mauricio1', 
            'USA Test Garage'
        ]
    )
    
    print(f"📊 Empresas de test encontradas: {empresas_test.count()}")
    
    for empresa in empresas_test:
        print(f"\n🏢 === EMPRESA: {empresa.nombre_taller} ===")
        print(f"   País: {empresa.pais}")
        print(f"   Email: {empresa.email}")
        print(f"   Teléfono: {empresa.telefono}")
        
        # Obtener documentos de esta empresa
        documentos = Documento.objects.filter(empresa=empresa)[:3]  # Solo 3 para probar
        
        print(f"   📋 Documentos: {documentos.count()}")
        
        for doc in documentos:
            print(f"\n   🔍 Documento: {doc.tipo_documento} #{doc.numero_documento}")
            print(f"      Cliente: {doc.cliente.nombre}")
            print(f"      Fecha: {doc.fecha}")
            
            # Contar elementos
            repuestos = doc.repuestos.all()
            servicios = doc.servicios.all()
            otros_servicios = doc.otros_servicios.all()
            
            print(f"      📦 Repuestos: {repuestos.count()}")
            print(f"      🔧 Servicios: {servicios.count()}")
            print(f"      🏢 Otros servicios: {otros_servicios.count()}")
            
            if repuestos.count() > 0 or servicios.count() > 0 or otros_servicios.count() > 0:
                try:
                    # Generar PDF
                    exporter = DocumentoPDFExporter(doc)
                    pdf_content = exporter.generar_pdf()
                    
                    if pdf_content:
                        filename = f"invoice_{empresa.pais}_{doc.id}.pdf"
                        with open(filename, 'wb') as f:
                            f.write(pdf_content)
                        print(f"      ✅ PDF generado: {filename} ({len(pdf_content):,} bytes)")
                    else:
                        print(f"      ❌ PDF vacío")
                        
                except Exception as e:
                    print(f"      ❌ Error: {str(e)}")
            else:
                print(f"      ⚠️ Documento sin items - omitiendo PDF")
    
    print("\n=== PRUEBA COMPLETADA ===")

if __name__ == "__main__":
    probar_pdf_cuentas_test()
