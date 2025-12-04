"""Provides a JSON API for the Company app."""

from django.db.models import Q
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as rest_filters

import part.models
from data_exporter.mixins import DataExportViewMixin
from InvenTree.api import ListCreateDestroyAPIView, MetadataView
from InvenTree.filters import SEARCH_ORDER_FILTER, SEARCH_ORDER_FILTER_ALIAS
from InvenTree.helpers import str2bool
from InvenTree.mixins import ListCreateAPI, RetrieveUpdateDestroyAPI

from .models import (
    Address,
    Company,
    CompanyCategory,
    Contact,
    ManufacturerPart,
    ManufacturerPartParameter,
    SupplierPart,
    SupplierPriceBreak,
)
from .serializers import (
    AddressSerializer,
    CompanySerializer,
    CompanyCategorySerializer,
    CompanyCategoryBriefSerializer,
    ContactSerializer,
    ManufacturerPartParameterSerializer,
    ManufacturerPartSerializer,
    SupplierPartSerializer,
    SupplierPriceBreakSerializer,
)

# [AGENT GENERATED CODE - REQUIREMENT:Delete Vendor Categories with Validation, Bulk Upload Vendor Categories with Validation]
class CompanyCategoryList(DataExportViewMixin, ListCreateAPI):
    """API endpoint for accessing a list of CompanyCategory objects.
    
    Provides two methods:
    
    - GET: Return list of objects
    - POST: Create a new CompanyCategory object
    """
    
    serializer_class = CompanyCategorySerializer
    queryset = CompanyCategory.objects.all()
    
    def get_queryset(self):
        """Return annotated queryset for the category list endpoint."""
        queryset = super().get_queryset()
        queryset = CompanyCategorySerializer.annotate_queryset(queryset)
        
        params = self.request.query_params
        
        # Filter by "structural" attribute
        structural = params.get('structural', None)
        if structural is not None:
            structural = str2bool(structural)
            queryset = queryset.filter(structural=structural)
            
        # Filter by "cascade" attribute - whether to include subcategories or not
        cascade = str2bool(params.get('cascade', True))
        
        # Filter by "parent" attribute
        parent = params.get('parent', None)
        
        if parent is not None:
            if parent.lower() == 'null':
                # Return only top-level categories (no parent)
                queryset = queryset.filter(parent=None)
            elif parent.lower() == 'all':
                # Return all categories (don't filter by parent)
                pass
            else:
                try:
                    # Look up the parent category
                    parent_category = CompanyCategory.objects.get(pk=parent)
                    
                    if cascade:
                        # Include subcategories
                        queryset = queryset.filter(parent__in=parent_category.get_descendants(include_self=True))
                    else:
                        # Only direct children of the specified category
                        queryset = queryset.filter(parent=parent)
                except (ValueError, CompanyCategory.DoesNotExist):
                    pass
        
        return queryset


class CompanyCategoryDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for a single CompanyCategory object.
    
    Provides three methods:
    
    - GET: Return a single category object
    - PATCH: Update a category object
    - DELETE: Delete a category object
    """
    
    serializer_class = CompanyCategorySerializer
    queryset = CompanyCategory.objects.all()
    
    def get_queryset(self):
        """Return annotated queryset for the category detail endpoint."""
        queryset = super().get_queryset()
        queryset = CompanyCategorySerializer.annotate_queryset(queryset)
        return queryset
    
    def get_serializer_context(self):
        """Pass extra context to the serializer."""
        ctx = super().get_serializer_context()
        
        try:
            ctx['category_detail'] = True
        except (ValueError, CompanyCategory.DoesNotExist):
            pass
        
        return ctx
# [/AGENT GENERATED CODE]


class CompanyList(DataExportViewMixin, ListCreateAPI):
    """API endpoint for accessing a list of Company objects.

    Provides two methods:

    - GET: Return list of objects
    - POST: Create a new Company object
    """

    serializer_class = CompanySerializer
    queryset = Company.objects.all()

    def get_queryset(self):
        """Return annotated queryset for the company list endpoint."""
        queryset = super().get_queryset()

        queryset = CompanySerializer.annotate_queryset(queryset)

        params = self.request.query_params

        is_supplier = params.get('is_supplier', None)
        is_manufacturer = params.get('is_manufacturer', None)
        is_customer = params.get('is_customer', None)
        active = params.get('active', None)

        # Filter by 'active' status
        if active is not None:
            active = str2bool(active)
            queryset = queryset.filter(active=active)

        # Filter by company type
        if is_supplier is not None:
            is_supplier = str2bool(is_supplier)
            queryset = queryset.filter(is_supplier=is_supplier)

        if is_manufacturer is not None:
            is_manufacturer = str2bool(is_manufacturer)
            queryset = queryset.filter(is_manufacturer=is_manufacturer)

        if is_customer is not None:
            is_customer = str2bool(is_customer)
            queryset = queryset.filter(is_customer=is_customer)

        # Filter by primary_part
        part = params.get('part', None)

        if part is not None:
            try:
                part = part.models.Part.objects.get(pk=part)
                queryset = queryset.filter(
                    Q(manufactured_parts__part=part) | Q(supplied_parts__part=part)
                ).distinct()
            except (ValueError, part.models.Part.DoesNotExist):
                pass

        # Filter by 'assigned' parts, i.e. parts which are already linked to this supplier
        assigned = params.get('assigned', None)

        if assigned is not None:
            assigned = str2bool(assigned)

            # Get list of valid part suppliers
            ps_list = SupplierPart.objects.filter(supplier__in=queryset)

            # Extract set of supplier IDs for these parts
            sp_list = [ps.supplier.id for ps in ps_list]

            if assigned:
                # Return companies which appear in this list
                queryset = queryset.filter(id__in=sp_list)
            else:
                # Return companies which do not appear in this list
                queryset = queryset.exclude(id__in=sp_list)

        # [AGENT GENERATED CODE - REQUIREMENT:Delete Vendor Categories with Validation, Bulk Upload Vendor Categories with Validation]
        # Filter by category
        cat_id = params.get('category', None)
        
        if cat_id:
            # If directly specified, filter by this category
            try:
                category = CompanyCategory.objects.get(pk=cat_id)
                queryset = queryset.filter(category=category)
            except (ValueError, CompanyCategory.DoesNotExist):
                pass
                
        # Filter by whether the company has a category assigned
        has_category = params.get('has_category', None)
        
        if has_category is not None:
            has_category = str2bool(has_category)
            
            if has_category:
                queryset = queryset.exclude(category=None)
            else:
                queryset = queryset.filter(category=None)
        # [/AGENT GENERATED CODE]

        return queryset


class CompanyDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a Company object."""

    serializer_class = CompanySerializer
    queryset = Company.objects.all()

    def get_queryset(self):
        """Return annotated queryset for the company detail endpoint."""
        queryset = super().get_queryset()
        queryset = CompanySerializer.annotate_queryset(queryset)
        return queryset


class ContactList(ListCreateAPI):
    """API endpoint for list view of Contact object(s)."""

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def get_queryset(self):
        """Custom filtering by query params."""
        queryset = super().get_queryset()

        company_id = self.request.query_params.get('company', None)

        if company_id:
            try:
                company = Company.objects.get(pk=company_id)
                queryset = queryset.filter(company=company)
            except (ValueError, Company.DoesNotExist):
                pass

        return queryset


class ContactDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a Contact object."""

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer


class AddressList(ListCreateAPI):
    """API endpoint for list view of Address object(s)."""

    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    def get_queryset(self):
        """Custom filtering by query params."""
        queryset = super().get_queryset()

        company_id = self.request.query_params.get('company', None)
        if company_id:
            try:
                company = Company.objects.get(pk=company_id)
                queryset = queryset.filter(company=company)
            except (ValueError, Company.DoesNotExist):
                pass

        return queryset


class AddressDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a Address object."""

    queryset = Address.objects.all()
    serializer_class = AddressSerializer


