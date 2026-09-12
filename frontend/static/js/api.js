// api.js — thin fetch wrapper for all /api/* endpoints.
// Never throws to the caller in a way that crashes the page; callers get
// { ok:false, error } and are expected to render an inline message.

const BASE = "/api";

async function request(path, { method = "GET", headers = {}, body, admin } = {}) {
  try {
    const opts = { method, headers: { ...headers } };
    if (admin) opts.headers["X-Admin-Token"] = admin;
    if (body instanceof FormData) {
      opts.body = body;
    } else if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(BASE + path, opts);
    let data = null;
    try {
      data = await res.json();
    } catch (_) {
      data = null;
    }
    if (!res.ok) {
      const msg = (data && (data.detail || data.error || data.message)) || `Request failed (${res.status})`;
      return { ok: false, status: res.status, error: msg, data };
    }
    return { ok: true, status: res.status, data };
  } catch (err) {
    return { ok: false, status: 0, error: "Network error — check your connection." };
  }
}

export const api = {
  locations: () => request("/locations"),
  location: (id) => request(`/locations/${encodeURIComponent(id)}`),
  locationMarket: (id) => request(`/locations/${encodeURIComponent(id)}/market`),
  search: (q) => request(`/search?q=${encodeURIComponent(q)}`),
  comparison: (ids) => request(`/comparison?ids=${encodeURIComponent(ids.join(","))}`),
  calculator: (payload) => request("/calculator", { method: "POST", body: payload }),
  heatmap: (metric, transactionType, propertyType) => {
    const params = new URLSearchParams();
    if (metric) params.set("metric", metric);
    if (transactionType) params.set("transaction_type", transactionType);
    if (propertyType) params.set("property_type", propertyType);
    return request(`/analytics/heatmap?${params.toString()}`);
  },
  geoBoundary: () => request("/geo/boundary"),
  geoLocalities: () => request("/geo/localities"),

  // Admin
  adminSources: (token) => request("/admin/sources", { admin: token }),
  adminAddLocation: (token, payload) => request("/admin/locations", { method: "POST", body: payload, admin: token }),
  adminAddMarket: (token, payload) => request("/admin/market", { method: "POST", body: payload, admin: token }),
  adminImportCsv: (token, file) => {
    const fd = new FormData();
    fd.append("file", file);
    return request("/admin/import/csv", { method: "POST", body: fd, admin: token });
  },
  adminImportGeojson: (token, file) => {
    const fd = new FormData();
    fd.append("file", file);
    return request("/admin/import/geojson", { method: "POST", body: fd, admin: token });
  },
};
