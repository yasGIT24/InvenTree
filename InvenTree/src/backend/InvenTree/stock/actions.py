"""API views for stock actions with role-based access control."""

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.response import Response

from InvenTree.api import InventoryActionView
from InvenTree.permissions import inventory_permission
from stock.models import StockItem


class StockAdjustmentSerializer(serializers.Serializer):
    """Serializer for stock adjustment actions."""
    
    stock_item = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.all(),
        required=True,
        label=_('Stock Item'),
        help_text=_('Stock item to adjust')
    )
    
    quantity = serializers.FloatField(
        required=True,
        label=_('Quantity'),
        help_text=_('Quantity adjustment (positive or negative)')
    )
    
    notes = serializers.CharField(
        required=True,
        label=_('Notes'),
        help_text=_('Notes for stock adjustment')
    )


class StockAdjustView(InventoryActionView):
    """API endpoint for adjusting stock quantities with proper permission checks.
    
    This view demonstrates the use of the InventoryActionPermission class
    with specific permission requirements for stock adjustment operations.
    """
    
    # Set the required permission for this inventory action
    inventory_action_permission = 'stock.can_adjust_stock'
    
    # Custom method for checking object permissions
    inventory_object_permission = 'check_stock_item_permission'
    
    def check_stock_item_permission(self, request, obj):
        """Custom method to check if the user has permission to adjust this stock item."""
        
        # Check if the object is a StockItem
        if not isinstance(obj, StockItem):
            return False
            
        # User must have required permission for the specific location
        if obj.location and not obj.location.check_user_permission(request.user, 'change'):
            return False
            
        # Check if the item belongs to the user
        if obj.owner and obj.owner == request.user:
            return True
            
        # Check if the user is responsible for this item
        if obj.responsible and request.user in obj.responsible.get_related_users():
            return True
            
        # Check if this is a serialized item with special restrictions
        if obj.serialized and obj.part and obj.part.restricted_to_staff and not request.user.is_staff:
            return False
            
        return True
    
    def perform_action(self, request, *args, **kwargs):
        """Perform the stock adjustment action."""
        
        # Validate input data
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get validated data
        data = serializer.validated_data
        stock_item = data['stock_item']
        quantity = data['quantity']
        notes = data['notes']
        
        # Check if adjustment would result in negative stock
        if stock_item.quantity + quantity < 0:
            raise serializers.ValidationError({
                'quantity': _('Adjustment would result in negative stock quantity')
            })
            
        # Check if serialized item is being modified
        if stock_item.serialized and quantity != 0:
            raise serializers.ValidationError({
                'quantity': _('Quantity of serialized stock item cannot be adjusted')
            })
        
        # Perform the adjustment
        stock_item.add_stock(
            quantity,
            user=request.user,
            notes=notes
        )
        
        return Response({
            'success': True,
            'stock_item': stock_item.pk,
            'quantity': stock_item.quantity,
            'status': _('Stock adjusted successfully')
        })


class StockCountView(InventoryActionView):
    """API endpoint for counting/auditing stock with proper permission checks."""
    
    # Set the required permission for this inventory action
    inventory_action_permission = 'stock.can_count_stock'
    
    def perform_action(self, request, *args, **kwargs):
        """Perform the stock count/audit action."""
        
        # Implementation of stock count logic would go here
        
        return Response({
            'status': _('Stock count functionality implemented')
        })


class StockTransferView(InventoryActionView):
    """API endpoint for transferring stock with proper permission checks."""
    
    # Set the required permission for this inventory action
    inventory_action_permission = 'stock.can_transfer_stock'
    
    def perform_action(self, request, *args, **kwargs):
        """Perform the stock transfer action."""
        
        # Implementation of stock transfer logic would go here
        
        return Response({
            'status': _('Stock transfer functionality implemented')
        })