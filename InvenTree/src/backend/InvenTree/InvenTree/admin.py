"""Admin classes."""

from django.contrib import admin
from django.http.request import HttpRequest

from djmoney.contrib.exchange.admin import RateAdmin
from djmoney.contrib.exchange.models import Rate

# <!-- AGENT GENERATED CODE: ADMIN DOCUMENTATION TOOLS -->
from InvenTree.documentation import (
    ChangeRequest,
    Requirement,
    RequirementCategory,
    RequirementDocument,
    TestCase,
    TestRun,
)


class CustomRateAdmin(RateAdmin):
    """Admin interface for the Rate class."""

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable the 'add' permission for Rate objects."""
        return False


@admin.register(RequirementCategory)
class RequirementCategoryAdmin(admin.ModelAdmin):
    """Admin interface for the RequirementCategory model."""

    list_display = ('name', 'description', 'default_importance', 'parent')
    search_fields = ('name', 'description')
    list_filter = ('default_importance',)
    autocomplete_fields = ('parent',)


@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    """Admin interface for the Requirement model."""

    list_display = (
        'reference',
        'name',
        'category',
        'importance',
        'status',
        'source',
        'creation_date',
        'verification_date',
    )
    list_filter = ('status', 'importance', 'category', 'creation_date', 'verification_date')
    search_fields = ('reference', 'name', 'description', 'source')
    date_hierarchy = 'creation_date'
    autocomplete_fields = ('category', 'created_by', 'verified_by')
    readonly_fields = ('creation_date',)


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    """Admin interface for the TestCase model."""

    list_display = (
        'reference',
        'name',
        'is_automated',
        'created_by',
        'creation_date',
    )
    list_filter = ('is_automated', 'creation_date', 'update_date')
    search_fields = ('reference', 'name', 'description')
    date_hierarchy = 'creation_date'
    filter_horizontal = ('requirements',)
    autocomplete_fields = ('created_by', 'updated_by')
    readonly_fields = ('creation_date', 'update_date')


@admin.register(TestRun)
class TestRunAdmin(admin.ModelAdmin):
    """Admin interface for the TestRun model."""

    list_display = (
        'test_case',
        'run_by',
        'run_date',
        'status',
    )
    list_filter = ('status', 'run_date')
    search_fields = ('test_case__reference', 'test_case__name', 'outcome')
    date_hierarchy = 'run_date'
    autocomplete_fields = ('test_case', 'run_by')
    readonly_fields = ('run_date',)


@admin.register(ChangeRequest)
class ChangeRequestAdmin(admin.ModelAdmin):
    """Admin interface for the ChangeRequest model."""

    list_display = (
        'reference',
        'title',
        'status',
        'priority',
        'created_by',
        'creation_date',
        'assigned_to',
    )
    list_filter = ('status', 'priority', 'impact', 'risk', 'creation_date')
    search_fields = ('reference', 'title', 'description')
    date_hierarchy = 'creation_date'
    filter_horizontal = ('requirements', 'test_cases')
    autocomplete_fields = (
        'created_by',
        'assigned_to',
        'approved_by',
        'implemented_by',
        'verified_by',
    )
    readonly_fields = ('creation_date',)


@admin.register(RequirementDocument)
class RequirementDocumentAdmin(admin.ModelAdmin):
    """Admin interface for the RequirementDocument model."""

    list_display = (
        'title',
        'document_type',
        'reference',
        'revision',
        'upload_date',
        'uploaded_by',
    )
    list_filter = ('document_type', 'upload_date')
    search_fields = ('title', 'reference', 'description')
    date_hierarchy = 'upload_date'
    autocomplete_fields = ('uploaded_by',)
    readonly_fields = ('upload_date',)


admin.site.unregister(Rate)
admin.site.register(Rate, CustomRateAdmin)