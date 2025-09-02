from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from taller.forms.empresa import EmpresaForm, DatosPersonalesForm
from taller.models.empresa import Empresa

@login_required
def configuracion(request):
    """Vista para configurar los datos de la empresa/taller y datos personales"""
    # Obtener o crear la empresa del usuario actual
    empresa, created = Empresa.objects.get_or_create(usuario=request.user)
    
    # Inicializar formularios
    empresa_form = EmpresaForm(instance=empresa)
    datos_form = DatosPersonalesForm(user=request.user)
    
    if request.method == 'POST':
        # Determinar qué formulario se envió
        if 'empresa_form' in request.POST:
            # Depuración completa de archivos subidos
            print("\n" + "="*50)
            print("🔍 DEBUG COMPLETO - Subida de archivos:")
            print(f"  POST data: {dict(request.POST)}")
            print(f"  FILES data: {dict(request.FILES)}")
            print(f"  Content type: {request.content_type}")
            print(f"  Method: {request.method}")
            
            if 'logo' in request.FILES:
                logo_file = request.FILES['logo']
                print(f"  📁 Archivo logo encontrado:")
                print(f"    - Nombre: {logo_file.name}")
                print(f"    - Tamaño: {logo_file.size} bytes")
                print(f"    - Tipo MIME: {logo_file.content_type}")
                print(f"    - Charset: {getattr(logo_file, 'charset', 'N/A')}")
                print(f"    - Multiple chunks: {logo_file.multiple_chunks()}")
            else:
                print("  ❌ NO se encontró archivo 'logo' en FILES")
                print(f"  ❌ Archivos disponibles: {list(request.FILES.keys())}")
            print("="*50)
            
            empresa_form = EmpresaForm(request.POST, request.FILES, instance=empresa)
            
            if empresa_form.is_valid():
                empresa_form.save()
                messages.success(request, '✅ Datos de la empresa actualizados correctamente!')
                return redirect('configuracion')
            else:
                messages.error(request, '❌ Error al guardar los datos de la empresa. Revisa los datos.')
        
        elif 'datos_form' in request.POST:
            datos_form = DatosPersonalesForm(request.POST, user=request.user)
            
            if datos_form.is_valid():
                # Actualizar datos del usuario
                user = request.user
                user.first_name = datos_form.cleaned_data['first_name']
                user.last_name = datos_form.cleaned_data['last_name']
                user.email = datos_form.cleaned_data['email']
                user.save()
                
                messages.success(request, '✅ Datos personales actualizados correctamente!')
                return redirect('configuracion')
            else:
                messages.error(request, '❌ Error al guardar los datos personales. Revisa los datos.')

    context = {
        'empresa_form': empresa_form,
        'datos_form': datos_form,
        'empresa': empresa,
        'created': created
    }
    # Usar template resolution en lugar de template hardcodeado
    from taller.utils.templates import select_country_lang_template
    from django.utils.translation import get_language
    from django.template.response import TemplateResponse
    
    template_name = select_country_lang_template(
        "configuracion.html", 
        getattr(request.user.empresa, 'pais', 'cl').lower(), 
        get_language()
    )
    
    return TemplateResponse(request, template_name, context)
