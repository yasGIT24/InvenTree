"""Documentation tools for requirements, test cases, and change request traceability.

This module provides tools for maintaining traceability between requirements,
test cases, and change requests in the InvenTree system.
"""

# <!-- AGENT GENERATED CODE: DOCUMENTATION TOOLS -->

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List, Optional, Union

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog

import InvenTree.fields
import InvenTree.helpers
import InvenTree.models

logger = structlog.get_logger('inventree')


class RequirementCategory(InvenTree.models.MetadataMixin, InvenTree.models.InvenTreeTree):
    """Hierarchical category model for organizing requirements.

    Attributes:
        name: Name of this category
        description: Description of this category
        default_importance: Default importance for requirements in this category
    """

    class Meta:
        """Metaclass options."""
        verbose_name = _('Requirement Category')
        verbose_name_plural = _('Requirement Categories')
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'parent'],
                name='unique_requirement_category_name'
            )
        ]

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the RequirementCategory model."""
        return reverse('api-requirement-category-list')

    def get_absolute_url(self):
        """Return the web URL associated with this RequirementCategory instance."""
        return InvenTree.helpers.pui_url(f'/documentation/requirement/category/{self.pk}/')

    default_importance = models.CharField(
        max_length=15,
        default='MEDIUM',
        choices=[
            ('CRITICAL', _('Critical')),
            ('HIGH', _('High')),
            ('MEDIUM', _('Medium')),
            ('LOW', _('Low')),
            ('NONE', _('None')),
        ],
        verbose_name=_('Default Importance'),
        help_text=_('Default importance for requirements in this category'),
    )


class RequirementStatus:
    """Status codes for the Requirement model."""

    DRAFT = 10
    PROPOSED = 20
    APPROVED = 30
    IMPLEMENTED = 40
    VERIFIED = 50
    DEFERRED = 60
    REJECTED = 70
    OBSOLETE = 80

    @classmethod
    def items(cls):
        """All available status codes."""
        return [
            (cls.DRAFT, _('Draft')),
            (cls.PROPOSED, _('Proposed')),
            (cls.APPROVED, _('Approved')),
            (cls.IMPLEMENTED, _('Implemented')),
            (cls.VERIFIED, _('Verified')),
            (cls.DEFERRED, _('Deferred')),
            (cls.REJECTED, _('Rejected')),
            (cls.OBSOLETE, _('Obsolete')),
        ]

    @classmethod
    def text(cls, code):
        """Return text value for specified status code."""
        for item_code, text in cls.items():
            if code == item_code:
                return text
        return ''

    @classmethod
    def active_codes(cls):
        """Return list of 'active' status codes."""
        return [
            cls.DRAFT,
            cls.PROPOSED,
            cls.APPROVED,
            cls.IMPLEMENTED,
        ]

    @classmethod
    def inactive_codes(cls):
        """Return list of 'inactive' status codes."""
        return [
            cls.DEFERRED,
            cls.REJECTED,
            cls.OBSOLETE,
        ]


class Requirement(
    InvenTree.models.InvenTreeAttachmentMixin,
    InvenTree.models.InvenTreeNotesMixin,
    InvenTree.models.MetadataMixin,
):
    """Model representing a single requirement for the system.

    Attributes:
        category: Category for this requirement
        reference: Unique reference for this requirement
        name: Short name for this requirement
        description: Detailed description of the requirement
        importance: Importance level of this requirement
        status: Current status of this requirement
        source: Source document or reference for this requirement
        created_by: User who created this requirement
        creation_date: Date this requirement was created
        verified_by: User who verified this requirement
        verification_date: Date this requirement was verified
        verification_method: Method used to verify this requirement
        verification_result: Result of verification
    """

    class Meta:
        """Metaclass options."""
        verbose_name = _('Requirement')
        verbose_name_plural = _('Requirements')
        ordering = ['reference', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['reference'],
                name='unique_requirement_reference'
            )
        ]

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the Requirement model."""
        return reverse('api-requirement-list')

    def get_absolute_url(self):
        """Return the web URL associated with this Requirement instance."""
        return InvenTree.helpers.pui_url(f'/documentation/requirement/{self.pk}/')

    category = models.ForeignKey(
        RequirementCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requirements',
        verbose_name=_('Category'),
        help_text=_('Category for this requirement'),
    )

    reference = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Reference'),
        help_text=_('Unique reference for this requirement'),
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Short name for this requirement'),
    )

    description = models.TextField(
        verbose_name=_('Description'),
        help_text=_('Detailed description of the requirement'),
    )

    importance = models.CharField(
        max_length=15,
        default='MEDIUM',
        choices=[
            ('CRITICAL', _('Critical')),
            ('HIGH', _('High')),
            ('MEDIUM', _('Medium')),
            ('LOW', _('Low')),
            ('NONE', _('None')),
        ],
        verbose_name=_('Importance'),
        help_text=_('Importance level of this requirement'),
    )

    status = models.IntegerField(
        default=RequirementStatus.DRAFT,
        choices=RequirementStatus.items(),
        verbose_name=_('Status'),
        help_text=_('Current status of this requirement'),
    )

    source = models.CharField(
        max_length=250,
        blank=True,
        verbose_name=_('Source'),
        help_text=_('Source document or reference for this requirement'),
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='requirements_created',
        verbose_name=_('Created By'),
        help_text=_('User who created this requirement'),
    )

    creation_date = models.DateField(
        auto_now_add=True,
        verbose_name=_('Creation Date'),
        help_text=_('Date this requirement was created'),
    )

    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='requirements_verified',
        verbose_name=_('Verified By'),
        help_text=_('User who verified this requirement'),
    )

    verification_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Verification Date'),
        help_text=_('Date this requirement was verified'),
    )

    verification_method = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Verification Method'),
        help_text=_('Method used to verify this requirement'),
    )

    verification_result = models.CharField(
        max_length=250,
        blank=True,
        verbose_name=_('Verification Result'),
        help_text=_('Result of verification'),
    )

    def __str__(self):
        """String representation of this Requirement."""
        return f"{self.reference}: {self.name}"
    
    def is_verified(self):
        """Return True if this requirement has been verified."""
        return self.status == RequirementStatus.VERIFIED and self.verification_date is not None

    def is_active(self):
        """Return True if this requirement is active."""
        return self.status in RequirementStatus.active_codes()


