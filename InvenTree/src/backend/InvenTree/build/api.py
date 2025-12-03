"""JSON API for the Build app."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db.models import F, Q
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as rest_filters
from drf_spectacular.utils import extend_schema, extend_schema_field
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

import build.serializers
import common.models
import part.models as part_models
import stock.models as stock_models
import stock.serializers
from build.kit import KitBuild, KitItem, KitStatus
from build.models import Build, BuildItem, BuildLine
from build.status_codes import BuildStatus, BuildStatusGroups
from data_exporter.mixins import DataExportViewMixin
from generic.states.api import StatusView
from InvenTree.api import BulkDeleteMixin, MetadataView
from InvenTree.filters import (
    SEARCH_ORDER_FILTER_ALIAS,
    InvenTreeDateFilter,
    NumberOrNullFilter,
)
from InvenTree.helpers import str2bool
from InvenTree.mixins import CreateAPI, ListCreateAPI, RetrieveUpdateDestroyAPI
from users.models import Owner


class BuildFilter(rest_filters.FilterSet):
    """Custom filterset for BuildList API endpoint."""

    class Meta:
        """Metaclass options."""

        model = Build
        fields = ['issued_by', 'sales_order', 'external']

    status = rest_filters.NumberFilter(label=_('Order Status'), method='filter_status')

    def filter_status(self, queryset, name, value):
        """Filter by integer status code.

        Note: Also account for the possibility of a custom status code
        """
        q1 = Q(status=value, status_custom_key__isnull=True)
        q2 = Q(status_custom_key=value)

        return queryset.filter(q1 | q2).distinct()

    active = rest_filters.BooleanFilter(label='Build is active', method='filter_active')

    # 'outstanding' is an alias for 'active' here
    outstanding = rest_filters.BooleanFilter(
        label='Build is outstanding', method='filter_active'
    )

    def filter_active(self, queryset, name, value):
        """Filter the queryset to either include or exclude orders which are active."""
        if str2bool(value):
            return queryset.filter(status__in=BuildStatusGroups.ACTIVE_CODES)
        return queryset.exclude(status__in=BuildStatusGroups.ACTIVE_CODES)

    parent = rest_filters.ModelChoiceFilter(
        queryset=Build.objects.all(), label=_('Parent Build'), field_name='parent'
    )

    include_variants = rest_filters.BooleanFilter(
        label=_('Include Variants'), method='filter_include_variants'
    )

    def filter_include_variants(self, queryset, name, value):
        """Filter by whether or not to include variants of the selected part.

        Note:
        - This filter does nothing by itself, and requires the 'part' filter to be set.
        - Refer to the 'filter_part' method for more information.
        """
        return queryset

    part = rest_filters.ModelChoiceFilter(
        queryset=part_models.Part.objects.all(),
        field_name='part',
        method='filter_part',
        label=_('Part'),
    )

    def filter_part(self, queryset, name, part):
        """Filter by 'part' which is being built.

        Note:
        - If "include_variants" is True, include all variants of the selected part.
        - Otherwise, just filter by the selected part.
        """
        if str2bool(self.request.query_params.get('include_variants', False)):
            # Include all variants of the selected part
            variant_ids = part.get_descendants(include_self=True).values('pk')
            return queryset.filter(part__pk__in=variant_ids)

        return queryset.filter(part=part)

    project_code = rest_filters.ModelChoiceFilter(
        queryset=common.models.ProjectCode.objects.all(),
        label=_('Project Code'),
    )

    has_project_code = rest_filters.BooleanFilter(
        field_name='project_code',
        label=_('Has project code'),
        lookup_expr='isnull',
        exclude=True,
    )

    completed = rest_filters.DateFromToRangeFilter(
        label=_('Completed'), field_name='completion_date'
    )

    required_by = rest_filters.DateFromToRangeFilter(
        label=_('Required by'), field_name='target_date'
    )

    responsible = rest_filters.ModelChoiceFilter(
        queryset=Owner.objects.all(),
        label=_('Responsible'),
    )

    assigned_to_me = rest_filters.BooleanFilter(label=_('Assigned to me'), method='filter_assigned_to_me')

    def filter_assigned_to_me(self, queryset, name, value):
        """Filter by orders which are assigned to the current user."""
        value = str2bool(value)

        # Work out who "me" is!
        owners = Owner.get_owners_matching_user(self.request.user)

        if value:
            return queryset.filter(responsible__in=owners)
        return queryset.exclude(responsible__in=owners)

    overdue = rest_filters.BooleanFilter(label=_('Overdue'), method='filter_overdue')

    def filter_overdue(self, queryset, name, value):
        """Filter by whether the build is 'overdue' or not."""
        value = str2bool(value)

        if value:
            return queryset.filter(Build.OVERDUE_FILTER)
        return queryset.exclude(Build.OVERDUE_FILTER)

    created = InvenTreeDateFilter(
        label=_('Created date'),
    )

    search = rest_filters.CharFilter(label=_('Search'), method='filter_search')

    def filter_search(self, queryset, name, value):
        """Custom search filter for the BuildList endpoint."""
        search_terms = value.strip().split()

        if not search_terms:
            return queryset

        search_fields = [
            'reference',
            'title',
            'part__name',
            'part__description',
            'part__IPN',
        ]

        search_query = build.serializers.build_search_query(search_fields, search_terms)
        queryset = queryset.filter(search_query)

        return queryset


# <!-- AGENT GENERATED CODE: KIT API INTEGRATION -->

class KitBuildFilter(rest_filters.FilterSet):
    """Custom filterset for KitBuild API endpoint."""

    class Meta:
        """Metaclass options."""

        model = KitBuild
        fields = ['build', 'part']

    status = rest_filters.NumberFilter(label=_('Kit Status'), method='filter_status')

    def filter_status(self, queryset, name, value):
        """Filter by integer status code."""
        return queryset.filter(status=value)

    completed = rest_filters.BooleanFilter(label=_('Completed'), method='filter_completed')

    def filter_completed(self, queryset, name, value):
        """Filter by whether the kit is completed or not."""
        if str2bool(value):
            return queryset.filter(status=KitStatus.COMPLETE)
        return queryset.exclude(status=KitStatus.COMPLETE)

    search = rest_filters.CharFilter(label=_('Search'), method='filter_search')

    def filter_search(self, queryset, name, value):
        """Custom search filter for the KitBuild endpoint."""
        search_terms = value.strip().split()

        if not search_terms:
            return queryset

        search_fields = [
            'reference',
            'title',
            'build__reference',
            'part__name',
            'part__description',
        ]

        queries = []

        for term in search_terms:
            query = None

            for field in search_fields:
                if query:
                    query |= Q(**{f"{field}__icontains": term})
                else:
                    query = Q(**{f"{field}__icontains": term})

            if query:
                queries.append(query)

        if queries:
            import functools
            query = functools.reduce(lambda x, y: x & y, queries)
            queryset = queryset.filter(query)

        return queryset


class KitItemFilter(rest_filters.FilterSet):
    """Custom filterset for KitItem API endpoint."""

    class Meta:
        """Metaclass options."""

        model = KitItem
        fields = ['kit', 'bom_item', 'stock_item', 'completed']

    part = rest_filters.ModelChoiceFilter(
        queryset=part_models.Part.objects.all(),
        label=_('Part'),
        method='filter_part',
    )

    def filter_part(self, queryset, name, value):
        """Filter by the part associated with this KitItem."""
        return queryset.filter(bom_item__sub_part=value)


class KitBuildSerializer(serializers.ModelSerializer):
    """Serializer for the KitBuild model."""

    status_text = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        """Metaclass options."""

        model = KitBuild
        fields = [
            'pk',
            'build',
            'part',
            'reference',
            'title',
            'quantity',
            'batch',
            'target_date',
            'completion_date',
            'status',
            'status_text',
            'completed_by',
            'link',
            'notes',
        ]

    def validate(self, data):
        """Perform validation on the KitBuild data."""
        # If part not specified, use the build part
        if 'part' not in data and 'build' in data:
            data['part'] = data['build'].part

        return data


class KitItemSerializer(serializers.ModelSerializer):
    """Serializer for the KitItem model."""

    part = serializers.PrimaryKeyRelatedField(
        source='bom_item.sub_part',
        read_only=True,
    )

    part_detail = part_models.PartSerializer(
        source='bom_item.sub_part',
        read_only=True,
        many=False,
    )

    class Meta:
        """Metaclass options."""

        model = KitItem
        fields = [
            'pk',
            'kit',
            'bom_item',
            'stock_item',
            'quantity',
            'install_into',
            'part',
            'part_detail',
            'completed',
            'notes',
        ]


class KitBuildList(ListCreateAPI):
    """API endpoint for accessing a list of KitBuild objects.

    - GET: Return a list of all KitBuild objects
    - POST: Create a new KitBuild object
    """

    queryset = KitBuild.objects.all()
    serializer_class = KitBuildSerializer
    filterset_class = KitBuildFilter

    def create(self, request, *args, **kwargs):
        """Create a new KitBuild object."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class KitBuildDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a single KitBuild object."""

    queryset = KitBuild.objects.all()
    serializer_class = KitBuildSerializer


