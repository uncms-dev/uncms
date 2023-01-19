(function($) {
    "use strict";
    function createElementShortcut (tagName, attributes) {
        // helper function to create element with attributes because the DOM
        // API is bad
        const element = document.createElement(tagName);

        if (attributes) {
            for (const [attribute, value] of Object.entries(attributes)) {
                if (attribute === "classes") {
                    for (const className of value) {
                        element.classList.add(className);
                    }
                } else {
                    element.setAttribute(attribute, value);
                }
            }
        }
        return element
    }

    const defaultOptions = {
        imageListApiUrl: "",
    }

    const baseClass = "trumbowyg-imagelibrary";
    const loadingClass = `${baseClass}-loader`;

    $.extend(true, $.trumbowyg, {
        langs: {
            en: {
                imagelibrary: "Insert image from library",
                imagelibraryModalTitle: "Image library",
                imagelibraryLoading: "Loading...",
                imageLibraryUpload: "Upload new image",
            }
        },

        plugins: {
            imagelibrary: {
                init: function (trumbowyg) {
                    trumbowyg.o.plugins.imagelibrary = $.extend(true, {}, defaultOptions, trumbowyg.o.plugins.imagelibrary || {});

                    trumbowyg.addBtnDef("imagelibrary", {
                        // This is where all the interesting stuff is!
                        fn: function () {
                            const mainElement = document.createElement('div')
                            mainElement.classList.add(loadingClass);
                            mainElement.innerText = trumbowyg.lang.imagelibraryLoading;

                            const modal = trumbowyg.openModal(
                                trumbowyg.lang.imagelibraryModalTitle,
                                mainElement,
                                true,
                            );

                            modal.on("tbwconfirm", function () {
                                trumbowyg.closeModal();
                            });
                            modal.on("tbwcancel", function (e) {
                                trumbowyg.closeModal();
                            });

                            const prefix = trumbowyg.o.prefix;

                            const fetchOptions = {
                                credentials: "include",
                            };

                            window.fetch(
                                trumbowyg.o.plugins.imagelibrary.imageListApiUrl,
                                fetchOptions,
                            ).then(async function (response) {
                                if (!response.ok) {
                                    loader.innerText = `Failed to fetch image list from ${trumbowyg.o.plugins.imagelibrary.imageListApiUrl}`;
                                    return;
                                }
                                const items = await response.json();
                                const gridElement = createElementShortcut('div', {
                                    classes: [`${baseClass}__grid`],
                                    tabindex: "0",
                                })

                                let firstItemElement = null;
                                for (const item of items) {
                                    const imageElement = createElementShortcut('img', {
                                        classes: [`${baseClass}__item-image`],
                                        src: item.thumbnail,
                                        title: item.title,
                                        loading: 'lazy',
                                    });

                                    // Using `<button>` gives us
                                    // click-on-enter
                                    const itemElement = createElementShortcut('button', {
                                        classes: [`${baseClass}__item`],
                                        type: 'button',
                                    });
                                    itemElement.appendChild(imageElement)

                                    // Insert the image when the item is clicked.
                                    itemElement.addEventListener("click", function (event) {
                                        event.preventDefault();
                                        trumbowyg.execCmd("insertImage", item.url, false, true);
                                        const $img = $("img[src='" + item.url + "']:not([alt])", trumbowyg.$box);
                                        $img.attr("alt", item.altText || "");
                                        trumbowyg.closeModal();
                                    })

                                    gridElement.append(itemElement);

                                    // We'll focus this when our list is built.
                                    firstItemElement = firstItemElement || itemElement;
                                }
                                // Re-use our loading div for the list.
                                mainElement.innerText = '';
                                mainElement.classList.remove(loadingClass);
                                mainElement.classList.add(baseClass);
                                mainElement.appendChild(gridElement);

                                if (firstItemElement) {
                                    firstItemElement.focus();
                                }
                                /*
                                There's no way to get the form with just the
                                cancel button. But we don't really want to
                                re-implement that behaviour, so just remove the
                                "Confirm" button.
                                */
                                document.querySelector('.trumbowyg-imagelibrary')
                                    .closest('.trumbowyg-modal-box')
                                    .querySelector('.trumbowyg-modal-submit')
                                    .remove();
                            });
                        },
                        text: trumbowyg.lang.imageLibrary,
                    })
                }
            }
        }
    });
})(window.jQuery);
