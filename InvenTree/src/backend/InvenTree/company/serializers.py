"""JSON serializers for Company app."""

import io

from django.core.files.base import ContentFile
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from sql_util.utils import SubqueryCount
from taggit.serializers import TagListSerializerField

import company.filters
import part.filters
import part.serializers as part_serializers
from importer.registry import register_importer
from InvenTree.mixins import DataImportExportSerializerMixin
from InvenTree.ready import isGeneratingSchema
from InvenTree.serializers import (
    InvenTreeCurrencySerializer,
    InvenTreeDecimalField,
    InvenTreeImageSerializerField,
    InvenTreeModelSerializer,
    InvenTreeMoneySerializer,
    InvenTreeTagModelSerializer,
    NotesFieldMixin,
    RemoteImageMixin,
)

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

# [AGENT GENERATED CODE - REQUIREMENT:BULK_UPLOAD_VENDOR_CATEGORIES]
@register_importer()
class CompanyCategoryImportSerializer(DataImportExportSerializerMixin, InvenTreeModelSerializer):
    """Serializer for importing CompanyCategory data."""

    class Meta:
        """Metaclass options."""

        model = CompanyCategory
        fields = [
            'pk',
            'name',
            'description',
            'parent',
            'default_location',
        ]
        
    def validate_parent(self, value):
        """Validate the parent field does not cause recursive hierarchy."""
        if value == self.instance:
            raise serializers.ValidationError(_("Category cannot be parent of itself"))
        
        # Check for parent loop recursion
        parent = value
        while parent is not None:
            if parent == self.instance:
                raise serializers.ValidationError(_("Parent category creates recursive loop"))
            parent = parent.parent
        
        return value
# [END AGENT GENERATED CODE]


class CompanyBriefSerializer(InvenTreeModelSerializer):
    """Serializer for Company object (limited detail)."""

    class Meta:
        """Metaclass options."""

        model = Company
        fields = [
            'pk',
            'active',
            'name',
            'description',
            'image',
            'thumbnail',
            'currency',
            'tax_id',
        ]
        read_only_fields = ['currency']

    image = InvenTreeImageSerializerField(read_only=True)

    thumbnail = serializers.CharField(source='get_thumbnail_url', read_only=True)


@register_importer()
class AddressSerializer(DataImportExportSerializerMixin, InvenTreeModelSerializer):
    """Serializer for the Address Model."""

    class Meta:
        """Metaclass options."""

        model = Address
        fields = [
            'pk',
            'company',
            'title',
            'primary',
            'line1',
            'line2',
            'postal_code',
            'postal_city',
            'province',
            'country',
            'shipping_notes',
            'internal_shipping_notes',
            'link',
        ]


class AddressBriefSerializer(InvenTreeModelSerializer):
    """Serializer for Address Model (limited)."""

    class Meta:
        """Metaclass options."""

        model = Address
        fields = [
            'pk',
            'line1',
            'line2',
            'postal_code',
            'postal_city',
            'province',
            'country',
            'shipping_notes',
            'internal_shipping_notes',
            'link',
        ]


@register_importer()
class CompanySerializerExport(DataImportExportSerializerMixin, InvenTreeTagModelSerializer):
    """Serializer for exporting Company."""

    # Get all addresses
    addresses = AddressSerializer(many=True, read_only=True)

    # Special field for tags
    tags = TagListSerializerField(required=False)

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        """Metaclass options."""

        model = Company
        fields = [
            'pk',
            'active',
            'url',
            'name',
            'description',
            'website',
            'phone',
            'email',
            'contact',
            'currency',
            'tax_id',
            'link',
            'is_customer',
            'is_manufacturer',
            'is_supplier',
            'notes',
            'tags',
            'addresses',
        ]
        read_only_fields = ['currency']


# [AGENT GENERATED CODE - REQUIREMENT:DELETE_VENDOR_CATEGORIES]
class CompanyCategorySerializer(InvenTreeModelSerializer):
    """Serializer for CompanyCategory."""

    class Meta:
        """Metaclass defining serializer fields."""
        model = CompanyCategory
        fields = [
            'pk',
            'name',
            'description',
            'default_location',
            'level',
            'parent',
            'icon',
            'pathstring',
            'path',
            'company_count',
            'url',
        ]

    def __init__(self, *args, **kwargs):
        """Initialize this serializer with custom fields."""
        super().__init__(*args, **kwargs)

    url = serializers.CharField(source='get_absolute_url', read_only=True)
    
    level = serializers.IntegerField(read_only=True)

    company_count = serializers.IntegerField(read_only=True)

    def get_company_count(self, obj):
        """Return the number of companies in this category."""
        return obj.companies.count()

    def validate_parent(self, value):
        """Validate the parent field does not cause recursive hierarchy."""
        if value == self.instance:
            raise serializers.ValidationError(_("Category cannot be parent of itself"))
        
        # Check for parent loop recursion
        parent = value
        while parent is not None:
            if parent == self.instance:
                raise serializers.ValidationError(_("Parent category creates recursive loop"))
            parent = parent.parent
        
        return value

    def save(self):
        """Save the CompanyCategory instance."""
        super().save()

        # Record the companie count for this category
        self.instance.company_count = self.instance.companies.count()
