document.addEventListener("DOMContentLoaded", () => {
    const mapEl = document.querySelector("#team-picker-map");
    if (!mapEl || !window.L) return;
    const latInput = document.querySelector("#team-latitude");
    const lngInput = document.querySelector("#team-longitude");
    const status = document.querySelector("#team-map-status");
    const startLat = Number(mapEl.dataset.lat || -23.5505);
    const startLng = Number(mapEl.dataset.lng || -46.6333);
    const map = L.map(mapEl).setView([startLat, startLng], 13);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(map);
    const marker = L.marker([startLat, startLng], { draggable: true }).addTo(map);
    const setPoint = (lat, lng) => {
        latInput.value = lat.toFixed(7);
        lngInput.value = lng.toFixed(7);
        marker.setLatLng([lat, lng]);
    };
    marker.on("dragend", () => {
        const point = marker.getLatLng();
        setPoint(point.lat, point.lng);
    });
    map.on("click", (event) => setPoint(event.latlng.lat, event.latlng.lng));
    document.querySelector("#geocode-team")?.addEventListener("click", async () => {
        const parts = [
            document.querySelector("[name='home_location']")?.value,
            document.querySelector("[name='neighborhood']")?.value,
            document.querySelector("[name='city']")?.value,
            document.querySelector("[name='state']")?.value,
        ].filter(Boolean);
        if (!parts.length) return;
        status.textContent = "Buscando endereco...";
        const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(parts.join(", "))}&limit=1`);
        const data = await response.json();
        if (data[0]) {
            const lat = Number(data[0].lat);
            const lng = Number(data[0].lon);
            map.setView([lat, lng], 15);
            setPoint(lat, lng);
            status.textContent = "Sede localizada. Ajuste se precisar.";
        } else {
            status.textContent = "Nao encontramos. Clique no mapa.";
        }
    });
    setPoint(startLat, startLng);
    setTimeout(() => map.invalidateSize(), 150);
});
