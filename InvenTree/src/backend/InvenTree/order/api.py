"""JSON API for the Order app."""

from datetime import datetime
from decimal import Decimal
from typing import cast

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db.models import F, Q
from django.http.response import JsonResponse
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _

import rest_framework.serializers
from django_filters import rest_framework as rest_filters
from django_ical.views import ICalFeed
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_field
from rest_framework import status
from rest_framework.response import Response

import build.models
import common.models
import common.settings
import company.models
import stock.models as stock_models
import stock.serializers as stock_serializers
from data_exporter.mixins import DataExportViewMixin
from generic.states.api import StatusView
from InvenTree.api import BulkUpdateMixin, ListCreateDestroyAPIView, MetadataView
from InvenTree.filters import (
    SEARCH_ORDER_FILTER,
    SEARCH_ORDER_FILTER_ALIAS,
    InvenTreeDateFilter,
)
from InvenTree.helpers import str2bool
from InvenTree.helpers_model import construct_absolute_url, get_base_url
from InvenTree.mixins import CreateAPI, ListAPI, ListCreateAPI, RetrieveUpdateDestroyAPI
from InvenTree.permissions import InventoryActionPermission
from order import models, serializers
from order.status_codes import (
    PurchaseOrderStatus,
    PurchaseOrderStatusGroups,
    ReturnOrderLineStatus,
    ReturnOrderStatus,
    SalesOrderStatus,
    SalesOrderStatusGroups,
)
from part.models import Part
from users.models import Owner


