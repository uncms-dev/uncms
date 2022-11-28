from django.contrib import admin

from tests.testing_app.models import (
    InlineModel,
    InlineModelNoPage,
    UsageContentBaseModelInline,
    UsageModelOne,
    UsageModelOneInline,
    UsageModelTwo,
)
from uncms.apps.pages.admin import page_admin


# Test-only model admins
class InlineModelNoPageInline(admin.StackedInline):
    model = InlineModelNoPage


class InlineModelInline(admin.StackedInline):
    model = InlineModel


class UsageContentBaseModelInlineAdmin(admin.StackedInline):
    model = UsageContentBaseModelInline


page_admin.register_content_inline(UsageContentBaseModelInline, UsageContentBaseModelInlineAdmin)


class UsageModelOneInlineAdmin(admin.StackedInline):
    model = UsageModelOneInline


@admin.register(UsageModelOne)
class UsageModelOneAdmin(admin.ModelAdmin):
    inlines = [UsageModelOneInlineAdmin]


@admin.register(UsageModelTwo)
class UsageModelTwoAdmin(admin.ModelAdmin):
    pass
