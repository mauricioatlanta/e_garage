"""
MonteAzulAdapter — adapta CatalogImporter al esquema SQLite real de MonteAzul.

Solo sobreescribe las diferencias respecto al esquema genérico:
  - Nombres de tablas: catalog_category, catalog_product, catalog_productimage
  - Columna de descripción: ficha_tecnica (en lugar de description)
  - Directorio de imágenes: productos/

Cualquier otra casa de repuestos crea su propio adapter de la misma forma.
"""
from commerce.services.catalog.importer import CatalogImporter


class MonteAzulAdapter(CatalogImporter):

    TABLE_CATEGORIES = "catalog_category"
    TABLE_PRODUCTS   = "catalog_product"
    TABLE_IMAGES     = "catalog_productimage"
    TABLE_COMPAT     = "catalog_productcompatibility"

    COL_DESCRIPTION  = "ficha_tecnica"

    IMAGE_SEARCH_DIRS: tuple[str, ...] = ("productos",)
