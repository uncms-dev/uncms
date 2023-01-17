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
                            );

                            modal.on("tbwconfirm", function () {
                                trumbowyg.closeModal();
                            });
                            modal.on("tbwcancel", function (e) {
                                trumbowyg.closeModal();
                            });

                            const fetchOptions = {
                                credentials: "include"
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
                                const gridElement = createElementShortcut('ul', {
                                    classes: [`${baseClass}__grid`]
                                })
                                gridElement.classList.add()
                                for (const item of items) {
                                    const imageElement = createElementShortcut('img', {
                                        classes: [`${baseClass}__item-image`],
                                        src: item.thumbnail,
                                        title: item.title,
                                        loading: 'lazy',
                                    });

                                    const itemElement = createElementShortcut('li', {classes: [`${baseClass}__item`]});
                                    itemElement.appendChild(imageElement)

                                    itemElement.addEventListener('click', function () {
                                        alert(item.url)
                                    })

                                    gridElement.append(itemElement)

                                    // Re-use our loading div for the list.
                                    mainElement.innerText = '';
                                    mainElement.classList.remove(loadingClass)
                                    mainElement.classList.add(baseClass)
                                    mainElement.appendChild(gridElement)
                                }
                            })
                        },
                        html: 'X'
                    })
                }
            }
        }
    });
})(window.jQuery);
