from taller.models import Modelo, Marca
try:
    from taller.models import ModeloVehiculo
except ImportError:
    ModeloVehiculo = None

def resolver_o_crear_modelo(modelo_id, marca_id=None, country="US"):
    if not modelo_id:
        return None
    modelo_str = str(modelo_id).strip()

    # 1. Por ID directo numérico
    if modelo_str.isdigit():
        m = Modelo.objects.filter(id=int(modelo_str)).first()
        if m:
            return m

    # 2. Por catálogo USA (ModeloVehiculo)
    if ModeloVehiculo and modelo_str.isdigit():
        mv = ModeloVehiculo.objects.filter(id=int(modelo_str)).first()
        if mv:
            marca_obj = Marca.objects.filter(nombre__iexact=mv.marca.nombre).first()
            if not marca_obj and marca_id:
                marca_obj = Marca.objects.filter(id=int(marca_id)).first() if str(marca_id).isdigit() else Marca.objects.filter(nombre__iexact=str(marca_id)).first()
            if marca_obj:
                m = Modelo.objects.filter(marca=marca_obj, nombre__iexact=mv.nombre).first()
                if not m:
                    m = Modelo.objects.create(marca=marca_obj, nombre=mv.nombre, country=country)
                return m

    # 3. Buscar por texto en Modelo
    qs = Modelo.objects.filter(nombre__iexact=modelo_str)
    if country:
        qs_c = qs.filter(country=country)
        if qs_c.exists():
            qs = qs_c
    m = qs.first()
    if m:
        return m

    # 4. Crear modelo si se conoce la marca
    if marca_id:
        marca_obj = Marca.objects.filter(id=int(marca_id)).first() if str(marca_id).isdigit() else Marca.objects.filter(nombre__iexact=str(marca_id).strip()).first()
        if marca_obj:
            m = Modelo.objects.create(marca=marca_obj, nombre=modelo_str, country=country)
            return m
    return None
