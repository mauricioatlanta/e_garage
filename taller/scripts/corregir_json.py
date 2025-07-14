import json

# Ruta del archivo JSON
json_path = "modelos.json"

try:
    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)  # Intenta cargar el JSON

    # Verifica si los datos están en lista y no tienen IDs duplicados
    seen_ids = set()
    valid_data = []

    for obj in data:
        pk = obj.get("pk")
        if pk in seen_ids:
            print(f"❌ ID duplicado encontrado: {pk}. Se omitirá.")
        else:
            seen_ids.add(pk)
            valid_data.append(obj)

    # Guarda el JSON corregido
    with open("modelos_corregido.json", "w", encoding="utf-8") as file:
        json.dump(valid_data, file, indent=4, ensure_ascii=False)

    print("✅ Archivo corregido guardado como modelos_corregido.json")

except json.JSONDecodeError as e:
    print(f"❌ Error en el JSON: {e}")

except FileNotFoundError:
    print("❌ El archivo modelos.json no existe.")
