/**
 * PWA Install Prompt Handler
 * Maneja la instalación de eGarage como PWA en Android e iOS
 * 
 * Funcionalidades:
 * - Detecta beforeinstallprompt en Android/Chrome
 * - Muestra instrucciones personalizadas para iOS
 * - Banner de instalación con diseño moderno
 * - Persistencia de preferencias del usuario
 */

(function() {
    'use strict';

    // Configuración
    const CONFIG = {
        // Clave para localStorage
        STORAGE_KEY: 'egarage_pwa_install_dismissed',
        STORAGE_KEY_INSTALLED: 'egarage_pwa_installed',
        // Días antes de volver a mostrar el prompt (si fue rechazado)
        RE_SHOW_AFTER_DAYS: 7,
        // Tiempo mínimo antes de mostrar el prompt (segundos)
        MIN_TIME_BEFORE_SHOW: 5,
        // Solo mostrar en dispositivos móviles
        MOBILE_ONLY: true,
        // Mostrar notificación en desktop
        SHOW_DESKTOP_NOTIFICATION: true,
        // Verificar instalación iOS cada X segundos
        IOS_INSTALL_CHECK_INTERVAL: 2000
    };

    // Variables globales
    let deferredPrompt = null;
    let installBanner = null;
    let iosBanner = null;
    let desktopNotification = null;
    let isStandalone = false;
    let iosInstallCheckInterval = null;
    let wasStandaloneBefore = false;

    /**
     * Detectar si la app ya está instalada (modo standalone)
     */
    function isAppInstalled() {
        // Verificar display-mode standalone
        if (window.matchMedia('(display-mode: standalone)').matches) {
            return true;
        }
        
        // Verificar si está en modo standalone en iOS
        if (window.navigator.standalone === true) {
            return true;
        }
        
        // Verificar referrer en Android
        if (document.referrer.includes('android-app://')) {
            return true;
        }
        
        return false;
    }

    /**
     * Detectar si es iOS
     */
    function isIOS() {
        return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream ||
               (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1) ||
               /iPhone/.test(navigator.userAgent);
    }

    /**
     * Detectar si es Android
     */
    function isAndroid() {
        return /Android/.test(navigator.userAgent);
    }

    /**
     * Detectar si es dispositivo móvil
     */
    function isMobile() {
        return isIOS() || isAndroid() || 
               /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               window.innerWidth <= 768;
    }

    /**
     * Verificar si el prompt fue rechazado recientemente
     */
    function wasDismissedRecently() {
        const dismissedData = localStorage.getItem(CONFIG.STORAGE_KEY);
        if (!dismissedData) {
            return false;
        }

        try {
            const data = JSON.parse(dismissedData);
            const dismissedDate = new Date(data.date);
            const daysSinceDismissed = (Date.now() - dismissedDate.getTime()) / (1000 * 60 * 60 * 24);
            
            return daysSinceDismissed < CONFIG.RE_SHOW_AFTER_DAYS;
        } catch (e) {
            console.warn('[PWA Install] Error al leer datos de localStorage:', e);
            return false;
        }
    }

    /**
     * Marcar el prompt como rechazado
     */
    function markAsDismissed() {
        const data = {
            date: new Date().toISOString(),
            platform: isIOS() ? 'ios' : isAndroid() ? 'android' : 'other'
        };
        localStorage.setItem(CONFIG.STORAGE_KEY, JSON.stringify(data));
    }

    /**
     * Crear banner de instalación para Android
     */
    function createAndroidBanner() {
        if (document.getElementById('pwa-install-banner')) {
            return document.getElementById('pwa-install-banner');
        }

        const banner = document.createElement('div');
        banner.id = 'pwa-install-banner';
        banner.className = 'pwa-install-banner pwa-install-banner-android';
        banner.innerHTML = `
            <div class="pwa-install-content">
                <div class="pwa-install-icon">
                    <i class="fas fa-download"></i>
                </div>
                <div class="pwa-install-text">
                    <h3>Instalar eGarage</h3>
                    <p>Agrega eGarage a tu pantalla de inicio para acceso rápido</p>
                </div>
                <div class="pwa-install-actions">
                    <button id="pwa-install-button" class="pwa-install-btn pwa-install-btn-primary">
                        <i class="fas fa-plus-circle"></i> Instalar
                    </button>
                    <button id="pwa-install-dismiss" class="pwa-install-btn pwa-install-btn-secondary">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(banner);
        return banner;
    }

    /**
     * Crear banner informativo para Android (cuando no hay beforeinstallprompt)
     */
    function showAndroidInfoBanner() {
        if (document.getElementById('pwa-install-banner-info')) {
            return;
        }

        const banner = document.createElement('div');
        banner.id = 'pwa-install-banner-info';
        banner.className = 'pwa-install-banner pwa-install-banner-android';
        banner.innerHTML = `
            <div class="pwa-install-content">
                <div class="pwa-install-icon">
                    <i class="fas fa-mobile-alt"></i>
                </div>
                <div class="pwa-install-text">
                    <h3>Instalar eGarage</h3>
                    <p>Para instalar eGarage en Android:</p>
                    <ol class="pwa-install-steps">
                        <li>
                            <span class="pwa-step-icon"><i class="fas fa-ellipsis-vertical"></i></span>
                            <span>Toca el menú <strong>(3 puntos)</strong> en la esquina superior derecha</span>
                        </li>
                        <li>
                            <span class="pwa-step-icon"><i class="fas fa-plus-square"></i></span>
                            <span>Selecciona <strong>"Instalar app"</strong> o <strong>"Agregar a pantalla de inicio"</strong></span>
                        </li>
                        <li>
                            <span class="pwa-step-icon"><i class="fas fa-check-square"></i></span>
                            <span>Confirma la instalación</span>
                        </li>
                    </ol>
                    <p style="margin-top: 12px; font-size: 0.85rem; color: #ffb3b3;">
                        <i class="fas fa-info-circle"></i> Nota: En HTTP, el prompt automático puede no aparecer. Usa HTTPS para la mejor experiencia.
                    </p>
                </div>
                <div class="pwa-install-actions">
                    <button id="pwa-install-dismiss-info" class="pwa-install-btn pwa-install-btn-dismiss">
                        <i class="fas fa-times-circle"></i> Cerrar
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(banner);
        banner.classList.add('pwa-install-banner-visible');

        setTimeout(() => {
            banner.classList.add('pwa-install-banner-animated');
        }, 100);

        const dismissButton = document.getElementById('pwa-install-dismiss-info');
        if (dismissButton) {
            dismissButton.addEventListener('click', () => {
                markAsDismissed();
                banner.classList.remove('pwa-install-banner-visible', 'pwa-install-banner-animated');
                setTimeout(() => {
                    if (banner.parentNode) {
                        banner.parentNode.removeChild(banner);
                    }
                }, 300);
            });
        }
    }

    /**
     * Crear banner de instalación para iOS
     */
    function createIOSBanner() {
        if (document.getElementById('pwa-install-banner-ios')) {
            return document.getElementById('pwa-install-banner-ios');
        }

        const banner = document.createElement('div');
        banner.id = 'pwa-install-banner-ios';
        banner.className = 'pwa-install-banner pwa-install-banner-ios';
        banner.innerHTML = `
            <div class="pwa-install-content">
                <div class="pwa-install-icon">
                    <i class="fas fa-mobile-alt"></i>
                </div>
                <div class="pwa-install-text">
                    <h3>Instalar eGarage</h3>
                    <p class="pwa-install-intro">Sigue estos pasos para agregar eGarage a tu pantalla de inicio:</p>
                    <ol class="pwa-install-steps">
                        <li>
                            <span class="pwa-step-icon"><i class="fas fa-share-square"></i></span>
                            <span>Toca el botón <strong>Compartir</strong> en la parte inferior</span>
                        </li>
                        <li>
                            <span class="pwa-step-icon"><i class="fas fa-plus-square"></i></span>
                            <span>Selecciona <strong>"Añadir a la pantalla de inicio"</strong></span>
                        </li>
                        <li>
                            <span class="pwa-step-icon"><i class="fas fa-check-square"></i></span>
                            <span>Toca <strong>"Añadir"</strong> para confirmar</span>
                        </li>
                    </ol>
                </div>
                <div class="pwa-install-actions">
                    <button id="pwa-install-dismiss-ios" class="pwa-install-btn pwa-install-btn-dismiss">
                        <i class="fas fa-times-circle"></i> Cerrar
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(banner);
        return banner;
    }

    /**
     * Mostrar banner de Android
     */
    function showAndroidBanner() {
        if (!deferredPrompt) {
            return;
        }

        installBanner = createAndroidBanner();
        installBanner.classList.add('pwa-install-banner-visible');

        // Botón de instalación
        const installButton = document.getElementById('pwa-install-button');
        if (installButton) {
            installButton.addEventListener('click', handleInstallClick);
        }

        // Botón de cerrar
        const dismissButton = document.getElementById('pwa-install-dismiss');
        if (dismissButton) {
            dismissButton.addEventListener('click', handleDismiss);
        }

        // Animar entrada
        setTimeout(() => {
            installBanner.classList.add('pwa-install-banner-animated');
        }, 100);
    }

    /**
     * Mostrar banner de iOS
     */
    function showIOSBanner() {
        iosBanner = createIOSBanner();
        iosBanner.classList.add('pwa-install-banner-visible');

        // Botón de cerrar
        const dismissButton = document.getElementById('pwa-install-dismiss-ios');
        if (dismissButton) {
            dismissButton.addEventListener('click', handleDismissIOS);
        }

        // Animar entrada
        setTimeout(() => {
            iosBanner.classList.add('pwa-install-banner-animated');
        }, 100);

        // Iniciar verificación periódica de instalación en iOS
        startIOSInstallCheck();
    }

    /**
     * Ocultar banner de Android
     */
    function hideAndroidBanner() {
        if (installBanner) {
            installBanner.classList.remove('pwa-install-banner-visible', 'pwa-install-banner-animated');
            setTimeout(() => {
                if (installBanner && installBanner.parentNode) {
                    installBanner.parentNode.removeChild(installBanner);
                }
            }, 300);
        }
    }

    /**
     * Ocultar banner de iOS
     */
    function hideIOSBanner() {
        if (iosBanner) {
            iosBanner.classList.remove('pwa-install-banner-visible', 'pwa-install-banner-animated');
            setTimeout(() => {
                if (iosBanner && iosBanner.parentNode) {
                    iosBanner.parentNode.removeChild(iosBanner);
                }
            }, 300);
        }
    }

    /**
     * Manejar clic en botón de instalación (Android)
     */
    function handleInstallClick() {
        if (!deferredPrompt) {
            return;
        }

        // Mostrar el prompt nativo
        deferredPrompt.prompt();

        // Esperar respuesta del usuario
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('[PWA Install] Usuario aceptó la instalación');
                hideAndroidBanner();
                
                // Mostrar mensaje de éxito
                showSuccessMessage();
            } else {
                console.log('[PWA Install] Usuario rechazó la instalación');
                markAsDismissed();
                hideAndroidBanner();
            }

            // Limpiar el prompt
            deferredPrompt = null;
        });
    }

    /**
     * Manejar cierre del banner (Android)
     */
    function handleDismiss() {
        markAsDismissed();
        hideAndroidBanner();
    }

    /**
     * Manejar cierre del banner (iOS)
     */
    function handleDismissIOS() {
        markAsDismissed();
        hideIOSBanner();
    }

    /**
     * Mostrar mensaje de éxito después de la instalación
     */
    function showSuccessMessage(showTour = false) {
        const message = document.createElement('div');
        message.className = 'pwa-install-success';
        message.innerHTML = `
            <div class="pwa-install-success-content">
                <div class="pwa-install-success-icon">
                    <i class="fas fa-check-circle"></i>
                </div>
                <div class="pwa-install-success-text">
                    <h4>¡eGarage instalado exitosamente!</h4>
                    <p>Ahora puedes acceder a eGarage sin conexión y desde tu pantalla de inicio</p>
                </div>
                ${showTour ? `
                <div class="pwa-install-success-actions">
                    <button id="pwa-tour-button" class="pwa-install-btn pwa-install-btn-primary">
                        <i class="fas fa-rocket"></i> Ver características
                    </button>
                </div>
                ` : ''}
            </div>
        `;
        document.body.appendChild(message);

        setTimeout(() => {
            message.classList.add('pwa-install-success-visible');
        }, 100);

        // Botón de tour si está disponible
        if (showTour) {
            const tourButton = document.getElementById('pwa-tour-button');
            if (tourButton) {
                tourButton.addEventListener('click', () => {
                    hideSuccessMessage(message);
                    // Aquí puedes agregar lógica para mostrar un tour
                    console.log('[PWA Install] Iniciar tour de características');
                    // Ejemplo: window.location.href = '/tour/';
                });
            }
        }

        // Auto-ocultar después de 5 segundos (o 10 si hay tour)
        setTimeout(() => {
            hideSuccessMessage(message);
        }, showTour ? 10000 : 5000);
    }

    /**
     * Ocultar mensaje de éxito
     */
    function hideSuccessMessage(message) {
        if (!message) return;
        message.classList.remove('pwa-install-success-visible');
        setTimeout(() => {
            if (message.parentNode) {
                message.parentNode.removeChild(message);
            }
        }, 300);
    }

    /**
     * Verificar instalación en iOS (detecta cambio a standalone)
     */
    function startIOSInstallCheck() {
        wasStandaloneBefore = isAppInstalled();
        
        if (iosInstallCheckInterval) {
            clearInterval(iosInstallCheckInterval);
        }

        iosInstallCheckInterval = setInterval(() => {
            const isNowStandalone = isAppInstalled();
            
            // Si cambió de no instalado a instalado
            if (!wasStandaloneBefore && isNowStandalone) {
                console.log('[PWA Install] iOS: App instalada detectada');
                clearInterval(iosInstallCheckInterval);
                hideIOSBanner();
                markAsInstalled();
                showSuccessMessage(true); // Mostrar con opción de tour
            }
            
            wasStandaloneBefore = isNowStandalone;
        }, CONFIG.IOS_INSTALL_CHECK_INTERVAL);

        // Limpiar después de 2 minutos (el usuario probablemente ya instaló o no lo hará)
        setTimeout(() => {
            if (iosInstallCheckInterval) {
                clearInterval(iosInstallCheckInterval);
                iosInstallCheckInterval = null;
            }
        }, 120000);
    }

    /**
     * Marcar como instalado
     */
    function markAsInstalled() {
        const data = {
            date: new Date().toISOString(),
            platform: isIOS() ? 'ios' : isAndroid() ? 'android' : 'other'
        };
        localStorage.setItem(CONFIG.STORAGE_KEY_INSTALLED, JSON.stringify(data));
    }

    /**
     * Verificar si ya fue instalado
     */
    function wasInstalled() {
        return localStorage.getItem(CONFIG.STORAGE_KEY_INSTALLED) !== null;
    }

    /**
     * Crear notificación para desktop
     */
    function createDesktopNotification() {
        if (document.getElementById('pwa-desktop-notification')) {
            return document.getElementById('pwa-desktop-notification');
        }

        const notification = document.createElement('div');
        notification.id = 'pwa-desktop-notification';
        notification.className = 'pwa-desktop-notification';
        notification.innerHTML = `
            <div class="pwa-desktop-notification-content">
                <i class="fas fa-info-circle"></i>
                <span>Instala eGarage en tu dispositivo móvil para acceso rápido y uso sin conexión</span>
                <button id="pwa-desktop-dismiss" class="pwa-desktop-dismiss-btn">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        document.body.appendChild(notification);
        return notification;
    }

    /**
     * Mostrar notificación en desktop
     */
    function showDesktopNotification() {
        if (!CONFIG.SHOW_DESKTOP_NOTIFICATION || isMobile()) {
            return;
        }

        desktopNotification = createDesktopNotification();
        setTimeout(() => {
            desktopNotification.classList.add('pwa-desktop-notification-visible');
        }, 100);

        const dismissButton = document.getElementById('pwa-desktop-dismiss');
        if (dismissButton) {
            dismissButton.addEventListener('click', () => {
                desktopNotification.classList.remove('pwa-desktop-notification-visible');
                setTimeout(() => {
                    if (desktopNotification.parentNode) {
                        desktopNotification.parentNode.removeChild(desktopNotification);
                    }
                }, 300);
            });
        }
    }

    /**
     * Inicializar el sistema de instalación
     */
    function init() {
        // Verificar si la app ya está instalada
        isStandalone = isAppInstalled();
        if (isStandalone) {
            console.log('[PWA Install] La app ya está instalada');
            // Si ya está instalada pero no lo habíamos marcado, marcarlo
            if (!wasInstalled()) {
                markAsInstalled();
            }
            return;
        }

        // Verificar si fue rechazado recientemente
        if (wasDismissedRecently()) {
            console.log('[PWA Install] El prompt fue rechazado recientemente');
            // Aún así, mostrar notificación en desktop si aplica
            if (!isMobile() && CONFIG.SHOW_DESKTOP_NOTIFICATION) {
                setTimeout(() => showDesktopNotification(), CONFIG.MIN_TIME_BEFORE_SHOW * 1000);
            }
            return;
        }

        // IMPORTANTE: Escuchar beforeinstallprompt INMEDIATAMENTE (puede dispararse antes de que el script se cargue)
        // No usar setTimeout aquí porque el evento puede perderse
        let beforeInstallPromptListener = (e) => {
            console.log('[PWA Install] ✅ beforeinstallprompt detectado!');
            e.preventDefault();
            deferredPrompt = e;
            
            // Esperar un poco antes de mostrar el banner (mejor UX)
            setTimeout(() => {
                if (!isAppInstalled() && !wasDismissedRecently()) {
                    showAndroidBanner();
                }
            }, CONFIG.MIN_TIME_BEFORE_SHOW * 1000);
        };
        
        // Registrar el listener INMEDIATAMENTE (no dentro de setTimeout)
        window.addEventListener('beforeinstallprompt', beforeInstallPromptListener);

        // Esperar un tiempo antes de mostrar otros elementos
        setTimeout(() => {
            // Detectar si es iOS y mostrar instrucciones
            if (isIOS()) {
                // Esperar un poco más para iOS (mejor UX)
                setTimeout(() => {
                    if (!isAppInstalled() && !wasDismissedRecently()) {
                        showIOSBanner();
                    }
                }, CONFIG.MIN_TIME_BEFORE_SHOW * 1000 + 2000);
            }

            // Mostrar notificación en desktop si no es móvil
            if (!isMobile() && CONFIG.SHOW_DESKTOP_NOTIFICATION) {
                showDesktopNotification();
            }

            // Detectar cuando la app fue instalada (Android/Chrome)
            window.addEventListener('appinstalled', () => {
                console.log('[PWA Install] App instalada exitosamente');
                hideAndroidBanner();
                hideIOSBanner();
                markAsInstalled();
                showSuccessMessage(true); // Mostrar con opción de tour
            });

            // Diagnóstico: Si después de 10 segundos no hay deferredPrompt y no es iOS
            if (!isIOS()) {
                setTimeout(() => {
                    if (!deferredPrompt && !isAppInstalled()) {
                        console.warn('[PWA Install] ⚠️ El evento beforeinstallprompt NO se disparó');
                        console.warn('[PWA Install] Posibles razones:');
                        console.warn('  1. Estás en HTTP (requiere HTTPS para beforeinstallprompt)');
                        console.warn('  2. El service worker no está registrado');
                        console.warn('  3. El manifest no es válido o no es accesible');
                        console.warn('  4. Ya instalaste la app antes');
                        console.warn('');
                        console.warn('[PWA Install] 💡 SOLUCIÓN: Usa HTTPS para probar completamente');
                        console.warn('[PWA Install] 💡 Puedes usar ngrok: ngrok http 8000');
                        
                        // Si es Android y no hay prompt, mostrar banner de iOS como alternativa
                        if (isAndroid() && !wasDismissedRecently()) {
                            console.log('[PWA Install] Mostrando banner alternativo para Android (sin beforeinstallprompt)');
                            // Crear un banner informativo sin el prompt nativo
                            showAndroidInfoBanner();
                        }
                    }
                }, 10000);
            }
        }, CONFIG.MIN_TIME_BEFORE_SHOW * 1000);
    }

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Exportar funciones útiles para uso externo
    window.egaragePWA = {
        showAndroidBanner: showAndroidBanner,
        showIOSBanner: showIOSBanner,
        hideAndroidBanner: hideAndroidBanner,
        hideIOSBanner: hideIOSBanner,
        showSuccessMessage: showSuccessMessage,
        isAppInstalled: isAppInstalled,
        isIOS: isIOS,
        isAndroid: isAndroid,
        markAsInstalled: markAsInstalled
    };
})();

