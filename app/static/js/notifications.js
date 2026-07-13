document.addEventListener("DOMContentLoaded", async () => {
    const counter = document.getElementById("notification-count");
    if (!counter) return;
    try {
        const response = await fetch("/api/notifications");
        if (!response.ok) return;
        const data = await response.json();
        if (data.count > 0) {
            counter.textContent = data.count;
            counter.style.display = "grid";
        }
    } catch (error) {
        console.debug("Notifications unavailable", error);
    }
});
