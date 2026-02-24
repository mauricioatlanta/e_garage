# 🚀 Marketplace - Guía de Inicio Rápido

## Instalación Rápida

### 1. Instalar Dependencias

```bash
pip install openpyxl>=3.1.0
```

### 2. Ejecutar Migraciones

```bash
python manage.py migrate marketplace
```

### 3. Crear Casa de Repuestos (Admin)

1. Ir a `/admin/marketplace/casarepuestos/add/`
2. Crear casa de repuestos (ej: "Indra")
3. Agregar teléfono y contacto

### 4. Importar Catálogo (Modo Offline)

```bash
# Formato Excel: part_number | nombre | precio_referencia | disponible
python manage.py import_catalog --casa "Indra" --file "catalogo_indra.xlsx"
```

### 5. Probar Funcionalidad

1. Ir a crear documento
2. Agregar repuesto
3. Escribir part_number (ej: "FIL-001")
4. Ver tooltip con precios de referencia
5. Hacer clic para cargar precio en campo de costo

---

## Configuración WhatsApp (Opcional)

### Variables de Entorno

```bash
# Ultramsg (Chile)
ULTRAMSG_INSTANCE_ID=tu_instance_id
ULTRAMSG_TOKEN=tu_token
ULTRAMSG_WEBHOOK_TOKEN=tu_token_secreto

# Twilio (USA/Escalabilidad)
TWILIO_ACCOUNT_SID=tu_account_sid
TWILIO_AUTH_TOKEN=tu_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

### Configurar Webhooks

En el panel de Ultramsg/Twilio, configurar webhooks:
```
POST https://tu-dominio.com/marketplace/webhooks/whatsapp/cliente/?provider=ultramsg&token=TU_TOKEN_SECRETO
```

---

## Estructura de Excel para Importación

```
| part_number | nombre              | precio_referencia | disponible |
|-------------|---------------------|-------------------|------------|
| FIL-001     | Filtro de Aceite   | 45000            | TRUE       |
| FIL-002     | Filtro de Aire     | 32000            | TRUE       |
| ACE-500     | Aceite Motor 5W30  | 25000            | FALSE      |
```

**Notas**:
- Primera fila puede ser encabezados (usar `--skip-rows 1`)
- Precios pueden tener formato: `45000`, `45000.00`, `$45.000`
- Disponible puede ser: `TRUE/FALSE`, `SI/NO`, `1/0`

---

## Comandos Útiles

```bash
# Importar para empresa específica
python manage.py import_catalog --casa "Indra" --file "catalogo.xlsx" --empresa 1

# Actualizar productos existentes
python manage.py import_catalog --casa "Indra" --file "catalogo.xlsx" --update

# Hoja específica
python manage.py import_catalog --casa "Indra" --file "catalogo.xlsx" --sheet "Hoja1"

# Saltar filas de encabezado
python manage.py import_catalog --casa "Indra" --file "catalogo.xlsx" --skip-rows 2
```

---

## Características Implementadas

✅ Buscador "Fantasma" con tooltip cyberpunk  
✅ Caché de precios (1 hora)  
✅ Modo offline con importación Excel  
✅ Rate limiting WhatsApp (30 min)  
✅ Seguridad webhooks (tokens)  
✅ Feedback visual (animación cian)  
✅ Manejo "No Encontrado" elegante  

---

## Próximo Paso

**¡Ir a mostrarle a la primera casa de repuestos lo que construiste!** 🎯