class GeneralExtraLineList(DataExportViewMixin):
    """General template for ExtraLine API classes."""

    def get_serializer(self, *args, **kwargs):
        """Return the serializer instance for this endpoint."""
        try:
            params = self.request.query_params3

            kwargs['order_detail'] = str2bool(params.get('order_detail', False))
        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return super().get_serializer(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        """Return the annotated queryset for this endpoint."""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related('order')

        return queryset

    filter_backends = SEARCH_ORDER_FILTER

    ordering_fields = ['quantity', 'notes', 'reference']

    search_fields = ['quantity', 'notes', 'reference', 'description']

    filterset_fields = ['order']


class OrderCreateMixin:
    """Mixin class which handles order creation via API."""

    def create(self, request, *args, **kwargs):
        """Save user information on order creation."""
        serializer = self.get_serializer(data=self.clean_data(request.data))
        serializer.is_valid(raise_exception=True)

        item = serializer.save()
        item.created_by = request.user
        item.save()

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


# [AGENT GENERATED CODE - REQUIREMENT:EDIT_LINE_ITEMS]
class SalesOrderLineItemApprove(RetrieveUpdateDestroyAPI):
    """API endpoint for approving edits to a SalesOrderLineItem.
    
    This endpoint allows users with appropriate permissions to approve
    line item changes that require approval.
    """
    
    queryset = models.SalesOrderLineItem.objects.all()
    serializer_class = serializers.SalesOrderLineItemSerializer
    permission_classes = [InventoryActionPermission]
    
    # Specify the required permission for this endpoint
    inventory_action_permission = 'order.can_approve_sales_order_line_item'
    
    def perform_update(self, serializer):
        """Approve the line item edit."""
        instance = self.get_object()
        
        # Mark the line item as approved
        instance.approved = True
        instance.approved_by = self.request.user
        instance.approved_date = datetime.now().date()
        instance.save()
        
        return Response({'success': _('Line item edit approved')})


class SalesOrderLineItemList(ListCreateAPI):
    """API endpoint for viewing a list of SalesOrderLineItem objects.
    
    - GET: Return list of SalesOrderLineItem objects
    - POST: Create a new SalesOrderLineItem
    """
    
    queryset = models.SalesOrderLineItem.objects.all()
    serializer_class = serializers.SalesOrderLineItemSerializer
    
    def get_serializer(self, *args, **kwargs):
        """Return the serializer instance for this endpoint."""
        try:
            params = self.request.query_params
            
            kwargs['part_detail'] = str2bool(params.get('part_detail', False))
            kwargs['order_detail'] = str2bool(params.get('order_detail', False))
            
        except AttributeError:
            pass
        
        kwargs['context'] = self.get_serializer_context()
        
        return super().get_serializer(*args, **kwargs)
    
    filter_backends = SEARCH_ORDER_FILTER
    
    filterset_fields = [
        'order',
        'part',
    ]
    
    ordering_fields = [
        'reference',
        'part__name',
    ]
    
    search_fields = [
        'reference',
        'part__name',
        'part__description',
        'part__IPN',
        'notes',
    ]


class SalesOrderLineItemDetail(RetrieveUpdateDestroyAPI):
    """Detail API endpoint for SalesOrderLineItem object.
    
    - GET: Retrieve a single SalesOrderLineItem object
    - PATCH: Update a SalesOrderLineItem object
    - DELETE: Delete a SalesOrderLineItem object
    """
    
    queryset = models.SalesOrderLineItem.objects.all()
    serializer_class = serializers.SalesOrderLineItemSerializer
    
    def get_serializer(self, *args, **kwargs):
        """Return the serializer instance for this endpoint."""
        kwargs['context'] = self.get_serializer_context()
        
        return super().get_serializer(*args, **kwargs)
# [END AGENT GENERATED CODE]


class OrderAdjustMixin:
    """Mixin class for various order adjustment actions."""

    def perform_action(self, serializer, do_action, action_name):
        """Perform an 'action' against an order instance.

        Raises an appropriate error if the action fails.
        """
        instance = serializer.save()

        # Special case for PurchaseOrder objects
        if isinstance(instance, order.models.PurchaseOrder):
            order_model = 'order.purchaseorder'
        elif isinstance(instance, order.models.SalesOrder):
            order_model = 'order.salesorder'
        elif isinstance(instance, order.models.ReturnOrder):
            order_model = 'order.returnorder'

        else:
            order_model = 'unknown'

        fail = do_action(instance)

        result = {'order_id': instance.pk, 'success': fail is None}

        if fail is not None:
            result['details'] = fail

        # Add context data (if provided by the serializer)
        if hasattr(serializer, 'get_context_data'):
            result.update(serializer.get_context_data())

        return Response(result)


class OrderListMixin:
    """Mixin class for Order List API endpoints."""

    def list(self, request, *args, **kwargs):
        """Override the default 'list' behaviour,
        as the serializer does some fancy custom stuff.
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
        else:
            serializer = self.get_serializer(queryset, many=True)

        data = serializer.data

        if page is not None:
            return self.get_paginated_response(data)
        else:
            return Response(data)

    def get_serializer(self, *args, **kwargs):
        """Return the serializer instance for this endpoint."""
        try:
            params = self.request.query_params

            kwargs['customer_detail'] = str2bool(params.get('customer_detail', False))
            kwargs['supplier_detail'] = str2bool(params.get('supplier_detail', False))
        except AttributeError:
            pass

        return self.serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        """Extend serializer context data."""
        ctx = super().get_serializer_context()
        ctx['request'] = self.request

        return ctx


class PurchaseOrderFilter(rest_filters.FilterSet):
    """Custom API filters for the PurchaseOrderList endpoint."""

    class Meta:
        """Metaclass options."""

        model = order.models.PurchaseOrder
        fields = ['supplier', 'status']

    # Exact match for reference
    reference = rest_filters.CharFilter(
        label='Filter by exact reference', field_name='reference', lookup_expr='iexact'
    )

    # Partial match for reference
    reference_contains = rest_filters.CharFilter(
        label='Filter by partial reference',
        field_name='reference',
        lookup_expr='icontains',
    )

    # Exact match for supplier reference
    supplier_reference = rest_filters.CharFilter(
        label='Filter by exact supplier reference',
        field_name='supplier_reference',
        lookup_expr='iexact',
    )

    # Partial match for supplier reference
    supplier_reference_contains = rest_filters.CharFilter(
        label='Filter by partial supplier reference',
        field_name='supplier_reference',
        lookup_expr='icontains',
    )

    responsible = rest_filters.ModelChoiceFilter(
        label='Filter by responsible',
        field_name='responsible',
        queryset=Owner.get_owner_queryset(),
    )

    assigned_to_me = rest_filters.BooleanFilter(
        label='Filter by orders assigned to me',
        method='filter_assigned_to_me',
    )

    def filter_assigned_to_me(self, queryset, name, value):
        """Filter by orders which are assigned to the current user."""
        value = str2bool(value)

        # Work out who "me" is!
        owners = Owner.get_owners_matching_user(self.request.user)

        if value:
            return queryset.filter(responsible__in=owners)
        else:
            return queryset.exclude(responsible__in=owners)

    status = rest_filters.NumberFilter(label='Filter by status')

    outstanding = rest_filters.BooleanFilter(
        label='Outstanding', method='filter_outstanding'
    )

    overdue = rest_filters.BooleanFilter(label='Overdue', method='filter_overdue')

    outstanding = rest_filters.BooleanFilter(
        label='Outstanding', method='filter_outstanding'
    )

    # Overdue order filter
    def filter_overdue(self, queryset, name, value):
        """Filter by whether the order is 'overdue' or not."""
        value = str2bool(value)

        filter = order.models.PurchaseOrder.overdue_filter()

        if value:
            return queryset.filter(filter)
        else:
            return queryset.exclude(filter)

    def filter_outstanding(self, queryset, name, value):
        """Filter by 'outstanding' status."""
        value = str2bool(value)

        if value:
            return queryset.filter(status__in=PurchaseOrderStatusGroups.OPEN)
        else:
            return queryset.exclude(status__in=PurchaseOrderStatusGroups.OPEN)

    # Related to a particular supplier part
    supplier_part = rest_filters.ModelChoiceFilter(
        label='Filter by supplier part',
        queryset=company.models.SupplierPart.objects.all(),
        method='filter_by_supplier_part',
    )

    def filter_by_supplier_part(self, queryset, name, supplier_part):
        """Filter by 'supplier_part'"""
        return queryset.filter(lines__part=supplier_part).distinct()

    # Related to a particular part
    part = rest_filters.ModelChoiceFilter(
        label='Filter by part',
        queryset=Part.objects.all(),
        method='filter_by_part',
    )

    def filter_by_part(self, queryset, name, part):
        """Filter by 'part'"""
        return queryset.filter(lines__part__part=part).distinct()

    # Filter by date range
    min_creation_date = rest_filters.DateFilter(
        'creation_date', label='Min creation date', lookup_expr='gte'
    )

    max_creation_date = rest_filters.DateFilter(
        'creation_date', label='Max creation date', lookup_expr='lte'
    )

    created_by = rest_filters.CharFilter(
        label='Order created by', field_name='created_by__username', lookup_expr='iexact'
    )


class SalesOrderFilter(rest_filters.FilterSet):
    """Custom API filter for the SalesOrderList endpoint."""

    class Meta:
        """Metaclass options."""

        model = order.models.SalesOrder
        fields = ['customer', 'status']

    # Exact match for reference
    reference = rest_filters.CharFilter(
        label='Filter by exact reference', field_name='reference', lookup_expr='iexact'
    )

    # Partial match for reference
    reference_contains = rest_filters.CharFilter(
        label='Filter by partial reference',
        field_name='reference',
        lookup_expr='icontains',
    )

    # Exact match for customer reference
    customer_reference = rest_filters.CharFilter(
        label='Filter by exact customer reference',
        field_name='customer_reference',
        lookup_expr='iexact',
    )

    # Partial match for customer reference
    customer_reference_contains = rest_filters.CharFilter(
        label='Filter by partial customer reference',
        field_name='customer_reference',
        lookup_expr='icontains',
    )

    responsible = rest_filters.ModelChoiceFilter(
        label='Filter by responsible',
        field_name='responsible',
        queryset=Owner.get_owner_queryset(),
    )

    assigned_to_me = rest_filters.BooleanFilter(
        label='Filter by orders assigned to me',
        method='filter_assigned_to_me',
    )

    def filter_assigned_to_me(self, queryset, name, value):
        """Filter by orders which are assigned to the current user."""
        value = str2bool(value)

        # Work out who "me" is!
        owners = Owner.get_owners_matching_user(self.request.user)

        if value:
            return queryset.filter(responsible__in=owners)
        else:
            return queryset.exclude(responsible__in=owners)

    status = rest_filters.NumberFilter(label='Filter by status')

    outstanding = rest_filters.BooleanFilter(
        label='Outstanding', method='filter_outstanding'
    )

    overdue = rest_filters.BooleanFilter(label='Overdue', method='filter_overdue')

    # Overdue order filter
    def filter_overdue(self, queryset, name, value):
        """Filter by whether the order is 'overdue' or not."""
        value = str2bool(value)

        filter = order.models.SalesOrder.overdue_filter()

        if value:
            return queryset.filter(filter)
        else:
            return queryset.exclude(filter)

    def filter_outstanding(self, queryset, name, value):
        """Filter by 'outstanding' status."""
        value = str2bool(value)

        if value:
            return queryset.filter(status__in=SalesOrderStatusGroups.OPEN)
        else:
            return queryset.exclude(status__in=SalesOrderStatusGroups.OPEN)

    # Related to a particular part
    part = rest_filters.ModelChoiceFilter(
        label='Filter by part',
        queryset=Part.objects.all(),
        method='filter_by_part',
    )

    def filter_by_part(self, queryset, name, part):
        """Filter by 'part'"""
        return queryset.filter(lines__part=part).distinct()

    # Filter by date range
    min_creation_date = rest_filters.DateFilter(
        'creation_date', label='Min creation date', lookup_expr='gte'
    )

    max_creation_date = rest_filters.DateFilter(
        'creation_date', label='Max creation date', lookup_expr='lte'
    )

    created_by = rest_filters.CharFilter(
        label='Order created by', field_name='created_by__username', lookup_expr='iexact'
    )


class ReturnOrderFilter(rest_filters.FilterSet):
    """Custom API filter for the ReturnOrderList endpoint."""

    class Meta:
        """Metaclass options."""

        model = order.models.ReturnOrder
        fields = ['customer', 'status']

    # Exact match for reference
    reference = rest_filters.CharFilter(
        label='Filter by exact reference', field_name='reference', lookup_expr='iexact'
    )

    # Partial match for reference
    reference_contains = rest_filters.CharFilter(
        label='Filter by partial reference',
        field_name='reference',
        lookup_expr='icontains',
    )

    # Exact match for customer reference
    customer_reference = rest_filters.CharFilter(
        label='Filter by exact customer reference',
        field_name='customer_reference',
        lookup_expr='iexact',
    )

    # Partial match for customer reference
    customer_reference_contains = rest_filters.CharFilter(
        label='Filter by partial customer reference',
        field_name='customer_reference',
        lookup_expr='icontains',
    )

    responsible = rest_filters.ModelChoiceFilter(
        label='Filter by responsible',
        field_name='responsible',
        queryset=Owner.get_owner_queryset(),
    )

    assigned_to_me = rest_filters.BooleanFilter(
        label='Filter by orders assigned to me',
        method='filter_assigned_to_me',
    )

    def filter_assigned_to_me(self, queryset, name, value):
        """Filter by orders which are assigned to the current user."""
        value = str2bool(value)

        # Work out who "me" is!
        owners = Owner.get_owners_matching_user(self.request.user)

        if value:
            return queryset.filter(responsible__in=owners)
        else:
            return queryset.exclude(responsible__in=owners)

    status = rest_filters.NumberFilter(label='Filter by status')

    outstanding = rest_filters.BooleanFilter(
        label='Outstanding', method='filter_outstanding'
    )

    overdue = rest_filters.BooleanFilter(label='Overdue', method='filter_overdue')

    # Overdue order filter
    def filter_overdue(self, queryset, name, value):
        """Filter by whether the order is 'overdue' or not."""
        value = str2bool(value)

        filter = order.models.ReturnOrder.overdue_filter()

        if value:
            return queryset.filter(filter)
        else:
            return queryset.exclude(filter)

    def filter_outstanding(self, queryset, name, value):
        """Filter by 'outstanding' status."""
        value = str2bool(value)

        if value:
            return queryset.filter(status=ReturnOrderStatus.IN_PROGRESS)
        else:
            return queryset.exclude(status=ReturnOrderStatus.IN_PROGRESS)

    # Filter by date range
    min_creation_date = rest_filters.DateFilter(
        'creation_date', label='Min creation date', lookup_expr='gte'
    )

    max_creation_date = rest_filters.DateFilter(
        'creation_date', label='Max creation date', lookup_expr='lte'
    )

    created_by = rest_filters.CharFilter(
        label='Order created by', field_name='created_by__username', lookup_expr='iexact'
    )


class PurchaseOrderList(OrderListMixin, ListCreateAPI):
    """API endpoint for accessing a list of PurchaseOrder objects.

    - GET: Return list of PurchaseOrder objects (with filters)
    - POST: Create a new PurchaseOrder
    """

    filterset_class = PurchaseOrderFilter
    queryset = order.models.PurchaseOrder.objects.all()
    serializer_class = serializers.PurchaseOrderSerializer

    ordering_fields = [
        'creation_date',
        'reference',
        'supplier__name',
        'target_date',
        'line_items',
        'status',
    ]

    ordering = '-creation_date'

    def get_queryset(self, *args, **kwargs):
        """Return an annotated queryset object."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = serializers.PurchaseOrderSerializer.annotate_queryset(queryset)

        return queryset


class PurchaseOrderDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a PurchaseOrder object."""

    queryset = order.models.PurchaseOrder.objects.all()
    serializer_class = serializers.PurchaseOrderSerializer

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = serializers.PurchaseOrderSerializer.annotate_queryset(queryset)

        return queryset


class PurchaseOrderHold(OrderAdjustMixin, CreateAPI):
    """API endpoint for marking a purchase order as 'held'."""

    serializer_class = serializers.PurchaseOrderHoldSerializer

    def perform_create(self, serializer):
        """Mark the order as 'hold'."""
        return self.perform_action(
            serializer, lambda x: x.hold_order(), 'hold_order'
        )


class PurchaseOrderCancel(OrderAdjustMixin, CreateAPI):
    """API endpoint for marking a purchase order as 'cancelled'."""

    serializer_class = serializers.PurchaseOrderCancelSerializer

    def perform_create(self, serializer):
        """Mark the order as 'cancel'."""
        return self.perform_action(
            serializer, lambda x: x.cancel_order(), 'cancel'
        )


class PurchaseOrderComplete(OrderAdjustMixin, CreateAPI):
    """API endpoint for marking a purchase order as 'complete'."""

    serializer_class = serializers.PurchaseOrderCompleteSerializer

    def get_serializer_context(self):
        """Pass the request object to the serializer."""
        ctx = super().get_serializer_context()

        return ctx

    def perform_create(self, serializer):
        """Mark the order as 'complete'."""
        return self.perform_action(
            serializer, lambda x: x.complete_order(), 'complete'
        )


class PurchaseOrderIssue(OrderAdjustMixin, CreateAPI):
    """API endpoint for issuing a purchase order."""

    serializer_class = serializers.PurchaseOrderIssueSerializer

    def perform_create(self, serializer):
        """Mark the order as 'issued'."""
        return self.perform_action(
            serializer, lambda x: x.place_order(), 'place'
        )


class SalesOrderList(OrderListMixin, ListCreateAPI):
    """API endpoint for accessing a list of SalesOrder objects.

    - GET: Return list of SalesOrder objects (with filters)
    - POST: Create a new SalesOrder
    """

    filterset_class = SalesOrderFilter
    queryset = order.models.SalesOrder.objects.all()
    serializer_class = serializers.SalesOrderSerializer

    ordering_fields = [
        'creation_date',
        'reference',
        'customer__name',
        'target_date',
        'line_items',
        'status',
    ]

    ordering = '-creation_date'

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = serializers.SalesOrderSerializer.annotate_queryset(queryset)

        return queryset


class SalesOrderDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a SalesOrder object."""

    queryset = order.models.SalesOrder.objects.all()
    serializer_class = serializers.SalesOrderSerializer

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = serializers.SalesOrderSerializer.annotate_queryset(queryset)

        return queryset


class SalesOrderHold(OrderAdjustMixin, CreateAPI):
    """API endpoint for marking a sales order as 'held'."""

    serializer_class = serializers.SalesOrderHoldSerializer

    def perform_create(self, serializer):
        """Mark the order as 'hold'."""
        return self.perform_action(serializer, lambda x: x.hold_order(), 'hold_order')


class SalesOrderCancel(OrderAdjustMixin, CreateAPI):
    """API endpoint for marking a sales order as 'cancelled'."""

    serializer_class = serializers.SalesOrderCancelSerializer

    def perform_create(self, serializer):
        """Mark the order as 'cancelled'."""
        return self.perform_action(serializer, lambda x: x.cancel_order(), 'cancel')


class SalesOrderComplete(OrderAdjustMixin, CreateAPI):
    """API endpoint for marking a sales order as 'complete'."""

    serializer_class = serializers.SalesOrderCompleteSerializer

    def get_serializer_context(self):
        """Pass the request object to the serializer."""
        ctx = super().get_serializer_context()
        return ctx

    def perform_create(self, serializer):
        """Mark the order as 'complete'."""
        return self.perform_action(
            serializer, lambda x: x.ship_order(allow_incomplete_lines=True), 'complete'
        )


class SalesOrderIssue(OrderAdjustMixin, CreateAPI):
    """API endpoint for issuing a sales order."""

    serializer_class = serializers.SalesOrderIssueSerializer

    def perform_create(self, serializer):
        """Mark the order as 'issued'."""
        return self.perform_action(serializer, lambda x: x.issue_order(), 'place')


class ReturnOrderList(OrderListMixin, ListCreateAPI):
    """API endpoint for accessing a list of ReturnOrder objects."""

    filterset_class = ReturnOrderFilter
    queryset = order.models.ReturnOrder.objects.all()
    serializer_class = serializers.ReturnOrderSerializer

    ordering_fields = [
        'creation_date',
        'reference',
        'customer__name',
        'target_date',
        'line_items',
        'status',
    ]

    ordering = '-creation_date'

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = serializers.ReturnOrderSerializer.annotate_queryset(queryset)

        return queryset


class ReturnOrderDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a ReturnOrder object."""

    queryset = order.models.ReturnOrder.objects.all()
    serializer_class = serializers.ReturnOrderSerializer

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = serializers.ReturnOrderSerializer.annotate_queryset(queryset)

        return queryset


class ReturnOrderHold(OrderAdjustMixin, CreateAPI):
    """API endpoint for marking a return order as 'held'."""

    serializer_class = serializers.ReturnOrderHoldSerializer

    def perform_create(self, serializer):
        """Mark the order as 'held'."""
        return self.perform_action(serializer, lambda x: x.hold_order(), 'hold_order')


class ReturnOrderCancel(OrderAdjustMixin, CreateAPI):
    """API endpoint for marking a return order as 'cancelled'."""

    serializer_class = serializers.ReturnOrderCancelSerializer

    def perform_create(self, serializer):
        """Mark the order as 'cancelled'."""
        return self.perform_action(serializer, lambda x: x.cancel_order(), 'cancel')


class ReturnOrderComplete(OrderAdjustMixin, CreateAPI):
    """API endpoint for marking a return order as 'complete'."""

    serializer_class = serializers.ReturnOrderCompleteSerializer

    def perform_create(self, serializer):
        """Mark the order as 'complete'."""
        return self.perform_action(
            serializer, lambda x: x.complete_order(), 'complete'
        )


class ReturnOrderIssue(OrderAdjustMixin, CreateAPI):
    """API endpoint for issuing a return order."""

    serializer_class = serializers.ReturnOrderIssueSerializer

    def perform_create(self, serializer):
        """Mark the order as 'issued'."""
        return self.perform_action(serializer, lambda x: x.issue_order(), 'place')


class PurchaseOrderLineItemList(ListCreateAPI):
    """API endpoint for accessing a list of PurchaseOrderLineItems."""

    queryset = order.models.PurchaseOrderLineItem.objects.all()
    serializer_class = serializers.PurchaseOrderLineItemSerializer

    def get_serializer(self, *args, **kwargs):
        """Return serializer instance for this endpoint."""
        try:
            params = self.request.query_params

            kwargs['part_detail'] = str2bool(params.get('part_detail', False))
            kwargs['order_detail'] = str2bool(params.get('order_detail', False))

        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        """Return an annotated queryset for this endpoint."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = serializers.PurchaseOrderLineItemSerializer.annotate_queryset(queryset)

        return queryset

    def filter_queryset(self, queryset):
        """Custom filter for the PurchaseOrderLineItemList endpoint."""
        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # Filter by order
        order_id = params.get('order', None)

        if order_id is not None:
            queryset = queryset.filter(order=order_id)

        # Filter by supplier part
        part_id = params.get('part', None)

        if part_id is not None:
            queryset = queryset.filter(part=part_id)

        # Special filtering for 'pending' status
        pending = params.get('pending', None)

        if pending is not None:
            pending = str2bool(pending)

            if pending:
                # Return *only* pending line items
                queryset = queryset.filter(received__lt=F('quantity'))
            else:
                # Return *only* line items which are not pending
                queryset = queryset.filter(received__gte=F('quantity'))

        return queryset

    filter_backends = SEARCH_ORDER_FILTER

    ordering_fields = [
        'part__name',
    ]

    search_fields = [
        'reference',
        'part__name',
        'part__description',
        'part__IPN',
        'part__supplier_part__SKU',
        'notes',
    ]

    filterset_fields = [
        'part',
        'order',
    ]


class PurchaseOrderLineItemDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a PurchaseOrderLineItem object."""

    queryset = order.models.PurchaseOrderLineItem.objects.all()
    serializer_class = serializers.PurchaseOrderLineItemSerializer

    def get_serializer(self, *args, **kwargs):
        """Return serializer for this endpoint with required context."""
        kwargs['part_detail'] = True
        kwargs['context'] = self.get_serializer_context()
        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset for this endpoint."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = serializers.PurchaseOrderLineItemSerializer.annotate_queryset(queryset)

        return queryset


class PurchaseOrderExtraLineList(GeneralExtraLineList, ListCreateAPI):
    """API endpoint for accessing a list of PurchaseOrderExtraLine objects."""

    queryset = order.models.PurchaseOrderExtraLine.objects.all()
    serializer_class = serializers.PurchaseOrderExtraLineSerializer

    def get_serializer(self, *args, **kwargs):
        """Return the serializer instance for this endpoint."""
        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)


class PurchaseOrderExtraLineDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a PurchaseOrderExtraLine object."""

    queryset = order.models.PurchaseOrderExtraLine.objects.all()
    serializer_class = serializers.PurchaseOrderExtraLineSerializer


class ReturnOrderExtraLineList(GeneralExtraLineList, ListCreateAPI):
    """API endpoint for accessing a list of ReturnOrderExtraLine objects."""

    queryset = order.models.ReturnOrderExtraLine.objects.all()
    serializer_class = serializers.ReturnOrderExtraLineSerializer


class ReturnOrderExtraLineDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a ReturnOrderExtraLine object."""

    queryset = order.models.ReturnOrderExtraLine.objects.all()
    serializer_class = serializers.ReturnOrderExtraLineSerializer


class SalesOrderExtraLineList(GeneralExtraLineList, ListCreateAPI):
    """API endpoint for accessing a list of SalesOrderExtraLine objects."""

    queryset = order.models.SalesOrderExtraLine.objects.all()
    serializer_class = serializers.SalesOrderExtraLineSerializer


class SalesOrderExtraLineDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a SalesOrderExtraLine object."""

    queryset = order.models.SalesOrderExtraLine.objects.all()
    serializer_class = serializers.SalesOrderExtraLineSerializer


class ReturnOrderLineItemList(ListCreateAPI):
    """API endpoint for accessing a list of ReturnOrderLineItem objects."""

    queryset = order.models.ReturnOrderLineItem.objects.all()
    serializer_class = serializers.ReturnOrderLineItemSerializer

    def get_serializer(self, *args, **kwargs):
        """Return serializer instance for this endpoint."""
        try:
            params = self.request.query_params

            kwargs['item_detail'] = str2bool(params.get('item_detail', False))
            kwargs['order_detail'] = str2bool(params.get('order_detail', False))
        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = [
        'order',
        'item',
    ]

    ordering_fields = [
        'item__part__name',
    ]


class ReturnOrderLineItemDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a ReturnOrderLineItem object."""

    queryset = order.models.ReturnOrderLineItem.objects.all()
    serializer_class = serializers.ReturnOrderLineItemSerializer


class ReturnOrderReceive(CreateAPI):
    """API endpoint for receiving items against a ReturnOrder."""

    queryset = order.models.ReturnOrder.objects.none()
    serializer_class = serializers.ReturnOrderReceiveSerializer

    def get_serializer_context(self):
        """Add extra context to the serializer for this endpoint."""
        ctx = super().get_serializer_context()

        try:
            ctx['order'] = order.models.ReturnOrder.objects.get(
                pk=self.kwargs.get('pk', None)
            )
        except:
            pass

        return ctx


class PurchaseOrderReceive(CreateAPI):
    """API endpoint for receiving items against a PurchaseOrder."""

    queryset = order.models.PurchaseOrder.objects.none()
    serializer_class = serializers.PurchaseOrderReceiveSerializer

    def get_serializer_context(self):
        """Add extra context to the serializer for this endpoint."""
        ctx = super().get_serializer_context()

        try:
            ctx['order'] = order.models.PurchaseOrder.objects.get(
                pk=self.kwargs.get('pk', None)
            )
        except:
            pass

        return ctx


class PurchaseOrderAttachmentList(AttachmentMixin, ListCreateDestroyAPIView):
    """API endpoint for listing (and creating) attachments for a PurchaseOrder."""

    pass


class SalesOrderAttachmentList(AttachmentMixin, ListCreateDestroyAPIView):
    """API endpoint for listing (and creating) attachments for a SalesOrder."""

    pass


class SalesOrderShipmentList(ListCreateAPI):
    """API endpoint for listing SalesOrderShipment objects."""

    queryset = order.models.SalesOrderShipment.objects.all()
    serializer_class = serializers.SalesOrderShipmentSerializer

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = ['order']


class SalesOrderShipmentDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for a single SalesOrderShipment object."""

    queryset = order.models.SalesOrderShipment.objects.all()
    serializer_class = serializers.SalesOrderShipmentSerializer


class SalesOrderShipmentComplete(CreateAPI):
    """API endpoint for completing (shipping) a SalesOrderShipment."""

    queryset = order.models.SalesOrderShipment.objects.all()
    serializer_class = serializers.SalesOrderShipmentCompleteSerializer

    def get_serializer_context(self):
        """Add context information to the serializer."""
        ctx = super().get_serializer_context()

        try:
            ctx['shipment'] = order.models.SalesOrderShipment.objects.get(
                pk=self.kwargs.get('pk', None)
            )
        except:
            pass

        return ctx


class SalesOrderAllocationList(ListCreateAPI):
    """API endpoint for listing SalesOrderAllocation objects."""

    queryset = order.models.SalesOrderAllocation.objects.all()
    serializer_class = serializers.SalesOrderAllocationSerializer

    def get_serializer(self, *args, **kwargs):
        """Return serializer instance for this endpoint."""
        try:
            params = self.request.query_params

            kwargs['part_detail'] = str2bool(params.get('part_detail', True))
            kwargs['item_detail'] = str2bool(params.get('item_detail', True))
            kwargs['order_detail'] = str2bool(params.get('order_detail', False))
            kwargs['location_detail'] = str2bool(params.get('location_detail', False))
            kwargs['customer_detail'] = str2bool(params.get('customer_detail', False))
        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def filter_queryset(self, queryset):
        """Custom queryset filtering for the SalesOrderAllocation API."""
        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # Filter by order
        order_id = params.get('order', None)

        if order_id is not None:
            try:
                order_id = int(order_id)
                queryset = queryset.filter(line__order=order_id)
            except ValueError:
                pass

        # Filter by line item
        line = params.get('line', None)

        if line is not None:
            try:
                line = int(line)
                queryset = queryset.filter(line=line)
            except ValueError:
                pass

        # Filter by "parts"
        part_id = params.get('part', None)

        if part_id:
            try:
                part_id = int(part_id)
                queryset = queryset.filter(item__part=part_id)
            except ValueError:
                pass

        # Filter by associated shipment
        shipment = params.get('shipment', None)

        if shipment is not None:
            try:
                shipment = int(shipment)
                queryset = queryset.filter(shipment=shipment)
            except ValueError:
                pass

        # Filter by "customer"
        customer_id = params.get('customer', None)

        if customer_id:
            try:
                customer_id = int(customer_id)
                queryset = queryset.filter(line__order__customer=customer_id)
            except ValueError:
                pass

        # Filter by "outstanding" allocation
        outstanding = params.get('outstanding', None)

        if outstanding is not None:
            outstanding = str2bool(outstanding)

            if outstanding:
                # Filter for allocations which are outstanding
                queryset = queryset.filter(
                    shipment__shipment_date=None,
                )
            else:
                # Filter for allocations which are *not* outstanding
                queryset = queryset.filter(
                    shipment__shipment_date__isnull=False,
                )

        return queryset

    filter_backends = SEARCH_ORDER_FILTER_ALIAS

    filterset_fields = [
        'item',
        'line',
        'line__part',
    ]

    ordering_fields = [
        'line__part__name',
    ]

    search_fields = [
        'line__part__name',
        'line__part__description',
    ]


class SalesOrderAllocationDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a SalesOrderAllocation object."""

    queryset = order.models.SalesOrderAllocation.objects.all()
    serializer_class = serializers.SalesOrderAllocationSerializer


class SalesOrderSerialAllocate(CreateAPI):
    """API endpoint to allocation stock items against a sales order, by serial number."""

    serializer_class = serializers.SalesOrderSerialAllocationSerializer
    queryset = order.models.SalesOrderAllocation.objects.all()

    def get_serializer_context(self):
        """Add extra context to the serializer for this endpoint."""
        ctx = super().get_serializer_context()

        ctx['order'] = order.models.SalesOrder.objects.get(pk=self.kwargs['pk'])

        return ctx


class SalesOrderShipmentAllocate(CreateAPI):
    """API endpoint to allocation stock items against a sales order shipment."""

    serializer_class = serializers.SalesOrderShipmentAllocationSerializer
    queryset = order.models.SalesOrderAllocation.objects.all()

    def get_serializer_context(self):
        """Add extra context to the serializer for this endpoint."""
        ctx = super().get_serializer_context()

        ctx['order'] = order.models.SalesOrder.objects.get(pk=self.kwargs['pk'])

        return ctx


order_api_urls = [
    # Purchase Orders
    path('po/', include([
        path('', PurchaseOrderList.as_view(), name='api-po-list'),

        # Purchase Order detail URLs
        path('<int:pk>/', include([
            path('', PurchaseOrderDetail.as_view(), name='api-po-detail'),
            path('hold/', PurchaseOrderHold.as_view(), name='api-po-hold'),
            path('cancel/', PurchaseOrderCancel.as_view(), name='api-po-cancel'),
            path('issue/', PurchaseOrderIssue.as_view(), name='api-po-issue'),
            path(
                'complete/',
                PurchaseOrderComplete.as_view(),
                name='api-po-complete',
            ),
            path('metadata/', MetadataView.as_view(), {'model': order.models.PurchaseOrder}, name='api-po-metadata'),
            path('attachments/', PurchaseOrderAttachmentList.as_view(), name='api-po-attachment-list'),
            path('receive/', PurchaseOrderReceive.as_view(), name='api-po-receive'),
        ]))
    ]),

    # Purchase Order Line Item URLs
    path('po-line/', include([
        path('', PurchaseOrderLineItemList.as_view(), name='api-po-line-list'),
        path('<int:pk>/', PurchaseOrderLineItemDetail.as_view(), name='api-po-line-detail'),
    ])),

    # Purchase Order Extra Line URLs
    path('po-extra-line/', include([
        path('', PurchaseOrderExtraLineList.as_view(), name='api-po-extra-line-list'),
        path('<int:pk>/', PurchaseOrderExtraLineDetail.as_view(), name='api-po-extra-line-detail'),
    ])),

    # Sales Orders
    path('so/', include([
        path('', SalesOrderList.as_view(), name='api-so-list'),

        path('<int:pk>/', include([
            path('', SalesOrderDetail.as_view(), name='api-so-detail'),
            path('hold/', SalesOrderHold.as_view(), name='api-so-hold'),
            path('cancel/', SalesOrderCancel.as_view(), name='api-so-cancel'),
            path('issue/', SalesOrderIssue.as_view(), name='api-so-issue'),
            path('complete/', SalesOrderComplete.as_view(), name='api-so-complete'),
            path('allocate/', SalesOrderSerialAllocate.as_view(), name='api-so-allocate'),
            path('allocate-shipment/', SalesOrderShipmentAllocate.as_view(), name='api-so-allocate-shipment'),
            path('metadata/', MetadataView.as_view(), {'model': order.models.SalesOrder}, name='api-so-metadata'),
            path('attachments/', SalesOrderAttachmentList.as_view(), name='api-so-attachment-list'),
        ])),
    ])),

    # [AGENT GENERATED CODE - REQUIREMENT:EDIT_LINE_ITEMS]
    # Sales Order Line Items
    path('so-line/', include([
        path('', SalesOrderLineItemList.as_view(), name='api-so-line-list'),
        path('<int:pk>/', include([
            path('', SalesOrderLineItemDetail.as_view(), name='api-so-line-detail'),
            path('approve/', SalesOrderLineItemApprove.as_view(), name='api-so-line-approve'),
        ])),
    ])),
    # [END AGENT GENERATED CODE]

    # Sales Order Shipment URLs
    path('so-shipment/', include([
        path('', SalesOrderShipmentList.as_view(), name='api-so-shipment-list'),
        path('<int:pk>/', include([
            path('', SalesOrderShipmentDetail.as_view(), name='api-so-shipment-detail'),
            path('complete/', SalesOrderShipmentComplete.as_view(), name='api-so-shipment-complete'),
            path('allocations/', SalesOrderAllocationList.as_view(), name='api-so-shipment-allocations'),
        ])),
    ])),

    # Sales Order Allocation URLs
    path('so-allocation/', include([
        path('', SalesOrderAllocationList.as_view(), name='api-so-allocation-list'),
        path('<int:pk>/', SalesOrderAllocationDetail.as_view(), name='api-so-allocation-detail'),
    ])),

    # Sales Order Extra Line URLs
    path('so-extra-line/', include([
        path('', SalesOrderExtraLineList.as_view(), name='api-so-extra-line-list'),
        path('<int:pk>/', SalesOrderExtraLineDetail.as_view(), name='api-so-extra-line-detail'),
    ])),

    # Return Orders
    path('ro/', include([
        path('', ReturnOrderList.as_view(), name='api-return-order-list'),

        # Return Order Detail URLs
        path('<int:pk>/', include([
            path('', ReturnOrderDetail.as_view(), name='api-return-order-detail'),
            path('hold/', ReturnOrderHold.as_view(), name='api-return-order-hold'),
            path('cancel/', ReturnOrderCancel.as_view(), name='api-return-order-cancel'),
            path('issue/', ReturnOrderIssue.as_view(), name='api-return-order-issue'),
            path('complete/', ReturnOrderComplete.as_view(), name='api-return-order-complete'),
            path('metadata/', MetadataView.as_view(), {'model': order.models.ReturnOrder}, name='api-return-order-metadata'),
            path('receive/', ReturnOrderReceive.as_view(), name='api-return-order-receive'),
        ])),
    ])),

    # Return Order Line URLs
    path('ro-line/', include([
        path('', ReturnOrderLineItemList.as_view(), name='api-return-order-line-list'),
        path('<int:pk>/', ReturnOrderLineItemDetail.as_view(), name='api-return-order-line-detail'),
    ])),

    # Return Order Extra Line URLs
    path('ro-extra-line/', include([
        path('', ReturnOrderExtraLineList.as_view(), name='api-return-order-extra-line-list'),
        path('<int:pk>/', ReturnOrderExtraLineDetail.as_view(), name='api-return-order-extra-line-detail'),
    ])),
]