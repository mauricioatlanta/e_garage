document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('busqueda-servicio');
    input.addEventListener('input', () => {
        const query = input.value.toLowerCase();
        document.querySelectorAll('.servicio-item').forEach(item => {
            item.style.display = item.textContent.toLowerCase().includes(query) ? 'block' : 'none';
        });
    });
});