document.addEventListener("DOMContentLoaded", () => {
    const select = document.getElementById("court-select");
    if (!select) return;
    const fields = {
        name: document.getElementById("location-name"),
        address: document.getElementById("location-address"),
        city: document.getElementById("location-city"),
        state: document.getElementById("location-state"),
        neighborhood: document.getElementById("location-neighborhood"),
    };
    const syncCourt = () => {
        const option = select.selectedOptions[0];
        const usingCourt = Boolean(select.value);
        fields.name.value = usingCourt ? option.dataset.name : fields.name.value;
        fields.address.value = usingCourt ? option.dataset.address : fields.address.value;
        fields.city.value = usingCourt ? option.dataset.city : fields.city.value;
        fields.state.value = usingCourt ? option.dataset.state : fields.state.value;
        fields.neighborhood.value = usingCourt ? option.dataset.neighborhood : fields.neighborhood.value;
        Object.values(fields).forEach((field) => {
            field.toggleAttribute("readonly", usingCourt);
            field.required = !usingCourt && ["location-name", "location-address", "location-city", "location-state"].includes(field.id);
        });
    };
    select.addEventListener("change", syncCourt);
    syncCourt();
});
