/*
    TinyMCE filebrowser implementation.
*/


$(function() {
    
    // Get the important values from TinyMCE.
    var win = tinyMCEPopup.getWindowArg("window");
    var inputId = tinyMCEPopup.getWindowArg("input");
    
    // Get the input from the opening window.
    var input = $("#" + inputId, win.document);

    // Make the links clickable.
    $("div#changelist tr.row1 a, div#changelist tr.row2 a").click(function() {
        var img = $("img", this);
        var title = img.attr("title");
        var permalink = img.attr("cms:permalink");
        // Set the permalink.
        input.attr("value", permalink);
        // Set the link dialogue values.
        $("#linktitle", win.document).attr("value", title);
        // Set the image dialogue values.
        if (typeof(win.ImageDialog) != "undefined") {
            if (win.ImageDialog.getImageData) {
                win.ImageDialog.getImageData();
            }
            if (win.ImageDialog.showPreviewImage) {
                win.ImageDialog.showPreviewImage(permalink);
            }
            $("#alt", win.document).attr("value", title);
            $("#title", win.document).attr("value", title);
        }
        // Close the dialogue.
        tinyMCEPopup.close();
        return false;
    });
    
});
