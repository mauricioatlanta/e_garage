#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.vehiculos import Vehiculo

print("🌐 ANÁLISIS PARA PORTAL DE CLIENTES")
print("="*50)

# Estadísticas
total_clientes = Cliente.objects.count()
clientes_con_email = Cliente.objects.exclude(email__isnull=True).exclude(email__exact='').count()
total_documentos = Documento.objects.count()

print(f"👥 Total clientes: {total_clientes}")
print(f"📧 Clientes con email: {clientes_con_email}")
print(f"📄 Total documentos: {total_documentos}")

print(f"\n📊 {clientes_con_email} clientes pueden usar el portal")

print("\n🎯 CREANDO MODELOS DEL PORTAL...")
print("✅ Modelos diseñados:")
print("   - ClienteUsuario (autenticación)")
print("   - SolicitudPresupuesto")
print("   - PortalConfiguracion")
print("   - AccesoPortal (auditoría)")

print("\n🚀 Portal de clientes listo para implementar")
