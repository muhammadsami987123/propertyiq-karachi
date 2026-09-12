// filters.js — floating filter panel state + dynamic legend rendering.
import { api } from "./api.js";
import { applyHeatmap } from "./map.js";

const METRIC_LABELS = {
  price: "Sale price",
  rent: "Rental price",
  price_per_sqft: "Price per sq ft",
  growth: "Market growth",
  yield: "Rental yield",
  density: "Density",
  confidence: "Confidence",
};

export function initFilters({ layerSelect, propertyTypeSelect, priceMinInput, priceMaxInput, legendEl, toggleBtn, panelEl }) {
  const state = {
    layer: layerSelect?.value || "price_per_sqft",
    propertyType: propertyTypeSelect?.value || "",
    priceMin: null,
    priceMax: null,
  };

  if (toggleBtn && panelEl) {
    toggleBtn.addEventListener("click", () => {
      const isHidden = panelEl.hasAttribute("hidden");
      if (isHidden) panelEl.removeAttribute("hidden");
      else panelEl.setAttribute("hidden", "");
      toggleBtn.setAttribute("aria-expanded", String(isHidden));
    });
  }

  async function refreshHeatmap() {
    const metric = state.layer;
    const transactionType = metric === "rent" ? "rent" : "sale";
    const res = await api.heatmap(metric, transactionType, state.propertyType || undefined);
    if (!res.ok || !res.data) {
      renderLegend(null, metric);
      return;
    }
    const { data } = res;
    const values = Array.isArray(data) ? data : data.results || [];
    const meta = Array.isArray(data) ? {} : data;
    applyHeatmap(values, meta);
    renderLegend(meta, metric, values);
  }

  function renderLegend(meta, metric, values) {
    if (!legendEl) return;
    if (!meta || (!meta.min && !meta.max && (!values || values.length === 0))) {
      legendEl.innerHTML = `<p class="text-xs text-[var(--text-dim)]">Layer data unavailable.</p>`;
      return;
    }
    const min = meta.min ?? (values && Math.min(...values.map((v) => v.value)));
    const max = meta.max ?? (values && Math.max(...values.map((v) => v.value)));
    legendEl.innerHTML = `
      <div class="text-xs text-[var(--text-dim)] mb-1.5">${METRIC_LABELS[metric] || metric}</div>
      <div class="legend-gradient"></div>
      <div class="flex justify-between text-[11px] text-[var(--text-faint)] mt-1 text-mono-num">
        <span>${formatShort(min)}</span>
        <span>${formatShort(max)}</span>
      </div>
    `;
  }

  function formatShort(v) {
    if (v === undefined || v === null) return "—";
    if (v >= 1_00_00_000) return (v / 1_00_00_000).toFixed(1) + "Cr";
    if (v >= 1_00_000) return (v / 1_00_000).toFixed(1) + "L";
    if (v >= 1000) return (v / 1000).toFixed(1) + "K";
    return String(Math.round(v));
  }

  layerSelect?.addEventListener("change", () => {
    state.layer = layerSelect.value;
    refreshHeatmap();
  });
  propertyTypeSelect?.addEventListener("change", () => {
    state.propertyType = propertyTypeSelect.value;
    refreshHeatmap();
  });
  priceMinInput?.addEventListener("change", () => { state.priceMin = priceMinInput.value ? Number(priceMinInput.value) : null; });
  priceMaxInput?.addEventListener("change", () => { state.priceMax = priceMaxInput.value ? Number(priceMaxInput.value) : null; });

  refreshHeatmap();

  return { state, refreshHeatmap };
}
