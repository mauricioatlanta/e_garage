#!/usr/bin/env python
import os
import sys
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio

def debug_documento_51():
    try:
        # Obtener el documento
        doc = Documento.objects.get(id=51)
        print(f"=== DOCUMENTO 51 ===")
        print(f"ID: {doc.id}")
        print(f"Número: {doc.numero_documento}")
        print(f"Estado: {doc.estado}")
        print(f"Cliente: {doc.cliente}")
        print()
        
        # Repuestos
        repuestos = LineaRepuesto.objects.filter(documento=doc)
        print(f"=== REPUESTOS ({repuestos.count()}) ===")
        subtotal_repuestos = Decimal('0')
        
        for i, rep in enumerate(repuestos, 1):
            precio = rep.precio_unitario or Decimal('0')
            cantidad = rep.cantidad or 1
            total = precio * cantidad
            subtotal_repuestos += total
            
            print(f"{i}. {rep.nombre} ({rep.codigo})")
            print(f"   Precio unitario: ${precio}")
            print(f"   Cantidad: {cantidad}")
            print(f"   Total: ${total}")
            print()
        
        print(f"SUBTOTAL REPUESTOS: ${subtotal_repuestos}")
        print()
        
        # Servicios
        servicios = LineaServicio.objects.filter(documento=doc)
        print(f"=== SERVICIOS ({servicios.count()}) ===")
        subtotal_servicios = Decimal('0')
        
        for i, serv in enumerate(servicios, 1):
            precio = serv.precio_unitario or Decimal('0')
            cantidad = serv.cantidad or 1
            total = precio * cantidad
            subtotal_servicios += total
            
            print(f"{i}. {serv.nombre}")
            print(f"   Precio unitario: ${precio}")
            print(f"   Cantidad: {cantidad}")
            print(f"   Total: ${total}")
            print()
        
        print(f"SUBTOTAL SERVICIOS: ${subtotal_servicios}")
        print()
        
        # Totales
        subtotal = subtotal_repuestos + subtotal_servicios
        iva = subtotal * Decimal('0.19')  # 19% IVA
        total = subtotal + iva
        
        print(f"=== TOTALES ===")
        print(f"Subtotal: ${subtotal}")
        print(f"IVA (19%): ${iva}")
        print(f"TOTAL: ${total}")
        
    except Documento.DoesNotExist:
        print("ERROR: Documento 51 no existe")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_documento_51()
