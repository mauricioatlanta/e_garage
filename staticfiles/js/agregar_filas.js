document.addEventListener("DOMContentLoaded", function () {
    const addBtn = document.getElementById("add-detalle");
    const tableBody = document.querySelector("#detalles-table tbody");
    const totalForms = document.querySelector("#id_detalles-TOTAL_FORMS");
    const emptyFormTemplate = document.querySelector("#empty-form-row").innerHTML;

    if (addBtn && tableBody && totalForms) {
        addBtn.addEventListener("click", function () {
            const formIndex = parseInt(totalForms.value);
            const newRowHtml = emptyFormTemplate.replace(/__prefix__/g, formIndex);

            const tempContainer = document.createElement("tbody");
            tempContainer.innerHTML = newRowHtml;

            const newRow = tempContainer.querySelector("tr");
            tableBody.appendChild(newRow);
            totalForms.value = formIndex + 1;
        });
    }
});
