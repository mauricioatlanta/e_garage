# -*- coding: utf-8 -*-
"""
Formularios para ubicación y direcciones.

Usa los modelos de taller.models.ubicacion (multi-país).
"""
from django import forms
from django.forms import ModelForm

from taller.models.ubicacion import Ciudad, Estado

from .models import Address


class AddressForm(ModelForm):
    """
    Formulario para crear/editar Address con selección de estado y ciudad.
    
    El campo 'estado' no está en Address pero se usa para filtrar ciudades.
    """
    estado = forms.ModelChoiceField(
        queryset=Estado.objects.all().order_by("nombre"),
        required=True,
        label="Estado/Región",
        widget=forms.Select(attrs={"id": "id_estado", "class": "form-select"}),
    )

    class Meta:
        model = Address
        fields = [
            "estado",  # Campo virtual para filtrar ciudades
            "city",
            "line1",
            "line2",
            "postal_code",
        ]
        widgets = {
            "city": forms.Select(attrs={"id": "id_ciudad", "class": "form-select"}),
            "line1": forms.TextInput(attrs={"class": "form-control", "placeholder": "Calle, número, edificio"}),
            "line2": forms.TextInput(attrs={"class": "form-control", "placeholder": "Apartamento, suite (opcional)"}),
            "postal_code": forms.TextInput(attrs={"id": "id_zip_code", "readonly": "readonly", "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Inicialmente sin ciudades hasta escoger estado
        self.fields["city"].queryset = Ciudad.objects.none()
        self.fields["city"].required = True

        # Si el Address ya existe, intenta setear estado desde city.estado
        if self.instance and self.instance.pk and hasattr(self.instance, "city") and self.instance.city:
            city = self.instance.city
            if hasattr(city, "estado_id") and city.estado_id:
                self.fields["estado"].initial = city.estado_id
                self.fields["city"].queryset = Ciudad.objects.filter(estado_id=city.estado_id).order_by("nombre")

        # Si viene POST, filtra ciudades por estado elegido
        if self.data.get("estado"):
            try:
                estado_id = int(self.data.get("estado"))
                self.fields["city"].queryset = Ciudad.objects.filter(estado_id=estado_id).order_by("nombre")
            except (TypeError, ValueError):
                pass

        # postal_code: no debe ser requerido porque viene del JS / backend
        self.fields["postal_code"].required = False

    def clean(self):
        cleaned = super().clean()
        estado = cleaned.get("estado")
        city = cleaned.get("city")

        # Validación: ciudad pertenece al estado elegido
        if estado and city and hasattr(city, "estado_id") and city.estado_id != estado.id:
            self.add_error("city", "La ciudad seleccionada no pertenece al estado elegido.")

        # Autocompletar postal_code desde la ciudad si existe
        if city and hasattr(city, "zip_code") and city.zip_code and not cleaned.get("postal_code"):
            cleaned["postal_code"] = city.zip_code

        return cleaned


class UbicacionForm(forms.Form):
    """
    Formulario legacy para registro de ubicación (sin Address).
    
    DEPRECADO: Usa AddressForm en su lugar.
    """
    estado = forms.ModelChoiceField(
        queryset=Estado.objects.all().order_by("nombre"),
        empty_label="Selecciona un estado",
        label="Estado",
        widget=forms.Select(attrs={"id": "id_estado", "class": "form-select"}),
    )
    ciudad = forms.ModelChoiceField(
        queryset=Ciudad.objects.none(),  # Se llena dinámicamente vía AJAX
        required=False,
        label="Ciudad",
        widget=forms.Select(attrs={"id": "id_ciudad", "class": "form-select"}),
    )
    zip_code = forms.CharField(
        label="Código Postal",
        required=False,
        widget=forms.TextInput(attrs={"readonly": "readonly", "id": "id_zip_code", "class": "form-control"}),
        help_text="Se completa automáticamente al seleccionar la ciudad",
    )
