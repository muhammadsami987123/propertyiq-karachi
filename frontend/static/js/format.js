// format.js — number/currency formatting + debounce helper

/**
 * Format a PKR amount.
 * style: "crore" (Lakh/Crore Pakistani style) | "standard" (plain grouped number)
 * Matches backend semantics: >=1,00,00,000 => Crore, >=1,00,000 => Lakh, else plain.
 */
export function formatPKR(amount, style = "crore") {
  if (amount === null || amount === undefined || Number.isNaN(Number(amount))) return "—";
  const n = Number(amount);
  const abs = Math.abs(n);
  const sign = n < 0 ? "-" : "";

  if (style === "standard") {
    return sign + "PKR " + abs.toLocaleString("en-IN", { maximumFractionDigits: 0 });
  }

  // Crore/Lakh style
  if (abs >= 1_00_00_000) {
    return `${sign}PKR ${(abs / 1_00_00_000).toFixed(2).replace(/\.00$/, "")} Cr`;
  }
  if (abs >= 1_00_000) {
    return `${sign}PKR ${(abs / 1_00_000).toFixed(2).replace(/\.00$/, "")} Lakh`;
  }
  return sign + "PKR " + abs.toLocaleString("en-IN", { maximumFractionDigits: 0 });
}

export function formatRange(min, max, style = "crore") {
  if (min === null || min === undefined) return "—";
  if (max === null || max === undefined || max === min) return formatPKR(min, style);
  return `${formatPKR(min, style)} – ${formatPKR(max, style)}`;
}

export function formatPct(v, decimals = 1) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return "—";
  return `${Number(v).toFixed(decimals)}%`;
}

export function debounce(fn, wait = 250) {
  let t;
  return function debounced(...args) {
    clearTimeout(t);
    t = setTimeout(() => fn.apply(this, args), wait);
  };
}

export function prefersReducedMotion() {
  return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}
