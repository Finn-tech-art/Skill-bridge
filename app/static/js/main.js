function syncDirectSwapFields() {
    document.querySelectorAll("[data-exchange-type-select]").forEach((select) => {
        const form = select.closest("form");
        const directSwapField = form.querySelector("[data-direct-swap-field]");
        const requesterSkillSelect = directSwapField?.querySelector("select");

        const updateState = () => {
            const isDirectSwap = select.value === "direct_swap";
            if (!directSwapField) {
                return;
            }

            directSwapField.hidden = !isDirectSwap;
            if (requesterSkillSelect) {
                requesterSkillSelect.required = isDirectSwap;
            }
        };

        select.addEventListener("change", updateState);
        updateState();
    });
}

function syncResetPasswordTokens() {
    const form = document.querySelector("[data-reset-password-form]");
    if (!form) {
        return;
    }

    const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
    const accessToken = params.get("access_token");
    const refreshToken = params.get("refresh_token");
    const status = document.querySelector("[data-reset-password-status]");

    if (accessToken && refreshToken) {
        form.querySelector('input[name="access_token"]').value = accessToken;
        form.querySelector('input[name="refresh_token"]').value = refreshToken;
        if (status) {
            status.textContent = "Recovery link verified. You can now set a new password.";
        }
        window.history.replaceState({}, document.title, window.location.pathname);
        return;
    }

    if (status) {
        status.textContent = "Open the reset link from your email on this page to continue.";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    syncDirectSwapFields();
    syncResetPasswordTokens();
});
