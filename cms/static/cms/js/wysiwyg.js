window.uncms = window.uncms || {};

window.uncms.activateEditor = function(element) {
    // activateEditor activates a single text editor on the given element.

    // Generate base settings for TinyMCE & merge with per-editor settings
    // (normally global settings)
    const settings = {
        selector: "#" + element.getAttribute("id")
    };

    const extendedSettings = Object.assign(
        settings,
        JSON.parse(element.dataset.wysiwygSettings)
    );

    // Init editor
    window.tinymce.init(extendedSettings);
};

window.uncms.activateEditors = function() {
    for (const element of document.querySelectorAll(".wysiwyg")) {
        // Don't activate one that is not visible.
        if (element.getBoundingClientRect().top) {
            window.uncms.activateEditor(element);
        }
    }
};

window.addEventListener("load", function () {
    window.setTimeout(window.uncms.activateEditors, 100);
});
