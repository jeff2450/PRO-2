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

/* ── Timer / Stopwatch for Test Taking ── */
document.querySelectorAll("[data-test-form]").forEach((form) => {
    const timerDisplay = form.querySelector("[data-timer-display]");
    const elapsedInput = form.querySelector("[data-elapsed-seconds]");
    const timerContainer = form.querySelector("[data-test-timer]");

    if (!timerDisplay || !elapsedInput) return;

    let startTime = Date.now();
    let rafId = null;
    let lastTick = 0;

    function updateTimer() {
        const now = Date.now();
        const elapsedMs = now - startTime;
        const totalSeconds = Math.floor(elapsedMs / 1000);

        if (totalSeconds !== lastTick) {
            lastTick = totalSeconds;
            elapsedInput.value = totalSeconds;
            const hours = Math.floor(totalSeconds / 3600);
            const minutes = Math.floor((totalSeconds % 3600) / 60);
            const seconds = totalSeconds % 60;

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
        }

        rafId = requestAnimationFrame(updateTimer);
    }

    /* Start the timer */
    updateTimer();

    /* Confirm before submitting - warn if less than 30 seconds elapsed */
    form.addEventListener("submit", (e) => {
        const totalSeconds = lastTick;
        if (totalSeconds < 30) {
            if (!confirm("Are you sure you want to submit? You have spent less than 30 seconds on this test.")) {
                e.preventDefault();
                return;
            }
        } else {
            if (!confirm("Are you sure you want to submit your test? Your elapsed time is " + timerDisplay.textContent + ".")) {
                e.preventDefault();
                return;
            }
        }

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