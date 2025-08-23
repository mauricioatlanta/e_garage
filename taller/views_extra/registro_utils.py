from taller.models.taller_info import TallerInfo
from django.db import models


from taller.models.trial import TrialRegistro

def validar_prueba(email, telefono):
    # Devuelve False si ya existe un registro con ese email o teléfono y ha_usado_prueba=True o TrialRegistro
    existe_taller = TallerInfo.objects.filter(
        (models.Q(user__email=email) | models.Q(telefono=telefono)),
        ha_usado_prueba=True
    ).exists()
    existe_trial = TrialRegistro.objects.filter(
        models.Q(email=email) | models.Q(nombre__icontains=telefono)
    ).exists()
    return not (existe_taller or existe_trial)
