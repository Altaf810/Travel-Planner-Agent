/**
 * TravelMind AI — Map JavaScript
 * Leaflet.js integration for destination and attraction maps
 */

let _resultMap = null;
let _dashMap = null;

/* ── Result / Planner Map ────────────────────────────────────── */
async function initResultMap(destination, travelData) {
  const container = document.getElementById("resultMap");
  if (!container) return;

  // Remove existing map
  if (_resultMap) {
    _resultMap.remove();
    _resultMap = null;
  }

  try {
    const coords = await geocode(destination);
    if (!coords) return;

    _resultMap = L.map("resultMap").setView([coords.lat, coords.lng], 11);
    addTileLayer(_resultMap);

    // Main destination marker
    const destIcon = L.divIcon({
      html: `<div style="background:linear-gradient(135deg,#1a56db,#7c3aed);
                          width:40px;height:40px;border-radius:50% 50% 50% 0;
                          transform:rotate(-45deg);border:3px solid white;
                          box-shadow:0 3px 12px rgba(0,0,0,.3)">
               <div style="transform:rotate(45deg);display:flex;align-items:center;
                           justify-content:center;width:100%;height:100%;color:white;font-size:18px">✈️</div>
             </div>`,
      iconSize: [40, 40],
      iconAnchor: [20, 40],
      popupAnchor: [0, -42],
      className: "",
    });

    L.marker([coords.lat, coords.lng], { icon: destIcon })
      .addTo(_resultMap)
      .bindPopup(
        `<div style="font-weight:600;font-size:14px">📍 ${destination}</div>
         <div style="font-size:12px;color:#666;margin-top:4px">Your destination</div>`,
        { maxWidth: 200 }
      )
      .openPopup();

    // Add nearby attraction markers from Nominatim
    addAttractionMarkers(_resultMap, coords, destination);

  } catch (err) {
    console.warn("Map init failed:", err);
    container.innerHTML = `
      <div class="d-flex align-items-center justify-content-center h-100 text-muted">
        <div class="text-center">
          <i class="bi bi-map fs-1 d-block mb-2 opacity-50"></i>
          <div>Map unavailable — check your internet connection</div>
        </div>
      </div>`;
  }
}

async function addAttractionMarkers(map, center, destination) {
  const types = [
    { osm: "tourism=attraction", emoji: "🏛️", color: "#f59e0b" },
    { osm: "tourism=museum", emoji: "🏛️", color: "#8b5cf6" },
    { osm: "natural=beach", emoji: "🏖️", color: "#06b6d4" },
    { osm: "leisure=park", emoji: "🌿", color: "#22c55e" },
    { osm: "amenity=restaurant", emoji: "🍽️", color: "#ef4444" },
    { osm: "amenity=hotel", emoji: "🏨", color: "#3b82f6" },
  ];

  for (const type of types.slice(0, 3)) {
    try {
      const url = `https://overpass-api.de/api/interpreter?data=[out:json][timeout:8];node["${type.osm}"](around:8000,${center.lat},${center.lng});out 6;`;
      const res = await fetch(url);
      const data = await res.json();
      if (data.elements) {
        data.elements.slice(0, 4).forEach((el) => {
          if (!el.lat || !el.lon) return;
          const name = el.tags?.name || el.tags?.["name:en"] || type.osm.split("=")[1];
          const icon = L.divIcon({
            html: `<div style="background:${type.color};width:30px;height:30px;border-radius:50%;
                               display:flex;align-items:center;justify-content:center;
                               border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,.2);font-size:14px">
                     ${type.emoji}
                   </div>`,
            iconSize: [30, 30],
            iconAnchor: [15, 15],
            className: "",
          });
          L.marker([el.lat, el.lon], { icon })
            .addTo(map)
            .bindPopup(`<div style="font-weight:600;font-size:13px">${type.emoji} ${name}</div>`);
        });
      }
    } catch { /* silent fail */ }
  }
}

/* ── Dashboard World Map ─────────────────────────────────────── */
function initDashboardMap() {
  const container = document.getElementById("dashboardMap");
  if (!container || _dashMap) return;

  _dashMap = L.map("dashboardMap", { scrollWheelZoom: false }).setView([20, 78], 4);
  addTileLayer(_dashMap);

  // Popular Indian destinations
  const spots = [
    { name: "Goa", lat: 15.2993, lng: 74.124, emoji: "🏖️" },
    { name: "Manali", lat: 32.2396, lng: 77.1887, emoji: "🏔️" },
    { name: "Jaipur, Rajasthan", lat: 26.9124, lng: 75.7873, emoji: "🏰" },
    { name: "Kerala Backwaters", lat: 9.4981, lng: 76.3388, emoji: "🌴" },
    { name: "Agra (Taj Mahal)", lat: 27.1767, lng: 78.0081, emoji: "🏯" },
    { name: "Darjeeling", lat: 27.0362, lng: 88.2627, emoji: "🍵" },
    { name: "Varanasi", lat: 25.3176, lng: 82.9739, emoji: "🙏" },
    { name: "Leh-Ladakh", lat: 34.1526, lng: 77.5771, emoji: "🏔️" },
    { name: "Andaman Islands", lat: 11.7401, lng: 92.6586, emoji: "🌊" },
  ];

  spots.forEach((s) => {
    const icon = L.divIcon({
      html: `<div style="font-size:20px;filter:drop-shadow(0 2px 4px rgba(0,0,0,.4))">${s.emoji}</div>`,
      iconSize: [28, 28],
      iconAnchor: [14, 14],
      className: "",
    });
    L.marker([s.lat, s.lng], { icon })
      .addTo(_dashMap)
      .bindPopup(`<b>${s.emoji} ${s.name}</b><br><a href="/planner?destination=${encodeURIComponent(s.name)}" 
                  style="color:#1a56db;font-size:12px">Plan a trip →</a>`);
  });
}

/* ── Geocoding (Nominatim) ───────────────────────────────────── */
async function geocode(place) {
  try {
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(place)}&limit=1`;
    const res = await fetch(url, { headers: { "Accept-Language": "en" } });
    const data = await res.json();
    if (data.length > 0) {
      return { lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon), display: data[0].display_name };
    }
  } catch { /* silent */ }
  return null;
}

/* ── Tile layer helper ───────────────────────────────────────── */
function addTileLayer(map) {
  const isDark = document.documentElement.getAttribute("data-bs-theme") === "dark";
  if (isDark) {
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map);
  } else {
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);
  }
}
