# 🧪 EJECUTAR TESTS DE REGISTRO Y PASSWORD RESET

Este documento explica cómo ejecutar los tests creados para verificar el funcionamiento del registro y recuperación de contraseña.

## 📋 Tests Creados

### 1. **Test Unitario**: `tests/unit/test_registration_and_password_reset.py`

Este archivo contiene tests para:
- ✅ Proceso completo de registro de usuarios
- ✅ Creación de empresa y suscripción
- ✅ Envío de emails de bienvenida
- ✅ Configuración de emails (subscription@egarage.cl)
- ✅ Proceso de recuperación de contraseña
- ✅ Validación de configuración de emails

## 🚀 Ejecutar Tests

### Opción 1: Ejecutar todos los tests del archivo

```bash
pytest tests/unit/test_registration_and_password_reset.py -v
```

### Opción 2: Ejecutar un test específico

```bash
# Test de registro completo
pytest tests/unit/test_registration_and_password_reset.py::TestRegistrationProcess::test_registration_service_creates_user_and_empresa -v

# Test de configuración de email
pytest tests/unit/test_registration_and_password_reset.py::TestEmailConfiguration::test_email_configuration_uses_subscription_egarage -v

# Test de password reset
pytest tests/unit/test_registration_and_password_reset.py::TestPasswordResetProcess -v
```

### Opción 3: Ejecutar con coverage

```bash
pytest tests/unit/test_registration_and_password_reset.py --cov=taller.reportes.services.registration_service --cov-report=html -v
```

## 📊 Tests Incluidos

### **TestRegistrationProcess**
- `test_registration_service_creates_user_and_empresa`: Verifica creación completa de usuario y empresa
- `test_registration_prevents_duplicate_email`: Verifica que no se puede registrar con email duplicado
- `test_registration_creates_trial_subscription`: Verifica creación de suscripción trial de 30 días
- `test_registration_sends_welcome_email`: Verifica envío de email de bienvenida
- `test_registration_uses_correct_country_config`: Verifica configuración según país

### **TestPasswordResetProcess**
- `test_password_reset_request_creates_token`: Verifica solicitud de reset
- `test_password_reset_sends_email`: Verifica envío de email de reset
- `test_password_reset_flow_creates_user_first`: Verifica flujo básico
- `test_password_reset_urls_exist`: Verifica que las URLs están configuradas
- `test_password_reset_email_configuration`: Verifica configuración de email

### **TestEmailConfiguration**
- `test_email_configuration_uses_subscription_egarage`: Verifica que se usa subscription@egarage.cl
- `test_support_email_not_configured`: Verifica que support@egarage.cl NO está configurado

### **TestRegistrationIntegration**
- `test_full_registration_flow`: Test de integración completo

## ⚠️ Notas Importantes

1. **Base de datos de prueba**: Los tests usan `@pytest.mark.django_db` para crear una base de datos temporal
2. **Mock de emails**: Algunos tests usan `@patch` para evitar enviar emails reales durante las pruebas
3. **Configuración**: Los tests usan la configuración de `gestion_taller.settings`

## 🔍 Verificar Resultados

Después de ejecutar los tests, deberías ver:

```
✅ PASSED - Todos los tests pasan
❌ FAILED - Algunos tests fallan (revisar mensajes de error)
⚠️ SKIPPED - Algunos tests fueron omitidos (común si falta configuración)
```

## 📝 Troubleshooting

### Error: "No module named 'taller'"
- Verifica que estás en el directorio raíz del proyecto
- Verifica que el entorno virtual está activado

### Error: "Database access not allowed"
- Asegúrate de usar `@pytest.mark.django_db` en los tests
- Verifica que `pytest-django` está instalado: `pip install pytest-django`

### Error: "Settings not configured"
- Verifica que `DJANGO_SETTINGS_MODULE` está configurado correctamente
- Revisa `pytest.ini` para la configuración

## 🔄 Próximos Pasos

Después de ejecutar los tests:

1. ✅ Revisar cualquier test que falle
2. ✅ Verificar que todos los procesos funcionan correctamente
3. ✅ Corregir cualquier inconsistencia encontrada
4. ✅ Actualizar documentación si es necesario





