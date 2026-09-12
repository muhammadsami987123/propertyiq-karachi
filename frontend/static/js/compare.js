// compare.js — page logic for compare.html: search-to-add locations, comparison table + chart.
import { api } from "./api.js";
import { initSearch } from "./search.js";
import { formatRange, formatPct } from "./format.js";
import { renderComparisonBarChart } from "./charts.js";

const MAX_LOCATIONS = 4;
const selected = []; // [{id, name, town}]

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

export function initComparePage({ searchInput, searchResults, searchLive, chipsEl, tableWrap, chartCanvas, emptyEl }) {
  initSearch({
    input: searchInput,
    resultsEl: searchResults,
    liveRegionEl: searchLive,
    onSelect: (result) => addLocation(result),
  });

  function renderChips() {
    chipsEl.innerHTML = "";
    if (selected.length === 0) {
      chipsEl.innerHTML = `<p class="text-sm text-[var(--text-dim)]">Search and add up to ${MAX_LOCATIONS} locations to compare.</p>`;
      return;
    }
    selected.forEach((loc) => {
      const chip = document.createElement("span");
      chip.className = "chip";
      chip.innerHTML = "";
      const label = document.createElement("span");
      label.textContent = loc.name;
      const removeBtn = document.createElement("button");
      removeBtn.setAttribute("aria-label", `Remove ${loc.name} from comparison`);
      removeBtn.className = "ml-1 text-[var(--text-faint)] hover:text-[var(--danger)]";
      removeBtn.textContent = "×";
      removeBtn.addEventListener("click", () => removeLocation(loc.id));
      chip.appendChild(label);
      chip.appendChild(removeBtn);
      chipsEl.appendChild(chip);
    });
  }

  async function addLocation(result) {
    if (selected.length >= MAX_LOCATIONS) return;
    if (selected.some((l) => String(l.id) === String(result.id))) return;
    selected.push({ id: result.id, name: result.name, town: result.town });
    renderChips();
    searchInput.value = "";
    await refreshComparison();
  }

  function removeLocation(id) {
    const idx = selected.findIndex((l) => String(l.id) === String(id));
    if (idx >= 0) selected.splice(idx, 1);
    renderChips();
    refreshComparison();
  }

  async function refreshComparison() {
    if (selected.length < 2) {
      tableWrap.innerHTML = "";
      chartCanvas.hidden = true;
      emptyEl.hidden = false;
      emptyEl.textContent = selected.length === 0
        ? "Add at least two locations to see a comparison."
        : "Add one more location to see a comparison.";
      return;
    }
    emptyEl.hidden = true;
    const res = await api.comparison(selected.map((l) => l.id));
    if (!res.ok || !res.data) {
      tableWrap.innerHTML = `<p class="error-inline">Comparison data is currently unavailable.</p>`;
      chartCanvas.hidden = true;
      return;
    }
    renderTable(res.data);
    renderChart(res.data);
  }

  function renderTable(rows) {
    const metrics = [
      { key: "sale_range", label: "Sale Range", fmt: (r) => formatRange(r.sale_min ?? r.sale_price_min, r.sale_max ?? r.sale_price_max) },
      { key: "rent_range", label: "Rent Range", fmt: (r) => formatRange(r.rent_min ?? r.rent_price_min, r.rent_max ?? r.rent_price_max) },
      { key: "price_per_sqft", label: "Price / sq ft", fmt: (r) => formatRange(r.price_per_sqft_min, r.price_per_sqft_max) },
      { key: "rental_yield", label: "Rental Yield", fmt: (r) => formatPct(r.rental_yield_pct ?? r.rental_yield) },
      { key: "trend", label: "Market Trend", fmt: (r) => (r.trend_pct !== undefined ? formatPct(r.trend_pct) : (r.trend || "—")) },
      { key: "confidence", label: "Data Confidence", fmt: (r) => r.confidence || "—" },
    ];

    let html = `<table class="data-table"><thead><tr><th>Metric</th>${rows.map((r) => `<th>${escapeHtml(r.name || r.location_id)}</th>`).join("")}</tr></thead><tbody>`;
    metrics.forEach((m) => {
      html += `<tr><td class="text-[var(--text-dim)]">${m.label}</td>${rows.map((r) => `<td class="text-mono-num">${escapeHtml(m.fmt(r))}</td>`).join("")}</tr>`;
    });
    html += `</tbody></table>`;
    tableWrap.innerHTML = html;
  }

  function renderChart(rows) {
    chartCanvas.hidden = false;
    const labels = rows.map((r) => r.name || String(r.location_id));
    const values = rows.map((r) => Number(r.price_per_sqft_avg ?? r.price_per_sqft_min ?? 0));
    renderComparisonBarChart(chartCanvas, labels, values, "Price / sq ft");
  }

  renderChips();
}
