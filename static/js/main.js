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

function initializeTestTimer() {
    document.querySelectorAll("[data-test-form]").forEach((form) => {
        const timerDisplay = form.querySelector("[data-timer-display]");
        const elapsedInput = form.querySelector("[data-elapsed-seconds]");
        const timerContainer = form.querySelector("[data-test-timer]");

        if (!timerDisplay || !elapsedInput || !timerContainer) return;

        const durationSeconds = parseInt(timerContainer.dataset.durationSeconds || 120 * 60, 10);
        const startTime = Date.now();
        let rafId = null;
        let lastTick = -1;
        let isSubmitted = false;

        function updateTimer() {
            if (isSubmitted) return;
            const now = Date.now();
            const elapsedMs = now - startTime;
            const elapsedSeconds = Math.floor(elapsedMs / 1000);
            const remainingSeconds = Math.max(0, durationSeconds - elapsedSeconds);

            if (remainingSeconds !== lastTick) {
                lastTick = remainingSeconds;
                elapsedInput.value = elapsedSeconds;

                const hours = Math.floor(remainingSeconds / 3600);
                const minutes = Math.floor((remainingSeconds % 3600) / 60);
                const seconds = remainingSeconds % 60;

                if (hours > 0) {
                    timerDisplay.textContent =
                        hours.toString().padStart(2, "0") + ":" +
                        minutes.toString().padStart(2, "0") + ":" +
                        seconds.toString().padStart(2, "0");
                } else {
                    timerDisplay.textContent =
                        minutes.toString().padStart(2, "0") + ":" +
                        seconds.toString().padStart(2, "0");
                }

                if (remainingSeconds <= 0) {
                    isSubmitted = true;
                    alert("Time is up! Your test will be submitted automatically.");
                    if (timerContainer) {
                        timerContainer.classList.add("timer-stopped");
                    }
                    form.submit();
                    if (rafId) {
                        cancelAnimationFrame(rafId);
                        rafId = null;
                    }
                    return;
                }
            }

            rafId = requestAnimationFrame(updateTimer);
        }

        /* Start the timer */
        updateTimer();

        /* Confirm before submitting */
        form.addEventListener("submit", (e) => {
            if (isSubmitted) return;
            const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
            if (elapsedSeconds < 30) {
                if (!confirm("Are you sure you want to submit? You have spent less than 30 seconds on this test.")) {
                    e.preventDefault();
                    return;
                }
            } else {
                if (!confirm("Are you sure you want to submit your test? You have " + timerDisplay.textContent + " remaining.")) {
                    e.preventDefault();
                    return;
                }
            }

            isSubmitted = true;
            /* User confirmed - stop the timer */
            if (timerContainer) {
                timerContainer.classList.add("timer-stopped");
            }
            if (rafId) {
                cancelAnimationFrame(rafId);
                rafId = null;
            }
        });

        /* Clean up if user navigates away */
        window.addEventListener("beforeunload", () => {
            if (rafId) {
                cancelAnimationFrame(rafId);
                rafId = null;
            }
        });
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeTestTimer);
} else {
    initializeTestTimer();
}
