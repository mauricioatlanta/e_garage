from django import forms
from django.utils.translation import gettext_lazy as _

from taller.models.repuesto import CategoriaRepuesto, Repuesto
from taller.models.tienda import Tienda
from utils.pais import formatear_precio, get_configuracion_pais


class RepuestoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Extraer usuario para obtener configuración de país
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Configurar labels y help_text según el idioma
        is_english = False
        if self.user and hasattr(self.user, "empresa"):
            is_english = self.user.empresa.pais == "US"

        if is_english:
            # English labels and help text
            self.fields["part_number"].label = "Part Number"
            self.fields["part_number"].help_text = "Unique identifier for the part"

            self.fields["nombre"].label = "Name"
            self.fields["nombre"].help_text = "Part name or description"

            self.fields["categoria"].label = "Category"
            self.fields["categoria"].help_text = "Part category"

            self.fields["precio_compra"].label = "Purchase Price"
            self.fields["precio_compra"].help_text = (
                "Price at which you bought the part"
            )

            self.fields["precio_venta"].label = "Sale Price"
            self.fields["precio_venta"].help_text = "Price at which you sell the part"

            self.fields["cantidad_stock"].label = "Stock Quantity"
            self.fields["cantidad_stock"].help_text = "Available quantity in stock"

            self.fields["proveedor"].label = "Supplier"
            self.fields["proveedor"].help_text = "Where you bought the part"

            # Filter categories for English users
            english_categories = [
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
            self.fields["categoria"].queryset = CategoriaRepuesto.objects.filter(
                empresa=self.user.empresa, nombre__in=english_categories
            )
        else:
            # Spanish labels and help text (default from model)
            self.fields["part_number"].label = "Número de Parte"
            self.fields["part_number"].help_text = "Identificador único de la parte"

            self.fields["nombre"].label = "Nombre"
            self.fields["nombre"].help_text = "Nombre o descripción de la parte"

            self.fields["categoria"].label = "Categoría"
            self.fields["categoria"].help_text = "Categoría de la parte"

            self.fields["precio_compra"].label = "Precio de Compra"
            self.fields["precio_compra"].help_text = (
                "Precio al que compraste el repuesto"
            )

            self.fields["precio_venta"].label = "Precio de Venta"
            self.fields["precio_venta"].help_text = "Precio al que vendes el repuesto"

            self.fields["cantidad_stock"].label = "Cantidad en Stock"
            self.fields["cantidad_stock"].help_text = "Cantidad disponible en stock"

            self.fields["proveedor"].label = "Proveedor"
            self.fields["proveedor"].help_text = "Donde compraste el repuesto"

            # Filter categories for Spanish users
            spanish_categories = [
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
            self.fields["categoria"].queryset = CategoriaRepuesto.objects.filter(
                empresa=self.user.empresa, nombre__in=spanish_categories
            )

        # Configurar placeholders y formatos según el país
        if self.user and hasattr(self.user, "empresa"):
            config = get_configuracion_pais(self.user.empresa)
            simbolo = config["simbolo_moneda"]
            moneda = config["moneda"]

            # Actualizar placeholders con la moneda correcta
            self.fields["precio_compra"].widget.attrs.update(
                {
                    "placeholder": (
                        f"{simbolo}0.00 {moneda}"
                        if config["decimales"] > 0
                        else f"{simbolo}0 {moneda}"
                    )
                }
            )
            self.fields["precio_venta"].widget.attrs.update(
                {
                    "placeholder": (
                        f"{simbolo}0.00 {moneda}"
                        if config["decimales"] > 0
                        else f"{simbolo}0 {moneda}"
                    )
                }
            )

    class Meta:
        model = Repuesto
        fields = [
            "part_number",
            "nombre",
            "categoria",
            "precio_compra",
            "precio_venta",
            "cantidad_stock",
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
                    "inputmode": "decimal",
                    "data-currency-field": "true",
                }
            ),
            "precio_venta": forms.TextInput(
                attrs={
                    "class": "w-full bg-black/40 text-white border border-cyan-400/30 rounded-lg p-2",
                    "inputmode": "decimal",
                    "data-currency-field": "true",
                }
            ),
            "cantidad_stock": forms.NumberInput(
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

    def clean_precio_compra(self):
        valor = self.cleaned_data["precio_compra"]

        # Determinar formato según el país del usuario
        if self.user and hasattr(self.user, "empresa"):
            config = get_configuracion_pais(self.user.empresa)
            separador_decimal = "." if config["decimales"] > 0 else ""
        else:
            separador_decimal = "."  # Default

        # Limpiar el valor: eliminar símbolos de moneda y separadores
        limpio = (
            str(valor).replace("$", "").replace("USD", "").replace("CLP", "").strip()
        )

        if separador_decimal and "." in limpio:
            # Para monedas con decimales (USD)
            limpio = limpio.replace(",", "")  # Remover separadores de miles
            try:
                return float(limpio)
            except ValueError:
                is_english = (
                    self.user
                    and hasattr(self.user, "empresa")
                    and self.user.empresa.pais == "US"
                )
                error_msg = (
                    "Purchase price must be a valid number"
                    if is_english
                    else "El precio de compra debe ser un número válido"
                )
                raise forms.ValidationError(error_msg)
        elif separador_decimal and "," in limpio and "." not in limpio:
            # Para formato europeo (comas como separador decimal)
            limpio = limpio.replace(",", ".")  # Convertir coma a punto
            try:
                return float(limpio)
            except ValueError:
                is_english = (
                    self.user
                    and hasattr(self.user, "empresa")
                    and self.user.empresa.pais == "US"
                )
                error_msg = (
                    "Purchase price must be a valid number"
                    if is_english
                    else "El precio de compra debe ser un número válido"
                )
                raise forms.ValidationError(error_msg)
        else:
            # Para monedas sin decimales (CLP)
            limpio = limpio.replace(".", "").replace(
                ",", ""
            )  # Remover todos los separadores
            try:
                return int(limpio)
            except ValueError:
                is_english = (
                    self.user
                    and hasattr(self.user, "empresa")
                    and self.user.empresa.pais == "US"
                )
                error_msg = (
                    "Purchase price must be a valid number"
                    if is_english
                    else "El precio de compra debe ser un número válido"
                )
                raise forms.ValidationError(error_msg)

    def clean_precio_venta(self):
        valor = self.cleaned_data["precio_venta"]
        # Determinar formato según el país del usuario
        if self.user and hasattr(self.user, "empresa"):
            config = get_configuracion_pais(self.user.empresa)
            separador_decimal = "." if config["decimales"] > 0 else ""
        else:
            separador_decimal = "."  # Default

        # Limpiar el valor: eliminar símbolos de moneda y separadores
        limpio = (
            str(valor).replace("$", "").replace("USD", "").replace("CLP", "").strip()
        )

        if separador_decimal and "." in limpio:
            # Para monedas con decimales (USD)
            limpio = limpio.replace(",", "")  # Remover separadores de miles
            try:
                return float(limpio)
            except ValueError:
                is_english = (
                    self.user
                    and hasattr(self.user, "empresa")
                    and self.user.empresa.pais == "US"
                )
                error_msg = (
                    "Sale price must be a valid number"
                    if is_english
                    else "El precio de venta debe ser un número válido"
                )
                raise forms.ValidationError(error_msg)
        elif separador_decimal and "," in limpio and "." not in limpio:
            # Para formato europeo (comas como separador decimal)
            limpio = limpio.replace(",", ".")  # Convertir coma a punto
            try:
                return float(limpio)
            except ValueError:
                is_english = (
                    self.user
                    and hasattr(self.user, "empresa")
                    and self.user.empresa.pais == "US"
                )
                error_msg = (
                    "Sale price must be a valid number"
                    if is_english
                    else "El precio de venta debe ser un número válido"
                )
                raise forms.ValidationError(error_msg)
        else:
            # Para monedas sin decimales (CLP)
            limpio = limpio.replace(".", "").replace(
                ",", ""
            )  # Remover todos los separadores
            try:
                return int(limpio)
            except ValueError:
                is_english = (
                    self.user
                    and hasattr(self.user, "empresa")
                    and self.user.empresa.pais == "US"
                )
                error_msg = (
                    "Sale price must be a valid number"
                    if is_english
                    else "El precio de venta debe ser un número válido"
                )
                raise forms.ValidationError(error_msg)

    def clean_part_number(self):
        """Validar que el part_number sea único para la empresa"""
        part_number = self.cleaned_data.get("part_number")

        if not part_number:
            return part_number  # Si está vacío, la validación del modelo se encargará

        # Verificar si ya existe un repuesto con el mismo part_number para la misma empresa
        if self.user and hasattr(self.user, "empresa"):
            empresa = self.user.empresa

            # Buscar repuestos existentes con el mismo part_number
            existing_repuestos = Repuesto.objects.filter(
                empresa=empresa, part_number=part_number
            )

            # Si estamos editando, excluir el repuesto actual
            if self.instance and self.instance.pk:
                existing_repuestos = existing_repuestos.exclude(pk=self.instance.pk)

            if existing_repuestos.exists():
                is_english = empresa.pais == "US"
                error_msg = (
                    f"Part number '{part_number}' already exists for this company"
                    if is_english
                    else f"El número de parte '{part_number}' ya existe para esta empresa"
                )
                raise forms.ValidationError(error_msg)

        return part_number

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Los valores ya están limpios por los métodos clean_*
        # No necesitamos hacer nada extra aquí

        if commit:
            instance.save()

        return instance
