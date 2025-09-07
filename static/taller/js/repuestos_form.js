// JavaScript para el formulario de repuestos
document.addEventListener('DOMContentLoaded', function() {
    console.log('Formulario de repuestos cargado');
    
    // Detectar país del usuario para aplicar formato correcto
    const containerElement = document.querySelector('[data-country]');
    const isChile = containerElement && containerElement.getAttribute('data-country') === 'CL';
    
    if (isChile) {
        // Formato para Chile: $2.500 CLP (sin decimales, puntos como separadores de miles)
        
        // Función para formatear precios chilenos
        function formatearPesosChilenos(valor) {
            if (!valor) return '';
            // Limpiar valor de cualquier carácter no numérico
            const limpio = valor.toString().replace(/\D/g, '');
            if (!limpio) return '';
            
            // Formatear con separadores de miles (puntos)
            const numero = parseInt(limpio);
            return '$' + numero.toLocaleString('es-CL').replace(/,/g, '.');
        }
        
        // Función para limpiar valor antes de enviar
        function limpiarPesosChilenos(valor) {
            return valor.replace(/\D/g, '');
        }
        
        // Función para formatear valor decimal de la base de datos
        function formatearDesdeDecimal(valor) {
            if (!valor) return '';
            // Si es un decimal como 2500.00, convertir a entero 2500
            const numero = parseFloat(valor);
            if (isNaN(numero)) return '';
            return Math.round(numero).toString();
        }
        
        // Aplicar formato a campos de precio
        const camposPrecios = ['id_precio_compra', 'id_precio_venta'];
        
        camposPrecios.forEach(campoId => {
            const campo = document.getElementById(campoId);
            if (campo) {
                // Formatear valor inicial si existe
                if (campo.value) {
                    // Primero convertir desde formato decimal si es necesario
                    const valorDecimal = formatearDesdeDecimal(campo.value);
                    const valorLimpio = limpiarPesosChilenos(valorDecimal || campo.value);
                    if (valorLimpio) {
                        campo.value = formatearPesosChilenos(valorLimpio);
                    }
                }
                
                // Evento para formatear mientras se escribe
                campo.addEventListener('input', function(e) {
                    const cursorPos = e.target.selectionStart;
                    const valorAnterior = e.target.value;
                    const valorLimpio = limpiarPesosChilenos(valorAnterior);
                    const valorFormateado = formatearPesosChilenos(valorLimpio);
                    
                    if (valorFormateado !== valorAnterior) {
                        e.target.value = valorFormateado;
                        // Mantener posición del cursor aproximada
                        const nuevaPos = Math.min(cursorPos, valorFormateado.length);
                        e.target.setSelectionRange(nuevaPos, nuevaPos);
                    }
                });
                
                // Evento para pegar contenido
                campo.addEventListener('paste', function(e) {
                    e.preventDefault();
                    const textoPegado = (e.clipboardData || window.clipboardData).getData('text');
                    const valorLimpio = limpiarPesosChilenos(textoPegado);
                    const valorFormateado = formatearPesosChilenos(valorLimpio);
                    e.target.value = valorFormateado;
                });
                
                // Antes de enviar el formulario, limpiar los valores
                const form = campo.closest('form');
                if (form) {
                    form.addEventListener('submit', function(e) {
                        const valorLimpio = limpiarPesosChilenos(campo.value);
                        campo.value = valorLimpio;
                    });
                }
                
                // Actualizar placeholder para Chile
                if (campo.id === 'id_precio_compra') {
                    campo.setAttribute('placeholder', '$0 CLP');
                } else if (campo.id === 'id_precio_venta') {
                    campo.setAttribute('placeholder', '$0 CLP');
                }
            }
        });
        
        console.log('Formato chileno aplicado a campos de precios');
    } else {
        // Formato para otros países (USD con decimales)
        console.log('Formato USD aplicado');
        
        // Aquí se podría agregar lógica específica para USD u otros países
        const camposPrecios = ['id_precio_compra', 'id_precio_venta'];
        camposPrecios.forEach(campoId => {
            const campo = document.getElementById(campoId);
            if (campo) {
                // Actualizar placeholder para USD
                if (campo.id === 'id_precio_compra') {
                    campo.setAttribute('placeholder', '$0.00 USD');
                } else if (campo.id === 'id_precio_venta') {
                    campo.setAttribute('placeholder', '$0.00 USD');
                }
            }
        });
    }
});
