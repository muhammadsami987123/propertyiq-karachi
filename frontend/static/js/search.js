// search.js — debounced fuzzy search UI: keyboard-navigable, accessible.
import { api } from "./api.js";
import { debounce } from "./format.js";

/**
 * Wire a search input + results list.
 * opts: { input, resultsEl, liveRegionEl, onSelect(result), minChars = 2 }
 */
export function initSearch({ input, resultsEl, liveRegionEl, onSelect, minChars = 2 }) {
  let results = [];
  let activeIndex = -1;
  let open = false;

  const run = debounce(async (q) => {
    if (q.trim().length < minChars) {
      closeResults();
      return;
    }
    const res = await api.search(q.trim());
    if (!res.ok) {
      renderMessage("Search is currently unavailable.");
      return;
    }
    results = res.data || [];
    renderResults();
  }, 220);

  input.addEventListener("input", () => run(input.value));

  input.addEventListener("keydown", (e) => {
    if (!open) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      activeIndex = Math.min(activeIndex + 1, results.length - 1);
      highlight();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      activeIndex = Math.max(activeIndex - 1, 0);
      highlight();
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (activeIndex >= 0 && results[activeIndex]) {
        select(results[activeIndex]);
      }
    } else if (e.key === "Escape") {
      closeResults();
    }
  });

  document.addEventListener("click", (e) => {
    if (!resultsEl.contains(e.target) && e.target !== input) closeResults();
  });

  function renderResults() {
    resultsEl.innerHTML = "";
    activeIndex = -1;
    if (results.length === 0) {
      renderMessage("No matches found.");
      return;
    }
    open = true;
    resultsEl.hidden = false;
    results.forEach((r, i) => {
      const li = document.createElement("li");
      li.setAttribute("role", "option");
      li.id = `search-opt-${i}`;
      li.className = "px-3 py-2.5 cursor-pointer flex items-center justify-between gap-3 hover:bg-[var(--surface)] min-h-[44px]";
      const left = document.createElement("div");
      left.innerHTML = "";
      const nameEl = document.createElement("div");
      nameEl.className = "text-sm text-[var(--text)] font-medium";
      nameEl.textContent = r.name;
      const townEl = document.createElement("div");
      townEl.className = "text-xs text-[var(--text-dim)]";
      townEl.textContent = r.town || "";
      left.appendChild(nameEl);
      left.appendChild(townEl);
      li.appendChild(left);
      li.addEventListener("click", () => select(r));
      resultsEl.appendChild(li);
    });
    if (liveRegionEl) liveRegionEl.textContent = `${results.length} result${results.length === 1 ? "" : "s"} found.`;
  }

  function renderMessage(msg) {
    resultsEl.innerHTML = "";
    open = true;
    resultsEl.hidden = false;
    const li = document.createElement("li");
    li.className = "px-3 py-2.5 text-sm text-[var(--text-dim)]";
    li.textContent = msg;
    resultsEl.appendChild(li);
    if (liveRegionEl) liveRegionEl.textContent = msg;
  }

  function highlight() {
    Array.from(resultsEl.children).forEach((el, i) => {
      el.classList.toggle("bg-[var(--surface-2)]", i === activeIndex);
      if (i === activeIndex) input.setAttribute("aria-activedescendant", el.id);
    });
  }

  function select(result) {
    closeResults();
    input.value = result.name;
    onSelect(result);
  }

  function closeResults() {
    open = false;
    resultsEl.hidden = true;
    resultsEl.innerHTML = "";
    activeIndex = -1;
    input.removeAttribute("aria-activedescendant");
  }

  return { closeResults };
}
