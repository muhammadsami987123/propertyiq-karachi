// charts.js — Chart.js helpers for trend + comparison charts.
// Handles the "insufficient data" empty state per product honesty principle.

const BRASS = "#c6a24d";
const STEEL = "#6f8590";
const GRID = "rgba(150,167,175,0.12)";
const TEXT_DIM = "#96a7af";

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
          borderColor: BRASS,
          backgroundColor: "rgba(198,162,77,0.12)",
          pointBackgroundColor: BRASS,
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
          backgroundColor: "#101d28",
          borderColor: "rgba(150,167,175,0.25)",
          borderWidth: 1,
          titleColor: "#ecebe3",
          bodyColor: "#ecebe3",
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
          backgroundColor: labels.map((_, i) => (i % 2 === 0 ? "rgba(198,162,77,0.8)" : "rgba(111,133,144,0.8)")),
          borderRadius: 2,
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
          backgroundColor: "#101d28",
          borderColor: "rgba(150,167,175,0.25)",
          borderWidth: 1,
          titleColor: "#ecebe3",
          bodyColor: "#ecebe3",
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
