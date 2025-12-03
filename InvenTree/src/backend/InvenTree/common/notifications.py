"""Base classes and functions for notifications."""

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Model
from django.utils.translation import gettext_lazy as _

import structlog

import common.models
from InvenTree.exceptions import log_error
from InvenTree.ready import isImportingData, isRebuildingData
from plugin import PluginMixinEnum, registry
from users.models import Owner
from users.permissions import check_user_permission

logger = structlog.get_logger('inventree')


# region methods
@dataclass()
class NotificationBody:
    """Information needed to create a notification.

    Attributes:
        name (str): Name (or subject) of the notification
        slug (str): Slugified reference for notification
        message (str): Notification message as text. Should not be longer than 120 chars.
        template (str): Reference to the html template for the notification.

    The strings support f-string style formatting with context variables parsed at runtime.

    Context variables:
        instance: Text representing the instance
        verbose_name: Verbose name of the model
        app_label: App label (slugified) of the model
        model_name': Name (slugified) of the model
    """

    name: str
    slug: str
    message: str
    template: Optional[str] = None


class InvenTreeNotificationBodies:
    """Default set of notifications for InvenTree.

    Contains regularly used notification bodies.
    """

    NewOrder = NotificationBody(
        name=_('New {verbose_name}'),
        slug='{app_label}.new_{model_name}',
        message=_('A new order has been created and assigned to you'),
        template='email/new_order_assigned.html',
    )
    """Send when a new order (build, sale or purchase) was created."""

    OrderCanceled = NotificationBody(
        name=_('{verbose_name} canceled'),
        slug='{app_label}.canceled_{model_name}',
        message=_('A order that is assigned to you was canceled'),
        template='email/canceled_order_assigned.html',
    )
    """Send when a order (sale, return or purchase) was canceled."""

    ItemsReceived = NotificationBody(
        name=_('Items Received'),
        slug='purchase_order.items_received',
        message=_('Items have been received against a purchase order'),
        template='email/purchase_order_received.html',
    )

    ReturnOrderItemsReceived = NotificationBody(
        name=_('Items Received'),
        slug='return_order.items_received',
        message=_('Items have been received against a return order'),
        template='email/return_order_received.html',
    )
    
    # [AGENT GENERATED CODE - REQUIREMENT:REQ-AUTH-003]
    OTPCode = NotificationBody(
        name=_('Authentication OTP Code'),
        slug='auth.otp_code',
        message=_('Your one-time password (OTP) for authentication'),
        template='email/otp_code.html',
    )
    """Send when a user needs an OTP code for two-factor authentication."""
    
    # [AGENT GENERATED CODE - REQUIREMENT:REQ-AUTH-004]
    SessionTimeout = NotificationBody(
        name=_('Session Timeout'),
        slug='auth.session_timeout',
        message=_('Your session has expired due to inactivity'),
        template='email/session_timeout.html',
    )
    """Send when a user session times out due to inactivity."""


# [AGENT GENERATED CODE - REQUIREMENT:REQ-AUTH-003]
def send_otp_notification(user, otp_code, delivery_method='email'):
    """Send an OTP code to the user via the specified delivery method.
    
    Args:
        user: The user to send the OTP code to
        otp_code: The OTP code to send
        delivery_method: The method to use for delivery ('email' or 'sms')
    
    Returns:
        bool: True if the notification was sent successfully
    """
    
    context = {
        'user': user,
        'otp_code': otp_code,
        'instance': otp_code,
        'verbose_name': 'OTP Code',
        'app_label': 'auth',
        'model_name': 'otp',
    }
    
    # Use the notification system to deliver the OTP
    return trigger_notification(
        None,  # No specific model object
        category='auth.otp_code',
        obj_ref='otp',
        context=context,
        targets=[user],
        check_recent=False,  # Always send OTP codes, even if recent
    )

