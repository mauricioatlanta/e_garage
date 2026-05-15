/**
 * i18n.js - Diccionario de traducciones del formulario de documentos
 * 
 * Extraído del código embebido en document_form.html
 */

(function() {
    'use strict';

    const EG = window.EG = window.EG || {};

    // Diccionario base (inglés)
    const I18N_EN = {
        no_clients: "No clients found",
        loading_vehicles: "Loading vehicles...",
        no_vehicles: "No vehicles registered",
        select_vehicle: "Select vehicle...",
        server_error: "Server error",
        error_loading_vehicles: "Error loading vehicles",
        no_services: "No services found",
        select_service: "Select service...",
        issue_date_required: "Issue Date is required",
        document_type_required: "Document Type is required",
        client_required: "Client is required",
        vehicle_required: "Vehicle is required",
        code: "Code",
        name: "Name",
        qty: "Qty",
        cost_price: "Cost Price",
        sale_price: "Sale Price",
        discount_pct: "Discount %",
        subtotal: "Subtotal",
        service: "Service",
        type_to_search_services: "Type to search services...",
        type_to_search_parts: "Type to search parts...",
        type_to_search_external: "Type to search external services...",
        no_parts: "No parts found",
        no_external_services: "No external services found",
        external_company: "External Company",
        create_part: "Create Part",
        create_service: "Create Service",
        remove_row: "Remove row",
        client_price: "Client Price",
        shop_price: "Shop Price",
        toggle_cost_visibility: "Toggle cost price visibility",
        part_number_required: "Part number is required",
        part_name_required: "Part name is required",
        part_created: "Part created successfully",
        part_exists: "Existing part loaded",
        save: "Save",
        cancel: "Cancel",
    };

    // Diccionario español (CL)
    const I18N_ES = {
        no_clients: "Sin clientes encontrados",
        loading_vehicles: "Cargando vehículos…",
        no_vehicles: "Sin vehículos registrados",
        select_vehicle: "Selecciona vehículo…",
        server_error: "Error del servidor",
        error_loading_vehicles: "Error cargando vehículos",
        no_parts: "Sin repuestos coincidentes",
        no_external_services: "Sin servicios externos",
        select_service: "Selecciona servicio…",
        issue_date_required: "La fecha de emisión es obligatoria",
        document_type_required: "El tipo de documento es obligatorio",
        client_required: "Debes seleccionar un cliente",
        vehicle_required: "Debes seleccionar un vehículo",
        code: "Código",
        name: "Nombre",
        qty: "Cant.",
        cost_price: "Precio compra",
        sale_price: "Precio venta",
        discount_pct: "% desc",
        subtotal: "Subtotal",
        service: "Servicio",
        type_to_search_services: "Escribe para buscar servicios…",
        type_to_search_parts: "Escribe para buscar repuestos…",
        type_to_search_external: "Escribe para buscar servicios externos…",
        client_price: "Precio al cliente",
        shop_price: "Costo al taller",
        external_company: "Empresa externa",
        create_part: "Crear repuesto",
        create_service: "Crear servicio",
        remove_row: "Eliminar fila",
        client_price: "Precio al cliente",
        shop_price: "Costo al taller",
        toggle_cost_visibility: "Mostrar/ocultar precio de compra",
        part_number_required: "El código del repuesto es obligatorio",
        part_name_required: "El nombre del repuesto es obligatorio",
        part_created: "Repuesto creado correctamente",
        part_exists: "Repuesto existente seleccionado",
        save: "Guardar",
        cancel: "Cancelar",
    };

    // Diccionarios adicionales por país
    const I18N_BY_COUNTRY = {
        CL: I18N_ES,
        MX: I18N_ES,
        PE: I18N_ES,
        CO: I18N_ES,
        AR: I18N_ES,
        US: I18N_EN,
        BR: {
            ...I18N_ES,
            // Ajustes para portugués de Brasil
        },
    };

    /**
     * Obtiene el diccionario según el país
     */
    function getI18N(country) {
        const c = (country || 'CL').toUpperCase();
        return I18N_BY_COUNTRY[c] || I18N_ES;
    }

    /**
     * Traduce una clave
     */
    function t(key) {
        const country = EG.cfg?.country || 'CL';
        const dict = getI18N(country);
        return dict[key] || I18N_ES[key] || I18N_EN[key] || key;
    }

    /**
     * Inicializar i18n con traducciones en el DOM
     */
    function init() {
        const country = EG.cfg?.country || 'CL';
        const dict = getI18N(country);
        
        // Copiar al namespace EG para acceso global
        EG.I18N = dict;
        EG.t = t;
        
        console.log('🌐 I18N initialized for country:', country);
    }

    // Exports
    EG.i18n = {
        getI18N,
        t,
        init,
        DICTIONARIES: {
            en: I18N_EN,
            es: I18N_ES,
        }
    };

})();
