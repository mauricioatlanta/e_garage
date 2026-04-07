/**
 * Serialización de datos para envío al backend
 */

class Serializer {
    constructor(state) {
        this.state = state;
    }

    // Serializar para envío al backend
    serializeForBackend() {
        return {
            repuestos: this.state.repuestos.map(r => ({
                codigo: r.codigo,
                nombre: r.nombre,
                cantidad: r.cantidad,
                precio_unitario: r.precio_unitario,
                descuento: r.descuento,
                iva: r.iva
            })),
            servicios: this.state.servicios.map(s => ({
                nombre: s.nombre,
                descripcion: s.descripcion,
                precio: s.precio,
                descuento: s.descuento,
                iva: s.iva
            })),
            cliente_id: this.state.cliente?.id || null,
            vehiculo_id: this.state.vehiculo?.id || null,
            observaciones: this.state.observaciones,
            fecha: this.state.fecha
        };
    }

    // Serializar para campos de formulario
    serializeForForm() {
        const data = this.serializeForBackend();
        
        return {
            repuestos_json: JSON.stringify(data.repuestos),
            servicios_json: JSON.stringify(data.servicios),
            cliente_id: data.cliente_id,
            vehiculo_id: data.vehiculo_id,
            observaciones: data.observaciones,
            fecha: data.fecha
        };
    }

    // Preparar formulario para envío
    prepareForm(formElement) {
        const formData = this.serializeForForm();
        
        // Agregar campos ocultos o actualizar existentes
        Object.entries(formData).forEach(([key, value]) => {
            let field = formElement.querySelector(`[name="${key}"]`);
            
            if (!field) {
                // Crear campo oculto si no existe
                field = document.createElement('input');
                field.type = 'hidden';
                field.name = key;
                formElement.appendChild(field);
            }
            
            field.value = value;
        });

        // También agregar total general si no existe
        const totalField = formElement.querySelector('[name="total"]');
        if (!totalField) {
            const total = this.calculateTotal();
            const totalInput = document.createElement('input');
            totalInput.type = 'hidden';
            totalInput.name = 'total';
            totalInput.value = total.toFixed(2);
            formElement.appendChild(totalInput);
        }

        return formData;
    }

    // Calcular total general
    calculateTotal() {
        const totalRepuestos = this.state.repuestos.reduce((sum, r) => {
            let subtotal = r.cantidad * r.precio_unitario;
            if (r.descuento > 0) subtotal *= (1 - r.descuento / 100);
            if (r.iva > 0) subtotal *= (1 + r.iva / 100);
            return sum + subtotal;
        }, 0);

        const totalServicios = this.state.servicios.reduce((sum, s) => {
            let subtotal = s.precio;
            if (s.descuento > 0) subtotal *= (1 - s.descuento / 100);
            if (s.iva > 0) subtotal *= (1 + s.iva / 100);
            return sum + subtotal;
        }, 0);

        return totalRepuestos + totalServicios;
    }

    // Validar datos antes de enviar
    validate() {
        const errors = [];

        // Validar repuestos
        this.state.repuestos.forEach((repuesto, index) => {
            if (!repuesto.nombre || repuesto.nombre.trim() === '') {
                errors.push(`Repuesto ${index + 1}: Nombre es requerido`);
            }
            if (repuesto.cantidad <= 0) {
                errors.push(`Repuesto ${index + 1}: Cantidad debe ser mayor a 0`);
            }
            if (repuesto.precio_unitario < 0) {
                errors.push(`Repuesto ${index + 1}: Precio no puede ser negativo`);
            }
            if (repuesto.descuento < 0 || repuesto.descuento > 100) {
                errors.push(`Repuesto ${index + 1}: Descuento debe estar entre 0 y 100`);
            }
            if (repuesto.iva < 0 || repuesto.iva > 100) {
                errors.push(`Repuesto ${index + 1}: IVA debe estar entre 0 y 100`);
            }
        });

        // Validar servicios
        this.state.servicios.forEach((servicio, index) => {
            if (!servicio.nombre || servicio.nombre.trim() === '') {
                errors.push(`Servicio ${index + 1}: Nombre es requerido`);
            }
            if (servicio.precio < 0) {
                errors.push(`Servicio ${index + 1}: Precio no puede ser negativo`);
            }
            if (servicio.descuento < 0 || servicio.descuento > 100) {
                errors.push(`Servicio ${index + 1}: Descuento debe estar entre 0 y 100`);
            }
            if (servicio.iva < 0 || servicio.iva > 100) {
                errors.push(`Servicio ${index + 1}: IVA debe estar entre 0 y 100`);
            }
        });

        // Validar cliente (opcional dependiendo de requisitos)
        if (!this.state.cliente) {
            errors.push('Cliente es requerido');
        }

        return {
            isValid: errors.length === 0,
            errors
        };
    }

    // Método para debug
    debug() {
        const data = this.serializeForBackend();
        console.log('=== DATOS SERIALIZADOS ===');
        console.log('Repuestos:', data.repuestos);
        console.log('Servicios:', data.servicios);
        console.log('Cliente ID:', data.cliente_id);
        console.log('Vehículo ID:', data.vehiculo_id);
        console.log('Observaciones:', data.observaciones);
        console.log('Fecha:', data.fecha);
        console.log('==========================');
        
        return data;
    }
}

export default Serializer;