"""Unit tests for line item editing operations."""

from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from company.models import Company, SupplierPart
from InvenTree.unit_test import InvenTreeAPITestCase
from order.models import PurchaseOrder, PurchaseOrderLineItem, SalesOrder, SalesOrderLineItem
from part.models import Part
from users.permissions import check_user_permission


# [AGENT GENERATED CODE - REQUIREMENT: USX]
# [AGENT SUMMARY: See requirement IDs US3, US5, US6 for agent run change_impact_analysis_review_final]
# Comprehensive test suite for line item editing operations including:
# - Individual line item editing with validation
# - Approval workflow integration
# - Inventory checks and total recalculation
# - Role-based access control


class LineItemEditTest(InvenTreeAPITestCase):
    """Test suite for line item editing operations."""

    roles = [
        'order.add_salesorder',
        'order.change_salesorder', 
        'order.view_salesorder',
        'order.add_purchaseorder',
        'order.change_purchaseorder',
        'order.view_purchaseorder'
    ]

    @classmethod
    def setUpTestData(cls):
        """Set up test data for line item editing tests."""
        super().setUpTestData()
        
        # Create test company and parts
        cls.supplier = Company.objects.create(
            name='Test Supplier',
            description='Test supplier company',
            is_supplier=True
        )
        
        cls.customer = Company.objects.create(
            name='Test Customer', 
            description='Test customer company',
            is_customer=True
        )
        
        cls.part = Part.objects.create(
            name='Test Part',
            description='Test part for orders',
            purchaseable=True,
            saleable=True,
            trackable=True
        )
        
        cls.supplier_part = SupplierPart.objects.create(
            supplier=cls.supplier,
            part=cls.part,
            SKU='SUPPLIER-001'
        )
        
        # Create test orders
        cls.purchase_order = PurchaseOrder.objects.create(
            supplier=cls.supplier,
            reference='PO-001',
            description='Test purchase order'
        )
        
        cls.sales_order = SalesOrder.objects.create(
            customer=cls.customer,
            reference='SO-001',
            description='Test sales order'
        )
        
        # Create test line items
        cls.po_line_item = PurchaseOrderLineItem.objects.create(
            order=cls.purchase_order,
            part=cls.supplier_part,
            quantity=10,
            purchase_price=25.50
        )
        
        cls.so_line_item = SalesOrderLineItem.objects.create(
            order=cls.sales_order,
            part=cls.part,
            quantity=5,
            sale_price=45.00
        )

    def test_edit_sales_order_line_quantity(self):
        """Test editing quantity of sales order line item."""
        url = reverse('api-so-line-detail', kwargs={'pk': self.so_line_item.pk})
        
        data = {
            'quantity': 8,  # Change from 5 to 8
            'sale_price': self.so_line_item.sale_price  # Keep price same
        }
        
        response = self.patch(url, data)
        self.assertEqual(response.status_code, 200)
        
        # Verify quantity updated
        self.so_line_item.refresh_from_db()
        self.assertEqual(self.so_line_item.quantity, 8)
        
        # Verify order total recalculated
        self.sales_order.refresh_from_db()
        expected_total = 8 * 45.00
        self.assertEqual(float(self.sales_order.total_price), expected_total)

    def test_edit_sales_order_line_price(self):
        """Test editing price of sales order line item."""
        url = reverse('api-so-line-detail', kwargs={'pk': self.so_line_item.pk})
        
        original_quantity = self.so_line_item.quantity
        new_price = Decimal('50.00')
        
        data = {
            'quantity': original_quantity,
            'sale_price': new_price
        }
        
        response = self.patch(url, data)
        self.assertEqual(response.status_code, 200)
        
        # Verify price updated
        self.so_line_item.refresh_from_db()
        self.assertEqual(self.so_line_item.sale_price, new_price)
        
        # Verify order total recalculated
        self.sales_order.refresh_from_db()
        expected_total = float(original_quantity * new_price)
        self.assertEqual(float(self.sales_order.total_price), expected_total)

    def test_edit_line_item_with_inventory_check(self):
        """Test line item editing triggers inventory availability check."""
        # Mock inventory check
        with patch('order.models.SalesOrderLineItem.check_inventory_availability') as mock_check:
            mock_check.return_value = True
            
            url = reverse('api-so-line-detail', kwargs={'pk': self.so_line_item.pk})
            
            data = {
                'quantity': 15,  # Increase quantity significantly
                'sale_price': self.so_line_item.sale_price
            }
            
            response = self.patch(url, data)
            self.assertEqual(response.status_code, 200)
            
            # Verify inventory check was called
            mock_check.assert_called()

    def test_edit_line_item_insufficient_inventory(self):
        """Test line item editing blocked when insufficient inventory."""
        # Mock inventory check to return false
        with patch('order.models.SalesOrderLineItem.check_inventory_availability') as mock_check:
            mock_check.return_value = False
            
            url = reverse('api-so-line-detail', kwargs={'pk': self.so_line_item.pk})
            
            data = {
                'quantity': 100,  # Large quantity that exceeds stock
                'sale_price': self.so_line_item.sale_price
            }
            
            response = self.patch(url, data)
            self.assertEqual(response.status_code, 400)
            
            # Verify error message
            self.assertIn('insufficient inventory', str(response.data).lower())

    def test_edit_line_item_requires_approval(self):
        """Test line item editing triggers approval workflow when configured."""
        # Mock approval requirement
        with patch('order.models.requires_approval') as mock_approval:
            mock_approval.return_value = True
            
            url = reverse('api-so-line-detail', kwargs={'pk': self.so_line_item.pk})
            
            data = {
                'quantity': 8,
                'sale_price': 55.00  # Significant price change
            }
            
            response = self.patch(url, data)
            self.assertEqual(response.status_code, 202)  # Accepted for approval
            
            # Verify approval task triggered
            response_data = response.data
            self.assertIn('approval_required', response_data)
            self.assertTrue(response_data['approval_required'])

    def test_edit_purchase_order_line_item(self):
        """Test editing purchase order line item."""
        url = reverse('api-po-line-detail', kwargs={'pk': self.po_line_item.pk})
        
        data = {
            'quantity': 15,  # Change from 10 to 15
            'purchase_price': 22.75  # Change price
        }
        
        response = self.patch(url, data)
        self.assertEqual(response.status_code, 200)
        
        # Verify updates
        self.po_line_item.refresh_from_db()
        self.assertEqual(self.po_line_item.quantity, 15)
        self.assertEqual(float(self.po_line_item.purchase_price), 22.75)
        
        # Verify order total recalculated
        self.purchase_order.refresh_from_db()
        expected_total = 15 * 22.75
        self.assertEqual(float(self.purchase_order.total_price), expected_total)

    def test_edit_line_item_validation_errors(self):
        """Test validation errors during line item editing."""
        url = reverse('api-so-line-detail', kwargs={'pk': self.so_line_item.pk})
        
        # Test negative quantity
        data = {
            'quantity': -5,
            'sale_price': self.so_line_item.sale_price
        }
        
        response = self.patch(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('positive', str(response.data).lower())
        
        # Test zero price
        data = {
            'quantity': 5,
            'sale_price': 0
        }
        
        response = self.patch(url, data)
        self.assertEqual(response.status_code, 400)

    def test_role_based_access_line_edit(self):
        """Test role-based access control for line item editing."""
        # Create user without edit permissions
        user_no_perm = User.objects.create_user(
            username='noeditperm',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=user_no_perm)
        
        url = reverse('api-so-line-detail', kwargs={'pk': self.so_line_item.pk})
        data = {
            'quantity': 8,
            'sale_price': 50.00
        }
        
        response = self.patch(url, data)
        self.assertEqual(response.status_code, 403)
        
        # Verify line item unchanged
        self.so_line_item.refresh_from_db()
        self.assertEqual(self.so_line_item.quantity, 5)  # Original value

    def test_bulk_line_item_edit(self):
        """Test bulk editing of multiple line items."""
        # Create additional line items
        line_item_2 = SalesOrderLineItem.objects.create(
            order=self.sales_order,
            part=self.part,
            quantity=3,
            sale_price=40.00
        )
        
        url = reverse('api-so-line-bulk-edit')
        
        data = {
            'line_items': [
                {'id': self.so_line_item.pk, 'quantity': 7, 'sale_price': 46.00},
                {'id': line_item_2.pk, 'quantity': 4, 'sale_price': 42.00}
            ]
        }
        
        response = self.post(url, data)
        self.assertEqual(response.status_code, 200)
        
        # Verify both line items updated
        self.so_line_item.refresh_from_db()
        line_item_2.refresh_from_db()
        
        self.assertEqual(self.so_line_item.quantity, 7)
        self.assertEqual(float(self.so_line_item.sale_price), 46.00)
        self.assertEqual(line_item_2.quantity, 4)
        self.assertEqual(float(line_item_2.sale_price), 42.00)

    def test_line_item_edit_audit_log(self):
        """Test audit logging for line item edits."""
        url = reverse('api-so-line-detail', kwargs={'pk': self.so_line_item.pk})
        
        original_quantity = self.so_line_item.quantity
        original_price = self.so_line_item.sale_price
        
        data = {
            'quantity': 12,
            'sale_price': 48.50
        }
        
        with patch('order.models.log_audit_event') as mock_log:
            response = self.patch(url, data)
            self.assertEqual(response.status_code, 200)
            
            # Verify audit log called
            mock_log.assert_called()
            call_args = mock_log.call_args[1]
            
            self.assertEqual(call_args['event_type'], 'line_item_edited')
            self.assertIn('quantity', call_args['changes'])
            self.assertIn('sale_price', call_args['changes'])

    def test_line_item_edit_with_approval_workflow(self):
        """Test complete approval workflow for line item edits."""
        # Create approver user
        approver = User.objects.create_user(
            username='approver',
            password='testpass123'
        )
        
        # Mock approval requirement for price changes over threshold
        with patch('order.models.requires_approval_for_price_change') as mock_approval:
            mock_approval.return_value = True
            
            url = reverse('api-so-line-detail', kwargs={'pk': self.so_line_item.pk})
            
            data = {
                'quantity': 5,
                'sale_price': 75.00  # Significant price increase
            }
            
            response = self.patch(url, data)
            self.assertEqual(response.status_code, 202)
            
            # Verify approval request created
            approval_data = response.data
            self.assertTrue(approval_data['approval_required'])
            self.assertIn('approval_id', approval_data)
            
            # Mock approval process
            approval_url = reverse('api-approval-approve', kwargs={'pk': approval_data['approval_id']})
            
            self.client.force_authenticate(user=approver)
            approval_response = self.post(approval_url, {'approved': True})
            
            self.assertEqual(approval_response.status_code, 200)
            
            # Verify line item updated after approval
            self.so_line_item.refresh_from_db()
            self.assertEqual(float(self.so_line_item.sale_price), 75.00)

    def test_concurrent_line_item_edits(self):
        """Test handling of concurrent line item edit attempts."""
        url = reverse('api-so-line-detail', kwargs={'pk': self.so_line_item.pk})
        
        # Simulate concurrent edits by updating line item before API call
        self.so_line_item.quantity = 6
        self.so_line_item.save()
        
        data = {
            'quantity': 8,
            'sale_price': self.so_line_item.sale_price,
            'version': 1  # Outdated version
        }
        
        response = self.patch(url, data)
        self.assertEqual(response.status_code, 409)  # Conflict
        
        # Verify optimistic locking error
        self.assertIn('concurrent', str(response.data).lower())

    def tearDown(self):
        """Clean up after each test."""
        super().tearDown()


class LineItemEditIntegrationTest(TestCase):
    """Integration tests for line item editing operations."""

    def setUp(self):
        """Set up integration test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_end_to_end_line_item_lifecycle(self):
        """Test complete line item editing lifecycle."""
        # Create test data
        supplier = Company.objects.create(
            name='Integration Supplier',
            is_supplier=True
        )
        
        part = Part.objects.create(
            name='Integration Part',
            purchaseable=True,
            saleable=True
        )
        
        order = SalesOrder.objects.create(
            customer=Company.objects.create(name='Integration Customer', is_customer=True),
            reference='INT-SO-001'
        )
        
        line_item = SalesOrderLineItem.objects.create(
            order=order,
            part=part,
            quantity=10,
            sale_price=30.00
        )
        
        original_total = order.total_price
        
        # Edit line item
        line_item.quantity = 15
        line_item.sale_price = 32.50
        line_item.save()
        
        # Verify order total updated
        order.refresh_from_db()
        expected_total = 15 * 32.50
        self.assertEqual(float(order.total_price), expected_total)
        self.assertNotEqual(order.total_price, original_total)