
document.addEventListener("DOMContentLoaded", function () {
  const whatsappBtn = document.createElement("a");
  whatsappBtn.href = "https://wa.me/56912345678";
  whatsappBtn.className = "floating-btn";
  whatsappBtn.textContent = "💬 Contáctanos";
  whatsappBtn.style.position = "fixed";
  whatsappBtn.style.bottom = "1.5rem";
  whatsappBtn.style.right = "1.5rem";
  whatsappBtn.style.background = "#00ffff";
  whatsappBtn.style.color = "#000";
  whatsappBtn.style.padding = "0.75rem 1rem";
  whatsappBtn.style.borderRadius = "9999px";
  whatsappBtn.style.boxShadow = "0 0 15px #00ffff88";
  whatsappBtn.style.fontWeight = "bold";
  whatsappBtn.style.zIndex = "100";
  whatsappBtn.style.transition = "background 0.3s ease";
  whatsappBtn.onmouseover = () => whatsappBtn.style.background = "#00e6e6";
  whatsappBtn.onmouseout = () => whatsappBtn.style.background = "#00ffff";

  document.body.appendChild(whatsappBtn);
});
