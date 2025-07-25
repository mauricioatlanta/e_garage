from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from taller.models.trial import TrialRegistro

@csrf_protect
def activar_trial(request):
    mensaje = error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        codigo = request.POST.get('codigo', '').strip()
        try:
            trial = TrialRegistro.objects.get(email=email, codigo=codigo)
            if trial.prueba_activa:
                mensaje = 'La prueba ya está activa. ¡Disfruta tus 30 días!'
                request.session['trial_email'] = email
            elif trial.prueba_expirada:
                error = 'La prueba ya expiró para este correo.'
            else:
                trial.prueba_activa = True
                trial.fecha_activacion = timezone.now()
                trial.save()
                request.session['trial_email'] = email
                mensaje = '¡Prueba activada! Tienes 30 días para disfrutar E-Garage.'
        except TrialRegistro.DoesNotExist:
            error = 'Correo o código incorrecto.'
    return render(request, 'activar_trial.html', {'mensaje': mensaje, 'error': error})
