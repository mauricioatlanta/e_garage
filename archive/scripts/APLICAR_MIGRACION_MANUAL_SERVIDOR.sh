#!/bin/bash
# Script para aplicar migración 0056 manualmente en el servidor

echo "🔍 Verificando estructura de migraciones..."
ls -1 taller/migrations/*.py | sort -V | tail -5

echo ""
echo "📝 Creando migración 0056..."
cat > taller/migrations/0056_add_company_settings_fields.py <<'EOF'
# Generated manually to add missing CompanySettings fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0005_remove_empresa_empresa_valor_mensual_gte_0_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="companysettings",
            name="terms_and_conditions",
            field=models.TextField(
                blank=True,
                help_text="Términos que aparecen en contratos y documentos",
                verbose_name="Términos y condiciones",
            ),
        ),
        migrations.AddField(
            model_name="companysettings",
            name="apply_tax_by_default",
            field=models.BooleanField(
                default=True,
                help_text="Aplicar impuesto automáticamente en nuevos documentos",
                verbose_name="Aplicar impuesto por defecto",
            ),
        ),
        migrations.AddField(
            model_name="companysettings",
            name="separate_by_technician",
            field=models.BooleanField(
                default=False,
                help_text="Mostrar reportes separados por técnico",
                verbose_name="Separar por técnico",
            ),
        ),
        migrations.AddField(
            model_name="companysettings",
            name="tax_rate",
            field=models.DecimalField(
                decimal_places=2,
                default=19.0,
                help_text="Tasa de impuesto por defecto (ej: 19.00 para Chile, 0.00 para USA)",
                max_digits=5,
                verbose_name="Tasa de impuesto",
            ),
        ),
    ]
EOF

echo "✅ Migración creada"
ls -la taller/migrations/0056*.py

echo ""
echo "💾 Aplicando cambios directamente en la base de datos..."
python3 <<'PYTHON'
import sqlite3
import os

db_path = 'db.sqlite3'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar columnas existentes
    cursor.execute("PRAGMA table_info(taller_companysettings)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Columnas actuales: {', '.join(columns)}")
    
    # Agregar columnas si no existen
    changes = False
    if 'terms_and_conditions' not in columns:
        cursor.execute("ALTER TABLE taller_companysettings ADD COLUMN terms_and_conditions text DEFAULT ''")
        print("✅ Agregada: terms_and_conditions")
        changes = True
    
    if 'apply_tax_by_default' not in columns:
        cursor.execute("ALTER TABLE taller_companysettings ADD COLUMN apply_tax_by_default integer DEFAULT 1")
        print("✅ Agregada: apply_tax_by_default")
        changes = True
    
    if 'separate_by_technician' not in columns:
        cursor.execute("ALTER TABLE taller_companysettings ADD COLUMN separate_by_technician integer DEFAULT 0")
        print("✅ Agregada: separate_by_technician")
        changes = True
    
    if 'tax_rate' not in columns:
        cursor.execute("ALTER TABLE taller_companysettings ADD COLUMN tax_rate text DEFAULT '19.00'")
        print("✅ Agregada: tax_rate")
        changes = True
    
    if not changes:
        print("ℹ️  Todas las columnas ya existen")
    else:
        conn.commit()
        print("✅ Cambios aplicados exitosamente")
    
    conn.close()
else:
    print("❌ Base de datos no encontrada en: " + db_path)
PYTHON

echo ""
echo "✅ Proceso completado"
