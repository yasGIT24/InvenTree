"""Unit tests for cancelled purchase order functionality."""

from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from company.models import Company, SupplierPart
from InvenTree.unit_test import InvenTreeAPITestCase
from order.models import PurchaseOrder, PurchaseOrderLineItem
from order.status_codes import PurchaseOrderStatus
from part.models import Part
from stock.models import StockItem


# [AGENT GENERATED CODE - REQUIREMENT: USX]
# [AGENT SUMMARY: See requirement IDs US4, US5, US6 for agent run change_impact_analysis_review_final]
# Comprehensive test suite for cancelled purchase order functionality including:
# - Cancelled PO visibility in inventory modules
# - Exclusion from inventory calculations and projections
# - Display in reconciliation reports
# - Impact on stock level calculations


class CancelledPurchaseOrderTest(InvenTreeAPITestCase):
    """Test suite for cancelled purchase order operations."""

    roles = [
        'order.add_purchaseorder',
        'order.change_purchaseorder', 
        'order.view_purchaseorder',
        'order.delete_purchaseorder'
    ]

    @classmethod
    def setUpTestData(cls):
        """Set up test data for cancelled purchase order tests."""
        super().setUpTestData()
        
        # Create test company and parts
        cls.supplier = Company.objects.create(
            name='Test Supplier',
            description='Test supplier company',
            is_supplier=True
        )
        
        cls.part = Part.objects.create(
            name='Test Part',
            description='Test part for cancelled PO testing',
            purchaseable=True,
            trackable=True
        )
        
        cls.supplier_part = SupplierPart.objects.create(
            supplier=cls.supplier,
            part=cls.part,
            SKU='SUPPLIER-PART-001'
        )
        
        # Create active purchase order
        cls.active_po = PurchaseOrder.objects.create(
            supplier=cls.supplier,
            reference='PO-ACTIVE-001',
            description='Active purchase order',
            status=PurchaseOrderStatus.PENDING
        )
        
        cls.active_line_item = PurchaseOrderLineItem.objects.create(
            order=cls.active_po,
            part=cls.supplier_part,
            quantity=50,
            purchase_price=15.00
        )
        
        # Create cancelled purchase order
        cls.cancelled_po = PurchaseOrder.objects.create(
            supplier=cls.supplier,
            reference='PO-CANCELLED-001', 
            description='Cancelled purchase order',
            status=PurchaseOrderStatus.CANCELLED
        )
        
        cls.cancelled_line_item = PurchaseOrderLineItem.objects.create(
            order=cls.cancelled_po,
            part=cls.supplier_part,
            quantity=30,
            purchase_price=15.00
        )
        
        # Create some stock for calculations
        cls.stock_item = StockItem.objects.create(
            part=cls.part,
            quantity=25,
            location_detail={'name': 'Test Location'}
        )

    def test_cancelled_po_visibility_in_order_lists(self):
        """Test cancelled POs are visible with clear cancellation status."""
        url = reverse('api-po-list')
        
        response = self.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Find both orders in response
        orders = response.data['results']
        
        active_order = next((o for o in orders if o['pk'] == self.active_po.pk), None)
        cancelled_order = next((o for o in orders if o['pk'] == self.cancelled_po.pk), None)
        
        self.assertIsNotNone(active_order)
        self.assertIsNotNone(cancelled_order)
        
        # Verify cancelled status is clearly marked
        self.assertEqual(cancelled_order['status'], PurchaseOrderStatus.CANCELLED)
        self.assertIn('cancelled', cancelled_order.get('status_text', '').lower())

    def test_cancelled_po_excluded_from_inventory_projections(self):
        """Test cancelled POs are excluded from projected stock calculations."""
        url = reverse('api-part-detail', kwargs={'pk': self.part.pk})
        params = {'include_projections': True}
        
        response = self.get(url, params)
        self.assertEqual(response.status_code, 200)
        
        part_data = response.data
        
        # Current stock should be 25 (from stock item)
        self.assertEqual(part_data['in_stock'], 25)
        
        # Projected stock should only include active PO (50), not cancelled PO (30)
        expected_projected = 25 + 50  # current stock + active PO
        self.assertEqual(part_data['projected_stock'], expected_projected)
        
        # Verify cancelled PO quantity not included
        self.assertNotEqual(part_data['projected_stock'], 25 + 50 + 30)

    def test_cancelled_po_appears_in_reconciliation_reports(self):
        """Test cancelled POs appear in inventory reconciliation reports."""
        url = reverse('api-inventory-reconciliation')
        params = {'part': self.part.pk, 'include_cancelled': True}
        
        response = self.get(url, params)
        self.assertEqual(response.status_code, 200)
        
        reconciliation_data = response.data
        
        # Verify both active and cancelled orders appear
        orders = reconciliation_data.get('purchase_orders', [])
        
        active_found = any(o['pk'] == self.active_po.pk for o in orders)
        cancelled_found = any(o['pk'] == self.cancelled_po.pk for o in orders)
        
        self.assertTrue(active_found)
        self.assertTrue(cancelled_found)
        
        # Verify cancelled order is clearly marked
        cancelled_order_data = next((o for o in orders if o['pk'] == self.cancelled_po.pk), None)
        self.assertEqual(cancelled_order_data['status'], PurchaseOrderStatus.CANCELLED)
        self.assertTrue(cancelled_order_data.get('excluded_from_calculations', False))

    def test_inventory_calculations_exclude_cancelled_pos(self):
        """Test inventory calculation algorithms exclude cancelled POs."""
        # Get inventory summary
        url = reverse('api-inventory-summary')
        params = {'part': self.part.pk}
        
        response = self.get(url, params)
        self.assertEqual(response.status_code, 200)
        
        inventory_data = response.data
        
        # Verify calculations
        self.assertEqual(inventory_data['current_stock'], 25)
        self.assertEqual(inventory_data['on_order'], 50)  # Only active PO
        self.assertEqual(inventory_data['available'], 75)  # 25 + 50
        
        # Verify cancelled PO not included in totals
        self.assertNotEqual(inventory_data['on_order'], 80)  # 50 + 30

    def test_cancelled_po_status_update_recalculates_projections(self):
        """Test cancelling a PO updates inventory projections."""
        # Get initial projections
        url = reverse('api-part-detail', kwargs={'pk': self.part.pk})
        params = {'include_projections': True}
        
        response = self.get(url, params)
        initial_projected = response.data['projected_stock']
        
        # Cancel the active PO
        po_url = reverse('api-po-detail', kwargs={'pk': self.active_po.pk})
        cancel_data = {'status': PurchaseOrderStatus.CANCELLED}
        
        response = self.patch(po_url, cancel_data)
        self.assertEqual(response.status_code, 200)
        
        # Check updated projections
        response = self.get(url, params)
        updated_projected = response.data['projected_stock']
        
        # Projected stock should decrease by cancelled PO quantity
        expected_change = -self.active_line_item.quantity
        self.assertEqual(updated_projected, initial_projected + expected_change)

    def test_cancelled_po_audit_trail(self):
        """Test audit trail for cancelled purchase orders."""
        po_url = reverse('api-po-detail', kwargs={'pk': self.active_po.pk})
        
        cancel_data = {
            'status': PurchaseOrderStatus.CANCELLED,
            'cancellation_reason': 'Supplier no longer available'
        }
        
        with patch('order.models.log_audit_event') as mock_log:
            response = self.patch(po_url, cancel_data)
            self.assertEqual(response.status_code, 200)
            
            # Verify audit log called
            mock_log.assert_called()
            call_args = mock_log.call_args[1]
            
            self.assertEqual(call_args['event_type'], 'purchase_order_cancelled')
            self.assertIn('cancellation_reason', call_args['details'])

    def test_cancelled_po_line_items_not_receivable(self):
        """Test cancelled PO line items cannot be received."""
        url = reverse('api-po-line-receive', kwargs={'pk': self.cancelled_line_item.pk})
        
        receive_data = {
            'quantity': 10,
            'location': 'Test Location'
        }
        
        response = self.post(url, receive_data)
        self.assertEqual(response.status_code, 400)
        
        # Verify error message
        self.assertIn('cancelled', str(response.data).lower())
        self.assertIn('cannot be received', str(response.data).lower())

    def test_cancelled_po_reports_filtering(self):
        """Test filtering options for cancelled POs in reports."""
        # Test excluding cancelled POs
        url = reverse('api-po-list')
        params = {'exclude_cancelled': True}
        
        response = self.get(url, params)
        self.assertEqual(response.status_code, 200)
        
        orders = response.data['results']
        cancelled_order_found = any(o['pk'] == self.cancelled_po.pk for o in orders)
        self.assertFalse(cancelled_order_found)
        
        # Test including only cancelled POs
        params = {'status': PurchaseOrderStatus.CANCELLED}
        
        response = self.get(url, params)
        self.assertEqual(response.status_code, 200)
        
        orders = response.data['results']
        for order in orders:
            self.assertEqual(order['status'], PurchaseOrderStatus.CANCELLED)

    def test_cancelled_po_supplier_order_history(self):
        """Test cancelled POs appear in supplier order history."""
        url = reverse('api-company-order-history', kwargs={'pk': self.supplier.pk})
        
        response = self.get(url)
        self.assertEqual(response.status_code, 200)
        
        order_history = response.data['purchase_orders']
        
        # Verify both orders in history
        active_found = any(o['pk'] == self.active_po.pk for o in order_history)
        cancelled_found = any(o['pk'] == self.cancelled_po.pk for o in order_history)
        
        self.assertTrue(active_found)
        self.assertTrue(cancelled_found)
        
        # Verify cancelled order marked appropriately
        cancelled_order = next((o for o in order_history if o['pk'] == self.cancelled_po.pk), None)
        self.assertTrue(cancelled_order.get('is_cancelled', False))

    def test_cancelled_po_performance_metrics(self):
        """Test cancelled POs impact on supplier performance metrics."""
        url = reverse('api-supplier-metrics', kwargs={'pk': self.supplier.pk})
        
        response = self.get(url)
        self.assertEqual(response.status_code, 200)
        
        metrics = response.data
        
        # Verify cancellation rate calculated
        total_orders = metrics['total_orders']
        cancelled_orders = metrics['cancelled_orders'] 
        cancellation_rate = metrics['cancellation_rate']
        
        self.assertEqual(total_orders, 2)  # Active + cancelled
        self.assertEqual(cancelled_orders, 1)
        self.assertEqual(cancellation_rate, 0.5)  # 1 out of 2

    def test_multiple_cancelled_pos_inventory_impact(self):
        """Test multiple cancelled POs don't affect inventory calculations."""
        # Create another cancelled PO
        cancelled_po_2 = PurchaseOrder.objects.create(
            supplier=self.supplier,
            reference='PO-CANCELLED-002',
            status=PurchaseOrderStatus.CANCELLED
        )
        
        PurchaseOrderLineItem.objects.create(
            order=cancelled_po_2,
            part=self.supplier_part,
            quantity=40,
            purchase_price=15.00
        )
        
        # Check inventory calculations
        url = reverse('api-part-detail', kwargs={'pk': self.part.pk})
        params = {'include_projections': True}
        
        response = self.get(url, params)
        part_data = response.data
        
        # Should still only include active PO (50), not cancelled POs (30 + 40)
        expected_projected = 25 + 50  # current stock + active PO only
        self.assertEqual(part_data['projected_stock'], expected_projected)

    def test_cancelled_po_reactivation_updates_calculations(self):
        """Test reactivating a cancelled PO updates inventory calculations."""
        # Get initial projections
        url = reverse('api-part-detail', kwargs={'pk': self.part.pk})
        params = {'include_projections': True}
        
        response = self.get(url, params)
        initial_projected = response.data['projected_stock']
        
        # Reactivate cancelled PO
        po_url = reverse('api-po-detail', kwargs={'pk': self.cancelled_po.pk})
        reactivate_data = {'status': PurchaseOrderStatus.PENDING}
        
        response = self.patch(po_url, reactivate_data)
        self.assertEqual(response.status_code, 200)
        
        # Check updated projections
        response = self.get(url, params)
        updated_projected = response.data['projected_stock']
        
        # Projected stock should increase by reactivated PO quantity
        expected_increase = self.cancelled_line_item.quantity
        self.assertEqual(updated_projected, initial_projected + expected_increase)

    def tearDown(self):
        """Clean up after each test."""
        super().tearDown()


