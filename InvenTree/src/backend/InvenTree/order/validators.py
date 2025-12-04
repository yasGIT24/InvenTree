"""Validation methods for the order app."""


def generate_next_sales_order_reference():
    """Generate the next available SalesOrder reference."""
    from order.models import SalesOrder

    return SalesOrder.generate_reference()


def generate_next_purchase_order_reference():
    """Generate the next available PurchasesOrder reference."""
    from order.models import PurchaseOrder

    return PurchaseOrder.generate_reference()


def generate_next_return_order_reference():
    """Generate the next available ReturnOrder reference."""
    from order.models import ReturnOrder

    return ReturnOrder.generate_reference()


def validate_sales_order_reference_pattern(pattern):
    """Validate the SalesOrder reference 'pattern' setting."""
    from order.models import SalesOrder

    SalesOrder.validate_reference_pattern(pattern)


def validate_purchase_order_reference_pattern(pattern):
    """Validate the PurchaseOrder reference 'pattern' setting."""
    from order.models import PurchaseOrder

    PurchaseOrder.validate_reference_pattern(pattern)


def validate_return_order_reference_pattern(pattern):
    """Validate the ReturnOrder reference 'pattern' setting."""
    from order.models import ReturnOrder

    ReturnOrder.validate_reference_pattern(pattern)


def validate_sales_order_reference(value):
    """Validate that the SalesOrder reference field matches the required pattern."""
    from order.models import SalesOrder

    SalesOrder.validate_reference_field(value)


def validate_purchase_order_reference(value):
    """Validate that the PurchaseOrder reference field matches the required pattern."""
    from order.models import PurchaseOrder

    PurchaseOrder.validate_reference_field(value)


def validate_return_order_reference(value):
    """Validate that the ReturnOrder reference field matches the required pattern."""
    from order.models import ReturnOrder

    ReturnOrder.validate_reference_field(value)


def validate_line_item_data(data):
    """Validate data for a line item in an order.
    
    Args:
        data: Dictionary containing line item data
        
    Returns:
        True if the data is valid
        
    Raises:
        ValidationError: If data validation fails
    """
    from django.core.exceptions import ValidationError
    from django.utils.translation import gettext_lazy as _
    
    errors = {}
    
    # Required fields for line items
    required_fields = ['order', 'quantity']
    
    for field in required_fields:
        if field not in data or data[field] is None:
            errors[field] = _('This field is required')
            
    # Validate quantity
    if 'quantity' in data and data['quantity'] is not None:
        try:
            quantity = float(data['quantity'])
            
            if quantity <= 0:
                errors['quantity'] = _('Quantity must be greater than zero')
                
        except (ValueError, TypeError):
            errors['quantity'] = _('Invalid quantity value')
            
    # Part validation depends on order type
    if 'order' in data and data['order'] is not None:
        order = data['order']
        
        # Different validation rules based on order type
        from order.models import PurchaseOrder, SalesOrder
        
        if isinstance(order, PurchaseOrder):
            # Purchase order line item requires a supplier part
            if 'part' not in data or not data['part']:
                errors['part'] = _('Supplier part must be specified')
                
            # Check if supplier part matches the order supplier
            if 'part' in data and data['part']:
                supplier_part = data['part']
                
                if supplier_part.supplier != order.supplier:
                    errors['part'] = _('Supplier part must match the order supplier')
                    
        elif isinstance(order, SalesOrder):
            # Sales order line item requires a part
            if 'part' not in data or not data['part']:
                errors['part'] = _('Part must be specified')
                
            # Check if part is salable
            if 'part' in data and data['part']:
                part = data['part']
                
                if not part.salable:
                    errors['part'] = _('Part must be salable')
    
    if errors:
        raise ValidationError(errors)
        
    return True


def validate_vendor_category(data):
    """Validate vendor category data.
    
    Args:
        data: Dictionary containing vendor category data
        
    Returns:
        True if the data is valid
        
    Raises:
        ValidationError: If data validation fails
    """
    from django.core.exceptions import ValidationError
    from django.utils.translation import gettext_lazy as _
    
    errors = {}
    
    # Check for recursive parent relationship
    if 'parent' in data and data['parent'] and 'id' in data and data['parent'] == data['id']:
        errors['parent'] = _('Category cannot be parent of itself')
        
    # Validate parent is not a descendant of this category
    if 'parent' in data and data['parent'] and 'id' in data:
        parent = data['parent']
        category_id = data['id']
        
        from company.models import CompanyCategory
        
        try:
            category = CompanyCategory.objects.get(pk=category_id)
            
            # Check if parent is in the descendants of this category
            if parent in category.get_descendants(include_self=False):
                errors['parent'] = _('Parent cannot be a descendant of this category')
                
        except (CompanyCategory.DoesNotExist, AttributeError):
            pass
    
    if errors:
        raise ValidationError(errors)
        
    return True


def validate_bulk_import_data(data, model_class):
    """Validate data for bulk import operations.
    
    Args:
        data: List of dictionaries containing data to import
        model_class: The model class to validate against
        
    Returns:
        True if the data is valid
        
    Raises:
        ValidationError: If data validation fails
    """
    from django.core.exceptions import ValidationError
    from django.utils.translation import gettext_lazy as _
    
    errors = {}
    
    # Get the field list from the serializer for this model
    serializer_class = None
    
    # Import registration module
    from importer.registry import registry
    
    # Find the serializer for this model
    for item in registry.items():
        if item[1].get('model') == model_class:
            serializer_class = item[1].get('serializer')
            break
            
    if not serializer_class:
        # No serializer found, cannot validate
        return True
        
    # Get fields from serializer
    serializer_fields = serializer_class().get_importable_fields()
    
    if not serializer_fields:
        # No fields to validate
        return True
        
    # Validate each row
    for idx, row in enumerate(data):
        row_errors = {}
        
        # Check required fields
        for field_name, field in serializer_fields.items():
            if field.required and field_name not in row:
                row_errors[field_name] = _('This field is required')
                
        if row_errors:
            errors[f'row_{idx}'] = row_errors
            
    if errors:
        raise ValidationError(errors)
        
    return True