class TestCase(
    InvenTree.models.InvenTreeAttachmentMixin,
    InvenTree.models.InvenTreeNotesMixin,
    InvenTree.models.MetadataMixin,
):
    """A TestCase represents a specific test to verify a requirement.

    Attributes:
        reference: Unique reference for this test case
        name: Short name for this test case
        description: Detailed description of the test case
        requirements: Requirements verified by this test case
        expected_result: Expected result of the test
        test_procedure: Steps to execute the test
        created_by: User who created this test case
        creation_date: Date this test case was created
        updated_by: User who last updated this test case
        update_date: Date this test case was last updated
        is_automated: Whether this test is automated
        test_script: Optional path to test script for automated tests
    """

    class Meta:
        """Metaclass options."""
        verbose_name = _('Test Case')
        verbose_name_plural = _('Test Cases')
        ordering = ['reference', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['reference'],
                name='unique_testcase_reference'
            )
        ]

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the TestCase model."""
        return reverse('api-testcase-list')

    def get_absolute_url(self):
        """Return the web URL associated with this TestCase instance."""
        return InvenTree.helpers.pui_url(f'/documentation/testcase/{self.pk}/')

    reference = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Reference'),
        help_text=_('Unique reference for this test case'),
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Short name for this test case'),
    )

    description = models.TextField(
        verbose_name=_('Description'),
        help_text=_('Detailed description of the test case'),
    )

    requirements = models.ManyToManyField(
        Requirement,
        related_name='test_cases',
        blank=True,
        verbose_name=_('Requirements'),
        help_text=_('Requirements verified by this test case'),
    )

    expected_result = models.TextField(
        verbose_name=_('Expected Result'),
        help_text=_('Expected result of the test'),
    )

    test_procedure = models.TextField(
        verbose_name=_('Test Procedure'),
        help_text=_('Steps to execute the test'),
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='test_cases_created',
        verbose_name=_('Created By'),
        help_text=_('User who created this test case'),
    )

    creation_date = models.DateField(
        auto_now_add=True,
        verbose_name=_('Creation Date'),
        help_text=_('Date this test case was created'),
    )

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='test_cases_updated',
        verbose_name=_('Updated By'),
        help_text=_('User who last updated this test case'),
    )

    update_date = models.DateField(
        auto_now=True,
        verbose_name=_('Update Date'),
        help_text=_('Date this test case was last updated'),
    )

    is_automated = models.BooleanField(
        default=False,
        verbose_name=_('Automated'),
        help_text=_('Whether this test is automated'),
    )

    test_script = models.CharField(
        max_length=250,
        blank=True,
        verbose_name=_('Test Script'),
        help_text=_('Path to test script for automated tests'),
    )

    def __str__(self):
        """String representation of this TestCase."""
        return f"{self.reference}: {self.name}"


class TestRun(
    InvenTree.models.InvenTreeAttachmentMixin,
    InvenTree.models.InvenTreeNotesMixin,
    InvenTree.models.MetadataMixin,
):
    """A TestRun represents a specific execution of a TestCase.

    Attributes:
        test_case: Associated test case
        run_by: User who ran the test
        run_date: Date the test was run
        status: Result status of the test run
        outcome: Detailed outcome of the test
        notes: Additional notes about the test run
    """

    class Meta:
        """Metaclass options."""
        verbose_name = _('Test Run')
        verbose_name_plural = _('Test Runs')
        ordering = ['-run_date', 'test_case']

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the TestRun model."""
        return reverse('api-testrun-list')

    def get_absolute_url(self):
        """Return the web URL associated with this TestRun instance."""
        return InvenTree.helpers.pui_url(f'/documentation/testrun/{self.pk}/')

    test_case = models.ForeignKey(
        TestCase,
        on_delete=models.CASCADE,
        related_name='test_runs',
        verbose_name=_('Test Case'),
        help_text=_('Associated test case'),
    )

    run_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='test_runs',
        verbose_name=_('Run By'),
        help_text=_('User who ran the test'),
    )

    run_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Run Date'),
        help_text=_('Date and time the test was run'),
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('PASS', _('Pass')),
            ('FAIL', _('Fail')),
            ('ERROR', _('Error')),
            ('SKIPPED', _('Skipped')),
            ('BLOCKED', _('Blocked')),
        ],
        verbose_name=_('Status'),
        help_text=_('Result status of the test run'),
    )

    outcome = models.TextField(
        blank=True,
        verbose_name=_('Outcome'),
        help_text=_('Detailed outcome of the test'),
    )

    def __str__(self):
        """String representation of this TestRun."""
        return f"{self.test_case} - {self.run_date} - {self.status}"

    @property
    def passed(self):
        """Return True if this test run passed."""
        return self.status == 'PASS'


