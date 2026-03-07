# 📤 Subir Archivos al Servidor

## Opción 1: Usar la IP del servidor

```bash
# Desde PowerShell en Windows
scp taller\models\memoria_seguimiento.py root@159.223.200.106:/srv/egarage/taller/models/
scp taller\models\regimen_fiscal.py root@159.223.200.106:/srv/egarage/taller/models/
```

## Opción 2: Crear los archivos directamente en el servidor

Si `scp` no funciona, puedes crear los archivos directamente en el servidor usando el contenido de los archivos locales.

## Opción 3: Usar WinSCP o FileZilla

Herramientas gráficas que facilitan la transferencia de archivos.
