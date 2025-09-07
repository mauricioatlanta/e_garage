// INSTRUCCIONES PARA LIMPIAR CACHE DEL NAVEGADOR

/* =====================================================
   MÉTODOS PARA FORZAR ACTUALIZACIÓN DEL NAVEGADOR
   ===================================================== */

// MÉTODO 1: Limpiar cache del navegador
// 1. Abre las herramientas de desarrollador (F12)
// 2. Haz clic derecho en el botón de recargar
// 3. Selecciona "Vaciar caché y recargar forzosamente" (Empty Cache and Hard Reload)

// MÉTODO 2: Usar Ctrl+F5 o Ctrl+Shift+R
// - Esto fuerza una recarga completa ignorando el cache

// MÉTODO 3: Abrir en ventana incógnita/privada
// - Chrome: Ctrl+Shift+N
// - Firefox: Ctrl+Shift+P
// - Edge: Ctrl+Shift+N

// MÉTODO 4: Limpiar manualmente el cache
// 1. Chrome: Configuración → Privacidad y seguridad → Borrar datos de navegación
// 2. Firefox: Configuración → Privacidad y seguridad → Limpiar datos
// 3. Edge: Configuración → Privacidad, búsqueda y servicios → Borrar datos de navegación

// MÉTODO 5: Añadir parámetros únicos a la URL
// Ejemplo: http://127.0.0.1:8000/us/documentos/form/?v=123456

/* =====================================================
   VERIFICACIÓN DE QUE LOS CAMBIOS SE APLICARON
   ===================================================== */

// SI VES ESTOS ELEMENTOS, LOS CAMBIOS SE APLICARON:
// ✅ Banner verde en la parte superior: "CSS FUTURISTA CARGADO"
// ✅ Botón "🧪 Debug Clientes" en esquina superior derecha
// ✅ Botón "⚙️ Settings" en el header
// ✅ En la consola (F12): "VERSIÓN ACTUALIZADA" y "JAVASCRIPT FUTURISTA CARGADO"

/* =====================================================
   TROUBLESHOOTING ADICIONAL
   ===================================================== */

// Si AÚN no se ven los cambios:
// 1. Verificar que el servidor Django esté ejecutándose
// 2. Comprobar que no hay errores en la consola del navegador
// 3. Verificar que los archivos estáticos se están sirviendo correctamente
// 4. Intentar con un navegador diferente
// 5. Verificar que no hay un proxy o CDN cachéando los archivos
