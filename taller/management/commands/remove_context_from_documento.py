"""
Elimina la columna 'context' de taller_documento cuando existe en la DB
pero NO en el modelo Django (drift de esquema).

Uso: python manage.py remove_context_from_documento [--dry-run]

Causa: La tabla en producción tiene context NOT NULL, el modelo no,
y los INSERT fallan con IntegrityError.
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = "Elimina la columna 'context' de taller_documento (reconstruye la tabla sin ella)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo mostrar qué se haría, sin ejecutar",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        with connection.cursor() as c:
            # 1) Verificar si la columna context existe
            c.execute("PRAGMA table_info(taller_documento)")
            columns = c.fetchall()
            col_names = [row[1] for row in columns]

            if "context" not in col_names:
                self.stdout.write(
                    self.style.SUCCESS("✅ La columna 'context' no existe. Nada que hacer.")
                )
                return

            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ Columna 'context' encontrada. Columnas actuales: {len(col_names)}"
                )
            )

            # 2) Obtener el SQL del CREATE TABLE actual
            c.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='taller_documento'"
            )
            row = c.fetchone()
            if not row:
                self.stderr.write(self.style.ERROR("❌ Tabla taller_documento no encontrada"))
                return
            original_sql = row[0]

            # 3) Columnas para el INSERT/SELECT (todas menos context)
            cols_for_copy = [name for name in col_names if name != "context"]
            cols_str = ", ".join(cols_for_copy)

            if dry_run:
                self.stdout.write(
                    self.style.NOTICE(f"[DRY-RUN] Se reconstruiría la tabla excluyendo 'context'")
                )
                self.stdout.write(f"Columnas a copiar ({len(cols_for_copy)}): {cols_str}")
                return

            self.stdout.write("Ejecutando reconstrucción de tabla...")

            # 4) Reconstruir tabla
            sql_steps = [
                "ALTER TABLE taller_documento RENAME TO taller_documento_old;",
                # Crear nueva tabla: mismo SQL pero sin la línea de context
                # Extraemos el body del CREATE y quitamos context
                self._build_create_without_context(original_sql),
                f"INSERT INTO taller_documento ({cols_str}) SELECT {cols_str} FROM taller_documento_old;",
                "DROP TABLE taller_documento_old;",
            ]

            try:
                with transaction.atomic():
                    for i, sql in enumerate(sql_steps):
                        self.stdout.write(f"  Paso {i + 1}/4...")
                        c.execute(sql)

                # Verificar
                c.execute("PRAGMA table_info(taller_documento)")
                new_cols = [r[1] for r in c.fetchall()]
                if "context" in new_cols:
                    self.stderr.write(
                        self.style.ERROR("❌ context sigue presente. Revisar manualmente.")
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Listo. taller_documento ahora tiene {len(new_cols)} columnas (sin context)."
                        )
                    )
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ Error durante la reconstrucción: {e}"))
                raise

    def _build_create_without_context(self, original_sql):
        """
        Parsea el CREATE TABLE original y devuelve uno igual pero sin la columna context.
        SQLite CREATE: CREATE TABLE nombre ( col1 type, col2 type, ... );
        """
        # Encontrar el paréntesis que contiene las columnas
        start = original_sql.upper().find(" (")
        if start == -1:
            raise ValueError("No se pudo parsear el CREATE TABLE")

        prefix = original_sql[: start + 2]  # "CREATE TABLE taller_documento ("
        rest = original_sql[start + 2 :]
        # rest = "col1 type, col2 type, ... );"
        end_paren = rest.rfind(")")
        body = rest[:end_paren]
        suffix = rest[end_paren:]  # ");"

        # Dividir por comas (cuidado con paréntesis internos en CHECK, etc.)
        parts = []
        depth = 0
        current = []
        for ch in body:
            if ch == "(":
                depth += 1
                current.append(ch)
            elif ch == ")":
                depth -= 1
                current.append(ch)
            elif ch == "," and depth == 0:
                parts.append("".join(current).strip())
                current = []
            else:
                current.append(ch)
        if current:
            parts.append("".join(current).strip())

        # Filtrar la parte que define la columna context
        def is_context_def(s):
            t = s.strip()
            # Quitar comillas iniciales del nombre de columna
            if t.startswith('"'):
                end = t.find('"', 1)
                name = t[1:end] if end > 0 else t
            elif t.startswith("'"):
                end = t.find("'", 1)
                name = t[1:end] if end > 0 else t
            else:
                name = t.split()[0] if t.split() else ""
            return name.upper() == "CONTEXT"

        filtered = [p for p in parts if not is_context_def(p)]
        new_body = ", ".join(filtered)
        return prefix + new_body + suffix