class ChangeRequest(
    InvenTree.models.InvenTreeAttachmentMixin,
    InvenTree.models.InvenTreeNotesMixin,
    InvenTree.models.MetadataMixin,
):
    """A ChangeRequest represents a request for change to the system.

    Attributes:
        reference: Unique reference for this change request
        title: Short title for this change request
        description: Detailed description of the change request
        requirements: Requirements affected by this change request
        test_cases: Test cases associated with this change request
        status: Current status of this change request
        priority: Priority of this change request
        impact: Impact level of this change request
        risk: Risk level of this change request
        created_by: User who created this change request
        creation_date: Date this change request was created
        assigned_to: User assigned to implement this change
        approved_by: User who approved this change
        approval_date: Date this change was approved
        implemented_by: User who implemented this change
        implementation_date: Date this change was implemented
        verified_by: User who verified this change
        verification_date: Date this change was verified
    """

    class Meta:
        """Metaclass options."""
        verbose_name = _('Change Request')
        verbose_name_plural = _('Change Requests')
        ordering = ['reference', 'title']
        constraints = [
            models.UniqueConstraint(
                fields=['reference'],
                name='unique_changerequest_reference'
            )
        ]

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the ChangeRequest model."""
        return reverse('api-changerequest-list')

    def get_absolute_url(self):
        """Return the web URL associated with this ChangeRequest instance."""
        return InvenTree.helpers.pui_url(f'/documentation/cr/{self.pk}/')

    reference = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Reference'),
        help_text=_('Unique reference for this change request'),
    )

    title = models.CharField(
        max_length=100,
        verbose_name=_('Title'),
        help_text=_('Short title for this change request'),
    )

    description = models.TextField(
        verbose_name=_('Description'),
        help_text=_('Detailed description of the change request'),
    )

    requirements = models.ManyToManyField(
        Requirement,
        related_name='change_requests',
        blank=True,
        verbose_name=_('Requirements'),
        help_text=_('Requirements affected by this change request'),
    )

    test_cases = models.ManyToManyField(
        TestCase,
        related_name='change_requests',
        blank=True,
        verbose_name=_('Test Cases'),
        help_text=_('Test cases associated with this change request'),
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', _('Draft')),
            ('SUBMITTED', _('Submitted')),
            ('APPROVED', _('Approved')),
            ('REJECTED', _('Rejected')),
            ('IN_PROGRESS', _('In Progress')),
            ('IMPLEMENTED', _('Implemented')),
            ('VERIFIED', _('Verified')),
            ('CLOSED', _('Closed')),
        ],
        default='DRAFT',
        verbose_name=_('Status'),
        help_text=_('Current status of this change request'),
    )

    priority = models.CharField(
        max_length=15,
        choices=[
            ('CRITICAL', _('Critical')),
            ('HIGH', _('High')),
            ('MEDIUM', _('Medium')),
            ('LOW', _('Low')),
        ],
        default='MEDIUM',
        verbose_name=_('Priority'),
        help_text=_('Priority of this change request'),
    )

    impact = models.CharField(
        max_length=15,
        choices=[
            ('HIGH', _('High')),
            ('MEDIUM', _('Medium')),
            ('LOW', _('Low')),
        ],
        default='MEDIUM',
        verbose_name=_('Impact'),
        help_text=_('Impact level of this change request'),
    )

    risk = models.CharField(
        max_length=15,
        choices=[
            ('HIGH', _('High')),
            ('MEDIUM', _('Medium')),
            ('LOW', _('Low')),
        ],
        default='MEDIUM',
        verbose_name=_('Risk'),
        help_text=_('Risk level of this change request'),
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='change_requests_created',
        verbose_name=_('Created By'),
        help_text=_('User who created this change request'),
    )

    creation_date = models.DateField(
        auto_now_add=True,
        verbose_name=_('Creation Date'),
        help_text=_('Date this change request was created'),
    )

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='change_requests_assigned',
        verbose_name=_('Assigned To'),
        help_text=_('User assigned to implement this change'),
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='change_requests_approved',
        verbose_name=_('Approved By'),
        help_text=_('User who approved this change'),
    )

    approval_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Approval Date'),
        help_text=_('Date this change was approved'),
    )

    implemented_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='change_requests_implemented',
        verbose_name=_('Implemented By'),
        help_text=_('User who implemented this change'),
    )

    implementation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Implementation Date'),
        help_text=_('Date this change was implemented'),
    )

    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='change_requests_verified',
        verbose_name=_('Verified By'),
        help_text=_('User who verified this change'),
    )

    verification_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Verification Date'),
        help_text=_('Date this change was verified'),
    )

    def __str__(self):
        """String representation of this ChangeRequest."""
        return f"{self.reference}: {self.title}"


class RequirementDocument(models.Model):
    """Model representing a document that contains requirements.

    Attributes:
        title: Document title
        document_type: Type of document
        reference: Unique reference for this document
        revision: Document revision or version
        description: Description of the document
        file: Associated file
        upload_date: Date the document was uploaded
        uploaded_by: User who uploaded the document
    """

    class Meta:
        """Metaclass options."""
        verbose_name = _('Requirement Document')
        verbose_name_plural = _('Requirement Documents')
        ordering = ['title']
        constraints = [
            models.UniqueConstraint(
                fields=['reference', 'revision'],
                name='unique_requirementdocument_reference'
            )
        ]

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the RequirementDocument model."""
        return reverse('api-requirementdocument-list')

    def get_absolute_url(self):
        """Return the web URL associated with this RequirementDocument instance."""
        return InvenTree.helpers.pui_url(f'/documentation/document/{self.pk}/')

    title = models.CharField(
        max_length=100,
        verbose_name=_('Title'),
        help_text=_('Document title'),
    )

    document_type = models.CharField(
        max_length=50,
        choices=[
            ('BRD', _('Business Requirements Document')),
            ('SRS', _('Software Requirements Specification')),
            ('SDD', _('Software Design Document')),
            ('STD', _('Software Test Document')),
            ('USER_STORY', _('User Story Document')),
            ('OTHER', _('Other')),
        ],
        default='USER_STORY',
        verbose_name=_('Document Type'),
        help_text=_('Type of document'),
    )

    reference = models.CharField(
        max_length=100,
        verbose_name=_('Reference'),
        help_text=_('Unique reference for this document'),
    )

    revision = models.CharField(
        max_length=10,
        default='1.0',
        verbose_name=_('Revision'),
        help_text=_('Document revision or version'),
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Description of the document'),
    )

    file = models.FileField(
        upload_to='requirement_documents/',
        verbose_name=_('File'),
        help_text=_('Associated file'),
    )

    upload_date = models.DateField(
        auto_now_add=True,
        verbose_name=_('Upload Date'),
        help_text=_('Date the document was uploaded'),
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='requirement_documents',
        verbose_name=_('Uploaded By'),
        help_text=_('User who uploaded the document'),
    )

    def __str__(self):
        """String representation of this RequirementDocument."""
        return f"{self.reference} Rev {self.revision}: {self.title}"


