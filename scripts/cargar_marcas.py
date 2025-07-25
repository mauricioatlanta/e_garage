import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')
django.setup()

from taller.models.marca import Marca

# Lista de marcas a poblar (extraídas del diccionario de modelos)
marcas = [
    "Acura", "Alfa Romeo", "AMC", "Asia Motors", "Audi", "Austin", "BAIC", "Bentley", "BMW", "Brilliance", "Bugatti", "Buick", "BYD", "Cadillac", "Changan", "Chery", "Chevrolet", "Chrysler", "Cupra", "Dacia", "Daewoo", "Daihatsu", "Datsun", "Dodge", "Dongfeng", "Effa", "FAW", "Ferrari", "Fiat", "Foton", "Geely", "Genesis", "GMC", "Great Wall", "Haima", "Haval", "Honda", "Hyundai", "Infiniti", "Isuzu", "Iveco", "JAC", "Jaguar", "Jeep", "Jetour", "JMC", "Jonway", "Kia", "King Long", "Koenigsegg", "Lada", "Lamborghini", "Lancia", "Land Rover", "Lexus", "Lifan", "Lincoln", "Lotus", "Mahindra", "Maserati", "Mazda", "McLaren", "Mercedes-Benz", "MG", "Mini", "Mitsubishi", "Morris", "Nissan", "Opel", "Peugeot", "Polestar", "Pontiac", "Porsche", "Proton", "RAM", "Renault", "Rolls-Royce", "Rover", "SAIC", "Seat", "Scania", "Skoda", "Smart", "SsangYong", "Subaru", "Suzuki", "Tata", "Tesla", "Toyota", "Volkswagen", "Volvo", "Wuling"
]

creadas = 0
for nombre in marcas:
    obj, created = Marca.objects.get_or_create(nombre=nombre)
    if created:
        print(f"✅ Marca creada: {nombre}")
        creadas += 1
    else:
        print(f"ℹ️ Marca ya existe: {nombre}")
print(f"Total nuevas marcas creadas: {creadas}")
