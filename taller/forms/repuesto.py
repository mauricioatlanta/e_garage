from decimal import Decimal, InvalidOperation

from django import forms

from taller.models.repuesto import CategoriaRepuesto, Repuesto

SPANISH_CATEGORIES = [
    "Motor",
    "Frenos",
    "Sistema Eléctrico",
    "Suspensión",
    "Transmisión",
    "Sistema de Escape",
    "Refrigeración",
    "Combustible",
    "Carrocería",
    "Neumáticos",
    "Filtros",
    "Aceites y Lubricantes",
]

ENGLISH_CATEGORIES = [
    "Engine",
    "Brake",
    "Electrical",
    "Suspension",
    "Transmission",
    "Exhaust",
    "Cooling",
    "Fuel",
    "Body",
    "Tires",
    "Filters",
    "Oils",
]

PORTUGUESE_CATEGORIES = [
    "Motor",
    "Freios",
    "Sistema Elétrico",
    "Suspensão",
    "Transmissão",
    "Sistema de Escape",
    "Arrefecimento",
    "Combustível",
    "Carroceria",
    "Pneus",
    "Filtros",
    "Óleos e Lubrificantes",
]

CATEGORY_MAP = {
    "US": ("en", ENGLISH_CATEGORIES),
    "BR": ("pt", PORTUGUESE_CATEGORIES),
    "MX": ("es", SPANISH_CATEGORIES),
    "VE": ("es", SPANISH_CATEGORIES),
    "PE": ("es", SPANISH_CATEGORIES),
    "CL": ("es", SPANISH_CATEGORIES),
}

EMPTY_LABELS = {
    "en": "Select a category",
    "es": "Selecciona una categoría",
    "pt": "Selecione uma categoria",
}

DECIMAL_ERROR = {
    "en": "Ensure that there are no more than 2 decimal places.",
    "es": "Asegúrese de que no haya más de 2 dígitos decimales.",
    "pt": "Garanta que não haja mais de 2 casas decimais.",
}

PURCHASE_NUMBER_ERROR = {
    "en": "Purchase price must be a valid number",
    "es": "El precio de compra debe ser un número válido",
    "pt": "O preço de compra deve ser um número válido",
}

SALE_NUMBER_ERROR = {
    "en": "Sale price must be a valid number",
    "es": "El precio de venta debe ser un número válido",
    "pt": "O preço de venda deve ser um número válido",
}

PART_NUMBER_EXIST_ERROR = {
    "en": "Part number '{value}' already exists for this company",
    "es": "El número de parte '{value}' ya existe para esta empresa",
    "pt": "O número da peça '{value}' já existe para esta empresa",
}


class RepuestoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Extraer usuario para obtener configuración de país
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        empresa = getattr(self.user, "empresa", None) if self.user else None
        country = (getattr(empresa, "pais", "CL") or "CL").strip().upper() if empresa else "CL"
        lang, category_names = CATEGORY_MAP.get(country, ("es", SPANISH_CATEGORIES))
        self.language = lang

        self._configure_labels(lang)
        self._ensure_default_categories(empresa, category_names)
        self._configure_categoria_field(empresa, lang)

        # Configurar placeholders simples
        self.fields["precio_compra"].widget.attrs.update({"placeholder": "0.00"})
        self.fields["precio_venta"].widget.attrs.update({"placeholder": "0.00"})

    class Meta:
        model = Repuesto
        fields = [
            "part_number",
            "nombre",
            "categoria",
            "precio_compra",
            "precio_venta",
            "cantidad_stock",
            "stock_minimo",
            "proveedor",
        ]
        widgets = {
            "part_number": forms.TextInput(
                attrs={
                    "class": "w-full bg-black/40 text-white border border-cyan-400/30 rounded-lg p-2"
                }
            ),
            "nombre": forms.TextInput(
                attrs={
                    "class": "w-full bg-black/40 text-white border border-cyan-400/30 rounded-lg p-2"
                }
            ),
            "categoria": forms.Select(
                attrs={
                    "class": "w-full bg-black/40 text-white border border-cyan-400/30 rounded-lg p-2"
                }
            ),
            "precio_compra": forms.TextInput(
                attrs={
                    "class": "w-full bg-black/40 text-white border border-cyan-400/30 rounded-lg p-2",
                    "placeholder": "0.00",
                }
            ),
            "precio_venta": forms.TextInput(
                attrs={
                    "class": "w-full bg-black/40 text-white border border-cyan-400/30 rounded-lg p-2",
                    "placeholder": "0.00",
                }
            ),
            "cantidad_stock": forms.NumberInput(
                attrs={
                    "class": "w-full bg-black/40 text-white border border-cyan-400/30 rounded-lg p-2"
                }
            ),
            "stock_minimo": forms.NumberInput(
                attrs={
                    "class": "w-full bg-black/40 text-white border border-cyan-400/30 rounded-lg p-2"
                }
            ),
            "proveedor": forms.TextInput(
                attrs={
                    "class": "w-full bg-black/40 text-white border border-cyan-400/30 rounded-lg p-2"
                }
            ),
        }

    def _configure_labels(self, lang: str) -> None:
        if lang == "en":
            self.fields["part_number"].label = "Part Number"
            self.fields["part_number"].help_text = "Unique identifier for the part"

            self.fields["nombre"].label = "Name"
            self.fields["nombre"].help_text = "Part name or description"

            self.fields["categoria"].label = "Category"
            self.fields["categoria"].help_text = "Part category"

            self.fields["precio_compra"].label = "Purchase Price"
            self.fields["precio_compra"].help_text = "Price at which you bought the part"

            self.fields["precio_venta"].label = "Sale Price"
            self.fields["precio_venta"].help_text = "Price at which you sell the part"

            self.fields["cantidad_stock"].label = "Stock Quantity"
            self.fields["cantidad_stock"].help_text = "Available quantity in stock"

            self.fields["stock_minimo"].label = "Minimum Stock"
            self.fields["stock_minimo"].help_text = "Optional threshold for replenishment alerts"

            self.fields["proveedor"].label = "Supplier"
            self.fields["proveedor"].help_text = "Where you bought the part"
        elif lang == "pt":
            self.fields["part_number"].label = "Número da Peça"
            self.fields["part_number"].help_text = "Identificador único da peça"

            self.fields["nombre"].label = "Nome"
            self.fields["nombre"].help_text = "Nome ou descrição da peça"

            self.fields["categoria"].label = "Categoria"
            self.fields["categoria"].help_text = "Categoria da peça"

            self.fields["precio_compra"].label = "Preço de Compra"
            self.fields["precio_compra"].help_text = "Preço pelo qual você comprou a peça"

            self.fields["precio_venta"].label = "Preço de Venda"
            self.fields["precio_venta"].help_text = "Preço pelo qual você vende a peça"

            self.fields["cantidad_stock"].label = "Quantidade em Estoque"
            self.fields["cantidad_stock"].help_text = "Quantidade disponível em estoque"

            self.fields["stock_minimo"].label = "Estoque Mínimo"
            self.fields["stock_minimo"].help_text = "Limite opcional para alertas de reposição"

            self.fields["proveedor"].label = "Fornecedor"
            self.fields["proveedor"].help_text = "Onde você comprou a peça"
        else:
            self.fields["part_number"].label = "Número de Parte"
            self.fields["part_number"].help_text = "Identificador único de la parte"

            self.fields["nombre"].label = "Nombre"
            self.fields["nombre"].help_text = "Nombre o descripción de la parte"

            self.fields["categoria"].label = "Categoría"
            self.fields["categoria"].help_text = "Categoría de la parte"

            self.fields["precio_compra"].label = "Precio de Compra"
            self.fields["precio_compra"].help_text = "Precio al que compraste el repuesto"

            self.fields["precio_venta"].label = "Precio de Venta"
            self.fields["precio_venta"].help_text = "Precio al que vendes el repuesto"

            self.fields["cantidad_stock"].label = "Cantidad en Stock"
            self.fields["cantidad_stock"].help_text = "Cantidad disponible en stock"

            self.fields["stock_minimo"].label = "Stock Mínimo"
            self.fields["stock_minimo"].help_text = (
                "Umbral opcional para alertas de reabastecimiento"
            )

            self.fields["proveedor"].label = "Proveedor"
            self.fields["proveedor"].help_text = "Donde compraste el repuesto"

    def _ensure_default_categories(self, empresa, category_names):
        if not empresa:
            return
        for name in category_names:
            CategoriaRepuesto.objects.get_or_create(empresa=empresa, nombre=name)

    def _configure_categoria_field(self, empresa, lang):
        if empresa:
            queryset = CategoriaRepuesto.objects.filter(empresa=empresa).order_by("nombre")
            self.fields["categoria"].queryset = queryset
        else:
            self.fields["categoria"].queryset = CategoriaRepuesto.objects.none()
        self.fields["categoria"].empty_label = EMPTY_LABELS.get(lang, EMPTY_LABELS["es"])

    def clean_precio_compra(self):
        valor = self.cleaned_data.get("precio_compra")
        if valor is None:
            return valor

        try:
            if isinstance(valor, (int, float)):
                valor_str = str(valor)
            else:
                valor_str = str(valor)

            decimal_valor = Decimal(valor_str)

            if decimal_valor.as_tuple().exponent < -2:
                raise forms.ValidationError(DECIMAL_ERROR.get(self.language, DECIMAL_ERROR["es"]))

            return decimal_valor
        except (ValueError, TypeError, InvalidOperation):
            raise forms.ValidationError(
                PURCHASE_NUMBER_ERROR.get(self.language, PURCHASE_NUMBER_ERROR["es"])
            )

    def clean_precio_venta(self):
        valor = self.cleaned_data.get("precio_venta")
        if valor is None:
            return valor

        try:
            if isinstance(valor, (int, float)):
                valor_str = str(valor)
            else:
                valor_str = str(valor)

            decimal_valor = Decimal(valor_str)

            if decimal_valor.as_tuple().exponent < -2:
                raise forms.ValidationError(DECIMAL_ERROR.get(self.language, DECIMAL_ERROR["es"]))

            return decimal_valor
        except (ValueError, TypeError, InvalidOperation):
            raise forms.ValidationError(
                SALE_NUMBER_ERROR.get(self.language, SALE_NUMBER_ERROR["es"])
            )

    def clean_part_number(self):
        """Validar que el part_number sea único para la empresa"""
        part_number = self.cleaned_data.get("part_number")

        if not part_number:
            return part_number

        if self.user and hasattr(self.user, "empresa"):
            empresa = self.user.empresa
            existing_repuestos = Repuesto.objects.filter(empresa=empresa, part_number=part_number)

            if self.instance and self.instance.pk:
                existing_repuestos = existing_repuestos.exclude(pk=self.instance.pk)

            if existing_repuestos.exists():
                message = PART_NUMBER_EXIST_ERROR.get(
                    self.language, PART_NUMBER_EXIST_ERROR["es"]
                ).format(value=part_number)
                raise forms.ValidationError(message)

        return part_number

    def save(self, commit=True):
        instance = super().save(commit=False)

        if commit:
            instance.save()

        return instance
