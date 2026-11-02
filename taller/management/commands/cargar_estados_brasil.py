"""
Comando para cargar estados y ciudades principales de Brasil
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from taller.models.ubicacion import Ciudad, Estado


class Command(BaseCommand):
    help = "Carga los 27 estados de Brasil y ciudades principales en la base de datos"

    def handle(self, *args, **options):
        self.stdout.write("[BR] Cargando estados de Brasil...")

        # 27 estados de Brasil con ICMS promedio
        estados_brasil = [
            {"sigla": "AC", "nome": "Acre", "codigo_ibge": "12", "icms": 19.00},
            {"sigla": "AL", "nome": "Alagoas", "codigo_ibge": "27", "icms": 18.00},
            {"sigla": "AP", "nome": "Amapá", "codigo_ibge": "16", "icms": 18.00},
            {"sigla": "AM", "nome": "Amazonas", "codigo_ibge": "13", "icms": 18.00},
            {"sigla": "BA", "nome": "Bahia", "codigo_ibge": "29", "icms": 18.00},
            {"sigla": "CE", "nome": "Ceará", "codigo_ibge": "23", "icms": 18.00},
            {"sigla": "DF", "nome": "Distrito Federal", "codigo_ibge": "53", "icms": 18.00},
            {"sigla": "ES", "nome": "Espírito Santo", "codigo_ibge": "32", "icms": 17.00},
            {"sigla": "GO", "nome": "Goiás", "codigo_ibge": "52", "icms": 17.00},
            {"sigla": "MA", "nome": "Maranhão", "codigo_ibge": "21", "icms": 18.00},
            {"sigla": "MT", "nome": "Mato Grosso", "codigo_ibge": "51", "icms": 17.00},
            {"sigla": "MS", "nome": "Mato Grosso do Sul", "codigo_ibge": "50", "icms": 17.00},
            {"sigla": "MG", "nome": "Minas Gerais", "codigo_ibge": "31", "icms": 18.00},
            {"sigla": "PA", "nome": "Pará", "codigo_ibge": "15", "icms": 17.00},
            {"sigla": "PB", "nome": "Paraíba", "codigo_ibge": "25", "icms": 18.00},
            {"sigla": "PR", "nome": "Paraná", "codigo_ibge": "41", "icms": 18.00},
            {"sigla": "PE", "nome": "Pernambuco", "codigo_ibge": "26", "icms": 18.00},
            {"sigla": "PI", "nome": "Piauí", "codigo_ibge": "22", "icms": 18.00},
            {"sigla": "RJ", "nome": "Rio de Janeiro", "codigo_ibge": "33", "icms": 20.00},
            {"sigla": "RN", "nome": "Rio Grande do Norte", "codigo_ibge": "24", "icms": 18.00},
            {"sigla": "RS", "nome": "Rio Grande do Sul", "codigo_ibge": "43", "icms": 18.00},
            {"sigla": "RO", "nome": "Rondônia", "codigo_ibge": "11", "icms": 17.50},
            {"sigla": "RR", "nome": "Roraima", "codigo_ibge": "14", "icms": 17.00},
            {"sigla": "SC", "nome": "Santa Catarina", "codigo_ibge": "42", "icms": 17.00},
            {"sigla": "SP", "nome": "São Paulo", "codigo_ibge": "35", "icms": 18.00},
            {"sigla": "SE", "nome": "Sergipe", "codigo_ibge": "28", "icms": 18.00},
            {"sigla": "TO", "nome": "Tocantins", "codigo_ibge": "17", "icms": 18.00},
        ]

        estados_creados = 0
        for estado_data in estados_brasil:
            estado, created = Estado.objects.get_or_create(
                codigo=estado_data["sigla"],
                pais="BR",
                defaults={
                    "nombre": estado_data["nome"],
                    "nome": estado_data["nome"],
                    "sigla": estado_data["sigla"],
                    "codigo_ibge": estado_data["codigo_ibge"],
                    "sales_tax": Decimal(str(estado_data["icms"])),
                    "timezone": "America/Sao_Paulo",  # Por defecto
                },
            )

            if created:
                estados_creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  [OK] {estado_data['nome']} ({estado_data['sigla']})")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"  [EXISTE] {estado_data['nome']} ({estado_data['sigla']}) ya existe"
                    )
                )

        self.stdout.write("")
        self.stdout.write(f"Estados creados: {estados_creados}/{len(estados_brasil)}")

        # Ciudades principales de Brasil
        self.stdout.write("")
        self.stdout.write("[CIUDADES] Cargando ciudades principales de Brasil...")

        ciudades_brasil = [
            # São Paulo
            {"nome": "São Paulo", "estado": "SP", "poblacion": 12300000, "es_capital": True},
            {"nome": "Campinas", "estado": "SP", "poblacion": 1200000, "es_capital": False},
            {"nome": "Santos", "estado": "SP", "poblacion": 433000, "es_capital": False},
            {"nome": "Ribeirão Preto", "estado": "SP", "poblacion": 700000, "es_capital": False},
            # Rio de Janeiro
            {"nome": "Rio de Janeiro", "estado": "RJ", "poblacion": 6700000, "es_capital": True},
            {"nome": "Niterói", "estado": "RJ", "poblacion": 515000, "es_capital": False},
            # Minas Gerais
            {"nome": "Belo Horizonte", "estado": "MG", "poblacion": 2500000, "es_capital": True},
            {"nome": "Uberlândia", "estado": "MG", "poblacion": 700000, "es_capital": False},
            # Rio Grande do Sul
            {"nome": "Porto Alegre", "estado": "RS", "poblacion": 1490000, "es_capital": True},
            {"nome": "Caxias do Sul", "estado": "RS", "poblacion": 517000, "es_capital": False},
            # Bahia
            {"nome": "Salvador", "estado": "BA", "poblacion": 2900000, "es_capital": True},
            # Paraná
            {"nome": "Curitiba", "estado": "PR", "poblacion": 1950000, "es_capital": True},
            {"nome": "Londrina", "estado": "PR", "poblacion": 575000, "es_capital": False},
            # Pernambuco
            {"nome": "Recife", "estado": "PE", "poblacion": 1650000, "es_capital": True},
            # Ceará
            {"nome": "Fortaleza", "estado": "CE", "poblacion": 2700000, "es_capital": True},
            # Santa Catarina
            {"nome": "Florianópolis", "estado": "SC", "poblacion": 515000, "es_capital": True},
            # Distrito Federal
            {"nome": "Brasília", "estado": "DF", "poblacion": 3000000, "es_capital": True},
            # Goiás
            {"nome": "Goiânia", "estado": "GO", "poblacion": 1500000, "es_capital": True},
            # Espírito Santo
            {"nome": "Vitória", "estado": "ES", "poblacion": 365000, "es_capital": True},
            # Amazonas
            {"nome": "Manaus", "estado": "AM", "poblacion": 2200000, "es_capital": True},
            # Pará
            {"nome": "Belém", "estado": "PA", "poblacion": 1500000, "es_capital": True},
            # Maranhão
            {"nome": "São Luís", "estado": "MA", "poblacion": 1100000, "es_capital": True},
        ]

        ciudades_creadas = 0
        for ciudad_data in ciudades_brasil:
            try:
                estado = Estado.objects.get(codigo=ciudad_data["estado"], pais="BR")
                ciudad, created = Ciudad.objects.get_or_create(
                    nombre=ciudad_data["nome"],
                    estado=estado,
                    defaults={
                        "nome": ciudad_data["nome"],
                        "poblacion": ciudad_data["poblacion"],
                        "es_capital": ciudad_data["es_capital"],
                        "sales_tax_local": (
                            Decimal("5.00") if not ciudad_data["es_capital"] else Decimal("5.00")
                        ),  # ISS promedio 5%
                    },
                )

                if created:
                    ciudades_creadas += 1
                    capital = "[CAPITAL]" if ciudad_data["es_capital"] else "[CIUDAD] "
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  {capital} {ciudad_data['nome']}, {ciudad_data['estado']}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  [EXISTE] {ciudad_data['nome']}, {ciudad_data['estado']} ya existe"
                        )
                    )
            except Estado.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"  [ERROR] Estado {ciudad_data['estado']} no encontrado para {ciudad_data['nome']}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(f"Ciudades creadas: {ciudades_creadas}/{len(ciudades_brasil)}")
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("[BR] Estados y ciudades de Brasil cargados exitosamente!")
        )
