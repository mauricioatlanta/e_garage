// eGarage Background Video Initializer
// Inicializa videos de fondo de forma eficiente
document.addEventListener("DOMContentLoaded", () => {
  const videos = document.querySelectorAll("[data-bgvid]");

  videos.forEach(video => {
    // Configurar video para reproducción automática
    video.muted = true;
    video.loop = true;
    video.playsInline = true;
    video.preload = "metadata";

    // Intentar reproducir
    const playPromise = video.play();

    if (playPromise !== undefined) {
      playPromise.catch(error => {
        console.log("Video autoplay failed:", error);
        // Fallback: mostrar poster si está disponible
        if (video.poster) {
          video.style.backgroundImage = `url(${video.poster})`;
          video.style.backgroundSize = "cover";
          video.style.backgroundPosition = "center";
        }
      });
    }

    // Optimización: pausar cuando no es visible
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          video.play().catch(() => {});
        } else {
          video.pause();
        }
      });
    });

    observer.observe(video);
  });
});
