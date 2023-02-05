/*
redirect-fields.js conditionally hides and shows the "test path" field when
"regular expression" is checked or unchecked.
*/
(function () {
    "use strict";
    window.addEventListener("DOMContentLoaded", function () {
        const checkboxField = document.getElementById("id_regular_expression");
        // The "regular expression" field is hidden if regular expression
        // redirects are disabled.
        if (!checkboxField) {
            return;
        }

        const testPathFieldRow = document.querySelector(".field-test_path");

        function checkboxChange(event) {
            testPathFieldRow.hidden = !checkboxField.checked;
            testPathFieldRow.querySelector("label").classList.toggle("required", checkboxField.checked);
        }

        checkboxField.addEventListener("change", checkboxChange);
        checkboxChange();
    });
})();
