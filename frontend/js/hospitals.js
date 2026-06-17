// Controller for hospitals.html (Leaflet.js Map & Overpass API Hospital Finder)

document.addEventListener('DOMContentLoaded', () => {
  if (!api.isAuthenticated()) return;

  // DOM Elements
  const statusDiv = document.getElementById('location-status');
  const statusText = document.getElementById('location-status-text');
  const listContainer = document.getElementById('hospitals-list');

  // Map variables
  let map;
  let userMarker;
  let hospitalMarkersGroup;

  // Default coordinates (New York City)
  let centerLat = 40.7128;
  let centerLon = -74.0060;
  let userLocationAvailable = false;
  let locationRequested = false;

  if (typeof L === 'undefined') {
    statusDiv.className = "bg-red-50 dark:bg-red-950/20 border border-red-100 dark:border-red-900/30 p-3 rounded-2xl text-xs text-red-700 dark:text-red-400 mb-4 flex items-center gap-2";
    statusText.textContent = "Map library failed to load. Please check your connection and refresh.";
    listContainer.innerHTML = '<div class="text-center text-slate-400 italic py-12">Hospital map is unavailable.</div>';
    return;
  }
  
  // Initialize Map
  initMap(centerLat, centerLon);

  // Add explicit retry controls for location permission flow
  const retryButton = document.createElement('button');
  retryButton.type = 'button';
  retryButton.className = 'ml-2 text-sky-600 dark:text-sky-400 font-semibold underline';
  retryButton.textContent = 'Try again';
  retryButton.style.display = 'none';
  retryButton.addEventListener('click', () => {
    retryButton.style.display = 'none';
    requestLocation();
  });
  statusDiv.appendChild(retryButton);

  requestLocation();

  function requestLocation() {
    if (locationRequested) return;
    locationRequested = true;

    if (!navigator.geolocation) {
      statusDiv.className = "bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-100 dark:border-yellow-900/30 p-3 rounded-2xl text-xs text-yellow-700 dark:text-yellow-400 mb-4 flex items-center gap-2";
      statusText.textContent = "Geolocation is not supported by this browser. Showing a default area instead.";
      fetchNearbyHospitals(centerLat, centerLon);
      return;
    }

    statusDiv.className = "bg-sky-50 dark:bg-sky-950/20 border border-sky-100 dark:border-sky-900/30 p-3 rounded-2xl text-xs text-sky-700 dark:text-sky-400 mb-4 flex items-center gap-2";
    statusText.textContent = "Please allow location access so we can find nearby hospitals.";

    navigator.geolocation.getCurrentPosition(
      (position) => {
        centerLat = position.coords.latitude;
        centerLon = position.coords.longitude;
        userLocationAvailable = true;

        statusDiv.className = "bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30 p-3 rounded-2xl text-xs text-emerald-700 dark:text-emerald-400 mb-4 flex items-center gap-2";
        statusText.textContent = "Location found. Fetching nearby hospitals...";
        updateMapCenter(centerLat, centerLon, "Your Location");
        fetchNearbyHospitals(centerLat, centerLon);
      },
      (error) => {
        console.warn("Geolocation failed or blocked:", error.message);
        statusDiv.className = "bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-100 dark:border-yellow-900/30 p-3 rounded-2xl text-xs text-yellow-700 dark:text-yellow-400 mb-4 flex items-center gap-2";
        statusText.textContent = "Location permission was denied. Using a default area instead.";
        retryButton.style.display = 'inline-block';
        fetchNearbyHospitals(centerLat, centerLon);
      },
      { timeout: 15000, enableHighAccuracy: true }
    );
  }

  // Initialize Map
  function initMap(lat, lon) {
    map = L.map('map').setView([lat, lon], 14);
    
    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    hospitalMarkersGroup = L.layerGroup().addTo(map);
  }

  // Update map center with user marker
  function updateMapCenter(lat, lon, label) {
    if (map) {
      map.setView([lat, lon], 14);
      
      if (userMarker) {
        userMarker.setLatLng([lat, lon]);
      } else {
        // Create custom blue pulse marker for user
        const userIcon = L.divIcon({
          className: 'user-location-marker',
          html: `<div class="relative w-4 h-4 rounded-full bg-sky-500 border-2 border-white shadow-lg flex items-center justify-center">
                   <div class="absolute -inset-1 rounded-full bg-sky-400 animate-ping opacity-75"></div>
                 </div>`,
          iconSize: [16, 16],
          iconAnchor: [8, 8]
        });
        
        userMarker = L.marker([lat, lon], { icon: userIcon }).addTo(map)
          .bindPopup(`<b>${label}</b>`).openPopup();
      }
    }
  }

  // Haversine Distance Calculator (km)
  function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  function escapeHtml(value) {
    return String(value || '').replace(/[&<>"']/g, char => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    }[char]));
  }

  // Fetch from Overpass API
  async function fetchNearbyHospitals(lat, lon) {
    const query = `[out:json][timeout:15];(node(around:5000,${lat},${lon})[amenity=hospital];way(around:5000,${lat},${lon})[amenity=hospital];node(around:5000,${lat},${lon})[amenity=clinic];way(around:5000,${lat},${lon})[amenity=clinic];);out center;`;
    const url = `https://overpass-api.de/api/interpreter?data=${encodeURIComponent(query)}`;

    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error("Overpass API error");
      const data = await response.json();
      const hospitals = processOverpassData(data.elements, lat, lon);

      if (hospitals.length === 0) {
        loadMockHospitals(lat, lon, "No live facilities found nearby. Showing fallback centers.");
      } else {
        renderHospitals(hospitals, lat, lon);
        statusDiv.classList.add('hidden');
      }
    } catch (err) {
      console.warn("Failed to fetch live hospital data, loading fallback mock data:", err);
      loadMockHospitals(lat, lon, "The map service is unavailable right now. Showing fallback centers.");
    }
  }

  // Format Overpass results
  function processOverpassData(elements, userLat, userLon) {
    return elements.map(el => {
      const lat = el.lat || (el.center && el.center.lat);
      const lon = el.lon || (el.center && el.center.lon);
      if (!lat || !lon) return null;
      const tags = el.tags || {};
      const name = tags.name || "Unnamed Medical Center";
      const street = tags['addr:street'] || "";
      const house = tags['addr:housenumber'] || "";
      const city = tags['addr:city'] || "";
      
      const address = [house, street, city].filter(Boolean).join(", ") || tags['addr:full'] || "Address details not available";
      const distance = calculateDistance(userLat, userLon, lat, lon);
      
      return {
        id: el.id,
        name,
        address,
        lat,
        lon,
        distance
      };
    }).filter(Boolean).sort((a, b) => a.distance - b.distance); // Sort by distance
  }

  // Fallback Mock data
  function loadMockHospitals(lat, lon, warningMsg) {
    statusDiv.className = "bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-100 dark:border-yellow-900/30 p-3 rounded-2xl text-xs text-yellow-700 dark:text-yellow-400 mb-4 flex items-center gap-2";
    statusText.textContent = warningMsg;
    
    // Simulate 3 hospitals around the coordinates
    const mocks = [
      {
        id: 'mock-1',
        name: 'City General Hospital',
        address: '100 Medical Center Parkway',
        lat: lat + 0.005,
        lon: lon + 0.008,
        distance: calculateDistance(lat, lon, lat + 0.005, lon + 0.008)
      },
      {
        id: 'mock-2',
        name: 'St. Jude Clinical Care',
        address: '450 Mercy Drive Avenue',
        lat: lat - 0.007,
        lon: lon - 0.004,
        distance: calculateDistance(lat, lon, lat - 0.007, lon - 0.004)
      },
      {
        id: 'mock-3',
        name: 'Community Wellness Center',
        address: '82 Health Way Road',
        lat: lat + 0.009,
        lon: lon - 0.006,
        distance: calculateDistance(lat, lon, lat + 0.009, lon - 0.006)
      }
    ].sort((a, b) => a.distance - b.distance);

    renderHospitals(mocks, lat, lon);
  }

  // Render Sidebar lists and Markers
  function renderHospitals(hospitals, userLat, userLon) {
    // Clear existing markers
    hospitalMarkersGroup.clearLayers();
    
    if (hospitals.length === 0) {
      listContainer.innerHTML = `
        <div class="text-center text-slate-400 italic py-12">
          <i class="fa-solid fa-hospital-user text-4xl mb-2 block"></i>
          No medical facilities found within 5km.
        </div>
      `;
      return;
    }

    // Populate Sidebar
    listContainer.innerHTML = hospitals.map((hosp, idx) => {
      const distFormatted = hosp.distance.toFixed(2);
      // Maps URL directions
      const mapsUrl = `https://www.google.com/maps/dir/?api=1&origin=${userLat},${userLon}&destination=${hosp.lat},${hosp.lon}`;
      
      return `
        <div onclick="focusHospital(${idx}, ${hosp.lat}, ${hosp.lon})" class="hospital-card p-4 bg-slate-50 dark:bg-slate-900/40 border border-slate-100 dark:border-slate-800 rounded-2xl hover:border-sky-500 dark:hover:border-sky-500 cursor-pointer transition-all duration-200 text-xs flex justify-between gap-3">
          <div class="space-y-1">
            <h4 class="font-bold text-sm text-sky-600 dark:text-sky-400">${escapeHtml(hosp.name)}</h4>
            <p class="text-slate-400 font-semibold uppercase tracking-wider text-[9px]">${distFormatted} km away</p>
            <p class="text-slate-500 dark:text-slate-400 max-w-[200px] truncate" title="${escapeHtml(hosp.address)}">${escapeHtml(hosp.address)}</p>
          </div>
          <a href="${mapsUrl}" target="_blank" onclick="event.stopPropagation()" class="self-center w-8 h-8 rounded-xl bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 hover:bg-sky-500 hover:text-white transition-colors flex items-center justify-center text-sm" title="Get Directions">
            <i class="fa-solid fa-diamond-turn-right"></i>
          </a>
        </div>
      `;
    }).join('');

    // Plot Markers
    hospitals.forEach((hosp, idx) => {
      // Red hospital marker icon
      const hospitalIcon = L.divIcon({
        className: 'hospital-marker-icon',
        html: `<div class="w-8 h-8 rounded-full bg-red-500 text-white flex items-center justify-center shadow-md border-2 border-white hover:scale-110 transition-transform">
                 <i class="fa-solid fa-plus text-xs"></i>
               </div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
        popupAnchor: [0, -16]
      });

      const marker = L.marker([hosp.lat, hosp.lon], { icon: hospitalIcon })
        .bindPopup(`
          <div class="hospital-popup p-1 text-slate-800">
            <h3 class="font-bold text-sky-600">${escapeHtml(hosp.name)}</h3>
            <p class="text-xs text-slate-500 my-1">${escapeHtml(hosp.address)}</p>
            <a href="https://www.google.com/maps/dir/?api=1&origin=${userLat},${userLon}&destination=${hosp.lat},${hosp.lon}" target="_blank" class="mt-2 block w-full text-center bg-sky-500 text-white py-1 rounded text-[10px] font-bold decoration-none hover:bg-sky-600">Get Directions</a>
          </div>
        `);
      
      hospitalMarkersGroup.addLayer(marker);
      
      // Cache leaflet marker ID inside hospital state list
      hosp.marker = marker;
    });

    // Zoom map to fit all markers including user location
    const groupBounds = L.featureGroup([
      ...(userMarker ? [userMarker] : []),
      ...hospitalMarkersGroup.getLayers()
    ]).getBounds();
    map.fitBounds(groupBounds, { padding: [40, 40] });

    // Expose focus function globally
    window.focusHospital = (idx, lat, lon) => {
      const hosp = hospitals[idx];
      if (hosp && hosp.marker) {
        map.setView([lat, lon], 15);
        hosp.marker.openPopup();
      }
    };
  }
});