class ManufacturerPartFilter(rest_filters.FilterSet):
    """Custom API filters for the ManufacturerPart list endpoint."""

    class Meta:
        """Metaclass defines filter set fields."""

        model = ManufacturerPart
        fields = ['manufacturer', 'MPN']


class ManufacturerPartList(DataExportViewMixin, ListCreateAPI):
    """API endpoint for list view of ManufacturerPart object."""

    queryset = ManufacturerPart.objects.all()
    serializer_class = ManufacturerPartSerializer
    filterset_class = ManufacturerPartFilter

    def get_serializer(self, *args, **kwargs):
        """Return a serializer instance for this endpoint."""
        # Add extra context based on query params
        kwargs.setdefault('part_detail', str2bool(self.request.query_params.get('part_detail', 'true')))
        kwargs.setdefault('manufacturer_detail', str2bool(self.request.query_params.get('manufacturer_detail', 'true')))
        kwargs.setdefault('pretty', str2bool(self.request.query_params.get('pretty', 'true')))

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self):
        """Annotate queryset before returning."""
        queryset = super().get_queryset()

        queryset = queryset.select_related('manufacturer')
        queryset = queryset.select_related('part')
        queryset = queryset.prefetch_related('part__category')
        queryset = queryset.prefetch_related('supplier_parts')

        return queryset

    def filter_queryset(self, queryset):
        """Custom filtering for the queryset."""
        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # Filter by "tagged" query param
        tags = params.get('tags', '')

        if tags:
            tags = tags.split(',')
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        # Filter by Part reference
        part = params.get('part', None)

        if part is not None:
            try:
                part = part.models.Part.objects.get(pk=part)
                queryset = queryset.filter(part=part)
            except (ValueError, part.models.Part.DoesNotExist):
                pass

        # Filter by 'active' status
        active = params.get('active', '')

        if active:
            active = str2bool(active)
            queryset = queryset.filter(active=active)

        # Filter by IPN
        ipn = params.get('IPN', '')

        if ipn:
            queryset = queryset.filter(part__IPN=ipn)

        return queryset


class ManufacturerPartDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of ManufacturerPart object."""

    queryset = ManufacturerPart.objects.all()
    serializer_class = ManufacturerPartSerializer


class ManufacturerPartParameterList(ListCreateAPI):
    """API endpoint for list view of ManufacturerPartParameter objects."""

    queryset = ManufacturerPartParameter.objects.all()
    serializer_class = ManufacturerPartParameterSerializer

    def get_queryset(self):
        """Custom filtering by query params."""
        queryset = super().get_queryset()

        # Filter by manufacturer part
        manufacturer_part = self.request.query_params.get('manufacturer_part', None)

        if manufacturer_part is not None:
            try:
                manufacturer_part = ManufacturerPart.objects.get(pk=manufacturer_part)
                queryset = queryset.filter(manufacturer_part=manufacturer_part)
            except (ValueError, ManufacturerPart.DoesNotExist):
                pass

        # Filter by name
        name = self.request.query_params.get('name', None)

        if name is not None:
            queryset = queryset.filter(name=name)

        # Filter by value
        value = self.request.query_params.get('value', None)

        if value is not None:
            queryset = queryset.filter(value=value)

        return queryset


class ManufacturerPartParameterDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of ManufacturerPartParameter object."""

    queryset = ManufacturerPartParameter.objects.all()
    serializer_class = ManufacturerPartParameterSerializer


class SupplierPartFilter(rest_filters.FilterSet):
    """Custom filters for the SupplierPart list."""

    class Meta:
        """Metaclass defines filter fields."""

        model = SupplierPart
        fields = SEARCH_ORDER_FILTER_ALIAS


