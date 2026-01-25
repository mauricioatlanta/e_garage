"""
Calculadora de Impuestos para Documentos
Centraliza toda la lógica fiscal en el backend
"""

from decimal import Decimal
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class TaxLine:
    """Línea de impuesto calculada"""

    id: str
    label: str
    rate: Decimal
    amount: Decimal
    applies_to: str  # 'repuestos', 'servicios', 'all'


class TaxCalculator:
    """
    Calculadora de impuestos centralizada.
    Toda la lógica fiscal debe estar aquí, no en los templates.
    """

    # Tasas de impuestos por país
    TAX_RATES = {
        "CL": {
            "iva": Decimal("0.19"),  # 19% IVA en Chile
        },
        "US": {
            "sales_tax": Decimal("0.08"),  # 8% Sales Tax por defecto (configurable)
        },
        "AR": {
            "iva": Decimal("0.21"),  # 21% IVA en Argentina
        },
    }

    def __init__(self, country_code: Optional[str] = None, config: Optional[Dict] = None):
        """
        Inicializar calculadora de impuestos.

        Args:
            country_code: Código de país (CL, US, AR, etc.). Si es None, usa 'CL' como default seguro.
            config: Configuración adicional (ej: sales_tax personalizado para US)
        """
        # ✅ DEFAULT SEGURO: Si country_code es None o vacío, usar CL como fallback
        if not country_code or not country_code.strip():
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"TaxCalculator: country_code es None o vacío. Usando 'CL' como default seguro."
            )
            country_code = "CL"

        self.country_code = country_code.upper()
        self.config = config or {}
        self.tax_rates = self.TAX_RATES.get(self.country_code, {})

        # ✅ Si el país no está en TAX_RATES, usar configuración de CL como fallback
        if not self.tax_rates:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"TaxCalculator: País '{self.country_code}' no encontrado en TAX_RATES. "
                f"Usando configuración de CL como fallback."
            )
            self.country_code = "CL"
            self.tax_rates = self.TAX_RATES.get("CL", {})

        # Permitir sobrescribir tasas desde config
        if "sales_tax" in self.config:
            self.tax_rates["sales_tax"] = Decimal(str(self.config["sales_tax"]))

    def calculate_taxes(
        self,
        subtotal_repuestos: Decimal,
        subtotal_servicios: Decimal,
        subtotal_otros: Decimal = Decimal("0"),
        apply_tax: bool = True,
    ) -> List[TaxLine]:
        """
        Calcula todos los impuestos aplicables según el país.

        Args:
            subtotal_repuestos: Subtotal de repuestos (antes de impuestos)
            subtotal_servicios: Subtotal de servicios
            subtotal_otros: Subtotal de otros servicios
            apply_tax: Si se deben aplicar impuestos (checkbox del formulario)

        Returns:
            Lista de TaxLine con todos los impuestos calculados
        """
        if not apply_tax:
            return []

        tax_lines = []

        if self.country_code == "CL":
            # Chile: IVA 19% solo sobre repuestos
            iva_rate = self.tax_rates.get("iva", Decimal("0.19"))
            iva_amount = subtotal_repuestos * iva_rate
            tax_lines.append(
                TaxLine(
                    id="iva",
                    label="IVA",
                    rate=iva_rate * 100,  # Convertir a porcentaje para display
                    amount=iva_amount,
                    applies_to="repuestos",
                )
            )

        elif self.country_code == "US":
            # USA: Sales Tax configurable solo sobre repuestos
            sales_tax_rate = self.tax_rates.get("sales_tax", Decimal("0.08"))
            sales_tax_amount = subtotal_repuestos * sales_tax_rate
            tax_lines.append(
                TaxLine(
                    id="sales_tax",
                    label="Sales Tax",
                    rate=sales_tax_rate * 100,
                    amount=sales_tax_amount,
                    applies_to="repuestos",
                )
            )

        elif self.country_code == "AR":
            # Argentina: IVA 21% solo sobre repuestos
            iva_rate = self.tax_rates.get("iva", Decimal("0.21"))
            iva_amount = subtotal_repuestos * iva_rate
            tax_lines.append(
                TaxLine(
                    id="iva",
                    label="IVA",
                    rate=iva_rate * 100,
                    amount=iva_amount,
                    applies_to="repuestos",
                )
            )

        return tax_lines

    def calculate_total(
        self,
        subtotal_repuestos: Decimal,
        subtotal_servicios: Decimal,
        subtotal_otros: Decimal = Decimal("0"),
        tax_lines: Optional[List[TaxLine]] = None,
    ) -> Decimal:
        """
        Calcula el total general sumando subtotales e impuestos.

        Args:
            subtotal_repuestos: Subtotal de repuestos
            subtotal_servicios: Subtotal de servicios
            subtotal_otros: Subtotal de otros servicios
            tax_lines: Líneas de impuestos (si no se proporcionan, se calculan)

        Returns:
            Total general
        """
        if tax_lines is None:
            tax_lines = self.calculate_taxes(subtotal_repuestos, subtotal_servicios, subtotal_otros)

        total_taxes = sum(tax.amount for tax in tax_lines)
        return subtotal_repuestos + subtotal_servicios + subtotal_otros + total_taxes

    def get_tax_config_for_ui(self) -> Dict:
        """
        Retorna configuración de impuestos para el template (ui_config.tax_lines).
        Esto permite que el template renderice las líneas de impuestos dinámicamente
        sin conocer la lógica fiscal.
        """
        tax_lines_config = []

        if self.country_code == "CL":
            tax_lines_config.append(
                {
                    "id": "iva",
                    "label": "IVA",
                    "rate": "19",
                    "applies_to": "repuestos",
                }
            )
        elif self.country_code == "US":
            rate = self.tax_rates.get("sales_tax", Decimal("0.08"))
            tax_lines_config.append(
                {
                    "id": "sales_tax",
                    "label": "Sales Tax",
                    "rate": str(rate * 100),
                    "applies_to": "repuestos",
                }
            )
        elif self.country_code == "AR":
            tax_lines_config.append(
                {
                    "id": "iva",
                    "label": "IVA",
                    "rate": "21",
                    "applies_to": "repuestos",
                }
            )

        return {
            "tax_lines": tax_lines_config,
            "currency_code": self._get_currency_code(),
            "currency_symbol": self._get_currency_symbol(),
        }

    def _get_currency_code(self) -> str:
        """Retorna código de moneda según país"""
        currency_map = {
            "CL": "CLP",
            "US": "USD",
            "AR": "ARS",
        }
        return currency_map.get(self.country_code, "USD")

    def _get_currency_symbol(self) -> str:
        """Retorna símbolo de moneda según país"""
        symbol_map = {
            "CL": "$",
            "US": "$",
            "AR": "$",
        }
        return symbol_map.get(self.country_code, "$")
