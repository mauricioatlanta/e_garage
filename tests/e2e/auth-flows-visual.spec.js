// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Pruebas E2E para flujos de autenticación de egarage.cl
 * 
 * Este test suite valida:
 * 1. Registro (Sign Up)
 * 2. Inicio de Sesión (Login)
 * 3. Recuperación de Contraseña (Password Reset)
 * 
 * Además, verifica la legibilidad visual de los campos de input
 * (contraste y colores) para detectar problemas de visibilidad.
 */

// Constantes para los tests
const BASE_URL = 'https://egarage.cl';
const TEST_EMAIL = 'test@example.com';
const TEST_PASSWORD = 'TestPassword123!';
const TEST_PASSWORD_CONFIRM = 'TestPassword123!';

/**
 * Función auxiliar para validar el contraste y legibilidad de un campo de input
 * @param {import('@playwright/test').Page} page - Página de Playwright
 * @param {string} selector - Selector CSS del campo
 * @param {string} fieldName - Nombre descriptivo del campo para logging
 * @returns {Promise<Object>} Objeto con información del contraste
 */
async function validateInputContrast(page, selector, fieldName) {
  const input = page.locator(selector).first();
  
  // Esperar a que el campo sea visible
  await expect(input).toBeVisible({ timeout: 10000 });
  
  // Obtener estilos computados
  const styles = await input.evaluate((el) => {
    const computed = window.getComputedStyle(el);
    return {
      color: computed.color,
      backgroundColor: computed.backgroundColor,
      opacity: computed.opacity,
      visibility: computed.visibility,
      borderColor: computed.borderColor,
    };
  });
  
  // Convertir colores RGB a HEX para mejor legibilidad
  const rgbToHex = (rgb) => {
    if (!rgb || rgb === 'transparent' || rgb === 'rgba(0, 0, 0, 0)') {
      return '#TRANSPARENT';
    }
    const match = rgb.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
    if (!match) {
      // Intentar con rgba
      const rgbaMatch = rgb.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)$/);
      if (rgbaMatch) {
        const r = parseInt(rgbaMatch[1], 10);
        const g = parseInt(rgbaMatch[2], 10);
        const b = parseInt(rgbaMatch[3], 10);
        return '#' + [r, g, b].map(x => {
          const hex = x.toString(16);
          return hex.length === 1 ? '0' + hex : hex;
        }).join('');
      }
      return rgb; // Devolver tal cual si no se puede parsear
    }
    return '#' + match.slice(1).map(x => {
      const hex = parseInt(x, 10).toString(16);
      return hex.length === 1 ? '0' + hex : hex;
    }).join('');
  };
  
  const textColorHex = rgbToHex(styles.color);
  const bgColorHex = rgbToHex(styles.backgroundColor);
  const opacity = parseFloat(styles.opacity);
  const visibility = styles.visibility;
  
  // Validar que el campo sea visible
  const isVisible = opacity === 1 && visibility === 'visible';
  
  // Calcular luminancia relativa para determinar si el texto es oscuro o claro
  const getLuminance = (hex) => {
    if (hex === '#TRANSPARENT') return 1; // Asumir blanco si es transparente
    const rgb = hex.match(/^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i);
    if (!rgb) return 0.5; // Valor por defecto
    const r = parseInt(rgb[1], 16) / 255;
    const g = parseInt(rgb[2], 16) / 255;
    const b = parseInt(rgb[3], 16) / 255;
    const [rs, gs, bs] = [r, g, b].map(val => {
      return val <= 0.03928 ? val / 12.92 : Math.pow((val + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  };
  
  const textLuminance = getLuminance(textColorHex);
  const bgLuminance = getLuminance(bgColorHex);
  
  // Calcular ratio de contraste
  const contrastRatio = bgLuminance > textLuminance
    ? (bgLuminance + 0.05) / (textLuminance + 0.05)
    : (textLuminance + 0.05) / (bgLuminance + 0.05);
  
  // Determinar si el texto es oscuro (luminancia baja) y el fondo claro (luminancia alta)
  const isTextDark = textLuminance < 0.5;
  const isBgLight = bgLuminance > 0.5;
  
  // Validar contraste (WCAG AA requiere al menos 4.5:1 para texto normal)
  const hasGoodContrast = contrastRatio >= 4.5;
  
  // Determinar estado
  let status = 'OK';
  let issues = [];
  
  if (!isVisible) {
    status = 'ERROR';
    issues.push('Campo no visible (opacity o visibility)');
  }
  
  if (!hasGoodContrast) {
    status = 'WARNING';
    issues.push(`Contraste bajo: ${contrastRatio.toFixed(2)}:1 (requerido: 4.5:1)`);
  }
  
  if (!isTextDark || !isBgLight) {
    status = 'WARNING';
    issues.push(`Colores inadecuados: Texto ${isTextDark ? 'oscuro' : 'claro'}, Fondo ${isBgLight ? 'claro' : 'oscuro'}`);
  }
  
  // Imprimir información en consola
  console.log('\n' + '='.repeat(60));
  console.log(`📋 VALIDACIÓN VISUAL: ${fieldName}`);
  console.log('='.repeat(60));
  console.log(`📍 Selector: ${selector}`);
  console.log(`🎨 Color Texto: ${textColorHex} (RGB: ${styles.color})`);
  console.log(`🎨 Color Fondo: ${bgColorHex} (RGB: ${styles.backgroundColor})`);
  console.log(`👁️  Opacity: ${opacity}`);
  console.log(`👁️  Visibility: ${visibility}`);
  console.log(`📊 Ratio de Contraste: ${contrastRatio.toFixed(2)}:1`);
  console.log(`✅ Estado: ${status}`);
  if (issues.length > 0) {
    console.log(`⚠️  Problemas detectados:`);
    issues.forEach(issue => console.log(`   - ${issue}`));
  } else {
    console.log(`✅ Todos los checks pasaron correctamente`);
  }
  console.log('='.repeat(60) + '\n');
  
  return {
    fieldName,
    selector,
    textColor: textColorHex,
    backgroundColor: bgColorHex,
    opacity,
    visibility,
    contrastRatio,
    status,
    issues,
    isVisible,
    hasGoodContrast,
  };
}

/**
 * Función auxiliar para escribir texto lentamente en un campo
 * (simula escritura humana para detectar problemas de actualización)
 */
async function typeSlowly(page, selector, text, delay = 100) {
  const input = page.locator(selector).first();
  await input.click();
  await input.clear();
  
  for (const char of text) {
    await input.type(char, { delay });
    // Verificar que el valor se actualizó correctamente
    const currentValue = await input.inputValue();
    if (!currentValue.includes(char)) {
      console.warn(`⚠️  Advertencia: El carácter "${char}" no se reflejó inmediatamente en el campo`);
    }
  }
  
  // Verificación final
  const finalValue = await input.inputValue();
  if (finalValue !== text) {
    throw new Error(`El valor final del campo no coincide. Esperado: "${text}", Obtenido: "${finalValue}"`);
  }
  
  return finalValue;
}

test.describe('Flujos de Autenticación - Validación Visual', () => {
  
  test('1. Registro (Sign Up) - Validación de campos y contraste', async ({ page }) => {
    console.log('\n🚀 Iniciando test: Registro (Sign Up)\n');
    
    // Navegar a la página de registro
    await page.goto(`${BASE_URL}/accounts/signup/`);
    await page.waitForLoadState('networkidle');
    
    // Esperar a que la página cargue completamente
    await page.waitForTimeout(2000);
    
    // Buscar campos de input comunes (adaptarse a la estructura real del sitio)
    const emailSelectors = [
      'input[type="email"]',
      'input[name="email"]',
      'input[id*="email"]',
      '#id_email',
    ];
    
    const passwordSelectors = [
      'input[type="password"]',
      'input[name="password1"]',
      'input[id*="password1"]',
      '#id_password1',
    ];
    
    const passwordConfirmSelectors = [
      'input[name="password2"]',
      'input[id*="password2"]',
      '#id_password2',
    ];
    
    // Validar campo de email
    let emailField = null;
    for (const selector of emailSelectors) {
      const count = await page.locator(selector).count();
      if (count > 0) {
        emailField = selector;
        break;
      }
    }
    
    if (emailField) {
      const emailValidation = await validateInputContrast(page, emailField, 'Email (Registro)');
      expect(emailValidation.isVisible, 'El campo de email debe ser visible').toBe(true);
      
      // Escribir en el campo y verificar que se actualiza
      await typeSlowly(page, emailField, TEST_EMAIL);
      console.log(`✅ Email escrito correctamente: ${TEST_EMAIL}`);
    } else {
      console.warn('⚠️  No se encontró el campo de email en el formulario de registro');
    }
    
    // Validar campo de contraseña
    let passwordField = null;
    for (const selector of passwordSelectors) {
      const count = await page.locator(selector).count();
      if (count > 0) {
        passwordField = selector;
        break;
      }
    }
    
    if (passwordField) {
      const passwordValidation = await validateInputContrast(page, passwordField, 'Contraseña (Registro)');
      expect(passwordValidation.isVisible, 'El campo de contraseña debe ser visible').toBe(true);
      
      // Escribir lentamente y verificar
      await typeSlowly(page, passwordField, TEST_PASSWORD);
      console.log(`✅ Contraseña escrita correctamente (${TEST_PASSWORD.length} caracteres)`);
    } else {
      console.warn('⚠️  No se encontró el campo de contraseña en el formulario de registro');
    }
    
    // Validar campo de confirmación de contraseña
    let passwordConfirmField = null;
    for (const selector of passwordConfirmSelectors) {
      const count = await page.locator(selector).count();
      if (count > 0) {
        passwordConfirmField = selector;
        break;
      }
    }
    
    if (passwordConfirmField) {
      const passwordConfirmValidation = await validateInputContrast(
        page, 
        passwordConfirmField, 
        'Confirmar Contraseña (Registro)'
      );
      expect(passwordConfirmValidation.isVisible, 'El campo de confirmación debe ser visible').toBe(true);
      
      await typeSlowly(page, passwordConfirmField, TEST_PASSWORD_CONFIRM);
      console.log(`✅ Confirmación de contraseña escrita correctamente`);
    } else {
      console.warn('⚠️  No se encontró el campo de confirmación de contraseña');
    }
    
    // Verificar que hay un botón de submit
    const submitButton = page.locator('button[type="submit"], input[type="submit"], button:has-text("Registr"), button:has-text("Sign up"), button:has-text("Crear")').first();
    const submitCount = await submitButton.count();
    if (submitCount > 0) {
      await expect(submitButton).toBeVisible();
      console.log('✅ Botón de registro encontrado y visible');
    }
    
    // Capturar screenshot para revisión manual
    await page.screenshot({ path: `test-results/signup-${Date.now()}.png`, fullPage: true });
    
    console.log('\n✅ Test de Registro completado\n');
  });
  
  test('2. Inicio de Sesión (Login) - Validación de campos y contraste', async ({ page }) => {
    console.log('\n🚀 Iniciando test: Inicio de Sesión (Login)\n');
    
    // Navegar a la página de login
    await page.goto(`${BASE_URL}/accounts/login/`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Buscar campos de login
    const emailSelectors = [
      'input[type="email"]',
      'input[name="login"]',
      'input[name="email"]',
      'input[id*="login"]',
      'input[id*="email"]',
      '#id_login',
    ];
    
    const passwordSelectors = [
      'input[type="password"]',
      'input[name="password"]',
      'input[id*="password"]',
      '#id_password',
    ];
    
    // Validar campo de email/login
    let emailField = null;
    for (const selector of emailSelectors) {
      const count = await page.locator(selector).count();
      if (count > 0) {
        emailField = selector;
        break;
      }
    }
    
    if (emailField) {
      const emailValidation = await validateInputContrast(page, emailField, 'Email/Login');
      expect(emailValidation.isVisible, 'El campo de email/login debe ser visible').toBe(true);
      
      await typeSlowly(page, emailField, TEST_EMAIL);
      console.log(`✅ Email escrito correctamente: ${TEST_EMAIL}`);
    } else {
      console.warn('⚠️  No se encontró el campo de email/login');
    }
    
    // Validar campo de contraseña
    let passwordField = null;
    for (const selector of passwordSelectors) {
      const count = await page.locator(selector).count();
      if (count > 0) {
        passwordField = selector;
        break;
      }
    }
    
    if (passwordField) {
      const passwordValidation = await validateInputContrast(page, passwordField, 'Contraseña (Login)');
      expect(passwordValidation.isVisible, 'El campo de contraseña debe ser visible').toBe(true);
      
      await typeSlowly(page, passwordField, TEST_PASSWORD);
      console.log(`✅ Contraseña escrita correctamente (${TEST_PASSWORD.length} caracteres)`);
    } else {
      console.warn('⚠️  No se encontró el campo de contraseña');
    }
    
    // Verificar botón de submit
    const submitButton = page.locator('button[type="submit"], input[type="submit"], button:has-text("Iniciar"), button:has-text("Login"), button:has-text("Entrar")').first();
    const submitCount = await submitButton.count();
    if (submitCount > 0) {
      await expect(submitButton).toBeVisible();
      console.log('✅ Botón de login encontrado y visible');
    }
    
    // Capturar screenshot
    await page.screenshot({ path: `test-results/login-${Date.now()}.png`, fullPage: true });
    
    console.log('\n✅ Test de Login completado\n');
  });
  
  test('3. Recuperación de Contraseña (Password Reset) - Validación crítica', async ({ page }) => {
    console.log('\n🚀 Iniciando test: Recuperación de Contraseña (PRIORIDAD ALTA)\n');
    
    // Paso 1: Navegar a la página de solicitud de reset
    await page.goto(`${BASE_URL}/accounts/password/reset/`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Buscar campo de email para solicitar reset
    const emailSelectors = [
      'input[type="email"]',
      'input[name="email"]',
      'input[id*="email"]',
      '#id_email',
    ];
    
    let emailField = null;
    for (const selector of emailSelectors) {
      const count = await page.locator(selector).count();
      if (count > 0) {
        emailField = selector;
        break;
      }
    }
    
    if (emailField) {
      const emailValidation = await validateInputContrast(page, emailField, 'Email (Solicitud Reset)');
      expect(emailValidation.isVisible, 'El campo de email debe ser visible').toBe(true);
      
      await typeSlowly(page, emailField, TEST_EMAIL);
      console.log(`✅ Email escrito correctamente: ${TEST_EMAIL}`);
    }
    
    // NOTA: En un entorno real, aquí se necesitaría un token de reset válido
    // Para este test, vamos a simular la navegación a la página de "Nueva Contraseña"
    // usando un formato típico de Django Allauth
    
    console.log('\n📝 Simulando acceso a página de "Nueva Contraseña"...\n');
    
    // Intentar navegar a una URL de reset (aunque no sea válida, para ver la estructura)
    // En producción, esto requeriría un token real del email
    const resetKeyUrl = `${BASE_URL}/accounts/password/reset/key/1234567890-abcdef/`;
    await page.goto(resetKeyUrl);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Buscar campos de nueva contraseña
    const newPasswordSelectors = [
      'input[type="password"]',
      'input[name="password1"]',
      'input[name="password"]',
      'input[id*="password1"]',
      '#id_password1',
    ];
    
    const confirmPasswordSelectors = [
      'input[name="password2"]',
      'input[id*="password2"]',
      '#id_password2',
    ];
    
    // Validar campo de nueva contraseña (CRÍTICO - aquí se reportó el error)
    let newPasswordField = null;
    for (const selector of newPasswordSelectors) {
      const count = await page.locator(selector).count();
      if (count > 0) {
        newPasswordField = selector;
        break;
      }
    }
    
    if (newPasswordField) {
      console.log('\n🔍 VALIDACIÓN CRÍTICA: Campo de Nueva Contraseña\n');
      
      const passwordValidation = await validateInputContrast(
        page, 
        newPasswordField, 
        'Nueva Contraseña (RESET - CRÍTICO)'
      );
      
      expect(passwordValidation.isVisible, 'El campo de nueva contraseña debe ser visible').toBe(true);
      
      // ESCRITURA LENTA Y VERIFICACIÓN DETALLADA (simula el bug reportado)
      console.log('⌨️  Escribiendo contraseña lentamente para detectar problemas de actualización...\n');
      
      const testPassword = 'NuevaPass123!';
      const input = page.locator(newPasswordField).first();
      
      await input.click();
      await input.clear();
      
      // Escribir carácter por carácter y verificar después de cada uno
      for (let i = 0; i < testPassword.length; i++) {
        const char = testPassword[i];
        await input.type(char, { delay: 150 });
        
        // Verificar inmediatamente después de escribir
        await page.waitForTimeout(50);
        const currentValue = await input.inputValue();
        const expectedValue = testPassword.substring(0, i + 1);
        
        if (currentValue !== expectedValue) {
          console.error(`❌ ERROR: Después de escribir "${char}" (posición ${i + 1})`);
          console.error(`   Esperado: "${expectedValue}"`);
          console.error(`   Obtenido: "${currentValue}"`);
          throw new Error(`El valor del campo no se actualizó correctamente en la posición ${i + 1}`);
        }
        
        console.log(`✅ Carácter ${i + 1}/${testPassword.length} ("${char}") - Valor actual: "${currentValue}"`);
      }
      
      // Verificación final
      const finalValue = await input.inputValue();
      if (finalValue !== testPassword) {
        throw new Error(`El valor final no coincide. Esperado: "${testPassword}", Obtenido: "${finalValue}"`);
      }
      
      console.log(`\n✅ Contraseña escrita correctamente: "${finalValue}" (${finalValue.length} caracteres)\n`);
      
      // Verificar contraste nuevamente después de escribir
      const passwordValidationAfter = await validateInputContrast(
        page, 
        newPasswordField, 
        'Nueva Contraseña (Después de escribir)'
      );
      
    } else {
      console.warn('⚠️  No se encontró el campo de nueva contraseña. Puede que el token de reset no sea válido o la página tenga una estructura diferente.');
      console.log('📸 Capturando screenshot de la página actual para análisis...');
    }
    
    // Validar campo de confirmación
    let confirmPasswordField = null;
    for (const selector of confirmPasswordSelectors) {
      const count = await page.locator(selector).count();
      if (count > 0) {
        confirmPasswordField = selector;
        break;
      }
    }
    
    if (confirmPasswordField) {
      const confirmValidation = await validateInputContrast(
        page, 
        confirmPasswordField, 
        'Confirmar Nueva Contraseña (RESET)'
      );
      expect(confirmValidation.isVisible, 'El campo de confirmación debe ser visible').toBe(true);
    }
    
    // Buscar y validar checkbox de "Terms and Conditions" si existe
    const termsSelectors = [
      'input[type="checkbox"][name*="terms"]',
      'input[type="checkbox"][id*="terms"]',
      'input[type="checkbox"]:near-text("terms")',
      'input[type="checkbox"]:near-text("condiciones")',
      'input[type="checkbox"]:near-text("Términos")',
    ];
    
    let termsCheckbox = null;
    for (const selector of termsSelectors) {
      const count = await page.locator(selector).count();
      if (count > 0) {
        termsCheckbox = selector;
        break;
      }
    }
    
    if (termsCheckbox) {
      const checkbox = page.locator(termsCheckbox).first();
      await expect(checkbox).toBeVisible();
      const isEnabled = await checkbox.isEnabled();
      expect(isEnabled, 'El checkbox de términos debe estar habilitado').toBe(true);
      console.log('✅ Checkbox de Terms and Conditions encontrado, visible y cliqueable');
      
      // Intentar hacer click
      await checkbox.click();
      const isChecked = await checkbox.isChecked();
      console.log(`✅ Checkbox clickeado. Estado: ${isChecked ? 'Marcado' : 'Desmarcado'}`);
    } else {
      console.log('ℹ️  No se encontró checkbox de Terms and Conditions (puede no estar presente en esta página)');
    }
    
    // Capturar screenshot
    await page.screenshot({ path: `test-results/password-reset-${Date.now()}.png`, fullPage: true });
    
    console.log('\n✅ Test de Recuperación de Contraseña completado\n');
  });
  
  test('4. Resumen de Validaciones Visuales', async ({ page }) => {
    // Este test recopila información de todos los campos encontrados
    console.log('\n📊 GENERANDO REPORTE DE VALIDACIONES VISUALES\n');
    
    const validations = [];
    
    // Test de registro
    await page.goto(`${BASE_URL}/accounts/signup/`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    const allInputs = await page.locator('input[type="email"], input[type="password"], input[type="text"]').all();
    console.log(`\nEncontrados ${allInputs.length} campos de input en la página de registro`);
    
    for (let i = 0; i < allInputs.length; i++) {
      const input = allInputs[i];
      const tagName = await input.evaluate(el => el.tagName);
      const inputType = await input.getAttribute('type') || 'text';
      const inputName = await input.getAttribute('name') || await input.getAttribute('id') || `input-${i}`;
      
      try {
        const validation = await validateInputContrast(
          page,
          `input:nth-of-type(${i + 1})`,
          `${inputName} (${inputType})`
        );
        validations.push(validation);
      } catch (error) {
        console.warn(`⚠️  No se pudo validar el campo ${inputName}: ${error.message}`);
      }
    }
    
    // Imprimir resumen final
    console.log('\n' + '='.repeat(60));
    console.log('📋 RESUMEN FINAL DE VALIDACIONES');
    console.log('='.repeat(60));
    
    const okCount = validations.filter(v => v.status === 'OK').length;
    const warningCount = validations.filter(v => v.status === 'WARNING').length;
    const errorCount = validations.filter(v => v.status === 'ERROR').length;
    
    console.log(`✅ Campos OK: ${okCount}`);
    console.log(`⚠️  Campos con Warnings: ${warningCount}`);
    console.log(`❌ Campos con Errores: ${errorCount}`);
    console.log('='.repeat(60) + '\n');
    
    // Asegurar que al menos los campos críticos estén visibles
    expect(errorCount, 'No debería haber campos con errores críticos de visibilidad').toBe(0);
  });
});





