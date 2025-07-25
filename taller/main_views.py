from django.shortcuts import render, redirect
from taller.documentos.forms import DocumentoForm
from taller.models.documento import Documento

def crear_documento(request):
    print("✅ Usando vista corregida crear_documento desde taller.documentos.views")

    if request.method == 'POST':
        form = DocumentoForm(request.POST)
        if form.is_valid():
            documento = form.save(commit=False)
            if not documento.numero_documento:
                tipo = documento.tipo_documento.lower().replace(" ", "_")
                count = Documento.objects.filter(tipo_documento=documento.tipo_documento).count() + 1
                documento.numero_documento = f"{tipo[:3].upper()}-{count:05d}"
            documento.save()
            form.save_m2m()
            return redirect('documentos:lista_documentos')
    else:
        form = DocumentoForm()

    return render(request, 'taller/documentos/crear_documento.html', {'form': form})

def landing_inicio(request):
    return render(request, 'public/landing_inicio.html')

def landing_premium(request):
    """Vista para la landing page premium de eGarage"""
    return render(request, 'landing.html')

def contacto_tailwind(request):
    return render(request, 'public/contacto_tailwind.html')

