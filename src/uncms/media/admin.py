from functools import partial

from django.contrib import admin, messages
from django.contrib.admin.views.main import IS_POPUP_VAR
from django.http import (
    HttpResponseForbidden,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import filesizeformat
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from reversion.admin import VersionAdmin
from watson.admin import SearchAdmin

from uncms.admin import get_related_objects_admin_urls
from uncms.conf import defaults
from uncms.media.filetypes import IMAGE_DB_QUERY
from uncms.media.forms import FileForm, ImageEditForm, ImageUploadForm
from uncms.media.models import File, Label


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    '''Admin settings for Label models.'''

    list_display = ('name',)

    search_fields = ('name',)


class FileTypeFilter(admin.SimpleListFilter):
    """
    Permit filtering the media list to only show images.
    """
    parameter_name = 'filetype'
    title = 'file type'

    def lookups(self, request, model_admin):
        return (
            ('image', _('Images')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'image':
            return queryset.filter(IMAGE_DB_QUERY)
        return queryset


@admin.register(File)
class FileAdmin(VersionAdmin, SearchAdmin):
    '''Admin settings for File models.'''

    # override necessary for VersionAdmin
    change_list_template = 'admin/media/file/change_list.html'

    fieldsets = [
        (None, {
            'fields': ['title', 'file'],
        }),
        ('Media management', {
            'fields': ['attribution', 'copyright', 'alt_text', 'labels'],
        }),
    ]
    filter_horizontal = ['labels']
    form = FileForm
    list_display = ['get_preview', 'title', 'get_size', 'id']
    list_display_links = ['get_preview', 'title', 'get_size']
    list_filter = [FileTypeFilter, 'labels']
    readonly_fields = ['used_on']
    search_fields = ['title']

    def add_label_action(self, request, queryset, label):
        '''Adds the label on the given queryset.'''
        for obj in queryset:
            obj.labels.add(label)

    def remove_label_action(self, request, queryset, label):
        '''Removes the label on the given queryset.'''
        for obj in queryset:
            obj.labels.remove(label)

    def get_actions(self, request):
        '''Generates the actions for assigning categories.'''
        if IS_POPUP_VAR in request.GET:
            return []
        opts = self.model._meta
        verbose_name_plural = opts.verbose_name_plural
        actions = super().get_actions(request)
        # Add the dynamic labels.
        for label in Label.objects.all():
            # Add action.
            action_function = partial(self.__class__.add_label_action, label=label)
            action_description = 'Add label %s to selected %s' % (label.name, verbose_name_plural)
            action_name = action_description.lower().replace(' ', '_')
            actions[action_name] = (action_function, action_name, action_description)
            # Remove action.
            action_function = partial(self.__class__.remove_label_action, label=label)
            action_description = 'Remove label %s from selected %s' % (label.name, verbose_name_plural)
            action_name = action_description.lower().replace(' ', '_')
            actions[action_name] = (action_function, action_name, action_description)
        return actions

    def get_fieldsets(self, request, obj=None):
        """
        Only display the "usage" fieldset when changing an instance, not when
        creating a new file.
        """
        fieldsets = super().get_fieldsets(request, obj=obj)

        if obj is not None:
            fieldsets = fieldsets + [('Usage', {
                # This is the used_on function, not a field.
                'fields': ['used_on'],
            })]
        return fieldsets

    def get_form(self, request, obj=None, change=False, **kwargs):
        # Patch in the "user" argument required by FileForm.
        form = super().get_form(request, obj=obj, change=change, **kwargs)
        return partial(form, user=request.user)

    # Custom display routines.
    @admin.display(description='size')
    def get_size(self, obj):
        '''Returns the size of the media in a human-readable format.'''
        try:
            return filesizeformat(obj.file.size)
        except OSError:
            return '0 bytes'

    @admin.display(description='preview')
    def get_preview(self, obj):
        '''Generates a thumbnail of the image, falling back to an appropriate
        icon if it is not an image file or if thumbnailing fails.'''
        icon = obj.icon
        permalink = obj.get_temporary_url()
        if obj.is_image():
            thumbnail = obj.get_admin_thumbnail()
            return format_html(
                '<img class="uncms-thumbnail" uncms:permalink="{}" uncms:alt-text="{}" src="{}" width="{}" height="{}" alt="" title="{}"/>',
                permalink,
                obj.alt_text or "",
                thumbnail.url,
                thumbnail.width,
                thumbnail.height,
                obj.title
            )

        return format_html(
            '<img class="uncms-fallback-icon" uncms:permalink="{}" src="{}" width="56" height="66" alt="" title="{}"/>',
            permalink,
            icon,
            obj.title
        )

    def used_on(self, obj=None):
        return render_to_string('admin/media/includes/file_used_on.html', {
            'related_objects': [
                use for use in get_related_objects_admin_urls(obj)
                if use['admin_url'] is not None
            ],
        })

    def changelist_view(self, request, extra_context=None):
        '''Renders the change list.'''
        context = extra_context or {}

        context.setdefault('changelist_template_parent', 'reversion/change_list.html')
        context['fancy_grid_css'] = defaults.MEDIA_LIST_GRID_VIEW

        return super().changelist_view(request, context)

    def edit_view(self, request, object_id):
        if not self.has_change_permission(request):
            return HttpResponseForbidden('You do not have permission to modify this file.')
        obj = get_object_or_404(File, pk=object_id)
        assert obj.is_image()

        if request.method == 'GET':
            context = {
                'add': False,
                'change': True,
                'form': ImageEditForm(),
                'has_add_permission': self.has_add_permission(request),
                # checked above
                'has_change_permission': True,
                'has_delete_permission': self.has_delete_permission(request, obj),
                'has_editable_inline_admin_formsets': False,
                'has_view_permission': True,
                'media': self.media,
                'image_editor': True,
                'is_edit_view': True,
                'is_popup': False,
                'original': obj,
                'opts': self.model._meta,
                'save_as': False,
                'show_delete': False,
                'show_save_and_add_another': False,
                'show_save_and_continue': False,
                'title': f'Edit {str(obj)}',
            }
            return TemplateResponse(request, ['admin/media/file/image_editor.html'], context)
        form = ImageEditForm(request.POST, instance=obj)

        # The form can never be invalid - either it has data, or it does not.
        # Someone who has change permission could construct a form with
        # garbage image data, but if they wanted to upload a nonsense file
        # they could just use the standard upload form to do the same.
        assert form.is_valid()

        form.save()

        message = _('The image “{}” was edited successfully.')
        messages.success(request, format_html(message, str(obj)))
        return HttpResponseRedirect(reverse('admin:media_file_change', args=[obj.pk]))

    def get_urls(self):
        urls = super().get_urls()

        new_urls = [
            path('<int:object_id>/editor/', self.admin_site.admin_view(self.edit_view), name='media_file_edit'),
            path('upload-api/', self.admin_site.admin_view(self.image_upload_api_view), name='media_file_image_upload_api'),
            path('image-list-api/', self.admin_site.admin_view(self.image_list_api_view), name='media_file_image_list_api'),
        ]

        return new_urls + urls

    def image_list_api_view(self, request):
        if not self.has_view_permission(request):
            return HttpResponseForbidden('Forbidden')

        response = JsonResponse(
            [
                {
                    'title': obj.title,
                    'url': obj.get_temporary_url(),
                    'thumbnail': obj.get_admin_thumbnail().url,
                    'altText': obj.alt_text,
                }
                for obj in self.get_queryset(request).filter(IMAGE_DB_QUERY)
            ],
            safe=False,
        )
        return response

    def image_upload_api_view(self, request):
        if not self.has_add_permission(request):
            return HttpResponseForbidden(b'Forbidden')
        form = ImageUploadForm(data=request.POST, files=request.FILES, user=request.user)
        if not form.is_valid():
            # it'd make more sense to return a status code here, but the
            # Trumbowyg upload plugin just wants a success true/false key
            return JsonResponse({
                'success': False,
                'detail': form.errors.get_json_data(),
            })

        form.save()
        return JsonResponse({
            'success': True,
            'file': form.instance.get_temporary_url(),
        })
