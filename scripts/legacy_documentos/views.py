from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from taller.models.documento import Documento


@login_required
def lista_documentos(request):
    # Mostrar solo documentos de la empresa del usuario
    try:
        empresa = request.user.empresa
        documentos = Documento.objects.filter(empresa=empresa).order_by("-fecha_emision", "-id")
    except AttributeError:
        # Si el usuario no tiene empresa asignada, mostrar lista vacía
        documentos = Documento.objects.none()

    return render(request, "taller/documentos/lista_documentos.html", {"documentos": documentos})
