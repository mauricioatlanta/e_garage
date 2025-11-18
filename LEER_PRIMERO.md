# ⚠️ INSTRUCCIONES URGENTES PARA EL SERVIDOR

## Problema
El archivo `taller/documentos/views.py` en el servidor tiene marcadores de conflicto de merge en la línea 336 que impiden que el servidor funcione.

## Solución Rápida

### Paso 1: Conéctate al servidor
```bash
ssh atlantareciclajes@ssh.pythonanywhere.com
```

### Paso 2: Ejecuta este comando COMPLETO (copia y pega todo):
```bash
cd /home/atlantareciclajes/apps/egarage/current && sed -i '/^<<<<<<</d; /^=======$/d; /^>>>>>>>/d' taller/documentos/views.py && python3 -m py_compile taller/documentos/views.py && touch /var/www/www_egarage_cl_wsgi.py && echo "✅ LISTO"
```

### Paso 3: Verifica que funcionó
Visita: https://www.egarage.cl/

---

## Si el comando anterior no funciona

### Opción A: Subir y ejecutar el script
1. En tu máquina local:
   ```bash
   scp fix_servidor.sh atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/
   ```

2. En el servidor:
   ```bash
   chmod +x ~/fix_servidor.sh
   cd /home/atlantareciclajes/apps/egarage/current
   ~/fix_servidor.sh
   ```

### Opción B: Restaurar desde Git
```bash
cd /home/atlantareciclajes/apps/egarage/current
git fetch origin main
git checkout origin/main -- taller/documentos/views.py
python3 -m py_compile taller/documentos/views.py
touch /var/www/www_egarage_cl_wsgi.py
```

---

## Nota Importante
El archivo local está correcto (sin conflictos). El problema está solo en el servidor. Cualquiera de las soluciones anteriores debería funcionar.

