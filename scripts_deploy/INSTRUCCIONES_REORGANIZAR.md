# 🔧 SOLUCIÓN RÁPIDA: Reorganizar archivos en el servidor

## Problema
El ZIP se descomprimió pero los archivos están directamente en `egarage_update/` en lugar de en `egarage_update/deploy_atlantareciclajes/`.

## Solución: Ejecutar en la consola de PythonAnywhere

Copia y pega estos comandos en la consola bash:

```bash
cd /home/atlantareciclajes/egarage_update/

# Crear la carpeta deploy_atlantareciclajes
mkdir -p deploy_atlantareciclajes

# Mover archivos y carpetas
[ -d "templates" ] && mv templates deploy_atlantareciclajes/ && echo "✅ templates/ movido"
[ -d "taller" ] && mv taller deploy_atlantareciclajes/ && echo "✅ taller/ movido"
[ -d "gestion_taller" ] && mv gestion_taller deploy_atlantareciclajes/ && echo "✅ gestion_taller/ movido"
[ -d "core" ] && mv core deploy_atlantareciclajes/ && echo "✅ core/ movido"
[ -d "ubicacion" ] && mv ubicacion deploy_atlantareciclajes/ && echo "✅ ubicacion/ movido"
[ -f "manage.py" ] && mv manage.py deploy_atlantareciclajes/ && echo "✅ manage.py movido"
[ -f "INFO_ACTUALIZACION.txt" ] && mv INFO_ACTUALIZACION.txt deploy_atlantareciclajes/ && echo "✅ INFO_ACTUALIZACION.txt movido"

# Verificar estructura
ls -la deploy_atlantareciclajes/
```

## Después de reorganizar

Una vez reorganizados los archivos, ejecuta el script de actualización:

```bash
cd /home/atlantareciclajes/scripts_deploy/
./2_actualizar_FIXED.sh
```

---

## Alternativa: Usar el script automatizado

Si prefieres, puedes subir el script `SOLUCION_RAPIDA_SERVIDOR.sh` al servidor y ejecutarlo:

1. **Con FileZilla**: Sube `scripts_deploy/SOLUCION_RAPIDA_SERVIDOR.sh` a `/home/atlantareciclajes/scripts_deploy/`

2. **En la consola**:
```bash
cd /home/atlantareciclajes/scripts_deploy/
chmod +x SOLUCION_RAPIDA_SERVIDOR.sh
./SOLUCION_RAPIDA_SERVIDOR.sh
```









