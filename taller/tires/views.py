import re
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from taller.models.tire import Tire
from taller.services.empresa_service import get_empresa_safe


def _tires_base(request):
    # /us/en/tires/crear/ -> /us/en/tires/ | /mx/es/tires/editar/5/ -> /mx/es/tires/
    path = request.path or ""
    if "/tires/" in path:
        return path.split("/tires/")[0] + "/tires/"
    return "/tires/"

def _go_lista(request):
    from django.shortcuts import redirect as _red
    return _red(_tires_base(request))

def _parse_medida(q):
    m = re.search(r"(\d{3})\D+(\d{2})\D+R?(\d{2})", q or "", re.I)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return None

@login_required
def lista_tires(request):
    empresa = get_empresa_safe(request)
    qs = Tire.objects.filter(empresa=empresa).order_by("ancho","perfil","aro","marca") if empresa else Tire.objects.none()
    q = (request.GET.get("q") or "").strip()
    if q:
        parsed = _parse_medida(q)
        if parsed:
            ancho, perfil, aro = parsed
            qs = qs.filter(ancho=ancho, perfil=perfil, aro=aro)
        else:
            qs = qs.filter(Q(marca__icontains=q) | Q(modelo__icontains=q) | Q(tipo__icontains=q))
    return render(request, "taller/tires/lista.html", {"tires": qs, "q": q, "empresa": empresa})

@login_required
def crear_tire(request):
    empresa = get_empresa_safe(request)
    if request.method == "POST":
        if not (request.POST.get("proveedor") or "").strip():
            messages.error(request, "Proveedor es obligatorio")
            return render(request, "taller/tires/crear.html", {"empresa": empresa})
        try:
            t = Tire(
                empresa=empresa,
                ancho=int(request.POST.get("ancho") or 0),
                perfil=int(request.POST.get("perfil") or 0),
                aro=int(request.POST.get("aro") or 0),
                marca=(request.POST.get("marca") or "Sin marca").strip() or "Sin marca",
                modelo=(request.POST.get("modelo") or "").strip(),
                indice=(request.POST.get("indice") or "").strip(),
                tipo=request.POST.get("tipo") or "Nuevo",
                uso=request.POST.get("uso") or "Ciudad",
                dot=(request.POST.get("dot") or "").strip(),
                cantidad_stock=int(request.POST.get("stock") or 0),
                precio_venta=request.POST.get("precio_venta") or 0,
                precio_instalado=request.POST.get("precio_instalado") or request.POST.get("precio_venta") or 0,
                precio_compra=request.POST.get("precio_compra") or 0,
                proveedor=(request.POST.get("proveedor") or "").strip(),
            )
            t.full_clean()
            t.save()
            messages.success(request, f"Neumatico creado: {t.medida} {t.tipo} {t.marca}")
            return _go_lista(request)
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, "taller/tires/crear.html", {"empresa": empresa})

@login_required
def editar_tire(request, pk):
    empresa = get_empresa_safe(request)
    t = get_object_or_404(Tire, pk=pk, empresa=empresa)
    if request.method == "POST":
        t.ancho=int(request.POST.get("ancho") or t.ancho)
        t.perfil=int(request.POST.get("perfil") or t.perfil)
        t.aro=int(request.POST.get("aro") or t.aro)
        t.marca=(request.POST.get("marca") or t.marca).strip() or "Sin marca"
        t.modelo=(request.POST.get("modelo") or t.modelo).strip()
        t.indice=(request.POST.get("indice") or t.indice).strip()
        t.dot=(request.POST.get("dot") or t.dot).strip()
        t.proveedor=(request.POST.get("proveedor") or t.proveedor or "").strip()
        t.tipo=request.POST.get("tipo") or t.tipo
        t.uso=request.POST.get("uso") or t.uso
        t.cantidad_stock=int(request.POST.get("stock") or t.cantidad_stock)
        t.precio_compra=request.POST.get("precio_compra") or t.precio_compra
        t.precio_venta=request.POST.get("precio_venta") or t.precio_venta
        t.precio_instalado=request.POST.get("precio_instalado") or t.precio_instalado
        t.save()
        messages.success(request, f"Editado: {t.medida} {t.tipo}")
        return _go_lista(request)
    return render(request, "taller/tires/crear.html", {"empresa": empresa, "tire": t, "editando": True})

