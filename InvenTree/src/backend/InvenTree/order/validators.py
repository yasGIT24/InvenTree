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


def validate_sales_order_line_edit(line_item, changes, user):
    """Validate edits to sales order line items.
    
    Args:
        line_item: The SalesOrderLineItem object being edited
        changes: Dictionary of changes to be applied
        user: The user making the changes
        
    Returns:
        bool: True if the changes are valid and can be applied directly, False if approval is needed
        
    Raises:
        ValidationError: If the changes are invalid and cannot be applied
    
    [AGENT GENERATED CODE - REQUIREMENT:Edit Individual Line Items in Sales Orders]
    """
    from django.core.exceptions import ValidationError
    from django.utils.translation import gettext_lazy as _

    needs_approval = False
    errors = {}
    
    # Check if the sales order is in a state where edits are allowed
    if line_item.order.status not in [10, 15, 25]:  # Pending, In Progress, On Hold
        raise ValidationError({
            'order': _('Cannot edit line items for an order that is not open')
        })
    
    # Check quantity changes
    if 'quantity' in changes:
        try:
            new_quantity = float(changes['quantity'])
            if new_quantity <= 0:
                errors['quantity'] = _('Quantity must be greater than zero')
            
            # Check if the change requires approval
            # Quantity increase of more than 20% requires approval
            if new_quantity > (line_item.quantity * 1.2):
                needs_approval = True
                
        except (ValueError, TypeError):
            errors['quantity'] = _('Invalid quantity value')
    
    # Check price changes
    if 'sale_price' in changes and changes['sale_price']:
        try:
            new_price_value = float(changes['sale_price'].amount)
            if new_price_value < 0:
                errors['sale_price'] = _('Price cannot be negative')
                
            # Price decreases of more than 10% require approval
            if line_item.sale_price and new_price_value < (float(line_item.sale_price.amount) * 0.9):
                needs_approval = True
                
        except (ValueError, TypeError, AttributeError):
            errors['sale_price'] = _('Invalid price value')
    
    # Check part changes
    if 'part' in changes and changes['part'] != line_item.part:
        # Part changes always require approval
        needs_approval = True
        
        # Check if the new part exists and is salable
        if changes['part'] and not changes['part'].salable:
            errors['part'] = _('Selected part is not salable')
    
    if errors:
        raise ValidationError(errors)
        
    # Check if user has approval rights
    if needs_approval and user and user.has_perm('order.approve_salesorderlineitem'):
        # User has approval rights, so changes can be applied immediately
        return True
        
    return not needs_approval  # True if no approval needed, False if approval required
