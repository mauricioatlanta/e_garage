from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import CategoriaServicio, Servicio, ServicioName, SubcategoriaServicio


class ServicioForm(forms.ModelForm):
    nombre_es = forms.CharField(label="Nombre (Español)", max_length=100)
    nombre_en = forms.CharField(label="Nombre (Inglés)", max_length=100)
    subcategoria = forms.ModelChoiceField(
        queryset=SubcategoriaServicio.objects.exclude(code__in=["especiales", "emergencias"]),
        label="Subcategoría",
    )
    country = forms.ChoiceField(choices=CategoriaServicio.COUNTRY_CHOICES, label="País")
    tipo = forms.ChoiceField(choices=[("interno", "Interno"), ("externo", "Externo")], label="Tipo")

    class Meta:
        model = Servicio
        fields = ["subcategoria", "country", "tipo"]

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tipo = self.cleaned_data["tipo"]
        instance.country = self.cleaned_data["country"]
        if commit:
            instance.save()
            ServicioName.objects.create(
                servicio=instance,
                language="es",
                label=self.cleaned_data["nombre_es"],
                is_default=True,
            )
            ServicioName.objects.create(
                servicio=instance,
                language="en",
                label=self.cleaned_data["nombre_en"],
                is_default=True,
            )
        return instance


@login_required
def crear_servicio(request):
    if request.method == "POST":
        form = ServicioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("servicios:servicios_menu")
    else:
        form = ServicioForm()
    return render(request, "taller/servicios/crear_servicio.html", {"form": form})
