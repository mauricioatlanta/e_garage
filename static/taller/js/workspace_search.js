(function () {
    const root = document.querySelector("[data-workspace-search-root]");
    if (!root) {
        return;
    }

    const input = root.querySelector("[data-search-input]");
    const dropdown = root.querySelector("[data-search-dropdown]");
    const content = root.querySelector("[data-search-content]");
    const liveRegion = root.querySelector("[data-search-live]");
    const shortcut = root.querySelector("[data-search-shortcut]");
    const searchUrl = root.dataset.searchUrl;
    const minChars = Number(root.dataset.minChars || "2");
    const i18n = window.workspaceSearchI18n || {};

    let debounceTimer = null;
    let controller = null;
    let activeIndex = -1;
    let cards = [];

    function t(key, fallback) {
        return i18n[key] || fallback;
    }

    function escapeHtml(value) {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function isEditableTarget(target) {
        if (!target) {
            return false;
        }
        const tagName = (target.tagName || "").toLowerCase();
        return (
            target.isContentEditable ||
            tagName === "input" ||
            tagName === "textarea" ||
            tagName === "select"
        );
    }

    function announce(message) {
        if (liveRegion) {
            liveRegion.textContent = message;
        }
    }

    function openDropdown() {
        dropdown.hidden = false;
        input.setAttribute("aria-expanded", "true");
        root.classList.add("is-open");
    }

    function closeDropdown() {
        dropdown.hidden = true;
        input.setAttribute("aria-expanded", "false");
        root.classList.remove("is-open");
        setActiveIndex(-1);
    }

    function resetCards() {
        cards = Array.from(content.querySelectorAll("[data-result-card]"));
        cards.forEach((card, index) => {
            card.dataset.index = String(index);
            card.addEventListener("mouseenter", function () {
                setActiveIndex(index);
            });
            card.addEventListener("click", function () {
                navigateTo(card.dataset.url);
            });
        });
    }

    function setActiveIndex(index) {
        activeIndex = index;
        cards.forEach((card, cardIndex) => {
            const isActive = cardIndex === activeIndex;
            card.classList.toggle("is-active", isActive);
            card.setAttribute("aria-selected", isActive ? "true" : "false");
            if (isActive) {
                card.scrollIntoView({ block: "nearest" });
            }
        });
    }

    function navigateTo(url) {
        if (!url) {
            return;
        }
        window.location.assign(url);
    }

    function renderState(icon, title, body, isLoading) {
        content.innerHTML = [
            '<div class="workspace-search-state">',
            '  <div class="workspace-search-state-title">',
            isLoading ? '    <span class="workspace-spinner" aria-hidden="true"></span>' : `    <span aria-hidden="true">${icon}</span>`,
            `    <span>${escapeHtml(title)}</span>`,
            "  </div>",
            `  <p class="workspace-search-state-copy">${escapeHtml(body)}</p>`,
            "</div>",
        ].join("");
        resetCards();
        openDropdown();
    }

    function renderHint() {
        renderState("/", t("hintTitle", "Comienza a escribir"), t("hintBody", "Usa al menos 2 caracteres."), false);
        announce(t("hintTitle", "Comienza a escribir"));
    }

    function renderLoading() {
        renderState("", t("loadingTitle", "Buscando en vivo"), t("loadingBody", "Consultando vehículos y clientes coincidentes..."), true);
        announce(t("loadingTitle", "Buscando en vivo"));
    }

    function renderEmpty() {
        renderState(".", t("emptyTitle", "Sin coincidencias"), t("emptyBody", "Prueba con otro dato."), false);
        announce(t("emptyTitle", "Sin coincidencias"));
    }

    function renderError() {
        renderState("!", t("errorTitle", "Búsqueda no disponible"), t("errorBody", "Intenta nuevamente en un momento."), false);
        announce(t("errorTitle", "Búsqueda no disponible"));
    }

    function renderCard(item, kind) {
        const badgeClass = kind === "vehiculo" ? "type-vehiculo" : "type-cliente";
        const badgeText = kind === "vehiculo" ? t("vehicleBadge", "Vehículo") : t("customerBadge", "Cliente");
        const auxText = kind === "vehiculo"
            ? (item.year ? escapeHtml(item.year) : escapeHtml(item.vin || ""))
            : escapeHtml(item.tax_id || item.telefono || "");
        const subtitle = item.subtitle || (kind === "vehiculo" ? t("untitledVehicle", "Vehículo sin patente") : "");
        const meta = item.meta || (kind === "vehiculo" ? t("unassignedCustomer", "Sin cliente asociado") : item.email || "");

        return [
            `<div class="workspace-result-card" role="option" tabindex="-1" data-result-card data-url="${escapeHtml(item.url || "")}" aria-selected="false">`,
            '  <div class="workspace-result-topline">',
            `    <span class="workspace-result-badge ${badgeClass}">${escapeHtml(badgeText)}</span>`,
            `    <span class="workspace-result-aux">${auxText}</span>`,
            "  </div>",
            `  <div class="workspace-result-title">${escapeHtml(item.title || "")}</div>`,
            `  <div class="workspace-result-subtitle">${escapeHtml(subtitle)}</div>`,
            '  <div class="workspace-result-meta">',
            `    <span>${escapeHtml(meta)}</span>`,
            `    <span class="workspace-result-open">${escapeHtml(t("openLabel", "Abrir"))}</span>`,
            "  </div>",
            "</div>",
        ].join("");
    }

    function renderSection(title, items, kind) {
        if (!items.length) {
            return "";
        }

        return [
            '<section class="workspace-search-section">',
            '  <div class="workspace-search-section-head">',
            `    <span class="workspace-search-section-title">${escapeHtml(title)}</span>`,
            `    <span class="workspace-search-section-count">${items.length}</span>`,
            "  </div>",
            '  <div class="workspace-result-grid">',
            items.map(function (item) {
                return renderCard(item, kind);
            }).join(""),
            "  </div>",
            "</section>",
        ].join("");
    }

    function renderResults(payload) {
        const vehiculos = Array.isArray(payload.vehiculos) ? payload.vehiculos : [];
        const clientes = Array.isArray(payload.clientes) ? payload.clientes : [];
        const total = vehiculos.length + clientes.length;

        if (!total) {
            renderEmpty();
            return;
        }

        content.innerHTML = [
            '<div class="workspace-search-summary">',
            `  <span>${total} ${escapeHtml(t("resultsLabel", "resultados"))}</span>`,
            `  <span>${vehiculos.length} ${escapeHtml(t("vehicles", "Vehículos"))} · ${clientes.length} ${escapeHtml(t("customers", "Clientes"))}</span>`,
            "</div>",
            renderSection(t("vehicles", "Vehículos"), vehiculos, "vehiculo"),
            renderSection(t("customers", "Clientes"), clientes, "cliente"),
        ].join("");

        resetCards();
        openDropdown();
        announce(`${total} ${t("resultsLabel", "resultados")}`);
    }

    function fetchResults(query) {
        if (controller) {
            controller.abort();
        }

        controller = new AbortController();
        renderLoading();

        const url = new URL(searchUrl, window.location.origin);
        url.searchParams.set("q", query);

        fetch(url.toString(), {
            method: "GET",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
            credentials: "same-origin",
            signal: controller.signal,
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return response.json();
            })
            .then(function (payload) {
                if (input.value.trim() !== query) {
                    return;
                }
                renderResults(payload);
            })
            .catch(function (error) {
                if (error.name === "AbortError") {
                    return;
                }
                if (input.value.trim() !== query) {
                    return;
                }
                renderError();
            });
    }

    function scheduleSearch() {
        const query = input.value.trim();
        window.clearTimeout(debounceTimer);

        if (!query) {
            renderHint();
            return;
        }

        if (query.length < minChars) {
            renderHint();
            return;
        }

        debounceTimer = window.setTimeout(function () {
            fetchResults(query);
        }, 300);
    }

    input.addEventListener("input", scheduleSearch);

    input.addEventListener("focus", function () {
        if (input.value.trim().length >= minChars && content.innerHTML.trim()) {
            openDropdown();
            return;
        }
        renderHint();
    });

    input.addEventListener("keydown", function (event) {
        if (event.key === "ArrowDown") {
            if (!cards.length) {
                return;
            }
            event.preventDefault();
            openDropdown();
            setActiveIndex(activeIndex < cards.length - 1 ? activeIndex + 1 : 0);
            return;
        }

        if (event.key === "ArrowUp") {
            if (!cards.length) {
                return;
            }
            event.preventDefault();
            openDropdown();
            setActiveIndex(activeIndex > 0 ? activeIndex - 1 : cards.length - 1);
            return;
        }

        if (event.key === "Enter") {
            if (activeIndex >= 0 && cards[activeIndex]) {
                event.preventDefault();
                navigateTo(cards[activeIndex].dataset.url);
            }
            return;
        }

        if (event.key === "Escape") {
            closeDropdown();
        }
    });

    document.addEventListener("mousedown", function (event) {
        if (!root.contains(event.target)) {
            closeDropdown();
        }
    });

    document.addEventListener("keydown", function (event) {
        if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
            event.preventDefault();
            input.focus();
            input.select();
            return;
        }

        if (event.key === "/" && !isEditableTarget(event.target)) {
            event.preventDefault();
            input.focus();
        }
    });

    if (shortcut) {
        shortcut.addEventListener("click", function () {
            input.focus();
            input.select();
        });
    }

    renderHint();
})();
