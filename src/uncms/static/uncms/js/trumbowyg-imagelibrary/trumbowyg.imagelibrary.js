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
                    /*
                    Shove our icon into the DOM so that the button, with its
                    default SVG xref to "#trumbowyg-<plugin>", can see it.
                    The official answer to "how to add an icon to a custom
                    plugin" is "make your own build of Trumbowyg":

                    https://github.com/Alex-D/Trumbowyg/issues/1119

                    Valid answer, but, ain't nobody got time for that!
                    */
                    if (!document.querySelector("#trumbowyg-imagelibrary")) {
                        const iconWrap = document.createElementNS("http://www.w3.org/2000/svg", "svg");
                        // this class is only here to allow CSS to hide it.
                        iconWrap.classList.add("trumbowyg-imagelibrary-icons");
                        // Icon by Remix Icon - https://remixicon.com/
                        iconWrap.innerHTML = `
                            <symbol id="trumbowyg-imagelibrary" viewBox="0 0 24 24">
                                <path d="m20 13-5 1a15 15 0 0 1 3 5h2v-6zm-4 6c-2-5-7-8-12-8v8h12zM4 9c4 0 7 1 10 4a11 11 0 0 1 6-2V3h1l1 1v16a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h3V1h2v4H4v4zm14-8v4h-8V3h6V1h2zm-1 9a2 2 0 1 1 0-3 2 2 0 0 1 0 3z"/>
                            </symbol>
                        `;
                        document.body.appendChild(iconWrap)
                    }

                    trumbowyg.o.plugins.imagelibrary = $.extend(true, {}, defaultOptions, trumbowyg.o.plugins.imagelibrary || {});

                    trumbowyg.addBtnDef("imagelibrary", {
                        // This is where all the interesting stuff is!
                        fn: function () {
                            const mainElement = document.createElement("div")
                            mainElement.classList.add(loadingClass);
                            mainElement.innerText = trumbowyg.lang.imagelibraryLoading;

                            const modal = trumbowyg.openModal(
                                trumbowyg.lang.imagelibraryModalTitle,
                                mainElement,
                                true,
                            );

                            // Note we only bind the "cancel" event and not
                            // the "confirm" event, because we delete the
                            // latter button later.
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
                                const gridElement = createElementShortcut("div", {
                                    classes: [`${baseClass}__grid`],
                                    tabindex: "0",
                                })

                                let firstItemElement = null;
                                for (const item of items) {
                                    const imageElement = createElementShortcut("img", {
                                        classes: [`${baseClass}__item-image`],
                                        src: item.thumbnail,
                                        title: item.title,
                                        // defer loading of off-screen images
                                        loading: "lazy",
                                    });

                                    // Using `<button>` gives us
                                    // click-on-enter for friendliness to
                                    // keyboard navigation.
                                    const itemElement = createElementShortcut("button", {
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
                                There's no way to get Trumbowyg to give us a
                                form with just the cancel button. But we don't
                                really want to re-implement the behaviour of
                                the button we *do* want, so just remove the
                                "Confirm" button.
                                */
                                document.querySelector(".trumbowyg-imagelibrary")
                                    .closest(".trumbowyg-modal-box")
                                    .querySelector(".trumbowyg-modal-submit")
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
