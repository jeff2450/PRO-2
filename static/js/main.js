const endpoint = document.body.dataset.endpoint;

document.querySelectorAll("[data-endpoint]").forEach((link) => {
    if (link.dataset.endpoint === endpoint) {
        link.classList.add("is-active");
        link.setAttribute("aria-current", "page");
    }
});

const menuButton = document.querySelector(".menu-button");
const primaryNav = document.querySelector("#primary-nav");

if (menuButton && primaryNav) {
    menuButton.addEventListener("click", () => {
        const isOpen = primaryNav.classList.toggle("is-open");
        menuButton.setAttribute("aria-expanded", String(isOpen));
    });
}

document.querySelectorAll("[data-resource-filters]").forEach((toolbar) => {
    const tableId = toolbar.dataset.targetTable;
    const table = document.getElementById(tableId);
    if (!table) return;

    const rows = Array.from(table.querySelectorAll("tbody tr"));
    const searchInput = toolbar.querySelector("[data-search-filter]");
    const subjectSelect = toolbar.querySelector("[data-subject-filter]");
    const yearSelect = toolbar.querySelector("[data-year-filter]");

    function filterRows() {
        const query = (searchInput?.value || "").trim().toLowerCase();
        const subject = subjectSelect?.value || "";
        const year = yearSelect?.value || "";

        rows.forEach((row) => {
            const matchesSearch = !query || (row.dataset.searchText || row.textContent.toLowerCase()).includes(query);
            const matchesSubject = !subject || row.dataset.subject === subject;
            const matchesYear = !year || row.dataset.year === year;
            row.hidden = !(matchesSearch && matchesSubject && matchesYear);
        });
    }

    searchInput?.addEventListener("input", filterRows);
    subjectSelect?.addEventListener("change", filterRows);
    yearSelect?.addEventListener("change", filterRows);
});

// Timer functionality is now handled by exam-timer.js for server-accurate countdown
// This ensures the timer is synchronized with server time and persists across page refreshes