class KitBuildComplete(CreateAPI):
    """API endpoint for completing a KitBuild."""

    queryset = KitBuild.objects.all()

    def get_serializer_class(self):
        """Return the appropriate serializer for this endpoint."""
        return KitBuildSerializer

    def create(self, request, *args, **kwargs):
        """Complete a KitBuild."""
        kit = self.get_object()

        if kit.is_complete:
            raise ValidationError({'status': _('Kit has already been completed')})

        kit.complete(request.user)

        serializer = self.get_serializer(kit)
        return Response(serializer.data)


class KitItemList(ListCreateAPI):
    """API endpoint for accessing a list of KitItem objects.

    - GET: Return a list of all KitItem objects
    - POST: Create a new KitItem object
    """

    queryset = KitItem.objects.all()
    serializer_class = KitItemSerializer
    filterset_class = KitItemFilter

    def create(self, request, *args, **kwargs):
        """Create a new KitItem object."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class KitItemDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a single KitItem object."""

    queryset = KitItem.objects.all()
    serializer_class = KitItemSerializer


class KitItemAllocate(CreateAPI):
    """API endpoint for allocating stock to a KitItem."""

    queryset = KitItem.objects.all()

    def get_serializer_class(self):
        """Return the appropriate serializer for this endpoint."""
        return KitItemSerializer

    def create(self, request, *args, **kwargs):
        """Allocate stock to a KitItem."""
        item = self.get_object()

        if item.is_allocated:
            raise ValidationError({'stock_item': _('KitItem has already been allocated')})

        stock_item_id = request.data.get('stock_item', None)

        stock_item = None

        if stock_item_id:
            try:
                stock_item = stock_models.StockItem.objects.get(pk=stock_item_id)
            except stock_models.StockItem.DoesNotExist:
                raise ValidationError({'stock_item': _('Stock item does not exist')})

        result = item.allocate(user=request.user, stock_item=stock_item)

        if not result:
            raise ValidationError({'stock_item': _('Failed to allocate stock item')})

        serializer = self.get_serializer(item)
        return Response(serializer.data)


