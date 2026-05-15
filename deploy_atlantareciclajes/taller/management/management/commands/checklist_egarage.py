from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.urls import get_resolver


class Command(BaseCommand):
    help = "Checklist eGarage completo"

    def handle(self, *args, **options):
        self.stdout.write("🔍 Ejecutando checklist eGarage completo...")
        self.stdout.write("=" * 50)

        resultados = []

        # 1. makemigrations / migrate
        self.stdout.write("1. ✅ makemigrations / migrate")
        try:
            call_command("makemigrations", check=True)
            call_command("migrate", check=True)
            self.stdout.write("   ✅ Migraciones OK")
            resultados.append(True)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Error en migraciones: {e}"))
            resultados.append(False)

        # 2. Árbol de URLs único por país/idioma
        self.stdout.write("\n2. ✅ Árbol de URLs único por país/idioma")
        try:
            resolver = get_resolver()
            names = [k for k in resolver.reverse_dict.keys() if isinstance(k, str)]

            # Verificar que no hay duplicados
            if len(names) == len(set(names)):
                self.stdout.write("   ✅ No hay duplicados en URLs")
                resultados.append(True)
            else:
                self.stdout.write(self.style.ERROR("   ❌ Hay duplicados en URLs"))
                resultados.append(False)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Error verificando URLs: {e}"))
            resultados.append(False)

        # 3. Verificar URLs específicas
        self.stdout.write("\n3. 🔎 Verificar URLs específicas")
        try:
            us_en_names = [name for name in names if "taller_us_en" in name]
            cl_es_names = [name for name in names if "taller_cl_es" in name]

            self.stdout.write(f"   ✅ {len(us_en_names)} URLs para US/EN")
            self.stdout.write(f"   ✅ {len(cl_es_names)} URLs para CL/ES")
            resultados.append(True)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Error verificando URLs específicas: {e}"))
            resultados.append(False)

        # 4. Test anti-duplicados de nombres de URL
        self.stdout.write("\n4. 🧪 Test anti-duplicados de nombres de URL")
        try:
            # Importar y ejecutar el test
            from tests.unit.test_urls_unique_names import test_unique_url_names

            test_unique_url_names()
            self.stdout.write("   ✅ Test anti-duplicados OK")
            resultados.append(True)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Error en test anti-duplicados: {e}"))
            resultados.append(False)

        # 5. KPIs usando solo fecha_emision
        self.stdout.write("\n5. 📊 KPIs usando solo fecha_emision")
        try:
            call_command("kpi_sanity_check")
            self.stdout.write("   ✅ KPIs OK")
            resultados.append(True)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Error verificando KPIs: {e}"))
            resultados.append(False)

        # 6. python manage.py check --deploy
        self.stdout.write("\n6. 🛡️ python manage.py check --deploy")
        try:
            call_command("check", "--deploy")
            self.stdout.write("   ✅ Check deploy OK")
            resultados.append(True)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Error en check deploy: {e}"))
            resultados.append(False)

        # Resumen final
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("📊 RESUMEN DEL CHECKLIST")
        self.stdout.write("=" * 50)

        total_checks = len(resultados)
        checks_ok = sum(resultados)

        self.stdout.write(f"Checks ejecutados: {checks_ok}/{total_checks}")

        if checks_ok == total_checks:
            self.stdout.write(self.style.SUCCESS("\n🎉 ¡TODOS LOS CHECKS PASARON!"))
            self.stdout.write(self.style.SUCCESS("✅ El sistema está listo para producción"))
        else:
            self.stdout.write(
                self.style.WARNING(f"\n⚠️  {total_checks - checks_ok} checks fallaron")
            )
            self.stdout.write(self.style.ERROR("❌ Revisar los errores antes de continuar"))

        return checks_ok == total_checks
