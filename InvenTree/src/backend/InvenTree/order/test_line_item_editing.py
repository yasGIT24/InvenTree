"""Unit tests for Sales Order line item editing functionality.

[AGENT GENERATED CODE - REQUIREMENT:Edit Individual Line Items in Sales Orders]
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from djmoney.money import Money

import order.validators
from InvenTree.unit_test import InvenTreeTestCase
from order.models import SalesOrder, SalesOrderLineItem
from part.models import Part
from users.models import Group

User = get_user_model()


class SalesOrderLineItemTest(InvenTreeTestCase):
    """Tests for SalesOrderLineItem model with editing functionality."""

    fixtures = [
        'category',
        'company',
        'part',
        'location',
        'sales_order',
        'users',
    ]

    def setUp(self):
        """Set up the test case."""
        super().setUp()

        # Create a sales order and line items
        self.order = SalesOrder.objects.get(pk=1)
        self.line_item = SalesOrderLineItem.objects.filter(order=self.order).first()

        # Create a salable part
        self.salable_part = Part.objects.filter(salable=True).first()

        # Set up users with different permissions
        self.admin_user = User.objects.get(username='allaccess')
        self.normal_user = User.objects.get(username='sam')
        
        # Make sure the normal user doesn't have approval permissions
        approval_group, _ = Group.objects.get_or_create(name='Line Item Approvers')
        approval_group.save()

        # Create a permission for approving line items
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        content_type = ContentType.objects.get_for_model(SalesOrderLineItem)
        permission, _ = Permission.objects.get_or_create(
            codename='approve_salesorderlineitem',
            name='Can approve sales order line item changes',
            content_type=content_type
        )
        
        approval_group.permissions.add(permission)
        self.admin_user.groups.add(approval_group)

    def test_validate_line_item_edits(self):
        """Test validation of sales order line item edits."""
        
        # Test quantity changes
        changes = {'quantity': 10.0}  # Assuming original quantity is much smaller
        
        # This should require approval
        needs_approval = not order.validators.validate_sales_order_line_edit(self.line_item, changes, self.normal_user)
        self.assertTrue(needs_approval, "Large quantity increase should require approval")
        
        # Admin user should be able to approve immediately
        needs_approval = not order.validators.validate_sales_order_line_edit(self.line_item, changes, self.admin_user)
        self.assertFalse(needs_approval, "Admin user should be able to approve changes")
        
        # Test invalid quantity
        with self.assertRaises(ValidationError):
            order.validators.validate_sales_order_line_edit(self.line_item, {'quantity': -5}, self.admin_user)
        
        # Test price changes
        self.line_item.sale_price = Money(100.0, 'USD')
        changes = {'sale_price': Money(80.0, 'USD')}  # 20% price reduction
        
        # This should require approval
        needs_approval = not order.validators.validate_sales_order_line_edit(self.line_item, changes, self.normal_user)
        self.assertTrue(needs_approval, "Significant price decrease should require approval")
        
        # Test part changes
        changes = {'part': self.salable_part}
        
        # This should require approval
        needs_approval = not order.validators.validate_sales_order_line_edit(self.line_item, changes, self.normal_user)
        self.assertTrue(needs_approval, "Part changes should require approval")
        
        # Test unsalable part
        unsalable_part = Part.objects.filter(salable=False).first()
        changes = {'part': unsalable_part}
        
        # This should fail validation
        with self.assertRaises(ValidationError):
            order.validators.validate_sales_order_line_edit(self.line_item, changes, self.admin_user)
    
    def test_edit_approval_workflow(self):
        """Test the complete approval workflow for line item edits."""
        
        # Set initial values
        self.line_item.quantity = 5
        self.line_item.sale_price = Money(50.0, 'USD')
        self.line_item.save()
        
        # Make changes that require approval
        changes = {
            'quantity': 10,
            'sale_price': Money(40.0, 'USD')
        }
        
        # Store pending changes
        self.line_item.pending_changes = changes
        self.line_item.needs_approval = True
        self.line_item.save()
        
        # Test approval process
        self.line_item.approve_changes(self.admin_user)
        
        # Refresh from database
        self.line_item.refresh_from_db()
        
        # Verify changes were applied
        self.assertEqual(self.line_item.quantity, 10)
        self.assertEqual(self.line_item.sale_price.amount, 40.0)
        self.assertEqual(self.line_item.approved_by, self.admin_user)
        self.assertIsNotNone(self.line_item.approval_date)
        self.assertFalse(self.line_item.needs_approval)
        self.assertIsNone(self.line_item.pending_changes)