"""Tests for Vendor Category functionality.

[AGENT GENERATED CODE - REQUIREMENT:Delete Vendor Categories with Validation]
[AGENT GENERATED CODE - REQUIREMENT:Bulk Upload Vendor Categories with Validation]
"""

import io

from django.core.exceptions import ValidationError
from django.urls import reverse

import company.models
from InvenTree.api_tester import InvenTreeAPITestCase
from company.models import Company, VendorCategory


class VendorCategoryTest(InvenTreeAPITestCase):
    """Tests for VendorCategory model."""

    fixtures = [
        'category',
        'company',
        'part',
    ]

    def setUp(self):
        """Set up test case with some base categories."""
        super().setUp()

        # Create some vendor categories
        self.top_category = VendorCategory.objects.create(
            name='Top', description='Top level category'
        )
        
        self.child_category = VendorCategory.objects.create(
            name='Child', description='Child category', parent=self.top_category
        )

    def test_category_tree(self):
        """Test basic category tree functionality."""
        self.assertEqual(self.top_category.parent, None)
        self.assertEqual(self.child_category.parent, self.top_category)
        self.assertEqual(self.top_category.children.count(), 1)

    def test_category_validation(self):
        """Test category validation."""
        # Test circular reference
        with self.assertRaises(ValidationError):
            self.top_category.parent = self.child_category
            self.top_category.save()
        
        # Reset the parent
        self.top_category.parent = None
        self.top_category.save()

    def test_delete_category(self):
        """Test that a category cannot be deleted if it has children."""
        # Cannot delete category with children
        with self.assertRaises(ValidationError):
            self.top_category.delete()
            
        # Delete child first, then the parent should delete fine
        self.child_category.delete()
        self.top_category.delete()
        
        # Categories should be gone
        self.assertEqual(VendorCategory.objects.count(), 0)

    def test_delete_category_in_use(self):
        """Test deletion validation when a category is in use."""
        # Assign a company to the child category
        company = Company.objects.first()
        company.category = self.child_category
        company.save()
        
        # Now we can't delete the child category
        with self.assertRaises(ValidationError):
            self.child_category.delete()

    def test_api_list(self):
        """Test the API list endpoint for vendor categories."""
        url = reverse('api-vendor-category-list')
        
        # Test list endpoint
        response = self.get(url)
        self.assertEqual(response.status_code, 200)
        
        # There should be 2 categories
        self.assertEqual(len(response.data), 2)
        
        # Check the structure of the response
        for cat in response.data:
            self.assertIn('name', cat)
            self.assertIn('description', cat)
            self.assertIn('pk', cat)
            
    def test_api_create(self):
        """Test the API create endpoint for vendor categories."""
        url = reverse('api-vendor-category-list')
        
        # Test creation via API
        response = self.post(
            url,
            {
                'name': 'New Category',
                'description': 'A new vendor category',
                'parent': self.top_category.pk
            },
            expected_code=201
        )
        
        # There should now be 3 categories
        self.assertEqual(VendorCategory.objects.count(), 3)
        
        # Test creation with duplicate name (under same parent) - should fail
        response = self.post(
            url,
            {
                'name': 'New Category',
                'description': 'Another category with same name',
                'parent': self.top_category.pk
            },
            expected_code=400
        )
        
    def test_api_delete(self):
        """Test the API delete endpoint for vendor categories."""
        # First, try to delete the top category (should fail)
        url = reverse('api-vendor-category-detail', kwargs={'pk': self.top_category.pk})
        response = self.delete(url, expected_code=400)
        
        # Delete the child category
        url = reverse('api-vendor-category-detail', kwargs={'pk': self.child_category.pk})
        response = self.delete(url)
        
        # There should now be 1 category
        self.assertEqual(VendorCategory.objects.count(), 1)
        
        # Now we should be able to delete the top category
        url = reverse('api-vendor-category-detail', kwargs={'pk': self.top_category.pk})
        response = self.delete(url)
        
        # There should now be 0 categories
        self.assertEqual(VendorCategory.objects.count(), 0)

    def test_bulk_import(self):
        """Test bulk import of vendor categories."""
        # Create CSV file for import
        csv_file = io.StringIO()
        csv_file.write("name,description,parent\n")
        csv_file.write("Category 1,First test category,\n")
        csv_file.write("Category 2,Second test category,Category 1\n")
        csv_file.write("Category 3,Third test category,Category 1\n")
        
        csv_file.seek(0)
        
        # Import the data
        from importer.models import DataImportSession
        
        session = DataImportSession.create_from_file(
            csv_file,
            model='vendorcategory',
            user=self.user
        )
        
        # Process the data
        session.process()
        
        # Should have 3 new categories plus 2 existing = 5 total
        self.assertEqual(VendorCategory.objects.count(), 5)
        
        # Check that parent relationships were established
        cat1 = VendorCategory.objects.get(name='Category 1')
        self.assertEqual(cat1.parent, None)
        
        cat2 = VendorCategory.objects.get(name='Category 2')
        self.assertEqual(cat2.parent, cat1)
        
        cat3 = VendorCategory.objects.get(name='Category 3')
        self.assertEqual(cat3.parent, cat1)