window.uncms = window.uncms || {};

window.uncms.activateEditor = function(element) {
    // activateEditor activates a single text editor on the given element.

    // These settings come from UNCMS['WYSIWYG_OPTIONS'].
    const settings = JSON.parse(element.dataset.wysiwygSettings);

    // We need a CSRF token. As we're being used in a Django form, we
    // definitely have a CSRF token somewhere on the page and hopefully under
    // this name.
    const csrfToken = document.querySelector("input[name='csrfmiddlewaretoken']").value

    settings.plugins = settings.plugins || {};
    settings.plugins.upload = settings.plugins.upload || {};
    settings.plugins.upload = {
        serverPath: element.dataset.wysiwygUploadUrl,
        fileFieldName: "file",
        headers: {
            "X-CSRFToken": csrfToken,
        },
        // If someone has defined this in their UnCMS config, allow this to
        // take precedence.
        ...settings.plugins.upload,
    }
    settings.plugins.imagelibrary = settings.plugins.imagelibrary || {};
    settings.plugins.imagelibrary = {
        imageListApiUrl: element.dataset.wysiwygImageListUrl,
        ...settings.plugins.imagelibrary,
    }

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