class TraceabilityMatrix:
    """Class for generating traceability matrices.

    This class is not a database model, but a utility class for generating
    traceability matrices between requirements, test cases, and change requests.
    """

    @staticmethod
    def requirement_test_matrix(requirements=None):
        """Generate a requirements-to-test traceability matrix.

        Args:
            requirements: QuerySet of requirements (optional)

        Returns:
            List of dicts with requirement and test coverage data
        """
        if requirements is None:
            requirements = Requirement.objects.all()

        matrix = []

        for req in requirements:
            test_cases = req.test_cases.all()

            # Calculate test coverage
            test_coverage = 0
            if test_cases.count() > 0:
                passed_tests = 0
                for test in test_cases:
                    latest_run = test.test_runs.order_by('-run_date').first()
                    if latest_run and latest_run.passed:
                        passed_tests += 1
                
                if test_cases.count() > 0:
                    test_coverage = (passed_tests / test_cases.count()) * 100

            matrix.append({
                'requirement': req,
                'test_cases': test_cases,
                'test_coverage': test_coverage,
                'test_count': test_cases.count(),
            })

        return matrix

    @staticmethod
    def requirement_cr_matrix(requirements=None):
        """Generate a requirements-to-change-request traceability matrix.

        Args:
            requirements: QuerySet of requirements (optional)

        Returns:
            List of dicts with requirement and change request data
        """
        if requirements is None:
            requirements = Requirement.objects.all()

        matrix = []

        for req in requirements:
            change_requests = req.change_requests.all()
            
            matrix.append({
                'requirement': req,
                'change_requests': change_requests,
                'cr_count': change_requests.count(),
            })

        return matrix

    @staticmethod
    def cr_test_matrix(change_requests=None):
        """Generate a change-request-to-test traceability matrix.

        Args:
            change_requests: QuerySet of change requests (optional)

        Returns:
            List of dicts with change request and test data
        """
        if change_requests is None:
            change_requests = ChangeRequest.objects.all()

        matrix = []

        for cr in change_requests:
            test_cases = cr.test_cases.all()
            
            # Calculate test coverage
            test_coverage = 0
            if test_cases.count() > 0:
                passed_tests = 0
                for test in test_cases:
                    latest_run = test.test_runs.order_by('-run_date').first()
                    if latest_run and latest_run.passed:
                        passed_tests += 1
                
                if test_cases.count() > 0:
                    test_coverage = (passed_tests / test_cases.count()) * 100
            
            matrix.append({
                'change_request': cr,
                'test_cases': test_cases,
                'test_coverage': test_coverage,
                'test_count': test_cases.count(),
            })

        return matrix


