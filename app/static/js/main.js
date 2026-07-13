document.addEventListener("DOMContentLoaded", () => {
    const shouldUppercase = (field) => {
        if (!field.matches("input, textarea")) return false;
        if (field.type && ["email", "password", "url", "number", "date", "time", "datetime-local", "month", "week", "file", "hidden", "checkbox", "radio", "submit", "button"].includes(field.type)) return false;
        if (field.dataset.keepCase === "true") return false;
        return true;
    };

    const uppercaseField = (field) => {
        const start = field.selectionStart;
        const end = field.selectionEnd;
        field.value = field.value.toLocaleUpperCase("pt-BR");
        if (typeof start === "number" && typeof end === "number") {
            field.setSelectionRange(start, end);
        }
    };

    document.querySelectorAll("input, textarea").forEach((field) => {
        if (!shouldUppercase(field)) return;
        if (field.value) uppercaseField(field);
        field.addEventListener("input", () => uppercaseField(field));
        field.addEventListener("change", () => uppercaseField(field));
    });

    document.querySelectorAll("form").forEach((form) => {
        form.addEventListener("submit", () => {
            if (form.classList.contains("ajax-like") || form.classList.contains("ajax-comment")) return;
            form.querySelectorAll("input, textarea").forEach((field) => {
                if (shouldUppercase(field)) uppercaseField(field);
            });
            const button = form.querySelector("button[type='submit'], input[type='submit']");
            if (button) setTimeout(() => button.setAttribute("disabled", "disabled"), 0);
        });
    });

    document.querySelectorAll(".toast").forEach((toast) => {
        setTimeout(() => toast.remove(), 4200);
    });

    document.querySelectorAll("[data-achievement-overlay]").forEach((overlay) => {
        const close = () => {
            overlay.classList.add("closing");
            setTimeout(() => overlay.remove(), 220);
        };
        overlay.querySelector("[data-achievement-close]")?.addEventListener("click", close);
        overlay.addEventListener("click", (event) => {
            if (event.target === overlay) close();
        });
        setTimeout(close, 7600);
    });

    document.querySelectorAll("#map").forEach((el) => {
        if (!window.L) return;
        const lat = Number(el.dataset.lat);
        const lng = Number(el.dataset.lng);
        const map = L.map(el).setView([lat, lng], 14);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(map);
        L.marker([lat, lng]).addTo(map);
        setTimeout(() => map.invalidateSize(), 150);
    });

    document.querySelectorAll("[data-message-preset]").forEach((button) => {
        button.addEventListener("click", () => {
            const field = document.querySelector("#request-message");
            if (field) field.value = button.dataset.messagePreset;
        });
    });

    document.querySelectorAll("[data-copy-combo]").forEach((button) => {
        button.addEventListener("click", async () => {
            await navigator.clipboard.writeText(button.dataset.copyCombo);
            const original = button.innerHTML;
            button.innerHTML = "<i class=\"bi bi-check2\"></i>Resumo copiado";
            setTimeout(() => { button.innerHTML = original; }, 1800);
        });
    });

    const happenedInput = document.querySelector("#happened-value");
    const scoreFields = document.querySelector("#score-fields");
    document.querySelectorAll("[data-happened-value]").forEach((button) => {
        button.addEventListener("click", () => {
            document.querySelectorAll("[data-happened-value]").forEach((item) => item.classList.remove("active"));
            button.classList.add("active");
            if (happenedInput) happenedInput.value = button.dataset.happenedValue;
            if (scoreFields) scoreFields.hidden = button.dataset.happenedValue === "no";
        });
    });

    document.querySelectorAll("#friendlies-map").forEach((el) => {
        if (!window.L) return;
        let points = [];
        try { points = JSON.parse(el.dataset.points || "[]"); } catch { points = []; }
        const center = points[0] ? [points[0].lat, points[0].lng] : [-23.55, -46.63];
        const map = L.map(el).setView(center, points[0] ? 12 : 10);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(map);
        points.forEach((point) => {
            L.marker([point.lat, point.lng]).addTo(map).bindPopup(`<strong>${point.title}</strong><br>${point.text}<br><a href="${point.route}" target="_blank" rel="noopener">Ver rota</a>`);
        });
        setTimeout(() => map.invalidateSize(), 150);
    });

    document.querySelectorAll(".ajax-like").forEach((form) => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            const response = await fetch(form.action, { method: "POST", body: new FormData(form), headers: { "X-Requested-With": "XMLHttpRequest" } });
            if (!response.ok) return;
            const data = await response.json();
            const counter = form.querySelector("[data-like-count]");
            if (counter) counter.textContent = data.likes;
        });
    });

    document.querySelectorAll(".ajax-comment").forEach((form) => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            const input = form.querySelector("input[name='content']");
            if (!input || !input.value.trim()) return;
            const response = await fetch(form.action, { method: "POST", body: new FormData(form), headers: { "X-Requested-With": "XMLHttpRequest" } });
            if (!response.ok) return;
            const data = await response.json();
            const comment = document.createElement("p");
            comment.innerHTML = `<strong>${data.author}</strong> ${data.content}`;
            form.before(comment);
            const card = form.closest(".social-post");
            const counter = card?.querySelector("[data-comment-count]");
            if (counter) counter.textContent = data.comments;
            input.value = "";
        });
    });
});