@login_required
def eliminar_tire(request, pk):
    empresa = get_empresa_safe(request)
    t = get_object_or_404(Tire, pk=pk, empresa=empresa)
    if request.method == "POST":
        t.delete()
        messages.success(request, "Neumatico eliminado")
        return _go_lista(request)
    return render(request, "taller/tires/eliminar.html", {"tire": t})

@login_required
def buscar_tires(request):
    return lista_tires(request)

@login_required
def kiosko_tires(request):
    """Kiosko / Vitrina - SOLO neumaticos, nunca repuestos. Para cliente y para mostrador."""
    empresa = get_empresa_safe(request)
    qs = Tire.objects.filter(empresa=empresa).order_by("ancho","perfil","aro","marca") if empresa else Tire.objects.none()
    q = (request.GET.get("q") or "").strip()
    if q:
        parsed = _parse_medida(q)
        if parsed:
            ancho, perfil, aro = parsed
            qs = qs.filter(ancho=ancho, perfil=perfil, aro=aro)
        else:
            qs = qs.filter(Q(marca__icontains=q) | Q(modelo__icontains=q))
    tipo = (request.GET.get("tipo") or "").strip()
    if tipo in ["Nuevo","Usado","Recapado"]:
        qs = qs.filter(tipo=tipo)
    return render(request, "taller/tires/kiosko.html", {"tires": qs, "q": q, "tipo": tipo, "empresa": empresa})

from django.http import JsonResponse

@login_required
def autocomplete_tires(request):
    """Devuelve medidas existentes para la lista emergente. ?q=175 o ?ancho=175&perfil=70"""
    empresa = get_empresa_safe(request)
    if not empresa:
        return JsonResponse({"results": []})
    qs = Tire.objects.filter(empresa=empresa)
    q = (request.GET.get("q") or "").strip()
    ancho = (request.GET.get("ancho") or "").strip()
    perfil = (request.GET.get("perfil") or "").strip()
    aro = (request.GET.get("aro") or "").strip()
    # Filtros progresivos: si ya escribió ancho, filtra por ese ancho, etc.
    if ancho.isdigit():
        qs = qs.filter(ancho=int(ancho))
    if perfil.isdigit():
        qs = qs.filter(perfil=int(perfil))
    if aro.isdigit():
        qs = qs.filter(aro=int(aro))
    if q:
        # Si escribe "175" o "175/70" filtra por texto
        m = _parse_medida(q)
        if m:
            qs = qs.filter(ancho=m[0], perfil=m[1], aro=m[2])
        elif q.isdigit():
            # NO usar icontains en campos numéricos (da error 500). Solo marca por texto.
            qs = qs.filter(Q(marca__icontains=q))
    # Medidas distintas con stock total
    from django.db.models import Count, Sum
    medidas = qs.values("ancho", "perfil", "aro").annotate(total=Count("id"), stock=Sum("cantidad_stock")).order_by("ancho", "perfil", "aro")[:20]
    results = []
    for r in medidas:
        medida = f"{r['ancho']}/{r['perfil']} R{r['aro']}"
        results.append({"ancho": r["ancho"], "perfil": r["perfil"], "aro": r["aro"], "medida": medida, "total": r["total"], "stock": r["stock"] or 0, "label": f"{medida} - {r['total']} tipo(s) - Stock {r['stock'] or 0}"})
    # También anchos / perfiles / aros sueltos para autocompletar cada campo
    anchos = list(qs.values_list("ancho", flat=True).distinct().order_by("ancho")[:20])
    perfiles = list(qs.values_list("perfil", flat=True).distinct().order_by("perfil")[:20])
    aros = list(qs.values_list("aro", flat=True).distinct().order_by("aro")[:20])
    return JsonResponse({"results": results, "anchos": anchos, "perfiles": perfiles, "aros": aros})

# --- VISTA PÚBLICA: la que ve todo el mundo, sin login ---
def kiosko_publico(request):
    """Kiosko público: sin login, solo muestra neumáticos en stock. No muestra precio compra."""
    from django.shortcuts import render as _render
    # Empresa: por ?empresa=, por sesión, o la primera que tenga neumáticos
    empresa = None
    empresa_id = request.GET.get("empresa") or request.session.get("empresa_id")
    if empresa_id:
        try:
            empresa = Empresa.objects.get(id=empresa_id)
        except Exception:
            empresa = None
    if empresa is None:
        # Si hay neumáticos, usar la empresa del primer neumático
        primer = Tire.objects.select_related("empresa").first()
        if primer:
            empresa = primer.empresa
    if empresa is None:
        empresa = Empresa.objects.first()
    tires = Tire.objects.filter(empresa=empresa, cantidad_stock__gt=0).order_by("ancho", "perfil", "aro", "marca") if empresa else Tire.objects.none()
    # NO mostrar precio_compra al público - solo venta / instalado
    return _render(request, "taller/tires/kiosko_mi_taller.html", {"empresa": empresa, "tires": tires, "publico": True})


