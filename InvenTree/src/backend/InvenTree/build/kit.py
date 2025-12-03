"""Kit database model definitions for InvenTree."""

# <!-- AGENT GENERATED CODE: KIT MANAGEMENT MODULE -->

import decimal
from datetime import datetime

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog

import InvenTree.fields
import InvenTree.helpers
import InvenTree.helpers_model
import InvenTree.models
import part.models
import stock.models
import users.models
from build.events import BuildEvents
from build.models import Build
from common.models import ProjectCode
from common.notifications import trigger_notification
from generic.states import StatusCodeMixin
from plugin.events import trigger_event
from stock.status_codes import StockHistoryCode, StockStatus

logger = structlog.get_logger('inventree')


class KitBuild(
    InvenTree.models.PluginValidationMixin,
    InvenTree.models.InvenTreeAttachmentMixin,
    InvenTree.models.InvenTreeBarcodeMixin,
    InvenTree.models.InvenTreeNotesMixin,
    InvenTree.models.MetadataMixin,
    StatusCodeMixin,
):
    """A KitBuild object organizes the assembly of kits for finished or in-process goods.

    Attributes:
        build: Reference to the parent Build object
        part: The part being assembled (should match the build.part)
        reference: Kit reference (must be unique)
        title: Brief title describing the kit (optional)
        quantity: Number of kits to be assembled
        target_date: Desired completion date
        completion_date: Date the kit assembly was completed
        batch: Batch code for kit components
        status: Kit status code
        link: External URL for more information
        notes: Text notes
        completed_by: User that completed the kit assembly
    """

    class Meta:
        """Metaclass options."""
        verbose_name = _('Kit')
        verbose_name_plural = _('Kits')
        constraints = [
            models.UniqueConstraint(fields=['reference'], name='unique_kit_reference'),
        ]

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the KitBuild model."""
        return reverse('api-kit-list')

    def get_absolute_url(self):
        """Return the web URL associated with this KitBuild instance."""
        return InvenTree.helpers.pui_url(f'/kit/{self.id}')

    def save(self, *args, **kwargs):
        """Custom save method for the KitBuild model."""
        if not self.reference:
            # Generate a reference
            self.reference = f"KIT-{self.id if self.id else InvenTree.helpers.generate_next_int()}"

        # Ensure the part matches the build part
        if self.build and not self.part:
            self.part = self.build.part

        super().save(*args, **kwargs)

    def clean(self):
        """Perform validation for the KitBuild model."""
        super().clean()

        if self.build and self.part != self.build.part:
            raise models.ValidationError({
                'part': _('Kit part must match the build part')
            })

    def __str__(self):
        """String representation."""
        return self.reference

    @transaction.atomic
    def complete(self, user):
        """Mark this kit as complete."""
        self.completion_date = datetime.now().date()
        self.completed_by = user
        self.status = KitStatus.COMPLETE
        self.save()

        # Trigger events
        trigger_event(BuildEvents.KIT_COMPLETED, id=self.pk, build_id=self.build.pk)

        # Notify relevant users
        targets = [self.build.issued_by, self.build.responsible]

        # Add any part subscribers
        targets.extend(self.part.get_subscribers())

        context = {
            'kit': self,
            'name': _(f'Kit {self} has been completed'),
            'slug': 'kit.completed',
            'message': _('A kit has been completed'),
            'link': InvenTree.helpers_model.construct_absolute_url(
                self.get_absolute_url()
            ),
        }

        trigger_notification(
            self,
            'kit.completed',
            targets=targets,
            context=context,
            target_exclude=[user],
        )

    # Relationships
    build = models.ForeignKey(
        Build,
        on_delete=models.CASCADE,
        related_name='kits',
        help_text=_('Build order'),
        verbose_name=_('Build Order'),
    )

    part = models.ForeignKey(
        'part.Part',
        verbose_name=_('Part'),
        on_delete=models.CASCADE,
        related_name='kit_builds',
        help_text=_('Kit part'),
        limit_choices_to={'assembly': True},
    )

    # Fields
    reference = models.CharField(
        unique=True,
        max_length=64,
        verbose_name=_('Reference'),
        help_text=_('Kit reference'),
    )

    title = models.CharField(
        blank=True,
        max_length=250,
        verbose_name=_('Title'),
        help_text=_('Brief description of the kit'),
    )

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_('Quantity'),
        help_text=_('Number of kits to create'),
    )

    batch = models.CharField(
        blank=True,
        max_length=100,
        verbose_name=_('Batch'),
        help_text=_('Batch code for kit components'),
    )

    target_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Target Date'),
        help_text=_('Target date for kit completion'),
    )

    completion_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Completion Date'),
        help_text=_('Date the kit was completed'),
    )

    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='completed_kits',
        verbose_name=_('Completed By'),
        help_text=_('User who completed the kit assembly'),
    )

    status = models.PositiveIntegerField(
        default=KitStatus.PENDING,
        choices=KitStatus.items(),
        validators=[MinValueValidator(0)],
        verbose_name=_('Status'),
        help_text=_('Kit status'),
    )

    link = InvenTree.fields.InvenTreeURLField(
        blank=True,
        verbose_name=_('Link'),
        help_text=_('External link to additional information'),
    )

    @property
    def is_complete(self):
        """Return True if this kit is complete."""
        return self.status == KitStatus.COMPLETE

    @property
    def components(self):
        """Return all KitItem objects for this kit."""
        return self.items.all()

    @transaction.atomic
    def allocate_stock(self, user):
        """Allocate stock to this kit."""
        for item in self.items.all():
            if item.stock_item and not item.is_allocated:
                item.allocate(user)

    @transaction.atomic
    def complete_allocation(self, user):
        """Complete allocation for this kit (for all items that have stock allocated)."""
        for item in self.items.filter(stock_item__isnull=False):
            if not item.is_complete:
                item.complete_allocation(user)


class KitStatus:
    """Status codes for the KitBuild model."""

    PENDING = 10
    IN_PROGRESS = 20
    COMPLETE = 30
    CANCELLED = 40

    @classmethod
    def items(cls):
        """All available status codes."""
        return [
            (cls.PENDING, _('Pending')),
            (cls.IN_PROGRESS, _('In Progress')),
            (cls.COMPLETE, _('Complete')),
            (cls.CANCELLED, _('Cancelled')),
        ]

    @classmethod
    def text(cls, code):
        """Return text value for specified status code."""
        for id, text in cls.items():
            if id == code:
                return text
        return ''


class KitItem(InvenTree.models.InvenTreeMetadataModel):
    """A KitItem represents a component part in a kit assembly.

    Attributes:
        kit: Link to a KitBuild object
        bom_item: Link to a BomItem object (defines the component)
        stock_item: Link to a StockItem (tracks component stock)
        quantity: Required quantity for this component
        install_into: Link to a StockItem (the completed kit item)
        notes: Component notes
    """

    class Meta:
        """Metaclass options."""
        verbose_name = _('Kit Item')
        verbose_name_plural = _('Kit Items')
        unique_together = [('kit', 'bom_item')]

    def save(self, *args, **kwargs):
        """Custom save method for the KitItem model."""
        self.clean()
        super().save(*args, **kwargs)

    def clean(self):
        """Validate this KitItem instance."""
        super().clean()

        if self.bom_item and self.bom_item.part != self.kit.part:
            raise models.ValidationError({
                'bom_item': _('BOM item must match the kit part')
            })

    @property
    def part(self):
        """Return the Part instance for this KitItem."""
        if self.bom_item:
            return self.bom_item.sub_part
        return None

    @property
    def is_allocated(self):
        """Return True if this KitItem has stock allocated."""
        return self.stock_item is not None

    @property
    def is_complete(self):
        """Return True if this KitItem is complete."""
        return self.completed is True

    @transaction.atomic
    def allocate(self, user=None, stock_item=None):
        """Allocate stock to this KitItem.

        Args:
            user: The user who is allocating stock
            stock_item: Specific stock item to allocate (optional)
        """
        if not self.bom_item:
            return

        # If stock_item not specified, attempt to find suitable stock
        if not stock_item:
            # Find available stock
            stock_items = stock.models.StockItem.objects.filter(
                part=self.bom_item.sub_part,
                quantity__gte=self.quantity
            )

            # Filter for available stock
            stock_items = stock_items.filter(stock.models.StockItem.IN_STOCK_FILTER)

            # Order by oldest first
            stock_items = stock_items.order_by('creation_date')

            if stock_items.count() > 0:
                stock_item = stock_items.first()
            else:
                return False

        # Assign stock to this kit item
        self.stock_item = stock_item
        self.save()

        # Add a tracking entry for this allocation
        stock_item.add_tracking_entry(
            StockHistoryCode.KIT_ALLOCATION,
            user,
            notes=f"Allocated to kit {self.kit.reference}",
            deltas={
                'kit': self.kit.pk,
                'kit_item': self.pk,
            }
        )

        return True

    @transaction.atomic
    def complete_allocation(self, user=None):
        """Complete the allocation for this KitItem.

        Args:
            user: The user who is completing the allocation
        """
        if not self.stock_item:
            return False

        # Mark this kit item as complete
        self.completed = True
        self.save()

        stock_item = self.stock_item

        # Add a tracking entry for this allocation
        stock_item.add_tracking_entry(
            StockHistoryCode.KIT_COMPONENT_INSTALLED,
            user,
            notes=f"Installed in kit {self.kit.reference}",
            deltas={
                'kit': self.kit.pk,
                'kit_item': self.pk,
            }
        )

        # If there is a destination item, install the stock there
        if self.install_into:
            self.stock_item.belongs_to = self.install_into
            self.stock_item.save()

        return True

    # Relationships
    kit = models.ForeignKey(
        KitBuild,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Kit'),
        help_text=_('Kit build'),
    )

    bom_item = models.ForeignKey(
        'part.BomItem',
        on_delete=models.CASCADE,
        related_name='kit_items',
        verbose_name=_('BOM Item'),
        help_text=_('BOM item in the kit'),
    )

    stock_item = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='kit_allocations',
        verbose_name=_('Stock Item'),
        help_text=_('Stock item for this kit component'),
    )

    install_into = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='installed_kit_items',
        verbose_name=_('Install Into'),
        help_text=_('Install this component into a specific stock item'),
    )

    # Fields
    quantity = models.DecimalField(
        decimal_places=5,
        max_digits=15,
        default=1,
        validators=[MinValueValidator(0)],
        verbose_name=_('Quantity'),
        help_text=_('Required quantity for this component'),
    )

    completed = models.BooleanField(
        default=False,
        verbose_name=_('Completed'),
        help_text=_('Has this component been installed?')
    )

    notes = models.CharField(
        blank=True,
        max_length=250,
        verbose_name=_('Notes'),
        help_text=_('Component notes'),
    )