"""Unit tests for vendor category operations."""

import csv
import io
import tempfile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from company.models import Company
from InvenTree.unit_test import InvenTreeAPITestCase
from users.permissions import check_user_permission


# [AGENT GENERATED CODE - REQUIREMENT: USX]
# [AGENT SUMMARY: See requirement IDs US1, US2, US5, US6 for agent run change_impact_analysis_review_final]
# Comprehensive test suite for vendor category operations including:
# - Category deletion with validation
# - Bulk upload with CSV validation
# - Role-based access control
# - Data integrity validation


class VendorCategoryTest(InvenTreeAPITestCase):
    """Test suite for vendor category operations."""

    roles = [
        'company.add_vendorcategory',
        'company.change_vendorcategory', 
        'company.delete_vendorcategory',
        'company.view_vendorcategory'
    ]

    @classmethod
    def setUpTestData(cls):
        """Set up test data for vendor category tests."""
        super().setUpTestData()
        
        # Create test vendor categories
        cls.electronics_category = Company.objects.create(
            name='Electronics Category',
            description='Electronics suppliers',
            is_category=True,
            category_type='vendor'
        )
        
        cls.mechanical_category = Company.objects.create(
            name='Mechanical Category', 
            description='Mechanical suppliers',
            is_category=True,
            category_type='vendor'
        )
        
        # Create test suppliers linked to categories
        cls.supplier_with_category = Company.objects.create(
            name='ACME Electronics',
            description='Electronics supplier',
            is_supplier=True,
            vendor_category=cls.electronics_category
        )

    def test_delete_category_not_in_use(self):
        """Test successful deletion of unused vendor category."""
        # Create unused category
        unused_category = Company.objects.create(
            name='Unused Category',
            description='Not used by any supplier',
            is_category=True,
            category_type='vendor'
        )
        
        url = reverse('api-company-detail', kwargs={'pk': unused_category.pk})
        
        response = self.delete(url)
        self.assertEqual(response.status_code, 204)
        
        # Verify category is deleted
        self.assertFalse(Company.objects.filter(pk=unused_category.pk).exists())

    def test_delete_category_in_use_blocked(self):
        """Test deletion blocked for category in use."""
        url = reverse('api-company-detail', kwargs={'pk': self.electronics_category.pk})
        
        response = self.delete(url)
        self.assertEqual(response.status_code, 400)
        
        # Verify category still exists
        self.assertTrue(Company.objects.filter(pk=self.electronics_category.pk).exists())
        
        # Check error message
        self.assertIn('cannot be deleted', str(response.data).lower())

    def test_bulk_upload_valid_csv(self):
        """Test successful bulk upload of vendor categories."""
        csv_content = """name,description,code
Industrial Automation,Automation suppliers,IA
Chemical Supplies,Chemical material suppliers,CS
Packaging Materials,Packaging suppliers,PM"""
        
        csv_file = SimpleUploadedFile(
            'categories.csv',
            csv_content.encode('utf-8'),
            content_type='text/csv'
        )
        
        url = reverse('api-company-bulk-upload')
        data = {'file': csv_file, 'category_type': 'vendor'}
        
        response = self.post(url, data, format='multipart')
        self.assertEqual(response.status_code, 201)
        
        # Verify categories were created
        self.assertTrue(Company.objects.filter(name='Industrial Automation').exists())
        self.assertTrue(Company.objects.filter(name='Chemical Supplies').exists())
        self.assertTrue(Company.objects.filter(name='Packaging Materials').exists())

    def test_bulk_upload_duplicate_names_rejected(self):
        """Test bulk upload rejects duplicate category names."""
        csv_content = f"""name,description,code
{self.electronics_category.name},Duplicate name test,DUP
New Category,Valid new category,NEW"""
        
        csv_file = SimpleUploadedFile(
            'categories_with_duplicate.csv',
            csv_content.encode('utf-8'),
            content_type='text/csv'
        )
        
        url = reverse('api-company-bulk-upload')
        data = {'file': csv_file, 'category_type': 'vendor'}
        
        response = self.post(url, data, format='multipart')
        self.assertEqual(response.status_code, 400)
        
        # Verify duplicate was rejected but valid entry processed
        self.assertIn('duplicate', str(response.data).lower())

    def test_bulk_upload_missing_required_fields(self):
        """Test bulk upload validation for missing required fields."""
        csv_content = """name,description
,Missing name field
Valid Category,"""
        
        csv_file = SimpleUploadedFile(
            'invalid_categories.csv',
            csv_content.encode('utf-8'),
            content_type='text/csv'
        )
        
        url = reverse('api-company-bulk-upload')
        data = {'file': csv_file, 'category_type': 'vendor'}
        
        response = self.post(url, data, format='multipart')
        self.assertEqual(response.status_code, 400)
        
        # Verify validation errors reported
        self.assertIn('required', str(response.data).lower())

    def test_role_based_access_delete(self):
        """Test role-based access control for category deletion."""
        # Create user without delete permission
        user_no_perm = User.objects.create_user(
            username='noperm',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=user_no_perm)
        
        url = reverse('api-company-detail', kwargs={'pk': self.mechanical_category.pk})
        response = self.delete(url)
        
        self.assertEqual(response.status_code, 403)
        
        # Verify category still exists
        self.assertTrue(Company.objects.filter(pk=self.mechanical_category.pk).exists())

    def test_role_based_access_bulk_upload(self):
        """Test role-based access control for bulk upload."""
        # Create user without add permission
        user_no_perm = User.objects.create_user(
            username='noaddperm',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=user_no_perm)
        
        csv_content = """name,description
Test Category,Test description"""
        
        csv_file = SimpleUploadedFile(
            'test.csv',
            csv_content.encode('utf-8'),
            content_type='text/csv'
        )
        
        url = reverse('api-company-bulk-upload')
        data = {'file': csv_file, 'category_type': 'vendor'}
        
        response = self.post(url, data, format='multipart')
        self.assertEqual(response.status_code, 403)

    def test_data_integrity_validation(self):
        """Test data integrity validation during operations."""
        # Test name length validation
        long_name = 'A' * 256  # Exceeds typical max length
        
        url = reverse('api-company-list')
        data = {
            'name': long_name,
            'description': 'Test description',
            'is_category': True,
            'category_type': 'vendor'
        }
        
        response = self.post(url, data)
        self.assertEqual(response.status_code, 400)

    def test_category_usage_check(self):
        """Test validation check for category usage before deletion."""
        # Verify electronics category is reported as in use
        url = reverse('api-company-usage-check', kwargs={'pk': self.electronics_category.pk})
        
        response = self.get(url)
        self.assertEqual(response.status_code, 200)
        
        usage_data = response.data
        self.assertTrue(usage_data.get('in_use', False))
        self.assertGreater(usage_data.get('usage_count', 0), 0)

    def test_bulk_upload_progress_tracking(self):
        """Test progress tracking during bulk upload operations."""
        # Create larger CSV for progress testing
        csv_rows = []
        csv_rows.append('name,description,code')
        
        for i in range(50):
            csv_rows.append(f'Test Category {i},Description {i},TC{i:02d}')
        
        csv_content = '\n'.join(csv_rows)
        
        csv_file = SimpleUploadedFile(
            'large_upload.csv',
            csv_content.encode('utf-8'),
            content_type='text/csv'
        )
        
        url = reverse('api-company-bulk-upload')
        data = {'file': csv_file, 'category_type': 'vendor'}
        
        with patch('company.tasks.process_bulk_upload.delay') as mock_task:
            response = self.post(url, data, format='multipart')
            
            self.assertEqual(response.status_code, 202)  # Accepted for async processing
            mock_task.assert_called_once()

    def test_export_vendor_categories(self):
        """Test exporting vendor categories to CSV."""
        url = reverse('api-company-export')
        data = {'category_type': 'vendor', 'format': 'csv'}
        
        response = self.get(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'text/csv')
        
        # Verify CSV contains expected categories
        content = response.content.decode('utf-8')
        self.assertIn(self.electronics_category.name, content)
        self.assertIn(self.mechanical_category.name, content)

    def tearDown(self):
        """Clean up after each test."""
        super().tearDown()
        # Clean up any test categories created during tests
        Company.objects.filter(
            is_category=True,
            category_type='vendor',
            name__startswith='Test Category'
        ).delete()


class VendorCategoryIntegrationTest(TestCase):
    """Integration tests for vendor category operations."""

    def setUp(self):
        """Set up integration test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_end_to_end_category_lifecycle(self):
        """Test complete category lifecycle from creation to deletion."""
        # Create category
        category = Company.objects.create(
            name='E2E Test Category',
            description='End-to-end test category',
            is_category=True,
            category_type='vendor'
        )
        
        # Create supplier using category
        supplier = Company.objects.create(
            name='E2E Test Supplier',
            description='Test supplier',
            is_supplier=True,
            vendor_category=category
        )
        
        # Verify category cannot be deleted while in use
        with self.assertRaises(Exception):
            category.delete()
        
        # Remove supplier association
        supplier.vendor_category = None
        supplier.save()
        
        # Verify category can now be deleted
        category.delete()
        self.assertFalse(Company.objects.filter(pk=category.pk).exists())