from django.db import models

# Importación actualizada: Ahora usamos Empresa en lugar de TallerInfo
from taller.models.empresa import Empresa
from taller.models.trial import TrialRegistro

# NO es necesario importar User aquí si el lookup se hace de Empresa


def validar_prueba(email, telefono):
    """
    Devuelve True si el email/telefono es elegible para una nueva prueba (no existe registro previo).

    Busca si:
    1. Ya existe una Empresa cuyo *usuario principal* tenga ese email o cuyo *teléfono* coincida,
       Y que esa Empresa ya haya usado la prueba (ha_usado_prueba=True).
    2. Existe un registro previo en TrialRegistro con ese email o teléfono.
    """

    # 1. Búsqueda en Empresas ya existentes (reemplazando TallerInfo)
    # Usamos la relación inversa (user__email) y el campo telefono de la propia Empresa.
    # El modelo Empresa está relacionado OneToOne a User, por lo que podemos usar
    # la relación inversa 'empresa' en el User, o el lookup 'user__email' si
    # la relación fuera ForeignKey, pero para un OneToOne, la búsqueda por la relación inversa
    # es más eficiente: Empresa.objects.filter(user__email=email, ha_usado_prueba=True)

    existe_empresa = Empresa.objects.filter(
        (
            models.Q(user__email=email)  # Búsqueda por email del usuario principal
            | models.Q(telefono=telefono)  # Búsqueda por el teléfono del taller
        ),
        ha_usado_prueba=True,  # Si ya usaron la prueba
    ).exists()

    # 2. Búsqueda en TrialRegistro
    # Se mantiene la lógica para buscar registros de leads o intentos fallidos
    existe_trial = TrialRegistro.objects.filter(
        models.Q(email=email) | models.Q(telefono=telefono)
    ).exists()

    # Si existe una Empresa que ya usó la prueba O si existe un registro de Trial, NO es elegible (False)
    return not (existe_empresa or existe_trial)
