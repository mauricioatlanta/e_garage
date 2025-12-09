# 📤 INSTRUCCIONES PARA SUBIR EL SCRIPT FALTANTE

## Problema
El script `2_actualizar_ESTRUCTURA_COMPLETA.sh` no está en el servidor.

## Solución: Subir el script con FileZilla

### Paso 1: Conectar con FileZilla
1. Abre **FileZilla**
2. Conecta a:
   - **Host**: `atlantareciclajes.pythonanywhere.com`
   - **Puerto**: `22` (SFTP)
   - **Usuario**: `atlantareciclajes`
   - **Contraseña**: [tu contraseña]

### Paso 2: Navegar a la carpeta de scripts
- **En el servidor**: `/home/atlantareciclajes/scripts_deploy/`

### Paso 3: Subir el script
- **En tu PC**: `E:\projecto\e_garage\scripts_deploy\2_actualizar_ESTRUCTURA_COMPLETA.sh`
- **Arrastra** el archivo al servidor

### Paso 4: Dar permisos de ejecución
En la consola de PythonAnywhere, ejecuta:

```bash
cd /home/atlantareciclajes/scripts_deploy/
chmod +x 2_actualizar_ESTRUCTURA_COMPLETA.sh
```

### Paso 5: Ejecutar el script
```bash
./2_actualizar_ESTRUCTURA_COMPLETA.sh
```

---

## Alternativa: Usar el script que ya existe

Si prefieres no subir el script nuevo, puedes usar el que ya está en el servidor:

```bash
./2_actualizar_FIXED.sh
```

Este script también funciona, pero `2_actualizar_ESTRUCTURA_COMPLETA.sh` es más completo e incluye más carpetas de templates.









