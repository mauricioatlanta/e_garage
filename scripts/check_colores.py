from django.db import connection

cursor = connection.cursor()
cursor.execute("PRAGMA table_info(taller_colorvehiculo);")
columns = [row[1] for row in cursor.fetchall()]
print("Columnas actuales:", columns)

if "country" not in columns:
    print("Agregando campo country...")
    cursor.execute("ALTER TABLE taller_colorvehiculo ADD COLUMN country VARCHAR(2) DEFAULT 'CL';")
    print("Campo agregado exitosamente")
else:
    print("Campo country ya existe")

# Verificar colores existentes
from taller.models.extras_vehiculo import ColorVehiculo

colores = ColorVehiculo.objects.all()
print(f"Colores existentes: {colores.count()}")
for color in colores:
    print(f"- {color.nombre}")
