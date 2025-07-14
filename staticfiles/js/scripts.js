document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('busqueda-input');
    const tabla = document.getElementById('tabla-clientes');

    input.addEventListener('keyup', function () {
        const query = input.value;
        const url = `/clientes/buscar/?q=${encodeURIComponent(query)}`;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                tabla.innerHTML = data.html;
            });
    });
});
