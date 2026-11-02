# Script de reproducción verificable
# Ejecutar en orden para validar el problema y luego el fix

## 1) CREAR DATOS DE PRUEBA (usando Django shell)

# Crear vehículo que faltó
E:/projecto/e_garage/.venv/Scripts/python.exe manage.py shell --settings=settings_sqlite -c "
from taller.models.vehiculos import Vehiculo
from taller.models.clientes import Cliente
from taller.models.empresa import Empresa
empresa = Empresa.objects.get(nombre_taller='CL SA')
cliente = Cliente.objects.get(empresa=empresa, nombre='Juan Pérez')
vehiculo, created = Vehiculo.objects.get_or_create(
    empresa=empresa,
    cliente=cliente,
    patente='ABC123',
    defaults={'anio': 2020}
)
print(f'Vehículo creado: {vehiculo} (ID: {vehiculo.id})')
"

## 2) PROBAR CREAR DOCUMENTO VÍA POST (debe fallar en redirección y totales)

# Login primero
http --session=test POST http://127.0.0.1:8000/accounts/login/ \
  username=testuser_cl password=test123 \
  --follow --print=HhBb

# Crear documento con líneas
http --session=test POST http://127.0.0.1:8000/cl/documentos/nuevo/ \
  tipo=OT \
  fecha=2025-08-22 \
  cliente=30 \
  vehiculo=? \
  tecnico=3 \
  kilometraje=123456 \
  estado=emitido \
  incluir_impuesto=on \
  'repuestos_data=[{"id":53,"cantidad":"2","precio":"50000","descuento":"10"}, {"id":54,"cantidad":"1","precio":"150000","descuento":"0"}]' \
  'servicios_data=[{"nombre":"Alineación","cantidad":"1","precio":"25000","descuento":"0","codigo":"ALI01"}]' \
  'otros_servicios_data=[{"nombre":"Rectificado","empresa_externa":"Tercero SPA","cantidad":"1","costo_interno":"10000","precio_cliente":"22000"}]' \
  --follow --print=HhBb

## 3) VERIFICAR DOCUMENTO CREADO VÍA DJANGO SHELL

E:/projecto/e_garage/.venv/Scripts/python.exe manage.py shell --settings=settings_sqlite -c "
from decimal import Decimal
from taller.models.documento import Documento

doc = Documento.objects.latest('id')
print('millas/km:', getattr(doc, 'millas', None) or getattr(doc, 'kilometraje', None))
print('neto_repuestos:', doc.neto_repuestos, 'neto_servicios:', doc.neto_servicios, 'tax_amount:', doc.tax_amount, 'total:', doc.total)
print('repuestos:', doc.lineas_repuesto.count(), 'servicios:', doc.lineas_servicio.count(), 'otros:', doc.lineas_otro_servicio.count())
for lr in doc.lineas_repuesto.all():
    print('REP:', lr.cantidad, lr.precio_unitario, lr.descuento)
for ls in doc.lineas_servicio.all():
    print('SER:', ls.nombre, ls.cantidad, ls.precio_unitario, ls.descuento)
for lo in doc.lineas_otro_servicio.all():
    print('OTR:', lo.nombre, lo.cantidad, lo.precio_cliente, 'gan:', lo.ganancia)
"

## 4) VERIFICAR DETALLE DEL DOCUMENTO EN BROWSER

http --session=test GET http://127.0.0.1:8000/cl/documentos/1/ \
  --print=HhBb
