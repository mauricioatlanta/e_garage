"""
Vistas de autocompletado para formularios de vehículos
Usando Django Autocomplete Light (DAL) para búsqueda inteligente
"""

from dal import autocomplete
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from taller.models.clientes import Cliente


class ClienteAutocomplete(autocomplete.Select2QuerySetView):
    """
    Autocompletado inteligente para clientes
    Búsqueda por: nombre, apellido, email, teléfono, tax_id
    Filtrado por empresa del usuario
    """
    
    def get_queryset(self):
        """Base queryset filtrado por empresa del usuario"""
        if not self.request.user.is_authenticated:
            return Cliente.objects.none()
        
        # Obtener empresa del usuario
        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            return Cliente.objects.none()
        
        # Base queryset filtrado por empresa
        qs = Cliente.objects.filter(empresa=empresa).order_by("nombre", "apellido")
        
        # Si hay término de búsqueda, filtrar
        if self.q:
            # Búsqueda case-insensitive en múltiples campos
            qs = qs.filter(
                Q(nombre__icontains=self.q) |
                Q(apellido__icontains=self.q) |
                Q(email__icontains=self.q) |
                Q(telefono__icontains=self.q) |
                Q(tax_id__icontains=self.q)
            ).distinct()
        
        return qs
    
    def get_result_label(self, result):
        """
        Formato personalizado para mostrar en el dropdown
        Muestra: "Nombre Apellido - Email (Teléfono)"
        """
        label_parts = []
        
        # Nombre completo
        if result.apellido:
            label_parts.append(f"{result.nombre} {result.apellido}")
        else:
            label_parts.append(result.nombre)
        
        # Email si existe
        if result.email:
            label_parts.append(f"- {result.email}")
        
        # Teléfono si existe
        if result.telefono:
            label_parts.append(f"({result.telefono})")
        
        return " ".join(label_parts)
    
    def get_result_value(self, result):
        """Valor que se guarda en el formulario (ID del cliente)"""
        return result.pk


# Vista alternativa más simple para casos específicos
class ClienteSimpleAutocomplete(autocomplete.Select2QuerySetView):
    """
    Autocompletado simple solo por nombre y apellido
    Para casos donde no necesitas búsqueda compleja
    """
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Cliente.objects.none()
        
        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            return Cliente.objects.none()
        
        qs = Cliente.objects.filter(empresa=empresa).order_by("nombre", "apellido")
        
        if self.q:
            qs = qs.filter(
                Q(nombre__icontains=self.q) |
                Q(apellido__icontains=self.q)
            )
        
        return qs


