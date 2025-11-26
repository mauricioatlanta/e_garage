from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.translation import get_language

from .models import CategoriaServicio, Servicio, ServicioName, SubcategoriaServicio
from .views import _detectar_pais, COUNTRY_LANGUAGE_MAP


class ServicioForm(forms.ModelForm):
    nombre_es = forms.CharField(label="Nombre (Español)", max_length=200, required=False)
    nombre_en = forms.CharField(label="Nombre (Inglés)", max_length=200, required=False)
    nombre = forms.CharField(label="Nombre del Servicio", max_length=200, required=True)
    subcategoria = forms.ModelChoiceField(
        queryset=SubcategoriaServicio.objects.none(),
        label="Subcategoría",
        required=True,
    )
    tipo = forms.ChoiceField(
        choices=[("interno", "Interno"), ("externo", "Externo")],
        label="Tipo",
        initial="interno",
    )

    class Meta:
        model = Servicio
        fields = ["subcategoria", "tipo"]

    def __init__(self, *args, **kwargs):
        country_code = kwargs.pop("country_code", "US")
        super().__init__(*args, **kwargs)
        # Filtrar subcategorías por país
        self.fields["subcategoria"].queryset = (
            SubcategoriaServicio.objects.filter(country=country_code)
            .exclude(code__in=["especiales", "emergencias"])
            .order_by("code")
        )

        # Si solo hay una opción, seleccionarla por defecto
        if self.fields["subcategoria"].queryset.count() == 1:
            self.fields["subcategoria"].initial = self.fields["subcategoria"].queryset.first()

    def save(self, commit=True, empresa=None, country_code=None, language=None):
        instance = super().save(commit=False)
        instance.tipo = self.cleaned_data["tipo"]

        if empresa:
            instance.empresa = empresa

        # Obtener categoría de la subcategoría
        if instance.subcategoria:
            instance.categoria = instance.subcategoria.categoria

        if commit:
            instance.save()

            # Crear nombres localizados
            nombre_principal = self.cleaned_data.get("nombre", "").strip()
            nombre_es = self.cleaned_data.get("nombre_es", "").strip() or nombre_principal
            nombre_en = self.cleaned_data.get("nombre_en", "").strip() or nombre_principal

            # Si el país es US, usar inglés como principal
            if country_code == "US":
                instance.nombre = nombre_en
                ServicioName.objects.get_or_create(
                    servicio=instance, language="en", is_default=True, defaults={"label": nombre_en}
                )
                if nombre_es and nombre_es != nombre_en:
                    ServicioName.objects.get_or_create(
                        servicio=instance,
                        language="es",
                        is_default=False,
                        defaults={"label": nombre_es},
                    )
            else:
                instance.nombre = nombre_es
                ServicioName.objects.get_or_create(
                    servicio=instance, language="es", is_default=True, defaults={"label": nombre_es}
                )
                if nombre_en and nombre_en != nombre_es:
                    ServicioName.objects.get_or_create(
                        servicio=instance,
                        language="en",
                        is_default=False,
                        defaults={"label": nombre_en},
                    )
            instance.save()
        return instance


@login_required
def crear_servicio(request):
    empresa = getattr(request.user, "empresa", None)
    country_code = _detectar_pais(request)
    lang = get_language() or "es"
    language = COUNTRY_LANGUAGE_MAP.get(country_code, (lang or "es")[:2])

    if request.method == "POST":
        form = ServicioForm(request.POST, country_code=country_code)
        if form.is_valid():
            servicio = form.save(empresa=empresa, country_code=country_code, language=language)
            return redirect("servicios:servicios_menu")
    else:
        form = ServicioForm(country_code=country_code)
        # Pre-llenar nombre según el idioma
        if language == "en":
            form.fields["nombre_en"].required = True
        else:
            form.fields["nombre_es"].required = True

    # Obtener categorías y subcategorías para el contexto
    categorias = CategoriaServicio.objects.filter(country=country_code).prefetch_related("names")
    subcategorias = (
        SubcategoriaServicio.objects.filter(country=country_code)
        .exclude(code__in=["especiales", "emergencias"])
        .prefetch_related("names")
    )

    return render(
        request,
        "taller/servicios/crear_servicio.html",
        {
            "form": form,
            "categorias": categorias,
            "subcategorias": subcategorias,
            "country_code": country_code,
            "language": language,
        },
    )
