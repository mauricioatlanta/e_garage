import sqlite3

try:
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF")

    # Buscar todas las tablas que empiezan con taller_
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'taller_%'")
    tablas = cursor.fetchall()

    for tabla in tablas:
        nombre = tabla[0]
        print(f"Limpiando tabla: {nombre}...")
        cursor.execute(f"DELETE FROM {nombre}")

    cursor.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    conn.close()
    print("\n[OK] Todas las tablas de la app 'taller' han sido vaciadas.")
except Exception as e:
    print(f"[ERROR]: {e}")
