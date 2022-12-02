window.addEventListener('DOMContentLoaded', function () {
  const fileInput = document.getElementById('id_file');
  const titleInput = document.getElementById('id_title');
  fileInput.addEventListener('change', function (event) {
    const value = event.target.value;
    // Don't overwrite a title.
    if (titleInput.value || !value) {
      return
    }
    // Trim to just the filename, minus path.
    let filename = value.split(/(\\|\/)/g).pop();
    // Trim off the file extension.
    filename = filename.replace(/\.[^/.]+$/, '');
    if (filename) {
      titleInput.value = filename
    }
  });
});
