// map.js — MapLibre GL init, locality layer, heatmap-driven fill, hover tooltip, click -> panel.
import { api } from "./api.js";
import { formatRange, prefersReducedMotion } from "./format.js";

const KARACHI_CENTER = [67.0011, 24.8607];
const STYLE_URL = "https://tiles.openfreemap.org/styles/liberty";

let map = null;
let hoveredId = null;
let selectedId = null;
let onLocalitySelect = null; // callback(locationId, feature)
let localitiesData = null;

export function initMap({ container = "map", onSelect } = {}) {
  onLocalitySelect = onSelect || (() => {});

  map = new maplibregl.Map({
    container,
    style: STYLE_URL,
    center: KARACHI_CENTER,
    zoom: 10.5,
    pitch: 0,
    attributionControl: { compact: true },
  });

  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

  map.on("load", async () => {
    await loadBoundary();
    await loadLocalities();
  });

  return map;
}

async function loadBoundary() {
  const res = await api.geoBoundary();
  if (!res.ok || !res.data) return;
  try {
    map.addSource("karachi-boundary", { type: "geojson", data: res.data });
    map.addLayer({
      id: "boundary-line",
      type: "line",
      source: "karachi-boundary",
      paint: { "line-color": "#c6a24d", "line-width": 1.25, "line-opacity": 0.4 },
    });
  } catch (_) {
    /* style not ready or bad geometry — non-fatal */
  }
}

async function loadLocalities() {
  const res = await api.geoLocalities();
  if (!res.ok || !res.data) {
    showMapError("Locality boundaries are currently unavailable.");
    return;
  }
  localitiesData = res.data;

  map.addSource("localities", {
    type: "geojson",
    data: localitiesData,
    promoteId: "location_id",
  });

  map.addLayer({
    id: "localities-fill",
    type: "fill",
    source: "localities",
    paint: {
      "fill-color": "#3a4f5c",
      "fill-opacity": 0.22,
    },
  });

  map.addLayer({
    id: "localities-outline",
    type: "line",
    source: "localities",
    paint: {
      "line-color": [
        "case",
        ["boolean", ["feature-state", "selected"], false],
        "#c6a24d",
        ["boolean", ["feature-state", "hover"], false],
        "#d9bd7c",
        "rgba(150,167,175,0.4)",
      ],
      "line-width": [
        "case",
        ["boolean", ["feature-state", "selected"], false],
        3,
        ["boolean", ["feature-state", "hover"], false],
        2,
        0.75,
      ],
    },
  });

  wireInteractions();
}

function wireInteractions() {
  const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 12 });

  map.on("mousemove", "localities-fill", (e) => {
    if (!e.features.length) return;
    map.getCanvas().style.cursor = "pointer";
    const f = e.features[0];
    const id = f.id;
    if (hoveredId !== null && hoveredId !== id) {
      map.setFeatureState({ source: "localities", id: hoveredId }, { hover: false });
    }
    hoveredId = id;
    map.setFeatureState({ source: "localities", id }, { hover: true });

    const props = f.properties || {};
    popup
      .setLngLat(e.lngLat)
      .setHTML(buildTooltipHTML(props))
      .addTo(map);
  });

  map.on("mouseleave", "localities-fill", () => {
    map.getCanvas().style.cursor = "";
    if (hoveredId !== null) {
      map.setFeatureState({ source: "localities", id: hoveredId }, { hover: false });
    }
    hoveredId = null;
    popup.remove();
  });

  map.on("click", "localities-fill", (e) => {
    if (!e.features.length) return;
    const f = e.features[0];
    selectFeature(f);
  });
}

