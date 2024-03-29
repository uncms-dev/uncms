# The Media app

The media app provides file and image management to the Django admin.
It also integrates with UnCMS's WYSIWYG text editor to provide a file browser and image browser interface that allows images and files to be added directly into the editor.

## Adding the media app to your site

You will need to add `'uncms.media'` to your `INSTALLED_APPS`.
If you are using any of UnCMS's other features,
you would have done this already.

You will also need something like this in your root urlconf (note the namespace `media_library`):

```
from django.urls import include, path

urlpatterns = [
    # other URLs here...
    path('library/', include('uncms.media.urls', namespace='media_library')),
]

```

## Configuring allowed file types

By default, UnCMS will only allow files with image extensions to be uploaded in the admin,
unless a user has the "upload dangerous files" permission, in which case they can upload any file at all
(this permission is also implied by a user having the "superuser" flag).
You can change this behaviour with three configuration options:

* To add extra file types which should be allowed, change [`MEDIA_UPLOAD_ALLOWED_EXTENSIONS`](configuration.md?id=MEDIA_UPLOAD_ALLOWED_EXTENSIONS).
* To turn off the "always allow images" option, change [`MEDIA_UPLOAD_ALWAYS_ALLOW_IMAGES`](configuration.md?id=MEDIA_UPLOAD_ALWAYS_ALLOW_IMAGES).
* To turn off the "permissions can bypass file upload restrictions" behaviour, change [`MEDIA_UPLOAD_PERMISSIONS_BYPASS`](configuration.md?id=MEDIA_UPLOAD_PERMISSIONS_BYPASS).

Note that these restrictions only apply to files uploaded through the Django administration interface;
you will need to implement your own restrictions if you are allowing uploads to the media library from elsewhere.

## Models

### File

`uncms.media.models.File` is a wrapper around Django's FileField.
This allows users to upload a file in one place and use it in more than one place.

`File` is not intended for files uploaded via the public front-end of a website (i.e. non-staff users).
For this, you'll want to use a simpler Django `django.db.models.FileField` or `ImageField`.

The default `FileAdmin` adds a nice grid view, with a thumbnail preview, falling back to an appropriate icon for the file type if the file is not an image. You can disable the grid view with the `MEDIA_LIST_GRID_VIEW` [configuration option](configuration.md).

For images, there is an in-browser image editor that gives quick access to common image operations such as cropping and rotating.

The admin will show a list of all the places where an object is used in a "Usage" fieldset, with links (where possible) to their admin URLs.
It's smart enough to know about usage within inlines, both those registered to normal models and as inlines on [content models](pages-app.md).

When uploading images, an attempt is made to guard against a file being uploaded with an extension that does not match its contents.
For example, you won't be able to upload a PNG file with a `.jpg` extension, or vice-versa.
This helps to prevent exceptions being thrown while thumbnailing images on the front-end of the site.

#### Model fields

* `title`: A name for the file.
You should not display this to users of your site.
In the admin, this is prepopulated from the filename when first uploaded, if no title is provided by the user.
* `labels`: A `ManyToManyField` to `Label` (see below).
* `file`: A Django `FileField`, which is the file itself
* `alt_text`: Text that will be used to describe this image to screen readers.
You should leave this empty for purely decorative images.
This will be used as a fallback by the [image rendering](rendering-images.md) template function.
* `attribution`, `copyright` Additional metadata fields.
It is up to you how, or if, to render these on the front end of the site.

In addition, the following fields are present on the model, but are not user-visible and are automatically populated on save:

* `width` and `height`: The image dimensions of the file, if the file is an image.
* `date_added`: The time the file was first uploaded. This is used for ordering in the admin (most recent first).

#### Model methods & properties

* `contents`: A cached property which returns the contents of the file as a `bytes` object. This will return an empty bytes object (`b''`) in the case of I/O errors; thus, it should always be safe to use in templates.
* `get_dimensions()`: If the file is an image, returns a tuple of (width, height), otherwise returns 0.
This is only used internally; you probably want to access the `width` and `height` fields on the model instead, as they incur no overhead.
* `icon`: A cached property that returns the path to an appropriate icon for the file type, e.g. `/static/media/img/x-office-spreadsheet.png`. This is used as a fallback in the media list if a file is not an image.
* `is_image()`: Returns `True` if the file is an image (based on the file extension), `False` otherwise.
* `text_contents`: As `contents`, but decodes as UTF-8 and returns a string. Unicode errors are silently swallowed, and will cause an empty string to be returned; as with `contents`, this is intended to make it safe to use in templates where exceptions cannot be caught.

### Label

`uncms.media.models.Label` helps administrators organise media;
think of them as tags, or notes to self.
They are not intended to be shown to users on the front end of a website.

Label has only one field: a `title`, which is also used as the ordering field.

## Fields

Four useful fields in the media app make it easier to integrate the media module into your project.
You should probably use these any time you want to reference a File.

`uncms.media.fields.FileRefField` provides a widget which allows a user to select a file from the media library.
This is a simple subclass of Django's `ForeignKey` that uses Django's `ForeignKeyRawIdWidget` -
if you're anything like us, your media libraries can get large enough to make dropdowns unusable.

`uncms.media.fields.ImageRefField` has the same functionality as `FileRefField`, but files are filtered to only show images (based on the extension of the file).
This will also display a small preview of the image in the widget in the admin.

`uncms.media.fields.VideoFileRefField` has the same functionality as `FileRefField`, but the files are filtered to only show videos.

`uncms.media.files.RestrictedFileRefField` will allow you to implement your own `FileField` which will only permit files with certain file extensions; it is used to implement `VideoRefField` and `ImageRefField`.
You will want to override the `allowed_extensions` attribute in a subclass;
this is a list of file extensions, minus the leading dot.

For example, you may want behaviour similar to `ImageRefField` to allow known raster image file types for a field, but also allow SVGs. You could implement such a field like this:

```python
from uncms.media.fields import RestrictedFileRefField
from uncms.media.filetypes import IMAGE_FILE_EXTENSIONS


class ImageOrSVGRefField(RestrictedFileRefField):
    allowed_extensions = IMAGE_FILE_EXTENSIONS + ['svg']
```

## Next steps

Learn about [rendering images](rendering-images.md) from your library.