# [END AGENT GENERATED CODE]


@register_importer()
class ContactSerializer(DataImportExportSerializerMixin, InvenTreeModelSerializer):
    """Serializer for Contact."""

    class Meta:
        """Metaclass options."""

        model = Contact
        fields = [
            'pk',
            'company',
            'name',
            'phone',
            'email',
            'role',
            'company_role',
            'notes',
        ]

    def validate_email(self, email):
        """Ensure that the email field is unique for the company."""
        company = self.context['company']

        # Other contacts
        others = Contact.objects.filter(company=company, email__iexact=email).exclude(pk=self.instance.pk if self.instance else None)

        if others.exists():
            raise serializers.ValidationError(_('Email must be unique for each contact in a company'))

        return email


class ContactBriefSerializer(InvenTreeModelSerializer):
    """Serializer for Contact (limited)."""

    class Meta:
        """Metaclass options."""

        model = Contact
        fields = [
            'pk',
            'name',
            'email',
        ]


@register_importer()
class CompanySerializer(DataImportExportSerializerMixin, RemoteImageMixin, InvenTreeTagModelSerializer):
    """Serializer for Company."""

    # Customer details
    currency = InvenTreeCurrencySerializer(required=False, allow_null=True)

    # Primary address field
    primary_address = AddressBriefSerializer(source='get_primary_address', read_only=True)

    # Special field for tags
    tags = TagListSerializerField(required=False)

    # Image / thumbnail field
    image = InvenTreeImageSerializerField(required=False, allow_null=True)

    thumbnail = serializers.CharField(source='get_thumbnail_url', read_only=True)

    # Number of used parts
    parts_supplied = serializers.IntegerField(read_only=True)
    parts_manufactured = serializers.IntegerField(read_only=True)

    # URL to link to this Company
    url = serializers.CharField(source='get_absolute_url', read_only=True)

    # [AGENT GENERATED CODE - REQUIREMENT:DELETE_VENDOR_CATEGORIES]
    # Category field
    category_detail = CompanyCategorySerializer(source='category', read_only=True)
    # [END AGENT GENERATED CODE]

    class Meta:
        """Metaclass options."""

        model = Company
        fields = [
            'pk',
            'active',
            'url',
            'name',
            'description',
            'website',
            'phone',
            'email',
            'contact',
            'currency',
            'tax_id',
            'link',
            'image',
            'is_customer',
            'is_manufacturer',
            'is_supplier',
            'notes',
            'tags',
            'remote_image',
            'parts_supplied',
            'parts_manufactured',
            'primary_address',
            'thumbnail',
            # [AGENT GENERATED CODE - REQUIREMENT:DELETE_VENDOR_CATEGORIES]
            'category',
            'category_detail',
            # [END AGENT GENERATED CODE]
        ]
        read_only_fields = ['currency']

    def __init__(self, *args, **kwargs):
        """Initialization routine for the CompanySerializer class."""
        data_import = kwargs.pop('data_import', False)

        super().__init__(*args, **kwargs)

        if data_import:
            for field in [
                'phone',
                'email',
                'contact',
                'currency',
                'active',
                'is_customer',
                'is_manufacturer',
                'is_supplier',
            ]:
                # Mark these fields as not required for data import
                self.fields[field].required = False

    @staticmethod
    def annotate_queryset(queryset):
        """Add extra information to the queryset.

        - Number of parts manufactured
        - Number of parts supplied
        """
        # Pre-fetch primary address information
        queryset = queryset.prefetch_related(
            Prefetch(
                'addresses',
                queryset=Address.objects.filter(primary=True),
                to_attr='primary_address_list',
            )
        )

        # Count number of parts manufactured
        queryset = queryset.annotate(
            parts_manufactured=SubqueryCount('manufactured_parts')
        )

        # Count number of parts supplied
        queryset = queryset.annotate(
            parts_supplied=SubqueryCount('supplied_parts')
        )

        return queryset

    def save(self):
        """Save the Company instance."""
        super().save()

        company = self.instance

        # If this is a new Company, create a primary address (placeholder)
        if company and not company.addresses.filter(primary=True).exists():
            address = Address(company=company, primary=True)
            address.save()


