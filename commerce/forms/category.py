from django import forms

from commerce.models import CommerceCategory


class CommerceCategoryForm(forms.ModelForm):
    class Meta:
        model = CommerceCategory
        fields = [
            "parent",
            "name",
            "slug",
            "description",
            "image",
            "is_active",
            "meta_title",
            "meta_description",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input-dark", "placeholder": "Ej: Filtros de aceite"}),
            "slug": forms.TextInput(attrs={"class": "form-input-dark", "placeholder": "auto-generado si se deja vacío"}),
            "description": forms.Textarea(attrs={"class": "form-input-dark", "rows": 3}),
            "meta_title": forms.TextInput(attrs={"class": "form-input-dark", "maxlength": 70}),
            "meta_description": forms.Textarea(attrs={"class": "form-input-dark", "rows": 2, "maxlength": 160}),
            "parent": forms.Select(attrs={"class": "form-input-dark"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-checkbox-dark"}),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa is not None:
            qs = CommerceCategory.objects.filter(empresa=empresa)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            self.fields["parent"].queryset = qs.order_by("name")
        self.fields["slug"].required = False
        self.fields["parent"].empty_label = "— Sin categoría padre —"
