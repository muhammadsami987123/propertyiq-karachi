// calculator.js — investment calculator page logic + localStorage saved calculations.
import { api } from "./api.js";
import { formatPKR, formatPct } from "./format.js";

const STORAGE_KEY = "propertyiq.savedCalculations";

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function readSaved() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch (_) {
    return [];
  }
}

function writeSaved(list) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  } catch (_) {
    /* storage unavailable — non-fatal */
  }
}

export function initCalculatorPage({ form, resultsEl, errorEl, pkrStyleToggle, saveBtn, savedListEl }) {
  let pkrStyle = "crore";
  let lastPayload = null;
  let lastResult = null;

  pkrStyleToggle?.addEventListener("change", () => {
    pkrStyle = pkrStyleToggle.checked ? "crore" : "standard";
    if (lastResult) renderResults(lastResult, lastPayload);
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.hidden = true;
    const fd = new FormData(form);
    const purchasePrice = Number(fd.get("purchase_price"));
    const downPayment = Number(fd.get("down_payment"));
    const payload = {
      purchase_price: purchasePrice,
      down_payment: downPayment,
      interest_rate_pct: Number(fd.get("interest_rate_pct")),
      loan_term_years: Number(fd.get("loan_term_years")),
      monthly_rent: Number(fd.get("monthly_rent")),
      monthly_maintenance: Number(fd.get("monthly_maintenance") || 0),
      annual_taxes_fees: Number(fd.get("annual_taxes_fees") || 0),
      vacancy_rate_pct: Number(fd.get("vacancy_rate_pct") || 0),
    };

    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = "Calculating…";

    const res = await api.calculator(payload);

    submitBtn.disabled = false;
    submitBtn.textContent = "Calculate";

    if (!res.ok) {
      errorEl.hidden = false;
      errorEl.textContent = res.error || "The calculator is currently unavailable.";
      resultsEl.innerHTML = "";
      return;
    }
    lastPayload = payload;
    lastResult = res.data;
    renderResults(lastResult, lastPayload);
  });

  function financingAmount(payload) {
    return Math.max(0, (payload.purchase_price || 0) - (payload.down_payment || 0));
  }

  function renderResults(r, payload) {
    const rows = [
      ["Financing amount", formatPKR(financingAmount(payload), pkrStyle)],
      ["Monthly mortgage payment", formatPKR(r.monthly_payment, pkrStyle)],
      ["Annual rental income", formatPKR(r.annual_rental_income, pkrStyle)],
      ["Annual expenses", formatPKR(r.annual_expenses, pkrStyle)],
      ["Net rental income", formatPKR(r.net_rental_income, pkrStyle)],
      ["Gross yield", formatPct(r.gross_yield_pct)],
      ["Net yield", formatPct(r.net_yield_pct)],
      ["Cash-on-cash return", formatPct(r.cash_on_cash_return_pct)],
      ["Breakeven", r.breakeven_years ? `${Number(r.breakeven_years).toFixed(1)} years` : "—"],
      ["Estimated total cost", formatPKR(r.estimated_total_cost, pkrStyle)],
    ];

    resultsEl.innerHTML = `
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 fade-in">
        ${rows.map(([label, value]) => `
          <div class="glass rounded-[3px] p-4">
            <div class="text-xs text-[var(--text-dim)] mb-1">${label}</div>
            <div class="text-lg font-semibold text-mono-num">${escapeHtml(value)}</div>
          </div>
        `).join("")}
      </div>
    `;
  }

  saveBtn?.addEventListener("click", () => {
    if (!lastResult || !lastPayload) return;
    const list = readSaved();
    list.unshift({
      id: Date.now(),
      savedAt: new Date().toISOString(),
      payload: lastPayload,
      result: lastResult,
    });
    writeSaved(list.slice(0, 20));
    renderSavedList();
  });

  function renderSavedList() {
    if (!savedListEl) return;
    const list = readSaved();
    if (list.length === 0) {
      savedListEl.innerHTML = `<p class="text-sm text-[var(--text-dim)]">No saved calculations yet.</p>`;
      return;
    }
    savedListEl.innerHTML = list.map((item) => `
      <div class="glass rounded-[3px] p-4 flex items-center justify-between gap-4" data-id="${item.id}">
        <div>
          <div class="text-sm font-medium text-mono-num">${escapeHtml(formatPKR(item.payload.purchase_price, pkrStyle))}</div>
          <div class="text-xs text-[var(--text-dim)]">Net yield ${escapeHtml(formatPct(item.result.net_yield_pct))} · ${new Date(item.savedAt).toLocaleDateString()}</div>
        </div>
        <button class="icon-btn delete-saved" aria-label="Delete saved calculation" data-id="${item.id}">×</button>
      </div>
    `).join("");

    savedListEl.querySelectorAll(".delete-saved").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = Number(btn.getAttribute("data-id"));
        writeSaved(readSaved().filter((it) => it.id !== id));
        renderSavedList();
      });
    });
  }

  renderSavedList();
}
