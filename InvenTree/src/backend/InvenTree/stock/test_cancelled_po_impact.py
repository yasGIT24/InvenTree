"""Unit tests for tracking cancelled purchase orders in inventory.

[AGENT GENERATED CODE - REQUIREMENT:Track and Display Cancelled Supplier Purchase Orders in Inventory]
"""

from django.db.models import Sum
from django.test import TestCase

from InvenTree.unit_test import InvenTreeTestCase
from order.models import PurchaseOrder, PurchaseOrderLineItem
from order.status_codes import PurchaseOrderStatus
from stock.models import StockItem


class CancelledPurchaseOrderTests(InvenTreeTestCase):
    """Tests for cancelled purchase orders and their impact on inventory calculations."""

    fixtures = [
        'category',
        'company',
        'location',
        'part',
        'supplier_part',
        'stock',
        'purchase_order',
        'users',
    ]

    def setUp(self):
        """Set up for tests."""
        super().setUp()
        
        # Get a purchase order that's in the PLACED state
        self.order = PurchaseOrder.objects.filter(status=PurchaseOrderStatus.PLACED.value).first()
        
        # If no order exists in the placed state, create one
        if not self.order:
            self.order = PurchaseOrder.objects.first()
            self.order.status = PurchaseOrderStatus.PLACED.value
            self.order.save()
            
        # Get the line items
        self.line_items = PurchaseOrderLineItem.objects.filter(order=self.order)
        
        # Make sure we have at least one line item
        if self.line_items.count() == 0:
            # Create a supplier part
            from company.models import SupplierPart
            supplier_part = SupplierPart.objects.first()
            
            # Create a line item
            line = PurchaseOrderLineItem.objects.create(
                order=self.order,
                part=supplier_part,
                quantity=10,
                received=0
            )
            self.line_items = PurchaseOrderLineItem.objects.filter(order=self.order)

    def test_cancel_purchase_order(self):
        """Test cancelling a purchase order."""
        
        # Get the parts and their initial stock counts
        parts = {}
        for item in self.line_items:
            part = item.part.part
            parts[part.pk] = {
                'part': part,
                'initial_stock': part.total_stock,
                'on_order': part.on_order
            }
            
        # Ensure we're tracking quantities
        for pk, data in parts.items():
            self.assertTrue(data['on_order'] > 0, f"Part {pk} should have items on order")
        
        # Cancel the order
        self.order.status = PurchaseOrderStatus.CANCELLED.value
        self.order.save()
        
        # Refresh parts data
        for pk in parts.keys():
            part = parts[pk]['part']
            part.refresh_from_db()
            parts[pk]['cancelled_stock'] = part.total_stock
            parts[pk]['cancelled_on_order'] = part.on_order
            
        # Verify that on_order quantities have been updated
        for pk, data in parts.items():
            # Cancelled orders should not contribute to on_order quantity
            self.assertEqual(data['cancelled_on_order'], 0, f"Part {pk} should have 0 items on order after cancellation")
            
            # Stock levels should remain unchanged
            self.assertEqual(data['initial_stock'], data['cancelled_stock'], 
                          f"Stock level for part {pk} should not change when cancelling an order")
            
    def test_cancelled_po_in_reports(self):
        """Test that cancelled POs appear in reconciliation reports."""
        
        # Cancel the order
        self.order.status = PurchaseOrderStatus.CANCELLED.value
        self.order.save()
        
        # Create some stock items from this cancelled PO
        for line in self.line_items:
            StockItem.objects.create(
                part=line.part.part,
                supplier_part=line.part,
                quantity=line.quantity,
                purchase_order=self.order,
                is_from_cancelled_po=True
            )
        
        # Get all stock from cancelled POs
        cancelled_stock = StockItem.objects.filter(is_from_cancelled_po=True)
        
        # Verify we have stock items
        self.assertTrue(cancelled_stock.count() > 0, "Should have stock items from cancelled POs")
        
        # Test stock reporting calculations
        for line in self.line_items:
            part = line.part.part
            
            # Get all stock for this part from cancelled POs
            cancelled_items = StockItem.objects.filter(
                part=part,
                is_from_cancelled_po=True
            )
            
            # Sum the quantities
            cancelled_quantity = cancelled_items.aggregate(
                q=Sum('quantity')
            )['q'] or 0
            
            # There should be stock from cancelled POs
            self.assertTrue(cancelled_quantity > 0, f"Part {part.pk} should have stock from cancelled POs")
            
    def test_inventory_calculations(self):
        """Test that inventory calculations exclude cancelled POs."""
        
        # Cancel the order
        self.order.status = PurchaseOrderStatus.CANCELLED.value
        self.order.save()
        
        # Verify that the cancelled order is not included in stock calculations
        for line in self.line_items:
            part = line.part.part
            
            # Test the on_order quantity
            self.assertEqual(part.on_order, 0, f"Part {part.pk} should have 0 on order after cancellation")
            
            # Create a new order for this part
            new_order = PurchaseOrder.objects.create(
                supplier=line.order.supplier,
                status=PurchaseOrderStatus.PLACED.value
            )
            
            # Add a line item
            new_line = PurchaseOrderLineItem.objects.create(
                order=new_order,
                part=line.part,
                quantity=5
            )
            
            # Refresh the part
            part.refresh_from_db()
            
            # Verify the on_order quantity only includes the new order
            self.assertEqual(part.on_order, 5, f"Part {part.pk} should only include the new order in on_order")