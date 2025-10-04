# taller/pdf/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from taller.models.documento import Documento


@login_required
def header(request, pk):
    """Vista para servir header de wkhtmltopdf"""
    obj = get_object_or_404(Documento, pk=pk, empresa=request.user.empresa)
    empresa = getattr(request.user, "empresa", None)
    
    context = {
        "obj": obj,
        "empresa_nombre": empresa.nombre_taller if empresa else "Mi Empresa",
    }
    
    return render(request, "pdf/header.html", context)


@login_required
def footer(request, pk):
    """Vista para servir footer de wkhtmltopdf"""
    obj = get_object_or_404(Documento, pk=pk, empresa=request.user.empresa)
    empresa = getattr(request.user, "empresa", None)
    
    context = {
        "obj": obj,
        "empresa_nombre": empresa.nombre_taller if empresa else "Mi Empresa",
    }
    
    return render(request, "pdf/footer.html", context)
