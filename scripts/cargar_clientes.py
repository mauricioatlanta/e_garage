from taller.models.clientes import Cliente

# Crear regiones y ciudades ficticias si no existen
region, _ = Region.objects.get_or_create(nombre="Región Metropolitana")
ciudad, _ = Ciudad.objects.get_or_create(nombre="Santiago", region=region)

nombres = [
    ("Mauricio", "Alvarado"),
    ("Daniela", "Torres"),
    ("Fernando", "Zampedri"),
    ("Ana", "García"),
    ("Carlos", "Muñoz"),
    ("Sofía", "Herrera"),
    ("Pablo", "Galmades"),
    ("Camila", "Alfaro"),
    ("Matías", "Ojeda"),
    ("Valentina", "Rivas"),
]

for nombre, apellido in nombres:
    Cliente.objects.create(
        nombre=nombre,
        apellido=apellido,
        telefono="9" + str(80000000 + hash(nombre + apellido) % 10000000),
        direccion=f"Calle {apellido} 123",
        ciudad=ciudad,
        region=region,
        email=f"{nombre.lower()}@tallerpro.cl"
    )

print("✅ 10 clientes creados correctamente.")