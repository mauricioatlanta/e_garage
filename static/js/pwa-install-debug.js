/**
 * PWA Install Debug Script
 * Script de diagnóstico para verificar por qué no aparece el banner de instalación
 * 
 * USO: Agrega este script temporalmente en base.html para diagnosticar
 * <script src="{% static 'js/pwa-install-debug.js' %}"></script>
 */

(function() {
    'use strict';

    console.log('🔍 ========================================');
    console.log('🔍 DIAGNÓSTICO PWA INSTALL PROMPT');
    console.log('🔍 ========================================');
    console.log('');

    // 1. Verificar Service Worker
    console.log('1️⃣ Verificando Service Worker...');
    if ('serviceWorker' in navigator) {
        console.log('   ✅ Service Worker está soportado');
        
        navigator.serviceWorker.getRegistrations().then(registrations => {
            if (registrations.length > 0) {
                console.log(`   ✅ Service Worker registrado: ${registrations.length} registro(s)`);
                registrations.forEach((reg, index) => {
                    console.log(`      - Registro ${index + 1}: ${reg.scope}`);
                    console.log(`        Estado: ${reg.active ? reg.active.state : 'no activo'}`);
                });
            } else {
                console.log('   ❌ NO hay Service Worker registrado');
                console.log('   💡 Verifica que el service worker se esté cargando correctamente');
            }
        });
    } else {
        console.log('   ❌ Service Worker NO está soportado en este navegador');
    }
    console.log('');

    // 2. Verificar Manifest
    console.log('2️⃣ Verificando Manifest...');
    const manifestLink = document.querySelector('link[rel="manifest"]');
    if (manifestLink) {
        console.log('   ✅ Manifest link encontrado:', manifestLink.href);
        
        fetch(manifestLink.href)
            .then(response => {
                if (response.ok) {
                    console.log('   ✅ Manifest es accesible');
                    return response.json();
                } else {
                    console.log('   ❌ Manifest NO es accesible:', response.status);
                }
            })
            .then(manifest => {
                if (manifest) {
                    console.log('   ✅ Manifest válido:', {
                        name: manifest.name,
                        short_name: manifest.short_name,
                        display: manifest.display,
                        icons: manifest.icons ? manifest.icons.length : 0
                    });
                }
            })
            .catch(error => {
                console.log('   ❌ Error al cargar manifest:', error);
            });
    } else {
        console.log('   ❌ NO se encontró el link al manifest');
    }
    console.log('');

    // 3. Verificar HTTPS
    console.log('3️⃣ Verificando Protocolo...');
    const protocol = window.location.protocol;
    const isHTTPS = protocol === 'https:';
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    
    console.log(`   Protocolo: ${protocol}`);
    console.log(`   Hostname: ${window.location.hostname}`);
    
    if (isHTTPS || isLocalhost) {
        console.log('   ✅ Protocolo válido para PWA (HTTPS o localhost)');
    } else {
        console.log('   ⚠️  Protocolo HTTP - El beforeinstallprompt puede NO funcionar');
        console.log('   💡 Las PWA requieren HTTPS para el prompt de instalación');
        console.log('   💡 Solución: Usa ngrok o similar para crear un túnel HTTPS');
    }
    console.log('');

    // 4. Verificar si ya está instalada
    console.log('4️⃣ Verificando si la app ya está instalada...');
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                         window.navigator.standalone === true ||
                         document.referrer.includes('android-app://');
    
    if (isStandalone) {
        console.log('   ✅ La app YA está instalada (modo standalone)');
        console.log('   💡 Por eso no aparece el banner');
    } else {
        console.log('   ✅ La app NO está instalada - el banner debería aparecer');
    }
    console.log('');

    // 5. Verificar localStorage
    console.log('5️⃣ Verificando localStorage...');
    const dismissedData = localStorage.getItem('egarage_pwa_install_dismissed');
    if (dismissedData) {
        try {
            const data = JSON.parse(dismissedData);
            const dismissedDate = new Date(data.date);
            const daysSinceDismissed = (Date.now() - dismissedDate.getTime()) / (1000 * 60 * 60 * 24);
            console.log('   ⚠️  El banner fue rechazado anteriormente');
            console.log(`   Fecha: ${dismissedDate.toLocaleString()}`);
            console.log(`   Hace: ${daysSinceDismissed.toFixed(1)} días`);
            if (daysSinceDismissed < 7) {
                console.log('   💡 Por eso no aparece el banner (se oculta por 7 días)');
            } else {
                console.log('   ✅ Ya pasaron 7 días, el banner debería aparecer');
            }
        } catch (e) {
            console.log('   ⚠️  Error al leer datos de localStorage:', e);
        }
    } else {
        console.log('   ✅ No hay datos de rechazo - el banner debería aparecer');
    }
    console.log('');

    // 6. Verificar dispositivo
    console.log('6️⃣ Verificando dispositivo...');
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream ||
                  (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    const isAndroid = /Android/.test(navigator.userAgent);
    const isMobile = isIOS || isAndroid || window.innerWidth <= 768;
    
    console.log(`   User Agent: ${navigator.userAgent.substring(0, 50)}...`);
    console.log(`   iOS: ${isIOS ? '✅' : '❌'}`);
    console.log(`   Android: ${isAndroid ? '✅' : '❌'}`);
    console.log(`   Móvil: ${isMobile ? '✅' : '❌'}`);
    console.log(`   Ancho pantalla: ${window.innerWidth}px`);
    console.log('');

    // 7. Verificar script de instalación
    console.log('7️⃣ Verificando script de instalación...');
    if (window.egaragePWA) {
        console.log('   ✅ Script pwa-install-prompt.js está cargado');
        console.log('   Funciones disponibles:', Object.keys(window.egaragePWA));
    } else {
        console.log('   ❌ Script pwa-install-prompt.js NO está cargado');
        console.log('   💡 Verifica que el script se esté incluyendo en base.html');
    }
    console.log('');

    // 8. Escuchar eventos
    console.log('8️⃣ Escuchando eventos PWA...');
    
    let beforeInstallPromptFired = false;
    window.addEventListener('beforeinstallprompt', (e) => {
        beforeInstallPromptFired = true;
        console.log('   ✅ EVENTO beforeinstallprompt DISPARADO!');
        console.log('   💡 Esto significa que la PWA es instalable');
    }, { once: true });

    window.addEventListener('appinstalled', () => {
        console.log('   ✅ EVENTO appinstalled DISPARADO!');
        console.log('   💡 La app fue instalada');
    }, { once: true });

    // Verificar después de 10 segundos
    setTimeout(() => {
        if (!beforeInstallPromptFired && !isStandalone) {
            console.log('   ⚠️  El evento beforeinstallprompt NO se disparó después de 10 segundos');
            console.log('   💡 Posibles razones:');
            console.log('      - Estás en HTTP (requiere HTTPS)');
            console.log('      - El service worker no está registrado');
            console.log('      - El manifest no es válido');
            console.log('      - Ya instalaste la app antes');
        }
    }, 10000);
    console.log('');

    // 9. Resumen final
    console.log('🔍 ========================================');
    console.log('🔍 RESUMEN DEL DIAGNÓSTICO');
    console.log('🔍 ========================================');
    console.log('');
    console.log('Para ver el banner de instalación, verifica:');
    console.log('1. ✅ Service Worker registrado');
    console.log('2. ✅ Manifest accesible y válido');
    console.log('3. ✅ HTTPS (o localhost para desarrollo)');
    console.log('4. ✅ App NO instalada');
    console.log('5. ✅ Banner NO rechazado recientemente');
    console.log('6. ✅ Dispositivo móvil');
    console.log('7. ✅ Script pwa-install-prompt.js cargado');
    console.log('');
    console.log('⏳ Espera 5-7 segundos después de cargar la página');
    console.log('   para que aparezca el banner');
    console.log('');
    console.log('💡 Si estás en HTTP, el beforeinstallprompt puede no funcionar');
    console.log('   Usa ngrok para crear un túnel HTTPS:');
    console.log('   ngrok http 8000');
    console.log('');

})();



