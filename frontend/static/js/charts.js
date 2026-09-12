// charts.js — Chart.js helpers for trend + comparison charts.
// Handles the "insufficient data" empty state per product honesty principle.

const CYAN = "#22d3ee";
const AMBER = "#f5a623";
const GRID = "rgba(255,255,255,0.06)";
const TEXT_DIM = "#8b93a1";

const chartRegistry = new Map();

function destroyIfExists(canvasEl) {
  const existing = chartRegistry.get(canvasEl);
  if (existing) {
    existing.destroy();
    chartRegistry.delete(canvasEl);
  }
}

/**
 * Render a market trend line chart, or an empty-state message if trends is empty/invalid.
 * container: element that holds the canvas (and will receive the empty message if needed)
 */
export function renderTrendChart(container, trends) {
  container.innerHTML = "";
  if (!trends || !Array.isArray(trends) || trends.length === 0) {
    const msg = document.createElement("div");
    msg.className = "empty-inline";
    msg.textContent = "Historical trend unavailable due to insufficient reliable observations.";
    container.appendChild(msg);
    return null;
  }

  const canvas = document.createElement("canvas");
  canvas.height = 180;
  container.appendChild(canvas);

  const sorted = [...trends].sort((a, b) => String(a.period).localeCompare(String(b.period)));
  const labels = sorted.map((t) => t.period);
  const values = sorted.map((t) => t.value);
  const metricLabel = sorted[0]?.metric || "value";

  const chart = new Chart(canvas.getContext("2d"), {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: metricLabel,
          data: values,
          borderColor: CYAN,
          backgroundColor: "rgba(34,211,238,0.12)",
          pointBackgroundColor: CYAN,
          pointRadius: 3,
          tension: 0.3,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0d1420",
          borderColor: "rgba(255,255,255,0.1)",
          borderWidth: 1,
          titleColor: "#e8eaed",
          bodyColor: "#e8eaed",
        },
      },
      scales: {
        x: { ticks: { color: TEXT_DIM, font: { size: 11 } }, grid: { color: GRID } },
        y: { ticks: { color: TEXT_DIM, font: { size: 11 } }, grid: { color: GRID } },
      },
    },
  });
  chartRegistry.set(canvas, chart);
  return chart;
}

/**
 * Render a bar chart comparing a numeric metric across labeled locations.
 */
export function renderComparisonBarChart(canvas, labels, values, label = "Price / sq ft") {
  destroyIfExists(canvas);
  if (!labels || labels.length === 0) return null;
  const chart = new Chart(canvas.getContext("2d"), {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label,
          data: values,
          backgroundColor: labels.map((_, i) => (i % 2 === 0 ? "rgba(34,211,238,0.75)" : "rgba(245,166,35,0.75)")),
          borderRadius: 4,
          maxBarThickness: 48,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0d1420",
          borderColor: "rgba(255,255,255,0.1)",
          borderWidth: 1,
          titleColor: "#e8eaed",
          bodyColor: "#e8eaed",
        },
      },
      scales: {
        x: { ticks: { color: TEXT_DIM, font: { size: 11 } }, grid: { display: false } },
        y: { ticks: { color: TEXT_DIM, font: { size: 11 } }, grid: { color: GRID } },
      },
    },
  });
  chartRegistry.set(canvas, chart);
  return chart;
}
