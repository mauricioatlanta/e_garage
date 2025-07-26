
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from ..forms.suscripcion import FormularioRegistro
from ..models.suscripcion import Suscripcion
from ..models.empresa import Empresa
from taller.models.taller_info import TallerInfo
from taller.views.registro_utils import validar_prueba
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages

# Vista original
@login_required
def suscripcion_bloqueada(request):
    return render(request, "suscripcion_bloqueada.html", {
        "dias_restantes": 0,
        "empresa": getattr(request, "empresa", None),
    })

# --- Registro y activación ---
import random
codigos_activacion = {}

def registro(request):
    if request.method == 'POST':
        form = FormularioRegistro(request.POST)
        tipo_registro = request.POST.get('tipo_registro')
        if form.is_valid():
            email = form.cleaned_data['email']
            telefono = form.cleaned_data['telefono']
            nombre_taller = form.cleaned_data['nombre_taller']
            plan = form.cleaned_data['plan']

            # VALIDACIÓN: Verificar si ya existe una empresa para este email/usuario
            if User.objects.filter(email=email).exists():
                existing_user = User.objects.get(email=email)
                if Empresa.objects.filter(user=existing_user).exists():
                    return render(request, 'suscripcion/usuario_existente.html')

            if tipo_registro == 'trial':
                # Validar si ya se usó prueba gratuita
                if not validar_prueba(email, telefono):
                    return render(request, 'suscripcion/prueba_ya_usada.html', {'email': email, 'telefono': telefono})

            user = form.save()

            # NUEVO: Verificar si el usuario ya tiene empresa asociada (por seguridad)
            if Empresa.objects.filter(user=user).exists():
                messages.warning(request, "Ya tienes una empresa registrada asociada a tu usuario.")
                return redirect('nombre_vista_deseada')  # Cambia por la vista que corresponda

            # Crear empresa automáticamente para el usuario
            empresa = Empresa.objects.create(
                user=user,
                nombre_taller=nombre_taller,
                email=email
            )

            ha_usado_prueba = (tipo_registro == 'trial')
            TallerInfo.objects.create(user=user, nombre_taller=nombre_taller, telefono=telefono, ha_usado_prueba=ha_usado_prueba)
            codigo = random.randint(100000, 999999)
            codigos_activacion[user.username] = str(codigo)
            send_mail(
                'Código de activación eGarage',
                f'Tu código de activación es: {codigo}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )
            send_mail(
                'Nuevo registro recibido',
                f'Se ha registrado el usuario: {user.username} - Plan: {plan} - Taller: {nombre_taller}',
                settings.DEFAULT_FROM_EMAIL,
                ['subcripcion@atlantareciclajes.cl']
            )
            request.session['usuario_activacion'] = user.username
            return render(request, 'registro_enviado.html', {'codigo': True})
    else:
        form = FormularioRegistro()
    return render(request, 'suscripcion/registro.html', {'form': form})


def activar(request):
    username = request.session.get('usuario_activacion')
    if not username:
        return render(request, 'error_activacion.html')
    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo')
        codigo_real = codigos_activacion.get(username)
        if codigo_ingresado and codigo_real and codigo_ingresado == codigo_real:
            user = User.objects.get(username=username)
            suscripcion = getattr(user, 'suscripcion', None)
            if suscripcion:
                suscripcion.activar()
                del codigos_activacion[username]
                del request.session['usuario_activacion']
                return render(request, 'activado.html')
        return render(request, 'error_activacion.html')
    return render(request, 'suscripcion/activar_codigo.html')
