"""Validation methods for the order app."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


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


# [AGENT GENERATED CODE - REQUIREMENT:Implement Data Integrity Validation]
def validate_line_item_edit(line_item, quantity=None, price=None, reference=None):
    """Validate editing of an order line item.
    
    This function validates that the requested changes to a line item are allowed based on:
    1. Order status (cannot edit items in cancelled/completed orders)
    2. Line item status (cannot reduce quantity below what's already received/shipped)
    3. Business rules (cannot set negative quantity/price)
    
    Args:
        line_item: The order line item being modified
        quantity: The new quantity value (if being changed)
        price: The new price value (if being changed)
        reference: The new reference value (if being changed)
        
    Raises:
        ValidationError: If the requested changes violate business rules
    """
    from order.models import PurchaseOrderLineItem, SalesOrderLineItem
    from order.status_codes import PurchaseOrderStatusGroups, SalesOrderStatusGroups
    
    errors = {}
    
    # Check if the parent order is in a state where editing is allowed
    if isinstance(line_item, PurchaseOrderLineItem):
        order = line_item.order
        
        # Cannot edit line items in cancelled/completed orders
        if order.status in PurchaseOrderStatusGroups.FAILED:
            errors['order'] = _('Cannot edit line items in a cancelled or failed order')
        
        # Check that quantity isn't being reduced below what's already received
        if quantity is not None and quantity < line_item.received:
            errors['quantity'] = _('Cannot reduce quantity below the amount already received')
    
    elif isinstance(line_item, SalesOrderLineItem):
        order = line_item.order
        
        # Cannot edit line items in cancelled/completed orders
        if order.status in [40, 50, 60]:  # Cancelled, Lost, Returned
            errors['order'] = _('Cannot edit line items in a cancelled or failed order')
        
        # Check that quantity isn't being reduced below what's already shipped/allocated
        if quantity is not None:
            shipped = line_item.shipped
            if quantity < shipped:
                errors['quantity'] = _('Cannot reduce quantity below the amount already shipped')
    
    # General validation
    if quantity is not None and quantity <= 0:
        errors['quantity'] = _('Quantity must be greater than zero')
    
    if price is not None and price < 0:
        errors['price'] = _('Price cannot be negative')
    
    if errors:
        raise ValidationError(errors)
# [END AGENT GENERATED CODE]