// Sistema simple y robusto de vista previa de imágenes
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Iniciando sistema de vista previa simple');

    // Elementos del DOM
    const fileInput = document.getElementById('id_logo');
    const noFileMessage = document.getElementById('no-file-message');
    const previewContainer = document.getElementById('preview-container');
    const previewImage = document.getElementById('preview-image');
    const previewName = document.getElementById('preview-name');
    const previewSize = document.getElementById('preview-size');
    const previewType = document.getElementById('preview-type');
    const errorMessage = document.getElementById('error-message');

    console.log('🔍 Elementos encontrados:', {
        fileInput: !!fileInput,
        noFileMessage: !!noFileMessage,
        previewContainer: !!previewContainer,
        previewImage: !!previewImage,
        previewName: !!previewName,
        previewSize: !!previewSize,
        previewType: !!previewType,
        errorMessage: !!errorMessage
    });

    function showError(message) {
        if (errorMessage) {
            errorMessage.textContent = message;
            errorMessage.classList.remove('hidden');
        }
        if (previewContainer) {
            previewContainer.classList.add('hidden');
        }
        if (noFileMessage) {
            noFileMessage.classList.add('hidden');
        }
        console.error('❌ Error:', message);
    }

    function hideError() {
        if (errorMessage) {
            errorMessage.classList.add('hidden');
        }
    }

    function showPreview(file) {
        console.log('📸 Mostrando vista previa para:', file.name);

        // Ocultar mensajes de error y "sin archivo"
        hideError();
        if (noFileMessage) {
            noFileMessage.classList.add('hidden');
        }

        // Actualizar información del archivo
        if (previewName) {
            previewName.textContent = file.name;
        }
        if (previewSize) {
            previewSize.textContent = (file.size / 1024).toFixed(1) + ' KB';
        }
        if (previewType) {
            previewType.textContent = file.type || 'Desconocido';
        }

        // Leer el archivo para la vista previa
        const reader = new FileReader();

        reader.onload = function(e) {
            console.log('✅ Archivo leído correctamente');
            if (previewImage) {
                previewImage.src = e.target.result;
            }
            if (previewContainer) {
                previewContainer.classList.remove('hidden');
            }
        };

        reader.onerror = function() {
            showError('No se pudo leer el archivo seleccionado.');
        };

        reader.readAsDataURL(file);
    }

    function hidePreview() {
        console.log('🚫 Ocultando vista previa');
        if (previewContainer) {
            previewContainer.classList.add('hidden');
        }
        if (noFileMessage) {
            noFileMessage.classList.remove('hidden');
        }
        hideError();
    }

    // Evento principal: cuando se selecciona un archivo
    if (fileInput) {
        fileInput.addEventListener('change', function(event) {
            console.log('🔄 Cambio detectado en input de archivo');

            const files = event.target.files;
            console.log('📂 Número de archivos:', files.length);

            if (files.length === 0) {
                console.log('⚠️ No hay archivos seleccionados');
                hidePreview();
                return;
            }

            const file = files[0];
            console.log('📁 Archivo seleccionado:', {
                name: file.name,
                size: file.size,
                type: file.type,
                lastModified: new Date(file.lastModified)
            });

            // Validaciones básicas
            if (file.size === 0) {
                showError('El archivo está vacío. Selecciona un archivo válido.');
                fileInput.value = '';
                return;
            }

            if (file.size > 5 * 1024 * 1024) { // 5MB
                showError('El archivo es muy grande. El tamaño máximo es 5MB.');
                fileInput.value = '';
                return;
            }

            if (!file.type.startsWith('image/')) {
                showError('Solo se permiten archivos de imagen (PNG, JPG, GIF, etc.).');
                fileInput.value = '';
                return;
            }

            // Todo bien, mostrar vista previa
            showPreview(file);
        });

        console.log('✅ Event listener agregado al input de archivo');
    } else {
        console.error('❌ No se encontró el elemento input de archivo con ID "id_logo"');
    }
});