class ManufacturerPartSerializer(DataImportExportSerializerMixin, InvenTreeTagModelSerializer):
    """Serializer for ManufacturerPart."""

    def __init__(self, *args, **kwargs):
        """Custom initialization routine for the ManufacturerPartSerializer."""
        manufacturer_detail = kwargs.pop('manufacturer_detail', False)
        part_detail = kwargs.pop('part_detail', False)
        super().__init__(*args, **kwargs)

        if manufacturer_detail is not True:
            self.fields.pop('manufacturer_detail')

        if part_detail is not True:
            self.fields.pop('part_detail')

    tags = TagListSerializerField(required=False)

    name = serializers.CharField(source='get_name', read_only=True)

    # Allow the manufacturer to be specified by name
    manufacturer_name = serializers.CharField(
        read_only=True, allow_null=True, allow_blank=True, source='manufacturer.name'
    )

    # Serial numbers for this manufacturer part
    serial_numbers = serializers.IntegerField(read_only=True)

    # Quantity of tracked items which are in stock
    in_stock = serializers.IntegerField(read_only=True)

    # Alternative to providing a manufacturer
    manufacturer_detail = CompanyBriefSerializer(source='manufacturer', read_only=True)

    # Part reference for this manufacturer part
    part_detail = part_serializers.PartBriefSerializer(source='part', read_only=True)

    # Supplier parts
    supplier_parts = serializers.IntegerField(read_only=True)

    class Meta:
        """Metaclass options."""

        model = ManufacturerPart
        fields = [
            'pk',
            'manufacturer',
            'manufacturer_name',
            'manufacturer_detail',
            'part',
            'part_detail',
            'name',
            'MPN',
            'description',
            'tags',
            'link',
            'supplier_parts',
            'in_stock',
            'serial_numbers',
        ]

        read_only_fields = ['name']

    @extend_schema_field(serializers.IntegerField(help_text=_('Number of parts in stock')))
    def get_in_stock(self, part):
        """Return the number of available parts in stock of the parent part for this ManufacturerPart."""
        if part.part:
            # Return the number of parts in stock
            return part.part.total_stock

        # Part is none, return 0
        return 0

    @staticmethod
    def annotate_queryset(queryset):
        """Add custom annotations to the queryset."""
        return queryset.annotate(
            supplier_parts=SubqueryCount('supplier_parts'),
            in_stock=SubqueryCount('part__stock_items', filter=part.filters.stock_status_filter()),
            serial_numbers=SubqueryCount('part__stock_items__serial'),
        )

    def validate_manufacturer(self, manufacturer):
        """Validate foreign key relationship to Manufacturer."""
        if manufacturer is not None:
            if not manufacturer.is_manufacturer:
                raise serializers.ValidationError(
                    _('Selected company is not a manufacturer')
                )

        return manufacturer

    def validate_part(self, part):
        """Validate that the linked part is a valid component."""
        if part is not None:
            if part.is_template:
                raise serializers.ValidationError(
                    _('Template part cannot have manufacturer part')
                )

            if part.assembly:
                raise serializers.ValidationError(
                    _('Assembly part cannot have manufacturer part')
                )

            if part.virtual:
                raise serializers.ValidationError(
                    _('Virtual part cannot have manufacturer part')
                )

        return part


@register_importer()
class ManufacturerPartImportSerializer(ManufacturerPartSerializer):
    """Serializer for importing ManufacturerPart."""

    import_only_fields = ['manufacturer_name']

    def validate(self, data):
        """Validate the ManufacturerPart data by handling manufacturer name imports."""
        data = super().validate(data)

        name = data.get('manufacturer_name', None)

        manufacturer = data.get('manufacturer', None)

        # Set the manufacturer by name (if provided)
        if name:
            matches = Company.objects.filter(name=name, is_manufacturer=True)

            if len(matches) == 1:
                manufacturer = matches[0]
            else:
                raise serializers.ValidationError({
                    'manufacturer_name': _('Manufacturer not found'),
                })

            data['manufacturer'] = manufacturer

        elif manufacturer is None:
            raise serializers.ValidationError({
                'manufacturer': _('Manufacturer must be provided'),
            })

        return data


