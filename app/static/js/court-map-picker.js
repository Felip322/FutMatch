document.addEventListener("DOMContentLoaded", () => {
    const mapEl = document.getElementById("court-picker-map");
    const latInput = document.getElementById("latitude");
    const lngInput = document.getElementById("longitude");
    const geocodeButton = document.getElementById("geocode-court");
    const status = document.getElementById("map-status");
    if (!mapEl || !latInput || !lngInput || !window.L) return;

    const initialLat = Number(latInput.value || mapEl.dataset.lat || -23.5505);
    const initialLng = Number(lngInput.value || mapEl.dataset.lng || -46.6333);
    const map = L.map(mapEl).setView([initialLat, initialLng], latInput.value ? 16 : 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(map);
    const marker = L.marker([initialLat, initialLng], { draggable: true }).addTo(map);

    const setPoint = (lat, lng, message = "Localizacao marcada.") => {
        latInput.value = Number(lat).toFixed(7);
        lngInput.value = Number(lng).toFixed(7);
        marker.setLatLng([lat, lng]);
        map.setView([lat, lng], 16);
        if (status) status.textContent = message;
    };

    marker.on("dragend", () => {
        const point = marker.getLatLng();
        setPoint(point.lat, point.lng, "Marcador ajustado manualmente.");
    });

    map.on("click", (event) => {
        setPoint(event.latlng.lat, event.latlng.lng, "Ponto definido pelo clique no mapa.");
    });

    const value = (name) => document.querySelector(`[name="${name}"]`)?.value?.trim() || "";
    const buildQuery = () => [value("address"), value("address_number"), value("neighborhood"), value("city"), value("state"), value("zip_code"), "Brasil"].filter(Boolean).join(", ");

    geocodeButton?.addEventListener("click", async () => {
        const query = buildQuery();
        if (!query || query === "Brasil") {
            if (status) status.textContent = "Preencha o endereco antes de localizar.";
            return;
        }
        if (status) status.textContent = "Buscando endereco no mapa...";
        try {
            const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(query)}`;
            const response = await fetch(url, { headers: { "Accept": "application/json" } });
            const results = await response.json();
            if (results.length) {
                setPoint(results[0].lat, results[0].lon, "Endereco encontrado. Ajuste o marcador se precisar.");
            } else if (status) {
                status.textContent = "Nao encontrei automaticamente. Clique no mapa para marcar.";
            }
        } catch (error) {
            if (status) status.textContent = "Nao foi possivel buscar agora. Clique no mapa para marcar.";
        }
    });

    setTimeout(() => map.invalidateSize(), 200);
});
