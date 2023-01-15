window.uncms = window.uncms || {};

window.uncms.activateEditor = function(element) {
    // activateEditor activates a single text editor on the given element.

    // Generate base settings for Trumbowyg & merge with per-editor settings
    // (normally global settings)

    const settings = JSON.parse(element.dataset.wysiwygSettings);

    settings.plugins = settings.plugins || {};
    settings.plugins.upload = settings.plugins.upload || {};
    settings.plugins.upload = {
        serverPath: element.dataset.wysiwygUploadUrl,
        // If someone has defined this in their UnCMS config, allow them to
        // override it this way.
        ...settings.plugins.upload,
    }
    console.log(settings)

    // Init editor
    window.django.jQuery(element).trumbowyg(settings);
};

window.uncms.activateEditors = function(parentElement) {
    for (const element of (parentElement || document).querySelectorAll(".wysiwyg")) {
        // Don't activate one that is not visible.
        if (element.getBoundingClientRect().top) {
            window.uncms.activateEditor(element);
        }
    }
};

window.addEventListener("load", function () {
    window.setTimeout(window.uncms.activateEditors, 100);

    // Handle new editors being created in inlines.
    //
    // There is no way at all, as far as I can see, to handle the
    // formset:added event without resorting to jQuery. :(
    if (window.django && window.django.jQuery) {
      window.django.jQuery(document).on("formset:added", (function(ev, jElement) {
          window.uncms.activateEditors(jElement[0]);
      }));
    }
});
