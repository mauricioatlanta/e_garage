/**
 * Gestión centralizada del estado del documento
 */

class DocumentState {
    constructor() {
        this.repuestos = [];
        this.servicios = [];
        this.otros = []; // Agregar array para otros servicios
        this.cliente = null;
        this.vehiculo = null;
        this.observaciones = '';
        this.fecha = new Date().toISOString().split('T')[0];
    }

    // Repuestos
    agregarRepuesto(repuesto) {
        this.repuestos.push({
            id: Date.now() + Math.random(),
            codigo: repuesto.codigo || '',
            nombre: repuesto.nombre || '',
            cantidad: parseFloat(repuesto.cantidad) || 1,
            precio_unitario: parseFloat(repuesto.precio_unitario) || 0,
            descuento: parseFloat(repuesto.descuento) || 0,
            iva: parseFloat(repuesto.iva) || 0
        });
        this.notificarCambio();
    }

    eliminarRepuesto(id) {
        this.repuestos = this.repuestos.filter(r => r.id !== id);
        this.notificarCambio();
    }

    actualizarRepuesto(id, datos) {
        const index = this.repuestos.findIndex(r => r.id === id);
        if (index !== -1) {
            this.repuestos[index] = { ...this.repuestos[index], ...datos };
            this.notificarCambio();
        }
    }

    // Servicios
    agregarServicio(servicio) {
        const servicioId = Date.now() + Math.random();
        const servicioData = {
            id: servicioId,
            servicio_id: servicio.servicio_id || '',
            nombre: servicio.nombre || '',
            precio: parseFloat(servicio.precio) || 0,
            empresa: servicio.empresa || '',
            precio_taller: parseFloat(servicio.precio_taller) || 0,
            tipo: 'servicio' // Para diferenciar de otros servicios
        };

        this.servicios.push(servicioData);
        this.notificarCambio();
        return servicioId; // Retornar ID para vinculación
    }

    eliminarServicio(id) {
        this.servicios = this.servicios.filter(s => s.id !== id);
        this.notificarCambio();
    }

    actualizarServicio(id, datos) {
        const index = this.servicios.findIndex(s => s.id === id);
        if (index !== -1) {
            this.servicios[index] = { ...this.servicios[index], ...datos };
            this.notificarCambio();
        }
    }

    // Otros servicios
    agregarOtroServicio(servicio) {
        const servicioId = Date.now() + Math.random();
        const servicioData = {
            id: servicioId,
            servicio_id: servicio.servicio_id || '',
            nombre: servicio.nombre || '',
            precio: parseFloat(servicio.precio) || 0,
            empresa: servicio.empresa || '',
            precio_taller: parseFloat(servicio.precio_taller) || 0,
            tipo: 'otro' // Para diferenciar de servicios normales
        };

        this.otros.push(servicioData);
        this.notificarCambio();
        return servicioId; // Retornar ID para vinculación
    }

    eliminarOtroServicio(id) {
        this.otros = this.otros.filter(s => s.id !== id);
        this.notificarCambio();
    }

    actualizarOtroServicio(id, datos) {
        const index = this.otros.findIndex(s => s.id === id);
        if (index !== -1) {
            this.otros[index] = { ...this.otros[index], ...datos };
            this.notificarCambio();
        }
    }

    // Método para obtener todos los servicios (normales + otros)
    getAllServicios() {
        return [...this.servicios, ...this.otros];
    }

    // Cliente y vehículo
    setCliente(cliente) {
        this.cliente = cliente;
        this.notificarCambio();
    }

    setVehiculo(vehiculo) {
        this.vehiculo = vehiculo;
        this.notificarCambio();
    }

    setObservaciones(observaciones) {
        this.observaciones = observaciones;
        this.notificarCambio();
    }

    setFecha(fecha) {
        this.fecha = fecha;
        this.notificarCambio();
    }

    // Serialización para backend
    serializar() {
        return {
            repuestos: this.repuestos.map(r => ({
                codigo: r.codigo,
                nombre: r.nombre,
                cantidad: r.cantidad,
                precio_unitario: r.precio_unitario,
                descuento: r.descuento,
                iva: r.iva
            })),
            servicios: this.getAllServicios().map(s => ({
                servicio_id: s.servicio_id || '',
                nombre: s.nombre,
                precio: s.precio,
                empresa: s.empresa || '',
                precio_taller: s.precio_taller || 0,
                tipo: s.tipo
            })),
            cliente_id: this.cliente?.id || null,
            vehiculo_id: this.vehiculo?.id || null,
            observaciones: this.observaciones,
            fecha: this.fecha
        };
    }

    // Notificación de cambios
    notificarCambio() {
        // Este método será sobrescrito por el controlador principal
        if (this.onChange) {
            this.onChange();
        }
    }

    // Reset
    reset() {
        this.repuestos = [];
        this.servicios = [];
        this.otros = [];
        this.cliente = null;
        this.vehiculo = null;
        this.observaciones = '';
        this.fecha = new Date().toISOString().split('T')[0];
        this.notificarCambio();
    }
}

export default DocumentState;