class KitItemComplete(CreateAPI):
    """API endpoint for completing a KitItem."""

    queryset = KitItem.objects.all()

    def get_serializer_class(self):
        """Return the appropriate serializer for this endpoint."""
        return KitItemSerializer

    def create(self, request, *args, **kwargs):
        """Complete a KitItem."""
        item = self.get_object()

        if item.is_complete:
            raise ValidationError({'status': _('KitItem has already been completed')})

        if not item.is_allocated:
            raise ValidationError({'status': _('KitItem has not been allocated')})

        result = item.complete_allocation(user=request.user)

        if not result:
            raise ValidationError({'status': _('Failed to complete KitItem')})

        serializer = self.get_serializer(item)
        return Response(serializer.data)


build_api_urls = [
    # Base URL for build API endpoints
    path('', include([
        # Build order endpoints
        path(r'build/', include([
            # Build list
            path('', build.serializers.BuildList.as_view(), name='api-build-list'),
            
            path(r'status/', StatusView.as_view(), {
                'model': Build,
                'status_model_key': 'status',
                'custom_status_key': 'status_custom_key',
            }, name='api-build-status'),
            # Build detail
            path(r'<int:pk>/', include([
                path('', build.serializers.BuildDetail.as_view(), name='api-build-detail'),
                path('allocate/', build.serializers.BuildAllocate.as_view(), name='api-build-allocate'),
                path('auto-allocate/', build.serializers.BuildAutoAllocate.as_view(), name='api-build-auto-allocate'),
                path('complete/', build.serializers.BuildComplete.as_view(), name='api-build-complete'),
                path('cancel/', build.serializers.BuildCancel.as_view(), name='api-build-cancel'),
                path('create-output/', build.serializers.BuildOutputCreate.as_view(), name='api-build-output-create'),
                path('delete-output/', build.serializers.BuildOutputDelete.as_view(), name='api-build-output-delete'),
                path('scrap-output/', build.serializers.BuildOutputScrap.as_view(), name='api-build-output-scrap'),
                path('complete-output/', build.serializers.BuildOutputComplete.as_view(), name='api-build-output-complete'),
                path('metadata/', MetadataView.as_view(), {'model': Build}, name='api-build-metadata'),
                path('overdue/', build.serializers.BuildOverdue.as_view(), name='api-build-overdue'),
                path('unallocated/', build.serializers.BuildUnallocated.as_view(), name='api-build-unallocated'),
                path('allocated/', build.serializers.BuildAllocatedDetail.as_view(), name='api-build-allocated-detail'),
                path('output/', build.serializers.BuildOutputDetail.as_view(), name='api-build-output'),
            ])),
        ])),

        # Build item endpoints
        path(r'build-item/', include([
            path('', build.serializers.BuildItemList.as_view(), name='api-build-item-list'),
            path('<int:pk>/', include([
                path('', build.serializers.BuildItemDetail.as_view(), name='api-build-item-detail'),
                path('install/', build.serializers.BuildItemInstall.as_view(), name='api-build-item-install'),
                path('metadata/', MetadataView.as_view(), {'model': BuildItem}, name='api-build-item-metadata'),
            ])),
        ])),

        # Build line endpoints
        path(r'build-line/', include([
            path('', build.serializers.BuildLineList.as_view(), name='api-build-line-list'),
            path('<int:pk>/', include([
                path('', build.serializers.BuildLineDetail.as_view(), name='api-build-line-detail'),
                path('metadata/', MetadataView.as_view(), {'model': BuildLine}, name='api-build-line-metadata'),
            ])),
        ])),

        # Kit endpoints
        path(r'kit/', include([
            path('', KitBuildList.as_view(), name='api-kit-list'),
            path('<int:pk>/', include([
                path('', KitBuildDetail.as_view(), name='api-kit-detail'),
                path('complete/', KitBuildComplete.as_view(), name='api-kit-complete'),
                path('metadata/', MetadataView.as_view(), {'model': KitBuild}, name='api-kit-metadata'),
            ])),
        ])),

        # Kit item endpoints
        path(r'kit-item/', include([
            path('', KitItemList.as_view(), name='api-kit-item-list'),
            path('<int:pk>/', include([
                path('', KitItemDetail.as_view(), name='api-kit-item-detail'),
                path('allocate/', KitItemAllocate.as_view(), name='api-kit-item-allocate'),
                path('complete/', KitItemComplete.as_view(), name='api-kit-item-complete'),
                path('metadata/', MetadataView.as_view(), {'model': KitItem}, name='api-kit-item-metadata'),
            ])),
        ])),

    ])]
]