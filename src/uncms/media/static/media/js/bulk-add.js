(function () {
    const bulkUpload = document.querySelector(".bulk-upload");
    const dropzone = document.querySelector(".bulk-upload__dropzone");
    const fileInput = document.querySelector("#id_files");
    const fileList = document.querySelector(".bulk-upload__file-list");
    const template = document.querySelector("#bulk-upload-file-template");

    if (!bulkUpload || !dropzone || !fileInput || !fileList || !template) {
        return;
    }

    const uploadUrl = bulkUpload.dataset.uploadUrl;
    if (!uploadUrl) {
        console.error("Upload URL not found"); // oxlint-disable-line no-console
        return;
    }

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]");
    if (!csrfToken) {
        console.error("CSRF token not found"); // oxlint-disable-line no-console
        return;
    }

    const uploadQueue = [];
    let activeUploads = 0;
    const maxConcurrentUploads = 2;

    function createFileItem(file) {
        const clone = template.content.cloneNode(true);
        const item = clone.querySelector(".bulk-upload__file-item");
        const nameEl = clone.querySelector(".bulk-upload__file-name");
        const sizeEl = clone.querySelector(".bulk-upload__file-size");
        const thumbnail = clone.querySelector(".bulk-upload__file-thumbnail");
        const editLink = clone.querySelector(".bulk-upload__file-edit");
        const cancelBtn = clone.querySelector(".bulk-upload__file-cancel");
        const progress = clone.querySelector(".bulk-upload__file-progress");
        const statusEl = clone.querySelector(".bulk-upload__file-status");

        nameEl.textContent = file.name;
        sizeEl.textContent = "";
        item.dataset.fileName = file.name;

        fileList.insertBefore(clone, fileList.firstChild);

        const elements = {
            item: item,
            progress: progress,
            thumbnail: thumbnail,
            editLink: editLink,
            cancelBtn: cancelBtn,
            nameEl: nameEl,
            sizeEl: sizeEl,
            statusEl: statusEl,
        };

        let abortController = null;

        cancelBtn.addEventListener("click", () => {
            if (abortController) {
                abortController.abort();
            }
            item.remove();
        });

        return {
            elements: elements,
            setAbortController: function (controller) {
                abortController = controller;
            },
        };
    }

    function scrollItemIntoView(item) {
        const rect = fileList.getBoundingClientRect();
        const visibleHeight = Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0);

        if (visibleHeight < 100) {
            item.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
    }

    function showUploadSuccess(elements, data) {
        elements.nameEl.textContent = "✓ " + data.name;
        elements.sizeEl.textContent = data.sizeFormatted;

        if (data.adminUrl) {
            elements.editLink.href = data.adminUrl;
            elements.editLink.hidden = false;
        }

        if (data.thumbnail) {
            const img = document.createElement("img");
            img.src = data.thumbnail;
            img.alt = data.name;
            img.className = "bulk-upload__file-thumbnail bulk-upload__file-thumbnail--image";
            elements.thumbnail.replaceWith(img);
        }

        elements.progress.hidden = true;
        elements.cancelBtn.hidden = true;
        elements.item.classList.add("bulk-upload__file-item--complete");
    }

    function showUploadError(elements, errorMessage) {
        elements.statusEl.textContent = errorMessage;
        elements.statusEl.classList.add("bulk-upload__file-status--error");
        elements.statusEl.hidden = false;
        elements.progress.hidden = true;
        elements.cancelBtn.hidden = true;
        elements.item.classList.add("bulk-upload__file-item--error");
    }

    function showUploadInProgress(elements) {
        elements.statusEl.hidden = true;
        elements.progress.hidden = false;
        elements.progress.value = 0;
        elements.item.classList.remove("bulk-upload__file-item--queued");
    }

    function showQueued(elements) {
        elements.statusEl.textContent = "Queued";
        elements.statusEl.hidden = false;
        elements.progress.hidden = true;
        elements.item.classList.add("bulk-upload__file-item--queued");
    }

    function uploadFile(file, fileItem) {
        const elements = fileItem.elements;
        const setAbortController = fileItem.setAbortController;

        scrollItemIntoView(elements.item);
        showUploadInProgress(elements);

        if (!file || !file.name) {
            showUploadError(elements, "Invalid file");
            return Promise.resolve();
        }

        return file
            .slice(0, 1)
            .arrayBuffer()
            .then(function () {
                const formData = new FormData();
                formData.append("file", file);

                return new Promise((resolve) => {
                    // Use XMLHttpRequest instead of fetch because fetch does
                    // not support upload progress events.
                    const xhr = new XMLHttpRequest();

                    const abortController = {
                        abort: () => xhr.abort(),
                    };
                    setAbortController(abortController);

                    xhr.upload.addEventListener("progress", (e) => {
                        if (e.lengthComputable) {
                            const percentComplete = (e.loaded / e.total) * 100;
                            elements.progress.value = percentComplete;
                        }
                    });

                    xhr.addEventListener("load", () => {
                        if (xhr.status >= 200 && xhr.status < 300) {
                            try {
                                const data = JSON.parse(xhr.responseText);
                                showUploadSuccess(elements, data);
                                resolve();
                            } catch (error) {
                                console.error("Failed to parse upload response:", error); // oxlint-disable-line no-console
                                showUploadError(elements, "Invalid response");
                                resolve();
                            }
                        } else {
                            try {
                                const data = JSON.parse(xhr.responseText);
                                showUploadError(elements, data.error || "Upload failed");
                            } catch {
                                showUploadError(elements, "Upload failed");
                            }
                            resolve();
                        }
                    });

                    xhr.addEventListener("error", () => {
                        showUploadError(elements, "Upload failed");
                        resolve();
                    });

                    xhr.addEventListener("abort", () => {
                        resolve();
                    });

                    xhr.open("POST", uploadUrl);
                    xhr.setRequestHeader("X-CSRFToken", csrfToken.value);
                    xhr.send(formData);
                });
            })
            .catch(function () {
                showUploadError(elements, "Cannot read file");
            });
    }

    function processQueue() {
        while (activeUploads < maxConcurrentUploads && uploadQueue.length > 0) {
            const queueItem = uploadQueue.shift();
            activeUploads += 1;

            uploadFile(queueItem.file, queueItem.fileItem).finally(() => {
                activeUploads -= 1;
                processQueue();
            });
        }
    }

    function handleFiles(files) {
        for (const file of files) {
            // oxlint-disable-next-line no-undefined
            if (!file || file.size === undefined) {
                continue;
            }

            const fileItem = createFileItem(file);
            showQueued(fileItem.elements);
            uploadQueue.push({ file: file, fileItem: fileItem });
        }

        processQueue();
        fileInput.value = "";
    }

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFiles(e.target.files);
        }
    });

    bulkUpload.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("bulk-upload__dropzone--dragover");
    });

    bulkUpload.addEventListener("dragleave", (e) => {
        e.preventDefault();
        dropzone.classList.remove("bulk-upload__dropzone--dragover");
    });

    bulkUpload.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("bulk-upload__dropzone--dragover");

        if (e.dataTransfer.files.length > 0) {
            handleFiles(e.dataTransfer.files);
        }
    });
})();
