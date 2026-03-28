# La columna sales_tax_rate existe en algunas BD (NOT NULL) sin estar en el modelo Django,
# lo que rompe INSERT/get_or_create. Sincronizamos estado ORM y aseguramos la columna si falta.

from decimal import Decimal

from django.db import migrations, models


def _column_exists(schema_editor, table: str, column: str) -> bool:
    conn = schema_editor.connection
    vendor = conn.vendor
    with conn.cursor() as cursor:
        if vendor == "sqlite":
            cursor.execute(f'PRAGMA table_info("{table}")')
            return any(row[1] == column for row in cursor.fetchall())
        if vendor == "postgresql":
            cursor.execute(
                """
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = %s AND column_name = %s
                """,
                [table, column],
            )
            return cursor.fetchone() is not None
        if vendor == "mysql":
            cursor.execute(
                """
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = DATABASE()
                  AND table_name = %s AND column_name = %s
                """,
                [table, column],
            )
            return cursor.fetchone() is not None
    return False


def add_sales_tax_rate_if_missing(apps, schema_editor):
    table = "taller_configuracionempresa"
    if _column_exists(schema_editor, table, "sales_tax_rate"):
        return
    if schema_editor.connection.vendor == "sqlite":
        schema_editor.execute(
            f'ALTER TABLE "{table}" ADD COLUMN sales_tax_rate decimal NOT NULL DEFAULT 0'
        )
    elif schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            f'ALTER TABLE "{table}" ADD COLUMN sales_tax_rate numeric(5,2) NOT NULL DEFAULT 0'
        )
    elif schema_editor.connection.vendor == "mysql":
        schema_editor.execute(
            f"ALTER TABLE `{table}` ADD COLUMN sales_tax_rate DECIMAL(5,2) NOT NULL DEFAULT 0"
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0093_merge_0091_0092"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="configuracionempresa",
                    name="sales_tax_rate",
                    field=models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0"),
                        help_text="Tasa de impuesto a ventas (porcentaje); complementa tasa_impuesto donde aplica.",
                        max_digits=5,
                        verbose_name="Sales tax rate (%)",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_sales_tax_rate_if_missing, noop_reverse),
            ],
        ),
    ]
