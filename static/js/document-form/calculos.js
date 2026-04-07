/**
 * Cálculos de totales del documento
 */

class CalculosManager {
    constructor(state) {
        this.state = state;
        this.init();
    }

    init() {
        // Vincular al cambio de estado
        this.state.onChange = () => this.calcularTotales();
        
        // Calcular inicialmente
        this.calcularTotales();
    }

    calcularTotales() {
        // Calcular subtotales de repuestos
        const subtotalRepuestos = this.state.repuestos.reduce((total, repuesto) => {
            let subtotal = repuesto.cantidad * repuesto.precio_unitario;
            
            // Aplicar descuento
            if (repuesto.descuento > 0) {
                subtotal = subtotal * (1 - repuesto.descuento / 100);
            }
            
            // Aplicar IVA
            if (repuesto.iva > 0) {
                subtotal = subtotal * (1 + repuesto.iva / 100);
            }
            
            return total + subtotal;
        }, 0);

        // Calcular subtotales de servicios
        const subtotalServicios = this.state.servicios.reduce((total, servicio) => {
            let subtotal = servicio.precio;
            
            // Aplicar descuento
            if (servicio.descuento > 0) {
                subtotal = subtotal * (1 - servicio.descuento / 100);
            }
            
            // Aplicar IVA
            if (servicio.iva > 0) {
                subtotal = subtotal * (1 + servicio.iva / 100);
            }
            
            return total + subtotal;
        }, 0);

        // Calcular total general
        const totalGeneral = subtotalRepuestos + subtotalServicios;

        // Calcular IVA total
        const ivaRepuestos = this.state.repuestos.reduce((total, repuesto) => {
            let base = repuesto.cantidad * repuesto.precio_unitario;
            
            // Aplicar descuento
            if (repuesto.descuento > 0) {
                base = base * (1 - repuesto.descuento / 100);
            }
            
            return total + (base * (repuesto.iva / 100));
        }, 0);

        const ivaServicios = this.state.servicios.reduce((total, servicio) => {
            let base = servicio.precio;
            
            // Aplicar descuento
            if (servicio.descuento > 0) {
                base = base * (1 - servicio.descuento / 100);
            }
            
            return total + (base * (servicio.iva / 100));
        }, 0);

        const ivaTotal = ivaRepuestos + ivaServicios;

        // Calcular descuentos totales
        const descuentoRepuestos = this.state.repuestos.reduce((total, repuesto) => {
            const base = repuesto.cantidad * repuesto.precio_unitario;
            return total + (base * (repuesto.descuento / 100));
        }, 0);

        const descuentoServicios = this.state.servicios.reduce((total, servicio) => {
            return total + (servicio.precio * (servicio.descuento / 100));
        }, 0);

        const descuentoTotal = descuentoRepuestos + descuentoServicios;

        // Actualizar UI
        this.actualizarUI({
            subtotalRepuestos,
            subtotalServicios,
            totalGeneral,
            ivaTotal,
            descuentoTotal,
            cantidadRepuestos: this.state.repuestos.length,
            cantidadServicios: this.state.servicios.length
        });
    }

    actualizarUI(totales) {
        // Buscar elementos en el DOM
        const elementos = {
            subtotalRepuestos: document.getElementById('subtotal-repuestos'),
            subtotalServicios: document.getElementById('subtotal-servicios'),
            totalGeneral: document.getElementById('total-general'),
            ivaTotal: document.getElementById('iva-total'),
            descuentoTotal: document.getElementById('descuento-total'),
            cantidadRepuestos: document.getElementById('cantidad-repuestos'),
            cantidadServicios: document.getElementById('cantidad-servicios')
        };

        // Actualizar cada elemento si existe
        Object.entries(elementos).forEach(([key, element]) => {
            if (element) {
                if (key.includes('cantidad')) {
                    element.textContent = totales[key];
                } else {
                    element.textContent = `$${totales[key].toFixed(2)}`;
                }
            }
        });

        // También actualizar campos ocultos para el formulario
        const totalHidden = document.getElementById('total-hidden');
        if (totalHidden) {
            totalHidden.value = totales.totalGeneral.toFixed(2);
        }
    }

    // Métodos para obtener valores
    getSubtotalRepuestos() {
        return this.state.repuestos.reduce((total, r) => {
            return total + (r.cantidad * r.precio_unitario);
        }, 0);
    }

    getSubtotalServicios() {
        return this.state.servicios.reduce((total, s) => {
            return total + s.precio;
        }, 0);
    }

    getTotalGeneral() {
        return this.getSubtotalRepuestos() + this.getSubtotalServicios();
    }

    getIvaTotal() {
        const ivaRepuestos = this.state.repuestos.reduce((total, r) => {
            const base = r.cantidad * r.precio_unitario;
            const baseConDescuento = r.descuento > 0 ? base * (1 - r.descuento / 100) : base;
            return total + (baseConDescuento * (r.iva / 100));
        }, 0);

        const ivaServicios = this.state.servicios.reduce((total, s) => {
            const baseConDescuento = s.descuento > 0 ? s.precio * (1 - s.descuento / 100) : s.precio;
            return total + (baseConDescuento * (s.iva / 100));
        }, 0);

        return ivaRepuestos + ivaServicios;
    }

    getDescuentoTotal() {
        const descuentoRepuestos = this.state.repuestos.reduce((total, r) => {
            const base = r.cantidad * r.precio_unitario;
            return total + (base * (r.descuento / 100));
        }, 0);

        const descuentoServicios = this.state.servicios.reduce((total, s) => {
            return total + (s.precio * (s.descuento / 100));
        }, 0);

        return descuentoRepuestos + descuentoServicios;
    }
}

export default CalculosManager;