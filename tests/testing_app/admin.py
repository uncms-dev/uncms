from django.contrib import admin

from tests.testing_app.models import (
    InlineModel,
    InlineModelNoPage,
    InlineWithFkNameModel,
    InlineWithMultipleFkModel,
    PageBaseModel,
    UsageContentBaseModelInline,
    UsageModelOne,
    UsageModelOneInline,
    UsageModelTwo,
)
from uncms.admin import PageBaseAdmin
from uncms.pages.admin import page_admin


# Test-only model admins
class InlineModelNoPageInline(admin.StackedInline):
    model = InlineModelNoPage


class InlineModelInline(admin.StackedInline):
    model = InlineModel


@admin.register(PageBaseModel)
class RealPageBaseAdmin(PageBaseAdmin):
    pass


class UsageContentBaseModelInlineAdmin(admin.StackedInline):
    model = UsageContentBaseModelInline


page_admin.register_content_inline(
    UsageContentBaseModelInline, UsageContentBaseModelInlineAdmin
)


class UsageModelOneInlineAdmin(admin.StackedInline):
    model = UsageModelOneInline


class InlineWithFkNameInline(admin.StackedInline):
    model = InlineWithFkNameModel
    fk_name = "not_registered_parent"


class InlineWithMultipleFkInline(admin.StackedInline):
    model = InlineWithMultipleFkModel


@admin.register(UsageModelOne)
class UsageModelOneAdmin(admin.ModelAdmin):
    inlines = [UsageModelOneInlineAdmin, InlineWithMultipleFkInline]


@admin.register(UsageModelTwo)
class UsageModelTwoAdmin(admin.ModelAdmin):
    pass
