from django import forms

from commerce.models import CommerceCategory, CommerceProduct


class CommerceProductAdminForm(forms.ModelForm):
    class Meta:
        model = CommerceProduct
        fields = [
            "category",
            "descripcion_larga",
            "compare_at_price",
            "is_publishable",
            "meta_title",
            "meta_description",
            "og_image",
        ]
        widgets = {
            "category": forms.Select(attrs={"class": "form-input-dark"}),
            "descripcion_larga": forms.Textarea(attrs={"class": "form-input-dark", "rows": 5}),
            "compare_at_price": forms.NumberInput(attrs={"class": "form-input-dark", "step": "0.01"}),
            "meta_title": forms.TextInput(attrs={"class": "form-input-dark", "maxlength": 70}),
            "meta_description": forms.Textarea(attrs={"class": "form-input-dark", "rows": 2, "maxlength": 160}),
            "is_publishable": forms.CheckboxInput(attrs={"class": "form-checkbox-dark"}),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa is not None:
            self.fields["category"].queryset = (
                CommerceCategory.objects.filter(empresa=empresa, is_active=True).order_by("name")
            )
        self.fields["category"].empty_label = "— Sin categoría —"
        self.fields["category"].required = False
        self.fields["compare_at_price"].required = False
        self.fields["og_image"].required = False
