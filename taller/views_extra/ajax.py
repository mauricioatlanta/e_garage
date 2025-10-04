from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse

from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.utils.empresa import get_or_create_empresa
from utils import pais


def _safe_fields(model):
    return {f.name for f in model._meta.get_fields()}


@login_required
def buscar_clientes(request):
    """Búsqueda AJAX de clientes con mejor manejo de errores"""
    try:
        term = (request.GET.get("q") or "").strip()
        
        # Debug logging
        print(f"[DEBUG] Buscando clientes: '{term}', Usuario: {request.user}")
        
        if not term or len(term) < 2:
            return JsonResponse({"results": []})
        
        empresa = get_or_create_empresa(request)
        print(f"🏢 Empresa obtenida: {empresa}")
        
        qs = Cliente.objects.all()
        print(f"[DEBUG] Total clientes antes del filtro: {qs.count()}")
        
        if empresa:
            qs = qs.filter(empresa=empresa)
            print(f"[DEBUG] Total clientes después del filtro de empresa: {qs.count()}")
        else:
            print("⚠️ No se encontró empresa para el usuario")
            
        # Búsqueda más inteligente
        qs = qs.filter(
            Q(nombre__icontains=term) | 
            Q(apellido__icontains=term) |
            Q(tax_id__icontains=term) | 
            Q(telefono__icontains=term) | 
            Q(email__icontains=term)
        )
        
        qs = qs.order_by("nombre")[:20]
        print(f"[DEBUG] Total clientes después de la búsqueda: {qs.count()}")
        
        results = []
        for c in qs:
            # Crear texto de visualización más completo
            display_text = f"{c.nombre}"
            if hasattr(c, 'apellido') and c.apellido:
                display_text += f" {c.apellido}"
            if c.tax_id:
                display_text += f" (RUT: {c.tax_id})"
                
            results.append({
                "id": c.id, 
                "text": display_text,
                "nombre": c.nombre,
                "apellido": getattr(c, 'apellido', ''),
                "rut": c.tax_id or "", 
                "telefono": getattr(c, "telefono", ""),
                "email": getattr(c, "email", "")
            })
        
        print(f"[OK] Encontrados {len(results)} clientes")
        return JsonResponse({"results": results})
        
    except Exception as e:
        print(f"[ERROR] Error en búsqueda de clientes: {e}")
        return JsonResponse({"error": "Error en la búsqueda", "results": []})


@login_required
def vehiculos_por_cliente(request):
    """Obtener vehículos de un cliente específico - Filtrado por empresa y cliente (drop-in correcto)"""
    try:
        cliente_id = request.GET.get("cliente_id") or request.GET.get("cliente")
        
        print(f"🚗 Buscando vehículos para cliente: {cliente_id}, Usuario: {request.user}")
        
        if not cliente_id:
            print("⚠️ No se proporcionó ID de cliente")
            return JsonResponse({"results": []})
        
        # Validar que cliente_id sea un número válido
        try:
            cliente_id = int(cliente_id)
        except (ValueError, TypeError):
            print(f"⚠️ ID de cliente inválido: {cliente_id}")
            return JsonResponse({"error": "ID de cliente inválido", "results": []})
            
        empresa = get_or_create_empresa(request)
        print(f"🏢 Empresa obtenida: {empresa}")
        
        if not empresa:
            print("⚠️ No se pudo obtener empresa del usuario")
            return JsonResponse({"error": "Empresa no encontrada", "results": []})
        
        # ✅ FILTRO CRÍTICO: empresa + cliente usando el nuevo manager
        qs = Vehiculo.objects.de_empresa(empresa).de_cliente(cliente_id).select_related('marca', 'modelo').order_by("-id")[:50]
        
        print(f"[DEBUG] Total vehículos encontrados: {qs.count()}")
        
        # Formatear respuesta usando el nuevo método display_label()
        data = []
        for v in qs:
            data.append({
                "id": v.id,
                "text": v.display_label(),
                "label": v.display_label(),  # Compatibilidad con diferentes frontends
                "patente": v.patente or "",
                "vin": v.vin or "",
                "marca": v.get_marca_display(),
                "modelo": v.get_modelo_display(),
                "anio": getattr(v, "anio", None),
            })
            
        print(f"[OK] Encontrados {len(data)} vehículos")
        return JsonResponse({"results": data})
        
    except Exception as e:
        print(f"[ERROR] Error obteniendo vehículos: {e}")
        return JsonResponse({"error": "Error obteniendo vehículos", "results": []})