class DocumentationReport:
    """Class for generating documentation reports.

    This class is not a database model, but a utility class for generating
    various documentation reports.
    """

    @staticmethod
    def requirements_coverage_report():
        """Generate a report on requirements test coverage.

        Returns:
            Dict with requirements coverage data
        """
        requirements = Requirement.objects.all()
        
        total_requirements = requirements.count()
        requirements_with_tests = 0
        requirements_verified = 0
        
        for req in requirements:
            if req.test_cases.exists():
                requirements_with_tests += 1
            
            if req.is_verified():
                requirements_verified += 1
        
        test_coverage = 0
        if total_requirements > 0:
            test_coverage = (requirements_with_tests / total_requirements) * 100
        
        verification_coverage = 0
        if total_requirements > 0:
            verification_coverage = (requirements_verified / total_requirements) * 100
        
        return {
            'total_requirements': total_requirements,
            'requirements_with_tests': requirements_with_tests,
            'requirements_verified': requirements_verified,
            'test_coverage': test_coverage,
            'verification_coverage': verification_coverage,
        }

    @staticmethod
    def change_request_status_report():
        """Generate a report on change request statuses.

        Returns:
            Dict with change request status data
        """
        change_requests = ChangeRequest.objects.all()
        
        total_crs = change_requests.count()
        status_counts = {}
        
        for status, _ in ChangeRequest._meta.get_field('status').choices:
            status_counts[status] = change_requests.filter(status=status).count()
        
        return {
            'total_change_requests': total_crs,
            'status_counts': status_counts,
        }

    @staticmethod
    def test_execution_report():
        """Generate a report on test execution status.

        Returns:
            Dict with test execution data
        """
        test_cases = TestCase.objects.all()
        test_runs = TestRun.objects.all()
        
        total_tests = test_cases.count()
        tests_executed = 0
        tests_passed = 0
        tests_failed = 0
        
        for test in test_cases:
            latest_run = test.test_runs.order_by('-run_date').first()
            
            if latest_run:
                tests_executed += 1
                if latest_run.passed:
                    tests_passed += 1
                else:
                    tests_failed += 1
        
        execution_rate = 0
        if total_tests > 0:
            execution_rate = (tests_executed / total_tests) * 100
        
        pass_rate = 0
        if tests_executed > 0:
            pass_rate = (tests_passed / tests_executed) * 100
        
        return {
            'total_tests': total_tests,
            'tests_executed': tests_executed,
            'tests_passed': tests_passed,
            'tests_failed': tests_failed,
            'execution_rate': execution_rate,
            'pass_rate': pass_rate,
        }