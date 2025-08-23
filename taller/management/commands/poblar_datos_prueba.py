from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.region_ciudad import TallerRegion, TallerCiudad
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaServicio, LineaRepuesto, LineaOtroServicio
from taller.models.repuesto import Repuesto
from taller.servicios.models import Servicio, SubcategoriaServicio, CategoriaServicio
from taller.models.tienda import Tienda
from taller.models.tecnico import Tecnico
import random
from datetime import date

class Command(BaseCommand):
    help = 'Crea 10 clientes de prueba (3 con más de 1 auto), 5 documentos por cliente, con repuestos, servicios y otros servicios.'

    def handle(self, *args, **options):
        # Buscar empresa USA de prueba
        empresa = Empresa.objects.filter(pais='US').first()
        if not empresa:
            self.stdout.write(self.style.ERROR('No existe empresa USA de prueba.'))
            return

        # Buscar o crear región y ciudad
        region, _ = TallerRegion.objects.get_or_create(nombre='Florida')
        ciudad, _ = TallerCiudad.objects.get_or_create(nombre='Miami', region=region)

        # Buscar o crear tienda
        tienda, _ = Tienda.objects.get_or_create(empresa=empresa, nombre='Tienda Central')

        # Buscar o crear técnico
        tecnico, _ = Tecnico.objects.get_or_create(empresa=empresa, nombre='John Mechanic')

        # Buscar o crear repuestos base
        repuestos = []
        for i in range(5):
            rep, _ = Repuesto.objects.get_or_create(
                empresa=empresa,
                tienda=tienda,
                nombre_repuesto=f'Repuesto Test {i+1}',
                part_number=f'RPT-{i+1}',
                defaults={'precio_venta': random.randint(50, 200), 'precio_compra': random.randint(20, 49), 'stock': 100}
            )
            repuestos.append(rep)

        # Buscar o crear servicios base
        categoria, _ = CategoriaServicio.objects.get_or_create(country='US', code='GEN')
        subcat, _ = SubcategoriaServicio.objects.get_or_create(categoria=categoria, country='US', code='GEN-SUB')
        servicios = []
        for i in range(5):
            serv, _ = Servicio.objects.get_or_create(
                subcategoria=subcat,
                country='US',
                tipo='interno',
                code=f'SRV-{i+1}',
                defaults={'precio_base': random.randint(100, 300)}
            )
            servicios.append(serv)

        # Crear clientes y autos
        clientes = []
        for i in range(10):
            cliente = Cliente.objects.create(
                empresa=empresa,
                nombre=f'Cliente{i+1}',
                apellido='Prueba',
                telefono=f'555-00{i+1}',
                direccion='Calle Falsa 123',
                region=region,
                ciudad=ciudad,
                email=f'cliente{i+1}@test.com'
            )
            clientes.append(cliente)

        # Crear autos (3 clientes con más de 1 auto)
        from taller.models.marca import Marca
        from taller.models.modelo import Modelo
        marca, _ = Marca.objects.get_or_create(nombre='Ford', country='US')
        modelo, _ = Modelo.objects.get_or_create(nombre='Focus', marca=marca, country='US')
        autos = {}
        for idx, cliente in enumerate(clientes):
            autos[cliente.id] = []
            num_autos = 2 if idx < 3 else 1
            for j in range(num_autos):
                auto = Vehiculo.objects.create(
                    empresa=empresa,
                    cliente=cliente,
                    marca=marca,
                    modelo=modelo,
                    patente=f'TEST{idx+1}{j+1}',
                    anio=2020+j,
                )
                autos[cliente.id].append(auto)

        # Crear documentos y asociar repuestos, servicios y otros servicios
        for cliente in clientes:
            for d in range(5):
                vehiculo = random.choice(autos[cliente.id])
                doc = Documento.objects.create(
                    empresa=empresa,
                    tipo_documento='Presupuesto',
                    numero_documento=f'DOC-{cliente.id}-{d+1}',
                    fecha=date.today(),
                    cliente=cliente,
                    vehiculo=vehiculo,
                    kilometraje=random.randint(10000, 90000),
                    tecnico=tecnico,
                    incluir_iva=True
                )
                # Agregar repuestos
                for _ in range(3):
                    rep = random.choice(repuestos)
                    LineaRepuesto.objects.create(
                        documento=doc,
                        repuesto=rep,
                        codigo=rep.part_number,
                        nombre=rep.nombre_repuesto,
                        cantidad=random.randint(1, 3),
                        precio_unitario=rep.precio_venta
                    )
                # Agregar servicios
                for _ in range(3):
                    srv = random.choice(servicios)
                    LineaServicio.objects.create(
                        empresa=empresa,
                        documento=doc,
                        nombre=srv.get_label(),
                        precio=srv.precio_base or 100
                    )
                # Agregar otros servicios
                for _ in range(2):
                    LineaOtroServicio.objects.create(
                        documento=doc,
                        nombre='Lavado Premium',
                        empresa_externa='CleanCar Inc.',
                        costo_interno=30,
                        precio_cliente=50
                    )
        self.stdout.write(self.style.SUCCESS('Datos de prueba generados correctamente.'))