def ciudades_por_region(request):
    pais_codigo = request.GET.get("pais")
    region = request.GET.get("region")
    ciudades = pais.get_ciudades(pais_codigo, region)
    return JsonResponse({"ciudades": ciudades})

    if q:
        fields = _safe_fields(Cliente)
        terms = q.split()
        for t in terms:
            cond = Q(nombre__icontains=t)
            if "apellido" in fields:
                cond |= Q(apellido__icontains=t)
            if "tax_id" in fields:
                cond |= Q(tax_id__icontains=t)
            if "telefono" in fields:
                cond |= Q(telefono__icontains=t)
            if "email" in fields:
                cond |= Q(email__icontains=t)
            qs = qs.filter(cond)

    qs = qs.order_by("nombre")
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(page)

    results = []
    fields = _safe_fields(Cliente)
    for c in page_obj.object_list:
        # [FIX] BISTURÍ: Construir texto con nombre+apellido
        nombre_parts = [c.nombre]
        if "apellido" in fields and getattr(c, "apellido", None):
            nombre_parts.append(c.apellido)
        text = " ".join(filter(None, nombre_parts))

        # Construir subtitle con info adicional
        extra = []
        if "tax_id" in fields and getattr(c, "tax_id", None):
            extra.append(c.tax_id)
        if "telefono" in fields and getattr(c, "telefono", None):
            extra.append(c.telefono)
        if "email" in fields and getattr(c, "email", None):
            extra.append(c.email)
        subtitle = " · ".join(extra) if extra else ""

        results.append(
            {
                "id": c.id,
                "text": text,
                "subtitle": subtitle,
            }
        )

    return JsonResponse(
        {
            "results": results,
            "more": page_obj.has_next(),
        }
    )


@login_required
def vehiculos_por_cliente(request):
    empresa = get_or_create_empresa(request)
    # [FIX] BISTURÍ: Aceptar tanto 'cliente' como 'cliente_id'
    cliente_id = request.GET.get("cliente") or request.GET.get("cliente_id")
    if not cliente_id:
        return JsonResponse({"results": []})

    qs = (
        Vehiculo.objects.filter(empresa=empresa, cliente_id=cliente_id)
        .select_related("marca", "modelo")
        .order_by("-id")[:50]
    )

    def _name(v):
        marca = (
            v.get_marca_display()
            if hasattr(v, "get_marca_display")
            else (
                getattr(getattr(v, "marca", None), "nombre", "")
                or getattr(v, "marca_texto", "")
                or ""
            )
        )
        modelo = (
            v.get_modelo_display()
            if hasattr(v, "get_modelo_display")
            else (
                getattr(getattr(v, "modelo", None), "nombre", "")
                or getattr(v, "modelo_texto", "")
                or ""
            )
        )
        tag = getattr(v, "patente", None) or getattr(v, "vin", None) or ""
        parts = [p for p in [marca, modelo, tag] if p]
        return " ".join(parts) if parts else f"Vehículo #{v.pk}"

    return JsonResponse({"results": [{"id": v.pk, "text": _name(v)} for v in qs]})


def ciudades_por_region(request):
    pais_codigo = request.GET.get("pais")
    region = request.GET.get("region")
    ciudades = pais.get_ciudades(pais_codigo, region)
    return JsonResponse({"ciudades": ciudades})