class SupplierPartList(DataExportViewMixin, ListCreateAPI):
    """API endpoint for list view of SupplierPart object."""

    queryset = SupplierPart.objects.all()
    serializer_class = SupplierPartSerializer
    filterset_class = SupplierPartFilter

    def get_serializer(self, *args, **kwargs):
        """Return serializer instance for this endpoint."""
        # Add extra context based on query params
        kwargs.setdefault('part_detail', str2bool(self.request.query_params.get('part_detail', 'true')))
        kwargs.setdefault('supplier_detail', str2bool(self.request.query_params.get('supplier_detail', 'true')))
        kwargs.setdefault('manufacturer_detail', str2bool(self.request.query_params.get('manufacturer_detail', 'true')))
        kwargs.setdefault('pretty', str2bool(self.request.query_params.get('pretty', 'true')))

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self):
        """Return an annotated queryset for this endpoint."""
        queryset = super().get_queryset()

        queryset = SupplierPartSerializer.annotate_queryset(queryset)

        return queryset

    def filter_queryset(self, queryset):
        """Custom queryset filtering."""
        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # Filter by manufacturer
        manufacturer = params.get('manufacturer', None)

        if manufacturer is not None:
            try:
                manufacturer = Company.objects.get(pk=manufacturer)
                queryset = queryset.filter(manufacturer_part__manufacturer=manufacturer)
            except (ValueError, Company.DoesNotExist):
                pass

        # Filter by EITHER manufacturer or supplier
        company = params.get('company', None)

        if company is not None:
            try:
                company = Company.objects.get(pk=company)
                queryset = queryset.filter(Q(manufacturer_part__manufacturer=company) | Q(supplier=company))
            except (ValueError, Company.DoesNotExist):
                pass

        # Filter by supplier
        supplier = params.get('supplier', None)

        if supplier is not None:
            try:
                supplier = Company.objects.get(pk=supplier)
                queryset = queryset.filter(supplier=supplier)
            except (ValueError, Company.DoesNotExist):
                pass

        # Filter by part
        part = params.get('part', None)

        if part is not None:
            try:
                part = part.models.Part.objects.get(pk=part)
                queryset = queryset.filter(part=part)
            except (ValueError, part.models.Part.DoesNotExist):
                pass

        # Filter by manufacturer_part
        manufacturer_part = params.get('manufacturer_part', None)

        if manufacturer_part is not None:
            try:
                manufacturer_part = ManufacturerPart.objects.get(pk=manufacturer_part)
                queryset = queryset.filter(manufacturer_part=manufacturer_part)
            except (ValueError, ManufacturerPart.DoesNotExist):
                pass

        # Filter by 'active' status
        active = params.get('active', None)

        if active is not None:
            active = str2bool(active)
            queryset = queryset.filter(active=active)

        # Filter by "assigned" status
        has_pricing = params.get('has_pricing', None)

        if has_pricing is not None:
            has_pricing = str2bool(has_pricing)

            if has_pricing:
                queryset = queryset.exclude(pricebreaks=None)
            else:
                queryset = queryset.filter(pricebreaks=None)

        # Filter by "MPN" value
        if 'MPN' in params:
            queryset = queryset.filter(manufacturer_part__MPN=params.get('MPN', ''))

        # Filter by "SKU" value
        if 'SKU' in params:
            queryset = queryset.filter(SKU=params.get('SKU', ''))

        if 'IPN' in params:
            queryset = queryset.filter(part__IPN=params.get('IPN', ''))

        return queryset


class SupplierPartDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of SupplierPart object."""

    queryset = SupplierPart.objects
    serializer_class = SupplierPartSerializer

    def get_queryset(self):
        """Return an annotated queryset object."""
        queryset = super().get_queryset()
        queryset = SupplierPartSerializer.annotate_queryset(queryset)

        return queryset

    def get_serializer(self, *args, **kwargs):
        """Return serializer for this endpoint with extra data as requested."""
        kwargs.setdefault('part_detail', True)
        kwargs.setdefault('supplier_detail', True)
        kwargs.setdefault('manufacturer_detail', True)

        return self.serializer_class(*args, **kwargs)


class SupplierPriceBreakList(ListCreateDestroyAPIView):
    """API endpoint for list view of SupplierPriceBreak object."""

    queryset = SupplierPriceBreak.objects.all()
    serializer_class = SupplierPriceBreakSerializer

    def get_serializer(self, *args, **kwargs):
        """Return serializer for this endpoint with extra data as requested."""
        kwargs.setdefault('part_detail', str2bool(self.request.query_params.get('part_detail', 'true')))
        kwargs.setdefault('supplier_detail', str2bool(self.request.query_params.get('supplier_detail', 'true')))

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self):
        """Return annotated queryset object."""
        queryset = super().get_queryset()

        queryset = SupplierPriceBreakSerializer.annotate_queryset(queryset)

        # Filter by part
        part = self.request.query_params.get('part', None)

        if part is not None:
            try:
                part = SupplierPart.objects.get(pk=part)
                queryset = queryset.filter(part=part)
            except (ValueError, SupplierPart.DoesNotExist):
                pass

        # Filter by supplier
        supplier = self.request.query_params.get('supplier', None)

        if supplier is not None:
            try:
                supplier = Company.objects.get(pk=supplier)
                queryset = queryset.filter(part__supplier=supplier)
            except (ValueError, Company.DoesNotExist):
                pass

        return queryset


class SupplierPriceBreakDetail(RetrieveUpdateDestroyAPI):
    """Detail endpoint for SupplierPriceBreak object."""

    queryset = SupplierPriceBreak.objects.all()
    serializer_class = SupplierPriceBreakSerializer


manufacturer_part_api_urls = [
    path('parameter/', include([
        path('', ManufacturerPartParameterList.as_view(), name='api-manufacturer-part-parameter-list'),
        path('<int:pk>/', ManufacturerPartParameterDetail.as_view(), name='api-manufacturer-part-parameter-detail'),
    ])),

    # Manufacturer part detail endpoints
    path('', ManufacturerPartList.as_view(), name='api-manufacturer-part-list'),
    path('<int:pk>/', ManufacturerPartDetail.as_view(), name='api-manufacturer-part-detail'),
]

supplier_part_api_urls = [
    # Supplier part detail endpoints
    path('', SupplierPartList.as_view(), name='api-supplier-part-list'),
    path('<int:pk>/', SupplierPartDetail.as_view(), name='api-supplier-part-detail'),
]


company_api_urls = [
    # [AGENT GENERATED CODE - REQUIREMENT:Delete Vendor Categories with Validation, Bulk Upload Vendor Categories with Validation]
    # Company category endpoints
    path('category/', include([
        path('', CompanyCategoryList.as_view(), name='api-company-category-list'),
        path('<int:pk>/', CompanyCategoryDetail.as_view(), name='api-company-category-detail'),
    ])),
    # [/AGENT GENERATED CODE]

    # Company detail endpoints
    path('', CompanyList.as_view(), name='api-company-list'),
    path('<int:pk>/', CompanyDetail.as_view(), name='api-company-detail'),

    # Endpoints for company contacts
    path('contact/', include([
        path('', ContactList.as_view(), name='api-contact-list'),
        path('<int:pk>/', ContactDetail.as_view(), name='api-contact-detail'),
    ])),

    # Endpoints for company address
    path('address/', include([
        path('', AddressList.as_view(), name='api-address-list'),
        path('<int:pk>/', AddressDetail.as_view(), name='api-address-detail'),
    ])),

    # Endpoints for price breaks
    path('price-break/', include([
        path('', SupplierPriceBreakList.as_view(), name='api-part-supplier-price-list'),
        path('<int:pk>/', SupplierPriceBreakDetail.as_view(), name='api-part-supplier-price-detail'),
    ])),

    # Endpoints for manufacturer parts
    path('manufacturer-part/', include(manufacturer_part_api_urls)),

    # Endpoints for supplier parts
    path('supplier-part/', include(supplier_part_api_urls)),

    # Meta-data endpoints
    path('metadata/', include([
        path('', MetadataView.as_view(), name='api-company-metadata'),
    ])),
]