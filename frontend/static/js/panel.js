// panel.js — location intelligence side panel (slide-in desktop / bottom sheet mobile).
import { api } from "./api.js";
import { formatRange, formatPct, prefersReducedMotion } from "./format.js";
import { renderTrendChart } from "./charts.js";

let panelEl, bodyEl, closeBtn, currentLocationId;

export function initPanel({ panel, body, close }) {
  panelEl = panel;
  bodyEl = body;
  closeBtn = close;
  closeBtn.addEventListener("click", closePanel);

  // Swipe-down to collapse on mobile
  let startY = null;
  panelEl.addEventListener("touchstart", (e) => { startY = e.touches[0].clientY; }, { passive: true });
  panelEl.addEventListener("touchend", (e) => {
    if (startY === null) return;
    const dy = e.changedTouches[0].clientY - startY;
    if (dy > 80) closePanel();
    startY = null;
  }, { passive: true });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && panelEl.classList.contains("open")) closePanel();
  });
}

export function closePanel() {
  panelEl.classList.remove("open");
}

export async function openPanelForLocation(locationId) {
  currentLocationId = locationId;
  panelEl.classList.add("open");
  panelEl.classList.remove("collapsed");
  renderLoading();

  const [locRes, marketRes] = await Promise.all([api.location(locationId), api.locationMarket(locationId)]);

  if (!locRes.ok) {
    renderError(locRes.status === 404 ? "Location not found." : "Location data is currently unavailable.");
    return;
  }
  renderContent(locRes.data, marketRes.ok ? marketRes.data : null, marketRes.ok ? null : marketRes.error);
}

function renderLoading() {
  bodyEl.innerHTML = `
    <div class="p-5 space-y-3">
      <div class="skeleton h-6 w-2/3"></div>
      <div class="skeleton h-4 w-1/3"></div>
      <div class="skeleton h-24 w-full"></div>
      <div class="skeleton h-32 w-full"></div>
    </div>
  `;
}

function renderError(msg) {
  bodyEl.innerHTML = `
    <div class="p-5">
      <p class="error-inline">${escapeHtml(msg)}</p>
    </div>
  `;
}

function confidenceBadgeClass(level) {
  const l = String(level || "").toLowerCase();
  if (l.includes("high")) return "badge-high";
  if (l.includes("medium")) return "badge-medium";
  if (l.includes("low")) return "badge-low";
  return "badge-demo";
}

function renderContent(loc, market, marketError) {
  const slug = loc.slug || loc.id;
  const explanation = market?.confidence_explanation || "";

  bodyEl.innerHTML = `
    <div class="p-5 space-y-6 fade-in">
      <div>
        <div class="flex items-start justify-between gap-3">
          <div>
            <h2 class="text-xl font-semibold">${escapeHtml(loc.name)}</h2>
            <p class="text-sm text-[var(--text-dim)]">${escapeHtml(loc.town || "")}</p>
          </div>
          <span class="badge ${confidenceBadgeClass(loc.market_category)}">${escapeHtml(loc.market_category || "—")}</span>
        </div>
      </div>

      ${marketError ? `<p class="error-inline">Market data is currently unavailable for this locality.</p>` : renderMarketSections(market)}

      <div>
        <h3 class="text-sm text-[var(--text-dim)] mb-2">Market trend</h3>
        <div id="panel-trend-chart"></div>
      </div>

      ${explanation ? `
      <div class="relative">
        <button id="confidence-explain-btn" class="badge ${confidenceBadgeClass('info')} cursor-pointer" aria-expanded="false">
          Why this confidence level
        </button>
        <div id="confidence-popover" hidden class="glass rounded-[3px] p-3 mt-2 text-xs text-[var(--text-dim)] leading-relaxed">
          ${escapeHtml(explanation)}
        </div>
      </div>` : ""}

      <div class="flex flex-col gap-2 pt-2 border-t divider">
        <a href="/karachi/${encodeURIComponent(slug)}" class="btn btn-primary justify-center">See the full analysis</a>
      </div>
    </div>
  `;

  const trendContainer = document.getElementById("panel-trend-chart");
  if (trendContainer) renderTrendChart(trendContainer, market?.trends);

  const expBtn = document.getElementById("confidence-explain-btn");
  const pop = document.getElementById("confidence-popover");
  if (expBtn && pop) {
    expBtn.addEventListener("click", () => {
      const isHidden = pop.hidden;
      pop.hidden = !isHidden;
      expBtn.setAttribute("aria-expanded", String(isHidden));
    });
  }
}

function renderMarketSections(market) {
  if (!market) return `<p class="empty-inline">Market data is currently unavailable for this locality.</p>`;
  const saleRows = (market.sale || []).map(rowHtml).join("");
  const rentRows = (market.rent || []).map(rowHtml).join("");

  return `
    <div class="space-y-4">
      <div>
        <h3 class="text-sm text-[var(--text-dim)] mb-2">Sale market</h3>
        ${saleRows ? `<div class="space-y-2">${saleRows}</div>` : `<p class="empty-inline">No sale data available.</p>`}
      </div>
      <div>
        <h3 class="text-sm text-[var(--text-dim)] mb-2">Rental market</h3>
        ${rentRows ? `<div class="space-y-2">${rentRows}</div>` : `<p class="empty-inline">No rental data available.</p>`}
      </div>
    </div>
  `;
}

function rowHtml(r) {
  const dataType = r.data_type ? String(r.data_type).replace(/_/g, " ") : "";
  return `
    <div class="border border-[var(--line)] rounded-[3px] p-3">
      <div class="flex items-center justify-between">
        <span class="text-sm font-medium capitalize">${escapeHtml(r.property_type || "Property")}</span>
        <span class="badge ${confidenceBadgeClass(r.confidence)}">${escapeHtml(r.confidence || "—")}</span>
      </div>
      <div class="text-sm text-mono-num mt-1">${formatRange(r.price_min, r.price_max)}</div>
      ${r.price_per_sqft_min ? `<div class="text-xs text-[var(--text-dim)] mt-0.5">${formatRange(r.price_per_sqft_min, r.price_per_sqft_max)} / sq ft</div>` : ""}
      <div class="text-[11px] text-[var(--text-faint)] mt-1">${escapeHtml(r.source || "Source unspecified")}${dataType ? ` (${escapeHtml(dataType)})` : ""}</div>
    </div>
  `;
}

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
