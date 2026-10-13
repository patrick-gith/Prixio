/* Enregistrement du Service Worker + prompt d'installation */
(function () {
  'use strict';

  // -------- Service Worker --------
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/service-worker.js', { scope: '/' })
        .then((reg) => {
          // Détecter une nouvelle version
          reg.addEventListener('updatefound', () => {
            const newWorker = reg.installing;
            if (!newWorker) return;
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                window.dispatchEvent(new CustomEvent('pwa:update-available'));
              }
            });
          });
        })
        .catch((err) => console.warn('[PWA] SW registration failed:', err));
    });
  }

  // -------- Online/offline --------
  function updateOnlineStatus() {
    window.dispatchEvent(new CustomEvent('pwa:online', {
      detail: { online: navigator.onLine },
    }));
  }
  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);

  // -------- Install prompt --------
  let deferredPrompt = null;

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    window.dispatchEvent(new CustomEvent('pwa:installable'));
  });

  window.addEventListener('appinstalled', () => {
    deferredPrompt = null;
    window.dispatchEvent(new CustomEvent('pwa:installed'));
  });

  // API publique pour déclencher le prompt depuis un bouton
  window.pwaInstall = async function () {
    if (!deferredPrompt) return false;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    deferredPrompt = null;
    return outcome === 'accepted';
  };

  window.pwaCanInstall = () => !!deferredPrompt;

  // -------- Standalone detection --------
  window.pwaIsStandalone = function () {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone === true;
  };
})();