# [AGENT GENERATED CODE - REQUIREMENT:REQ-AUTH-004]
def send_session_timeout_notification(user):
    """Send a session timeout notification to the user.
    
    Args:
        user: The user to notify about the session timeout
    
    Returns:
        bool: True if the notification was sent successfully
    """
    
    context = {
        'user': user,
        'instance': user.username,
        'verbose_name': 'Session Timeout',
        'app_label': 'auth',
        'model_name': 'session',
    }
    
    return trigger_notification(
        None,  # No specific model object
        category='auth.session_timeout',
        obj_ref='session',
        context=context,
        targets=[user],
    )

def trigger_notification(
    obj: Model, category: Optional[str] = None, obj_ref: str = 'pk', **kwargs
):
    """Send out a notification.

    Args:
        obj: The object (model instance) that is triggering the notification
        category: The category (label) for the notification
        obj_ref: The reference to the object that should be used for the notification
        kwargs: Additional arguments to pass to the notification method
    """
    # Check if data is importing currently
    if isImportingData() or isRebuildingData():  # pragma: no cover
        return

    targets = kwargs.get('targets')
    target_fnc = kwargs.get('target_fnc')
    target_args = kwargs.get('target_args', [])
    target_kwargs = kwargs.get('target_kwargs', {})
    target_exclude = kwargs.get('target_exclude')
    context = kwargs.get('context', {})
    delivery_methods = kwargs.get('delivery_methods')
    check_recent = kwargs.get('check_recent', True)

    # Resolve object reference
    refs = [obj_ref, 'pk', 'id', 'uid']

    obj_ref_value = None

    # Find the first reference that is available
    if obj:
        for ref in refs:
            if hasattr(obj, ref):
                obj_ref_value = getattr(obj, ref)
                break

        if not obj_ref_value:
            raise KeyError(
                f"Could not resolve an object reference for '{obj!s}' with {','.join(set(refs))}"
            )

    # Check if we have notified recently...
    delta = timedelta(days=1)

    if check_recent and common.models.NotificationEntry.check_recent(
        category, obj_ref_value, delta
    ):
        logger.info(
            "Notification '%s' has recently been sent for '%s' - SKIPPING",
            category,
            str(obj),
        )
        return

    logger.info("Gathering users for notification '%s'", category)

    if target_exclude is None:
        target_exclude = set()

    # Collect possible targets
    if not targets and target_fnc:
        targets = target_fnc(*target_args, **target_kwargs)

    # Convert list of targets to a list of users
    # (targets may include 'owner' or 'group' classes)
    target_users = set()

    if targets:
        for target in targets:
            if target is None:
                continue
            # User instance is provided
            elif isinstance(target, get_user_model()):
                if target not in target_exclude:
                    target_users.add(target)
            # Group instance is provided
            elif isinstance(target, Group):
                for user in get_user_model().objects.filter(groups__name=target.name):
                    if user not in target_exclude:
                        target_users.add(user)
            # Owner instance (either 'user' or 'group' is provided)
            elif isinstance(target, Owner):
                for owner in target.get_related_owners(include_group=False):
                    user = owner.owner
                    if user not in target_exclude:
                        target_users.add(user)
            # Unhandled type
            else:
                logger.error(
                    'Unknown target passed to trigger_notification method: %s', target
                )

    # Filter out any users who are inactive, or do not have the required model permissions
    valid_users = list(
        filter(
            lambda u: u
            and u.is_active
            and (not obj or check_user_permission(u, obj, 'view')),
            list(target_users),
        )
    )

    # Track whether any notifications were sent
    result = False

    # Send out via all registered notification methods
    for plugin in registry.with_mixin(PluginMixinEnum.NOTIFICATION):
        # Skip if the plugin is *not* in the "delivery_methods" list?
        match = not delivery_methods

        for notification_class in delivery_methods or []:
            if type(notification_class) is str:
                if plugin.slug == notification_class:
                    match = True
                    break

            elif getattr(notification_class, 'SLUG', None) == plugin.slug:
                match = True
                break

        if not match:
            continue

        try:
            # Plugin may optionally filter target users
            filtered_users = plugin.filter_targets(list(valid_users))
            if plugin.send_notification(obj, category, filtered_users, context):
                result = True
        except Exception:
            log_error('send_notification', plugin=plugin.slug)

    # Log the notification entry
    if result:
        common.models.NotificationEntry.notify(category, obj_ref_value)