class ManufacturerPartParameterSerializer(InvenTreeModelSerializer):
    """Serializer for the ManufacturerPartParameter model."""

    class Meta:
        """Metaclass options."""

        model = ManufacturerPartParameter
        fields = [
            'pk',
            'manufacturer_part',
            'name',
            'value',
            'units',
        ]


class ManufacturerPartAttachmentSerializer(InvenTreeModelSerializer):
    """Serializer for the ManufacturerPartAttachment model."""

    class Meta:
        """Metaclass options."""

        model = ManufacturerPartParameter
        fields = [
            'pk',
            'manufacturer_part',
            'attachment',
            'comment',
        ]


class SupplierPartSerializer(DataImportExportSerializerMixin, InvenTreeTagModelSerializer):
    """Serializer for SupplierPart."""

    def __init__(self, *args, **kwargs):
        """Custom initialization for this serializer.

        - Add detail fields if required
        """
        supplier_detail = kwargs.pop('supplier_detail', False)
        part_detail = kwargs.pop('part_detail', False)
        manufacturer_detail = kwargs.pop('manufacturer_detail', False)
        pricing_detail = kwargs.pop('pricing_detail', False)
        pretty = kwargs.pop('pretty', False)

        super().__init__(*args, **kwargs)

        if supplier_detail is not True:
            self.fields.pop('supplier_detail')

        if part_detail is not True:
            self.fields.pop('part_detail')

        if manufacturer_detail is not True:
            self.fields.pop('manufacturer_detail')

        if pricing_detail is not True:
            self.fields.pop('price_breaks')

        if pretty is not True:
            self.fields.pop('pretty_price')
            self.fields.pop('pretty_availability')

    tags = TagListSerializerField(required=False)

    part_detail = part_serializers.PartBriefSerializer(source='get_base_part', read_only=True)

    supplier_detail = CompanyBriefSerializer(source='supplier', read_only=True)

    manufacturer_detail = ManufacturerPartSerializer(source='manufacturer_part', read_only=True)

    price_breaks = serializers.SerializerMethodField()

    pretty_price = serializers.SerializerMethodField()

    pretty_availability = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField(help_text=_('Price as string')))
    def get_pretty_price(self, supplier_part):
        """Get a pretty price value for display."""
        return supplier_part.pretty_price

    @extend_schema_field(serializers.CharField(help_text=_('Availability as string')))
    def get_pretty_availability(self, supplier_part):
        """Get a pretty availability value for display."""
        return supplier_part.pretty_availability

    @extend_schema_field(serializers.ListField(help_text=_('List of supplier price breaks')))
    def get_price_breaks(self, supplier_part):
        """Return serialized price breaks."""
        if isGeneratingSchema():
            return []

        # No pricing information for supplier part
        if supplier_part.pk is None:
            return []

        from .models import SupplierPriceBreak

        return [
            SupplierPriceBreakSerializer(pb, many=False, context=self.context).data
            for pb in SupplierPriceBreak.objects.filter(part=supplier_part).order_by('quantity')
        ]

    class Meta:
        """Metaclass options."""

        model = SupplierPart
        fields = [
            'pk',
            'part',
            'part_detail',
            'supplier',
            'supplier_detail',
            'manufacturer_part',
            'manufacturer_detail',
            'SKU',
            'description',
            'link',
            'tags',
            'note',
            'base_cost',
            'multiple',
            'minimum_order',
            'packaging',
            'pack_size',
            'pack_quantity',
            'available',
            'availability_updated',
            'lead_time',
            'active',
            'price_breaks',
            'pretty_price',
            'pretty_availability',
        ]

        read_only_fields = ['part_detail']

    @staticmethod
    def annotate_queryset(queryset):
        """Ensure all parent detail objects are annotated."""
        return queryset.annotate(
            base_part_available=part.filters.get_stock_count_label('part'),
        )

    def validate_supplier(self, supplier):
        """Validate supplier field."""
        if supplier is not None:
            if not supplier.is_supplier:
                raise serializers.ValidationError(
                    _('Selected company is not a supplier')
                )

        return supplier


