#!/usr/bin/env python
"""
Script para probar la funcionalidad de impresión de documentos PDF
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.documento import Documento
from taller.utils.export_utils import DocumentoPDFExporter

def probar_pdf_documento():
    """Prueba la generación de PDF para un documento existente"""
    print("=== PROBANDO GENERACIÓN DE PDF ===")
    
    # Obtener un documento para probar
    documentos = Documento.objects.all()[:5]
    
    if not documentos:
        print("❌ No hay documentos para probar")
        return
    
    print(f"📋 Documentos disponibles: {documentos.count()}")
    
    for doc in documentos:
        print(f"\n🔍 Probando documento: {doc.tipo_documento} #{doc.numero_documento}")
        print(f"   Cliente: {doc.cliente.nombre}")
        print(f"   Fecha: {doc.fecha}")
        print(f"   Empresa: {doc.empresa.nombre_taller}")
        
        try:
            # Crear el exportador
            exporter = DocumentoPDFExporter(doc)
            
            # Verificar datos para el PDF
            repuestos = doc.repuestos.all()
            servicios = doc.servicios.all()
            otros_servicios = doc.otros_servicios.all()
            
            print(f"   📦 Repuestos: {repuestos.count()}")
            print(f"   🔧 Servicios: {servicios.count()}")
            print(f"   🏢 Otros servicios: {otros_servicios.count()}")
            
            # Calcular totales
            total_repuestos = sum(r.total for r in repuestos)
            total_servicios = sum(s.precio for s in servicios)
            total_otros_servicios = sum(os.precio_cliente for os in otros_servicios)
            
            print(f"   💰 Total repuestos: ${total_repuestos:,.0f}")
            print(f"   💰 Total servicios: ${total_servicios:,.0f}")
            print(f"   💰 Total otros servicios: ${total_otros_servicios:,.0f}")
            
            subtotal = total_repuestos + total_servicios + total_otros_servicios
            iva = subtotal * 0.19 if doc.incluir_iva else 0
            total = subtotal + iva
            
            print(f"   💰 SUBTOTAL: ${subtotal:,.0f}")
            if doc.incluir_iva:
                print(f"   💰 IVA (19%): ${iva:,.0f}")
            print(f"   💰 TOTAL: ${total:,.0f}")
            
            # Intentar generar PDF
            pdf_content = exporter.generar_pdf()
            
            if pdf_content:
                print(f"   ✅ PDF generado exitosamente ({len(pdf_content)} bytes)")
                
                # Guardar PDF de prueba
                filename = f"test_pdf_{doc.id}.pdf"
                with open(filename, 'wb') as f:
                    f.write(pdf_content)
                print(f"   💾 PDF guardado como: {filename}")
            else:
                print(f"   ❌ Error: PDF vacío")
                
        except Exception as e:
            print(f"   ❌ Error al generar PDF: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n=== PRUEBA COMPLETADA ===")

if __name__ == "__main__":
    probar_pdf_documento()
