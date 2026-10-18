const yearElement = document.getElementById("current-year");

if (yearElement) {
    yearElement.textContent = new Date().getFullYear();
}

document.querySelectorAll("[data-confirm]").forEach((button) => {
    button.addEventListener("click", (event) => {
        const message = button.dataset.confirm;

        if (!window.confirm(message)) {
            event.preventDefault();
        }
    });
});