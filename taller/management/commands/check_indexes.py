from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Verifica y valida la presencia de índices esperados en la base de datos"

    def add_arguments(self, parser):
        parser.add_argument(
            '--fail-on-missing',
            action='store_true',
            help='Falla con SystemExit(1) si falta algún índice esperado',
        )

    def handle(self, *args, **options):
        fail_on_missing = options.get('fail_on_missing', False)
        
        self.stdout.write("🔍 Verificando índices en base de datos...")
        self.stdout.write("=" * 50)
        
        # Índices esperados por tabla
        expected_indexes = {
            "taller_documento": [
                ("empresa", "fecha_emision"),
                ("fecha_emision",),
                ("tecnico_responsable", "fecha_emision"),
                ("estado", "fecha_emision"),
                ("tipo", "fecha_emision"),
                ("tecnico_responsable",),
                ("cliente", "fecha_emision"),
            ],
            "taller_lineaservicio": [
                ("documento", "servicio"),
            ],
            "taller_linearepuesto": [
                ("documento", "repuesto"),
                ("codigo",),
            ],
            "taller_lineaotroservicio": [
                ("documento", "servicio"),
                ("empresa_externa",),
            ],
        }
        
        missing_indexes = []
        total_expected = 0
        total_found = 0
        
        for table, expected in expected_indexes.items():
            self.stdout.write(f"\n📊 {table}:")
            
            # Obtener índices existentes
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"PRAGMA index_list('{table}')")
                    existing_indexes = cursor.fetchall()
                    
                    # Extraer nombres de índices
                    existing_names = [row[1] for row in existing_indexes if row[1]]
                    
                    self.stdout.write(f"   Índices existentes: {len(existing_indexes)}")
                    for idx in existing_indexes:
                        self.stdout.write(f"   - {idx[1]} ({'UNIQUE' if idx[2] else 'INDEX'})")
                    
                    # Verificar índices esperados
                    for expected_fields in expected:
                        total_expected += 1
                        
                        # Buscar índice que contenga estos campos
                        found = False
                        for idx_name in existing_names:
                            if self._index_contains_fields(cursor, idx_name, expected_fields):
                                found = True
                                total_found += 1
                                break
                        
                        if found:
                            self.stdout.write(
                                self.style.SUCCESS(f"   ✅ {expected_fields}")
                            )
                        else:
                            self.stdout.write(
                                self.style.ERROR(f"   ❌ {expected_fields} - FALTANTE")
                            )
                            missing_indexes.append((table, expected_fields))
                            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Error verificando {table}: {e}")
                )
                missing_indexes.append((table, f"ERROR: {e}"))
        
        # Resumen
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("📊 RESUMEN DE ÍNDICES")
        self.stdout.write("=" * 50)
        
        self.stdout.write(f"Índices esperados: {total_expected}")
        self.stdout.write(f"Índices encontrados: {total_found}")
        self.stdout.write(f"Índices faltantes: {len(missing_indexes)}")
        
        if missing_indexes:
            self.stdout.write("\n❌ Índices faltantes:")
            for table, fields in missing_indexes:
                self.stdout.write(f"   - {table}: {fields}")
            
            if fail_on_missing:
                self.stdout.write(
                    self.style.ERROR("\n💥 FALLO: Índices faltantes detectados")
                )
                raise SystemExit(1)
            else:
                self.stdout.write(
                    self.style.WARNING("\n⚠️  ADVERTENCIA: Índices faltantes detectados")
                )
        else:
            self.stdout.write(
                self.style.SUCCESS("\n✅ TODOS LOS ÍNDICES ESTÁN PRESENTES")
            )
        
        self.stdout.write("\n💡 Para crear índices faltantes:")
        self.stdout.write("   python manage.py makemigrations taller")
        self.stdout.write("   python manage.py migrate")
        
        return len(missing_indexes) == 0
    
    def _index_contains_fields(self, cursor, index_name, expected_fields):
        """Verifica si un índice contiene los campos esperados."""
        try:
            # Obtener información del índice
            cursor.execute(f"PRAGMA index_info('{index_name}')")
            index_info = cursor.fetchall()
            
            # Extraer nombres de campos del índice
            index_fields = [row[2] for row in index_info]
            
            # Verificar si todos los campos esperados están en el índice
            return all(field in index_fields for field in expected_fields)
            
        except Exception:
            return False