@register_importer()
class SupplierPartImportSerializer(SupplierPartSerializer):
    """Special serializer class for importing SupplierPart data."""

    manufacturer_name = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)
    manufacturer_mpn = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)
    supplier_name = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)
    part_name = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)
    part_ipn = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)

    import_only_fields = ['manufacturer_name', 'manufacturer_mpn', 'supplier_name', 'part_name', 'part_ipn']

    def validate(self, data):
        """Validation for the serializer."""
        data = super().validate(data)

        # Add manufacturer part link
        manufacturer_name = data.pop('manufacturer_name', None)
        manufacturer_mpn = data.pop('manufacturer_mpn', None)

        part = data.get('part', None)
        supplier = data.get('supplier', None)

        # Construct a part reference
        if part is None and supplier is None:
            # Check if part_name is supplied
            part_name = data.pop('part_name', None)
            part_ipn = data.pop('part_ipn', None)

            if part_name or part_ipn:
                queryset = part.models.Part.objects.all()

                if part_name:
                    queryset = queryset.filter(name=part_name)

                if part_ipn:
                    queryset = queryset.filter(IPN=part_ipn)

                try:
                    data['part'] = queryset.get()
                except (
                    part.models.Part.DoesNotExist,
                    part.models.Part.MultipleObjectsReturned,
                ):
                    raise serializers.ValidationError({
                        'part_name': _('Part not found')
                    })

        if supplier is None:
            supplier_name = data.pop('supplier_name', None)

            if supplier_name:
                try:
                    data['supplier'] = Company.objects.filter(name=supplier_name, is_supplier=True).get()
                except Company.DoesNotExist:
                    raise serializers.ValidationError({
                        'supplier_name': _('Supplier not found')
                    })

        if manufacturer_mpn:
            try:
                manufacturer = None

                if manufacturer_name:
                    manufacturer = Company.objects.filter(name=manufacturer_name, is_manufacturer=True).get()

                queryset = ManufacturerPart.objects.all(MPN=manufacturer_mpn)

                if manufacturer:
                    queryset = queryset.filter(manufacturer=manufacturer)

                data['manufacturer_part'] = queryset.get()
            except (ManufacturerPart.DoesNotExist, ManufacturerPart.MultipleObjectsReturned):
                raise serializers.ValidationError({
                    'manufacturer_mpn': _('Manufacturer part not found'),
                })

        return data


class SupplierPriceBreakSerializer(DataImportExportSerializerMixin, InvenTreeModelSerializer):
    """Serializer for SupplierPriceBreak object."""

    price = InvenTreeMoneySerializer(source='cost', allow_null=True)

    price_currency = serializers.CharField(source='currency', read_only=True)

    supplier_part_detail = SupplierPartSerializer(source='part', read_only=True)

    class Meta:
        """Metaclass options."""

        model = SupplierPriceBreak
        fields = [
            'pk',
            'part',
            'supplier_part_detail',
            'quantity',
            'price',
            'price_currency',
            'updated',
        ]


@register_importer()
class SupplierPriceBreakImportSerializer(SupplierPriceBreakSerializer):
    """Serializer for importing SupplierPriceBreak data."""

    part_sku = serializers.CharField(read_only=True, allow_blank=False, allow_null=False)
    supplier_name = serializers.CharField(read_only=True, allow_blank=False, allow_null=False)

    import_only_fields = ['part_sku', 'supplier_name']

    def validate(self, data):
        """Import data validation."""
        data = super().validate(data)

        part = data.get('part', None)

        part_sku = data.get('part_sku', None)
        supplier_name = data.get('supplier_name', None)

        if part is None:
            if part_sku and supplier_name:
                try:
                    supplier = Company.objects.filter(name=supplier_name, is_supplier=True).get()
                    data['part'] = SupplierPart.objects.filter(SKU=part_sku, supplier=supplier).get()
                except (Company.DoesNotExist, SupplierPart.DoesNotExist):
                    raise serializers.ValidationError({
                        'supplier_part': _('Supplier part not found'),
                    })
        else:
            # Make sure the provided SupplierPart is valid
            try:
                SupplierPart.objects.get(pk=part.pk)
            except SupplierPart.DoesNotExist:
                raise serializers.ValidationError({
                    'part': _('Supplier part not found'),
                })

        return data


class SupplierPriceBreakBulkDeleteSerializer(serializers.Serializer):
    """Serializer for bulk deletion of supplier price breaks."""

    items = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=SupplierPriceBreak.objects.all(),
        required=True,
    )

    class Meta:
        """Metaclass options."""

        fields = ['items']


class SupplierPriceBreakAttachmentSerializer(InvenTreeModelSerializer):
    """Serializer for the SupplierPriceBreakAttachment model."""

    class Meta:
        """Metaclass options."""

        model = SupplierPriceBreak
        fields = [
            'pk',
            'supplier_part',
            'attachment',
            'comment',
        ]


class SupplierPartAttachmentSerializer(InvenTreeModelSerializer):
    """Serializer for the SupplierPartAttachment model."""

    class Meta:
        """Metaclass options."""

        model = SupplierPart
        fields = [
            'pk',
            'supplier_part',
            'attachment',
            'comment',
        ]