# --- KIOSKO PUBLICO REAL: SIN base.html interna, SIN login ---
def kiosko_mi_taller_publico(request, slug=None):
    """PUBLICO: solo un taller, por slug. Ej: /us/en/tires/public/mauricioatlanta/ - SIN login, SIN base interna. A prueba de errores."""
    from django.shortcuts import render as _render
    from django.utils.text import slugify
    try:
        empresa = None
        if slug:
            s = str(slug).strip()
            if s.isdigit():
                empresa = Empresa.objects.filter(id=int(s)).first()
            else:
                # 1. Por slug del nombre
                try:
                    for e in Empresa.objects.all()[:500]:
                        try:
                            if slugify(getattr(e, "nombre", "") or "") == s:
                                empresa = e
                                break
                        except Exception:
                            continue
                except Exception:
                    pass
                # 2. Por nombre contiene
                if empresa is None:
                    try:
                        empresa = Empresa.objects.filter(nombre__icontains=s.replace("-", " ")).first()
                    except Exception:
                        pass
                # 3. Por slug field si existe
                if empresa is None:
                    try:
                        empresa = Empresa.objects.filter(slug__iexact=s).first()
                    except Exception:
                        pass
        if empresa is None:
            empresa = Empresa.objects.first()
        try:
            tires = Tire.objects.filter(empresa=empresa, cantidad_stock__gt=0).order_by("ancho", "perfil", "aro", "marca") if empresa else Tire.objects.none()
        except Exception:
            tires = Tire.objects.none()
        return _render(request, "taller/tires/kiosko_mi_taller.html", {"empresa": empresa, "tires": tires})
    except Exception as e:
        # Si algo falla, no dar 500: mostrar página pública vacía con el error en log
        import traceback
        traceback.print_exc()
        try:
            return _render(request, "taller/tires/kiosko_mi_taller.html", {"empresa": None, "tires": [], "error": str(e)})
        except Exception:
            from django.http import HttpResponse
            return HttpResponse(f"<h1>Kiosko</h1><p>Error temporal: {e}</p>", status=200)


def kiosko_global_publico(request):
    """Kiosko Global POR PAIS, a prueba de errores."""
    from django.shortcuts import render as _render
    try:
        q = (request.GET.get("q") or "").strip()
        pais = "cl"
        try:
            partes = [x for x in (request.path or "").split("/") if x]
            paises_validos = ["us", "cl", "mx", "co", "pe", "ar", "br", "ve", "ec", "uy"]
            if partes and partes[0].lower() in paises_validos:
                pais = partes[0].lower()
            elif (request.GET.get("pais") or "").lower() in paises_validos:
                pais = request.GET.get("pais").lower()
        except Exception:
            pais = "cl"
        try:
            tires_qs = Tire.objects.filter(cantidad_stock__gt=0).order_by("ancho", "perfil", "aro", "marca")
        except Exception:
            tires_qs = Tire.objects.none()
        if q:
            import re as _re
            m = _re.search(r"(\d{3})\s*/\s*(\d{2,3})\s*R?\s*(\d{2})", q)
            try:
                if m:
                    tires_qs = tires_qs.filter(ancho=int(m.group(1)), perfil=int(m.group(2)), aro=int(m.group(3)))
                else:
                    tires_qs = tires_qs.filter(marca__icontains=q) | tires_qs.filter(modelo__icontains=q)
            except Exception:
                pass
        try:
            lista = list(tires_qs[:200])
        except Exception:
            lista = []
        return _render(request, "taller/tires/kiosko_global.html", {"tires": lista, "q": q, "pais": pais})
    except Exception as e:
        import traceback
        traceback.print_exc()
        from django.http import HttpResponse
        return HttpResponse("<h1>Kiosko Global</h1><p>Error temporal: " + str(e) + "</p>", status=200)