function buildTooltipHTML(props) {
  const name = escapeHtml(props.name || "Unknown locality");
  const category = escapeHtml(props.market_category || "—");
  return `
    <div class="map-tooltip">
      <div class="t-name">${name}</div>
      <div class="t-row"><span>Market</span><span>${category}</span></div>
      <div class="t-cta">Click to open the full picture</div>
    </div>
  `;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

export function selectLocationById(locationId) {
  if (!localitiesData) return;
  const feature = localitiesData.features.find((f) => String(f.properties.location_id) === String(locationId));
  if (feature) selectFeature(feature, true);
}

function selectFeature(feature, skipFly = false) {
  const id = feature.id;
  if (selectedId !== null && selectedId !== id) {
    map.setFeatureState({ source: "localities", id: selectedId }, { selected: false });
  }
  selectedId = id;
  map.setFeatureState({ source: "localities", id }, { selected: true });

  if (!skipFly) {
    const reduced = prefersReducedMotion();
    const center = getFeatureCenter(feature);
    if (center) {
      map.flyTo({
        center,
        zoom: Math.max(map.getZoom(), 13.5),
        duration: reduced ? 0 : 900,
        essential: true,
      });
    }
  }

  onLocalitySelect(feature.properties.location_id, feature);
}

function getFeatureCenter(feature) {
  try {
    const geom = feature.geometry;
    if (geom.type === "Point") return geom.coordinates;
    if (geom.type === "Polygon") return polygonCentroid(geom.coordinates[0]);
    if (geom.type === "MultiPolygon") return polygonCentroid(geom.coordinates[0][0]);
  } catch (_) {
    return null;
  }
  return null;
}

function polygonCentroid(ring) {
  let x = 0, y = 0;
  for (const [lng, lat] of ring) {
    x += lng;
    y += lat;
  }
  return [x / ring.length, y / ring.length];
}

function showMapError(message) {
  const container = document.getElementById("map");
  if (!container) return;
  const el = document.createElement("div");
  el.className = "glass fade-in";
  el.style.cssText = "position:absolute;bottom:1rem;left:1rem;right:1rem;max-width:420px;padding:.75rem 1rem;border-radius:10px;z-index:20;";
  el.innerHTML = `<p class="error-inline" style="border:none;background:none;padding:0;">${escapeHtml(message)}</p>`;
  container.parentElement.appendChild(el);
}

/**
 * Recolor the fill layer based on heatmap values keyed by location_id.
 * legendInfo: { min, max }
 */
export function applyHeatmap(values, legendInfo) {
  if (!map || !map.getLayer("localities-fill")) return;
  if (!values || values.length === 0) {
    map.setPaintProperty("localities-fill", "fill-color", "#3a4f5c");
    map.setPaintProperty("localities-fill", "fill-opacity", 0.22);
    return;
  }
  const min = legendInfo?.min ?? Math.min(...values.map((v) => v.value));
  const max = legendInfo?.max ?? Math.max(...values.map((v) => v.value));
  const range = max - min || 1;

  const matchExpr = ["match", ["get", "location_id"]];
  const byId = {};
  for (const v of values) byId[v.location_id] = v.value;

  // Build a data-driven color via interpolation on a computed property.
  // Since MapLibre expressions can't easily do a JS object lookup + interpolate combined
  // cleanly across many ids, we set per-feature-state color buckets instead.
  values.forEach((v) => {
    const t = Math.max(0, Math.min(1, (v.value - min) / range));
    const color = interpolateColor(t);
    map.setFeatureState({ source: "localities", id: v.location_id }, { heatColor: color });
  });

  map.setPaintProperty("localities-fill", "fill-color", [
    "case",
    ["!=", ["feature-state", "heatColor"], null],
    ["feature-state", "heatColor"],
    "#3a4149",
  ]);
  map.setPaintProperty("localities-fill", "fill-opacity", 0.55);
}

function interpolateColor(t) {
  // slate -> muted steel -> brass, matching the legend gradient
  const stops = [
    [34, 53, 65],
    [111, 133, 144],
    [198, 162, 77],
  ];
  const seg = t < 0.5 ? 0 : 1;
  const localT = t < 0.5 ? t / 0.5 : (t - 0.5) / 0.5;
  const a = stops[seg];
  const b = stops[seg + 1];
  const r = Math.round(a[0] + (b[0] - a[0]) * localT);
  const g = Math.round(a[1] + (b[1] - a[1]) * localT);
  const bl = Math.round(a[2] + (b[2] - a[2]) * localT);
  return `rgb(${r},${g},${bl})`;
}

export function getMap() {
  return map;
}