class CancelledPurchaseOrderIntegrationTest(TestCase):
    """Integration tests for cancelled purchase order functionality."""

    def setUp(self):
        """Set up integration test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_end_to_end_po_cancellation_workflow(self):
        """Test complete PO cancellation workflow and inventory impact."""
        # Create test data
        supplier = Company.objects.create(
            name='Integration Supplier',
            is_supplier=True
        )
        
        part = Part.objects.create(
            name='Integration Part',
            purchaseable=True,
            trackable=True
        )
        
        supplier_part = SupplierPart.objects.create(
            supplier=supplier,
            part=part,
            SKU='INT-PART-001'
        )
        
        # Create initial stock
        stock = StockItem.objects.create(
            part=part,
            quantity=10
        )
        
        # Create PO
        po = PurchaseOrder.objects.create(
            supplier=supplier,
            reference='INT-PO-001',
            status=PurchaseOrderStatus.PENDING
        )
        
        line_item = PurchaseOrderLineItem.objects.create(
            order=po,
            part=supplier_part,
            quantity=20,
            purchase_price=10.00
        )
        
        # Verify initial projected stock includes PO
        initial_projected = part.get_projected_stock()
        self.assertEqual(initial_projected, 30)  # 10 + 20
        
        # Cancel PO
        po.status = PurchaseOrderStatus.CANCELLED
        po.save()
        
        # Verify projected stock updated to exclude cancelled PO
        updated_projected = part.get_projected_stock()
        self.assertEqual(updated_projected, 10)  # Only current stock
        
        # Verify PO still visible in reports but marked as cancelled
        self.assertTrue(PurchaseOrder.objects.filter(pk=po.pk).exists())
        self.assertEqual(po.status, PurchaseOrderStatus.CANCELLED)