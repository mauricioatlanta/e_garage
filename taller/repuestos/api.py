from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse

from taller.models.repuesto import Repuesto


@login_required
def api_repuesto_por_codigo(request):
    """API para obtener repuesto por código con búsqueda inteligente"""
    try:
        code = request.GET.get("codigo", "").strip()
        
        print(f"🔧 Buscando repuestos: '{code}', Usuario: {request.user}")
        
        if not code or len(code) < 2:
            return JsonResponse({"results": []})
            
        empresa = getattr(request.user, "empresa", None)
        print(f"🏢 Empresa obtenida: {empresa}")
        
        qs = Repuesto.objects.all()
        print(f"📊 Total repuestos antes del filtro: {qs.count()}")
        
        if empresa:
            qs = qs.filter(empresa=empresa)
            print(f"📊 Total repuestos después del filtro de empresa: {qs.count()}")
        else:
            print("⚠️ No se encontró empresa para el usuario")
            
        # Búsqueda inteligente por part_number y nombre
        qs = qs.filter(
            Q(part_number__icontains=code) | 
            Q(nombre__icontains=code)
        )
        
        qs = qs.order_by("part_number")[:20]
        print(f"📊 Total repuestos después de la búsqueda: {qs.count()}")
        
        results = []
        for r in qs:
            # Crear texto de visualización más completo
            display_text = r.part_number or "Sin código"
            if r.nombre:
                display_text += f" - {r.nombre}"
                
            results.append({
                "id": r.id,
                "text": display_text,
                "codigo": r.part_number or "",
                "nombre": r.nombre or "",
                "precio_compra": str(getattr(r, "precio_compra", 0) or 0),
                "precio_venta": str(getattr(r, "precio_venta", 0) or 0),
                "stock": getattr(r, "cantidad_stock", 0),
            })
            
        print(f"✅ Encontrados {len(results)} repuestos")
        return JsonResponse({"results": results})
        
    except Exception as e:
        print(f"❌ Error en búsqueda de repuestos: {e}")
        return JsonResponse({"error": "Error en la búsqueda", "results": []})
