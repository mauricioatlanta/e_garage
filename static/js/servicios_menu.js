
    (() => {
      const configNode = document.getElementById("servicios-menu-config");
      if (!configNode) {
        return;
      }

      const config = JSON.parse(configNode.textContent);
      const refs = {
        searchInput: document.getElementById("searchInput"),
        categoriaFilter: document.getElementById("categoriaFilter"),
        subcategoriaFilter: document.getElementById("subcategoriaFilter"),
        reloadButton: document.getElementById("reloadButton"),
        resultsSummary: document.getElementById("resultsSummary"),
        loadingState: document.getElementById("loadingState"),
        errorState: document.getElementById("errorState"),
        emptyState: document.getElementById("emptyState"),
        servicesGrid: document.getElementById("servicesGrid")
      };

      let abortController = null;

      const debounce = (callback, delay = 220) => {
        let timer = null;
        return (...args) => {
          window.clearTimeout(timer);
          timer = window.setTimeout(() => callback(...args), delay);
        };
      };

      const escapeHtml = (value = "") =>
        String(value)
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#39;");

      const showState = (state) => {
        refs.loadingState.classList.toggle("hidden", state !== "loading");
        refs.errorState.classList.toggle("hidden", state !== "error");
        refs.emptyState.classList.toggle("hidden", state !== "empty");
        refs.servicesGrid.classList.toggle("hidden", state !== "grid");
      };

      const updateSummary = (total) => {
        const number = Number(total) || 0;
        refs.resultsSummary.textContent = number === 1
          ? config.labels.resultsSingle
          : `${number} ${config.labels.resultsPluralSuffix}`;
      };

      const syncSubcategorias = () => {
        const categoria = refs.categoriaFilter.value;
        let selectedStillVisible = false;

        Array.from(refs.subcategoriaFilter.options).forEach((option, index) => {
          if (index === 0) {
            option.hidden = false;
            return;
          }

          const matches = !categoria || option.dataset.categoria === categoria;
          option.hidden = !matches;
          if (matches && option.value === refs.subcategoriaFilter.value) {
            selectedStillVisible = true;
          }
        });

        if (!selectedStillVisible) {
          refs.subcategoriaFilter.value = "";
        }
      };

      const renderCard = (item) => {
        const labels = config.labels || {};
        const hasView = !!item.view_url;
        const hasEdit = !!item.edit_url;
        const hasDelete = !!item.delete_url;
        const code = escapeHtml(item.codigo_interno || "");
        const descripcion = item.descripcion
          ? `<p class="service-card__description">${escapeHtml(item.descripcion)}</p>`
          : "";

        const actions = [];
        if (hasView) {
          actions.push(`<a class="ghost-btn" href="${escapeHtml(item.view_url)}">${escapeHtml(labels.viewLabel || "Ver")}</a>`);
        }
        if (hasEdit) {
          actions.push(`<a class="ghost-btn" href="${escapeHtml(item.edit_url)}">${escapeHtml(labels.editLabel || "Editar")}</a>`);
        }
        if (hasDelete) {
          actions.push(
            `<button type="button" class="danger-btn" data-delete-url="${escapeHtml(item.delete_url)}" data-name="${escapeHtml(item.nombre)}">`
            + `${escapeHtml(labels.deleteLabel || "Eliminar")}`
            + `</button>`
          );
        }

        return `
          <article class="service-card">
            <div class="service-card__head">
              <div class="service-card__title-block">
                <h3>${escapeHtml(item.nombre || "-")}</h3>
                ${code ? `<p class="service-card__code">${code}</p>` : ""}
              </div>
              <span class="service-pill">${escapeHtml(item.tipo || "-")}</span>
            </div>
            <div class="service-meta">
              <div class="meta-item">
                <span>${escapeHtml(labels.categoryLabel || "Categoria")}</span>
                <strong>${escapeHtml(item.categoria || "-")}</strong>
              </div>
              <div class="meta-item">
                <span>${escapeHtml(labels.subcategoryLabel || "Subcategoria")}</span>
                <strong>${escapeHtml(item.subcategoria || "-")}</strong>
              </div>
              ${descripcion}
            </div>
            ${actions.length ? `<div class="service-actions">${actions.join("")}</div>` : ""}
          </article>
        `;
      };

      const bindDeleteButtons = () => {
        refs.servicesGrid.querySelectorAll("[data-delete-url]").forEach((button) => {
          button.addEventListener("click", async () => {
            const serviceName = button.dataset.name || "";
            const confirmed = window.confirm(`${config.labels.deleteConfirm}\n\n${serviceName}`);
            if (!confirmed) {
              return;
            }

            button.disabled = true;
            try {
              const response = await fetch(button.dataset.deleteUrl, {
                method: "POST",
                headers: {
                  "X-CSRFToken": config.csrfToken,
                  "X-Requested-With": "XMLHttpRequest"
                },
                credentials: "same-origin"
              });

              if (response.redirected) {
                window.location.href = response.url;
                return;
              }

              if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
              }

              loadServices();
            } catch (error) {
              window.alert(config.labels.deleteError);
            } finally {
              button.disabled = false;
            }
          });
        });
      };

      const renderServices = (items, total) => {
        if (!Array.isArray(items) || !items.length) {
          refs.servicesGrid.innerHTML = "";
          updateSummary(total);
          showState("empty");
          return;
        }

        refs.servicesGrid.innerHTML = items.map(renderCard).join("");
        bindDeleteButtons();
        updateSummary(total);
        showState("grid");
      };

      const renderError = () => {
        refs.errorState.textContent = config.labels.searchError;
        showState("error");
      };

      const loadServices = async () => {
        showState("loading");
        refs.loadingState.textContent = config.labels.loading;

        if (abortController) {
          abortController.abort();
        }
        abortController = new AbortController();

        const params = new URLSearchParams();
        const query = refs.searchInput.value.trim();
        if (query) {
          params.set("q", query);
        }
        if (refs.categoriaFilter.value) {
          params.set("categoria", refs.categoriaFilter.value);
        }
        if (refs.subcategoriaFilter.value) {
          params.set("subcategoria", refs.subcategoriaFilter.value);
        }
        params.set("limit", "24");

        try {
          const response = await fetch(`${config.dataUrl}?${params.toString()}`, {
            headers: {
              "Accept": "application/json",
              "X-Requested-With": "XMLHttpRequest"
            },
            credentials: "same-origin",
            signal: abortController.signal
          });

          if (response.redirected) {
            window.location.href = response.url;
            return;
          }

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
          }

          const payload = await response.json();
          renderServices(payload.servicios || [], payload.total || 0);
        } catch (error) {
          if (error.name === "AbortError") {
            return;
          }
          renderError();
        }
      };

      const debouncedLoad = debounce(loadServices);

      refs.searchInput.addEventListener("input", debouncedLoad);
      refs.searchInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          loadServices();
        }
      });
      refs.categoriaFilter.addEventListener("change", () => {
        syncSubcategorias();
        loadServices();
      });
      refs.subcategoriaFilter.addEventListener("change", loadServices);
      refs.reloadButton.addEventListener("click", loadServices);

      syncSubcategorias();
      loadServices();
    })();
  
