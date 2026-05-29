/**
 * Inventario Inteligente (desarme) — selección por tile, drawer, localStorage, precios editables.
 * Uso: x-data="inventarioInteligente({ items: [...], storageKey: '...', isStaff: bool })"
 */
function inventarioInteligente(config) {
  const editUrlPattern =
    (typeof window !== "undefined" && window.INVENTARIO_EDIT_URL_PATTERN) || "";

  return {
    items: Array.isArray(config.items) ? config.items : [],
    storageKey: config.storageKey || "inventario-inteligente",
    isStaff: Boolean(config.isStaff),

    search: "",
    searchFocused: false,
    category: "",
    stockFilter: "",
    sortBy: "name",

    selected: [],
    quantities: {},
    salePrices: {},

    mobilePanel: false,
    drawerOpen: false,
    editUrlPattern,

    chipClass:
      "border border-white/10 bg-white/5 text-slate-300 hover:border-cyan-400/30 hover:text-cyan-200",
    activeChipClass:
      "border border-cyan-400/30 bg-cyan-400/15 text-cyan-200 shadow-[0_0_12px_rgba(34,211,238,0.12)]",

    editUrl(id) {
      if (!this.editUrlPattern) return "#";
      return this.editUrlPattern
        .replace(/\/0\//, "/" + id + "/")
        .replace(/\/0$/, "/" + id);
    },

    init() {
      this.restoreState();

      this.$watch("selected", () => this.persistState(), { deep: true });
      this.$watch("quantities", () => this.persistState(), { deep: true });
      this.$watch("salePrices", () => this.persistState(), { deep: true });
    },

    persistState() {
      try {
        const payload = {
          selected: this.selected,
          quantities: this.quantities,
          salePrices: this.salePrices,
        };
        localStorage.setItem(this.storageKey, JSON.stringify(payload));
      } catch (e) {
        console.warn("inventario: persistState", e);
      }
    },

    restoreState() {
      try {
        const raw = localStorage.getItem(this.storageKey);
        if (!raw) return;

        const data = JSON.parse(raw);
        const validIds = new Set(this.items.map((i) => i.id));

        this.selected = Array.isArray(data.selected)
          ? data.selected.filter((id) => validIds.has(id))
          : [];

        this.quantities = {};
        if (data.quantities && typeof data.quantities === "object") {
          Object.entries(data.quantities).forEach(([id, qty]) => {
            const numericId = Number(id);
            if (validIds.has(numericId)) {
              this.quantities[numericId] = this.normalizePositiveInt(qty, 1);
            }
          });
        }

        this.salePrices = {};
        if (data.salePrices && typeof data.salePrices === "object") {
          Object.entries(data.salePrices).forEach(([id, price]) => {
            const numericId = Number(id);
            if (validIds.has(numericId)) {
              this.salePrices[numericId] = this.normalizeNonNegativeNumber(price, 0);
            }
          });
        }

        this.selected.forEach((id) => {
          if (!this.quantities[id]) this.quantities[id] = 1;
          if (typeof this.salePrices[id] === "undefined" || this.salePrices[id] === null) {
            const item = this.items.find((x) => x.id === id);
            this.salePrices[id] = Number(item?.precio || 0);
          }
        });
      } catch (error) {
        console.warn("inventario: restoreState", error);
      }
    },

    normalizePositiveInt(value, fallback) {
      if (fallback === undefined) fallback = 1;
      const n = parseInt(value, 10);
      if (Number.isNaN(n) || n < 1) return fallback;
      return n;
    },

    normalizeNonNegativeNumber(value, fallback) {
      if (fallback === undefined) fallback = 0;
      const n = Number(value);
      if (Number.isNaN(n) || n < 0) return fallback;
      return n;
    },

    sanitizeQuantity(id) {
      this.quantities[id] = this.normalizePositiveInt(this.quantities[id], 1);
    },

    sanitizePrice(id, basePrice) {
      const base = Number(basePrice || 0);
      this.salePrices[id] = this.normalizeNonNegativeNumber(this.salePrices[id], base);
    },

    basePriceFor(id) {
      const item = this.items.find((x) => x.id === id);
      return Number(item?.precio || 0);
    },

    effectiveSalePrice(id, basePrice) {
      const base = Number(basePrice || 0);
      const current = this.salePrices[id];
      if (current === undefined || current === null || current === "") {
        return base;
      }
      return this.normalizeNonNegativeNumber(current, base);
    },

    lineTotal(id, basePrice) {
      const qty = this.normalizePositiveInt(this.quantities[id], 1);
      const price = this.effectiveSalePrice(id, basePrice);
      return qty * price;
    },

    normalizeText(v) {
      return String(v || "")
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");
    },

    itemHaystack(item) {
      const terms = Array.isArray(item.search_terms)
        ? item.search_terms.join(" ")
        : "";
      return this.normalizeText(
        [
          item.nombre,
          item.sku,
          item.categoria,
          item.ubicacion,
          item.vehiculo,
          terms,
        ].join(" ")
      );
    },

    escapeHtml(str) {
      return String(str || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    },

    escapeRegExp(s) {
      return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    },

    /** Resalta coincidencias del término buscado (insensible a mayúsculas). */
    highlightNombre(raw) {
      const q = this.search.trim();
      const text = raw == null ? "" : String(raw);
      const escaped = this.escapeHtml(text);
      if (!q) return escaped;
      try {
        const re = new RegExp(`(${this.escapeRegExp(q)})`, "gi");
        return escaped.replace(re, '<mark class="inv-search-mark">$1</mark>');
      } catch (e) {
        return escaped;
      }
    },

    get categories() {
      return [...new Set(this.items.map((i) => i.categoria).filter(Boolean))].sort();
    },

    get suggestions() {
      const q = this.normalizeText(this.search.trim());
      if (!q) return [];

      const pool = [];
      this.items.forEach((item) => {
        if (this.normalizeText(item.nombre).includes(q)) {
          pool.push({ label: item.nombre, type: "nombre" });
        }
        if (this.normalizeText(item.sku).includes(q)) {
          pool.push({ label: item.sku, type: "código" });
        }
        if (this.normalizeText(item.categoria).includes(q)) {
          pool.push({ label: item.categoria, type: "categoría" });
        }
        if (this.normalizeText(item.ubicacion).includes(q)) {
          pool.push({ label: item.ubicacion, type: "ubicación" });
        }
      });

      const seen = new Set();
      return pool
        .filter((s) => {
          const key = s.type + "-" + s.label;
          if (seen.has(key)) return false;
          seen.add(key);
          return true;
        })
        .slice(0, 8);
    },

    applySuggestion(suggestion) {
      this.search = suggestion.label;
      this.searchFocused = false;
    },

    get filteredItems() {
      let result = [...this.items];
      const q = this.normalizeText(this.search.trim());

      if (q) {
        result = result.filter((item) => this.itemHaystack(item).includes(q));
      }

      if (this.category) {
        result = result.filter((item) => item.categoria === this.category);
      }

      if (this.stockFilter === "in_stock") {
        result = result.filter((item) => Number(item.stock) > 0);
      }

      if (this.stockFilter === "out_stock") {
        result = result.filter((item) => Number(item.stock) <= 0);
      }

      if (this.sortBy === "name") {
        result.sort((a, b) => (a.nombre || "").localeCompare(b.nombre || ""));
      } else if (this.sortBy === "stock_desc") {
        result.sort((a, b) => Number(b.stock || 0) - Number(a.stock || 0));
      } else if (this.sortBy === "price_desc") {
        result.sort((a, b) => Number(b.precio || 0) - Number(a.precio || 0));
      } else if (this.sortBy === "price_asc") {
        result.sort((a, b) => Number(a.precio || 0) - Number(b.precio || 0));
      }

      return result;
    },

    get selectedItems() {
      return this.items.filter((item) => this.selected.includes(item.id));
    },

    get totalQuantity() {
      return this.selectedItems.reduce((acc, item) => {
        return acc + this.normalizePositiveInt(this.quantities[item.id], 1);
      }, 0);
    },

    get totalPrice() {
      return this.selectedItems.reduce((acc, item) => {
        return acc + this.lineTotal(item.id, item.precio);
      }, 0);
    },

    get serializedSelection() {
      return JSON.stringify(
        this.selectedItems.map((item) => ({
          id: item.id,
          cantidad: this.normalizePositiveInt(this.quantities[item.id], 1),
          precio_venta: this.effectiveSalePrice(item.id, item.precio),
        }))
      );
    },

    toggleSelect(itemOrId) {
      const id =
        typeof itemOrId === "object" && itemOrId && "id" in itemOrId
          ? itemOrId.id
          : itemOrId;
      const item = this.items.find((i) => i.id === id);
      if (item && item.vendible === false) return;

      if (this.selected.includes(id)) {
        this.selected = this.selected.filter((x) => x !== id);
        delete this.quantities[id];
        delete this.salePrices[id];
      } else {
        this.selected.push(id);
        const basePrice = this.basePriceFor(id);
        this.quantities[id] = 1;
        this.salePrices[id] = basePrice;
      }
    },

    isSelected(id) {
      return this.selected.includes(id);
    },

    clearSelection() {
      this.selected = [];
      this.quantities = {};
      this.salePrices = {};
      try {
        localStorage.removeItem(this.storageKey);
      } catch (e) {}
    },

    clearFilters() {
      this.search = "";
      this.category = "";
      this.stockFilter = "";
      this.sortBy = "name";
      this.searchFocused = false;
    },

    selectVisible() {
      this.filteredItems.forEach((item) => {
        if (item.vendible && !this.selected.includes(item.id)) {
          this.selected.push(item.id);
          this.quantities[item.id] = 1;
          this.salePrices[item.id] = Number(item.precio || 0);
        }
      });
    },

    openSalePanel() {
      this.drawerOpen = true;
    },

    formatCLP(value) {
      const n = Number(value || 0);
      if (typeof Intl !== "undefined" && Intl.NumberFormat) {
        try {
          return new Intl.NumberFormat("es-CL", {
            style: "currency",
            currency: "CLP",
            maximumFractionDigits: 0,
          }).format(n);
        } catch (e) {}
      }
      return "$" + n.toLocaleString("es-CL", { maximumFractionDigits: 0 });
    },
  };
}

if (typeof window !== "undefined") {
  window.inventarioInteligente = inventarioInteligente;
}
