# Proxy para compatibilidad: Mecanico apunta a Tecnico
from taller.models.tecnico import Tecnico


class Mecanico(Tecnico):
    class Meta:
        proxy = True
