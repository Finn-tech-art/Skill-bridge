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

document.addEventListener("DOMContentLoaded", () => {
    syncDirectSwapFields();
});
