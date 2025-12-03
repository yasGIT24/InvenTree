"""Background tasks for the stock app."""

import structlog
import datetime
from decimal import Decimal
from django.db.models import Sum, F, Q
from django.utils.translation import gettext_lazy as _
from opentelemetry import trace

tracer = trace.get_tracer(__name__)
logger = structlog.get_logger('inventree')


@tracer.start_as_current_span('rebuild_stock_items')
def rebuild_stock_items():
    """Rebuild the entire StockItem tree structure.

    This may be necessary if the tree structure has become corrupted or inconsistent.
    """
    from InvenTree.exceptions import log_error
    from InvenTree.sentry import report_exception
    from stock.models import StockItem

    logger.info('Rebuilding StockItem tree structure')

    try:
        StockItem.objects.rebuild()
    except Exception as e:
        # This is a critical error, explicitly report to sentry
        report_exception(e)

        log_error('rebuild_stock_items')
        logger.exception('Failed to rebuild StockItem tree: %s', e)


def rebuild_stock_item_tree(tree_id: int, rebuild_on_fail: bool = True) -> bool:
    """Rebuild the stock tree structure.

    Arguments:
        tree_id (int): The ID of the StockItem tree to rebuild.
        rebuild_on_fail (bool): If True, will attempt to rebuild the entire StockItem tree if the partial rebuild fails.

    Returns:
        bool: True if the partial tree rebuild was successful, False otherwise.

    - If the rebuild fails, schedule a rebuild of the entire StockItem tree.
    """
    from InvenTree.exceptions import log_error
    from InvenTree.sentry import report_exception
    from InvenTree.tasks import offload_task
    from stock.models import StockItem

    if tree_id:
        try:
            StockItem.objects.partial_rebuild(tree_id)
            logger.info('Rebuilt StockItem tree for tree_id: %s', tree_id)
            return True
        except Exception as e:
            # This is a critical error, explicitly report to sentry
            report_exception(e)

            log_error('rebuild_stock_item_tree')
            logger.warning('Failed to rebuild StockItem tree for tree_id: %s', tree_id)
            # If the partial rebuild fails, rebuild the entire tree
            if rebuild_on_fail:
                offload_task(rebuild_stock_items, group='stock')
            return False
    else:
        # No tree_id provided, so rebuild the entire tree
        StockItem.objects.rebuild()
        return True


@tracer.start_as_current_span('update_stock_consumption_rates')
def update_stock_consumption_rates():
    """Update consumption rates for all stock items.
    
    This task calculates average consumption rates based on historical stock usage.
    
    The calculation uses a weighted average of recent stock movements that
    indicate consumption (such as stock removal, allocation to builds, etc.).
    """
    from InvenTree.exceptions import log_error
    from InvenTree.sentry import report_exception
    from stock.models import StockItem, StockItemTracking
    from InvenTree.status_codes import StockHistoryCode
    from common.settings import get_global_setting
    from InvenTree.helpers import current_date
    
    # Get analysis window (days to look back for consumption data)
    analysis_days = get_global_setting('STOCK_CONSUMPTION_ANALYSIS_DAYS', 90)
    
    # Calculate the date threshold
    today = current_date()
    threshold_date = today - datetime.timedelta(days=analysis_days)
    
    try:
        # Get all stock items with tracking information related to consumption
        stock_items = StockItem.objects.all()
        
        consumption_codes = [
            StockHistoryCode.STOCK_REMOVE.value,
            StockHistoryCode.SPLIT_FROM_PARENT.value,
            StockHistoryCode.INSTALLED_INTO_ASSEMBLY.value,
            StockHistoryCode.SENT_TO_CUSTOMER.value,
        ]
        
        for item in stock_items:
            # Get consumption history for this item
            tracking_info = StockItemTracking.objects.filter(
                item=item,
                date__gte=threshold_date,
                tracking_type__in=consumption_codes
            ).order_by('date')
            
            if not tracking_info.exists():
                continue
                
            # Calculate consumption rate based on tracking history
            total_consumed = Decimal(0)
            
            for entry in tracking_info:
                # Try to extract quantity from tracking entry
                if entry.deltas and 'removed' in entry.deltas:
                    try:
                        total_consumed += Decimal(entry.deltas['removed'])
                    except (ValueError, TypeError):
                        pass
            
            # Only update if we have consumed something
            if total_consumed > 0:
                # Calculate consumption rate (per day)
                daily_rate = total_consumed / analysis_days
                
                # Update the stock item
                item.consumption_rate = daily_rate
                item.last_consumption_date = today
                item.save()
    
    except Exception as e:
        # Report error to sentry
        report_exception(e)
        
        log_error('update_stock_consumption_rates')
        logger.exception('Failed to update stock consumption rates: %s', e)


@tracer.start_as_current_span('check_stock_thresholds')
def check_stock_thresholds():
    """Check stock thresholds and send notifications for items below thresholds.
    
    This task evaluates all stock items against their threshold settings and triggers
    notifications when stock levels are below safety stock or reorder point.
    """
    from InvenTree.exceptions import log_error
    from InvenTree.sentry import report_exception
    from plugin.events import trigger_event
    from stock.models import StockItem
    from stock.events import StockEvents
    
    try:
        # Get all in-stock items
        stock_items = StockItem.objects.filter(StockItem.IN_STOCK_FILTER)
        
        # Items below safety stock (critical)
        safety_items = []
        
        # Items below reorder point (warning)
        reorder_items = []
        
        for item in stock_items:
            # Skip items with no thresholds set
            if item.safety_stock <= 0 and item.reorder_point <= 0:
                continue
                
            # Check threshold status
            status = item.check_threshold_status()
            
            if status['below_safety']:
                safety_items.append(item.pk)
            elif status['below_reorder']:
                reorder_items.append(item.pk)
        
        # Trigger events for items below safety stock (critical)
        if safety_items:
            trigger_event(
                StockEvents.STOCK_THRESHOLD_SAFETY,
                ids=safety_items,
                threshold_type='safety'
            )
            
            logger.info(f"Found {len(safety_items)} items below safety stock threshold")
        
        # Trigger events for items below reorder point (warning)
        if reorder_items:
            trigger_event(
                StockEvents.STOCK_THRESHOLD_REORDER,
                ids=reorder_items,
                threshold_type='reorder'
            )
            
            logger.info(f"Found {len(reorder_items)} items below reorder threshold")
            
    except Exception as e:
        # Report error to sentry
        report_exception(e)
        
        log_error('check_stock_thresholds')
        logger.exception('Failed to check stock thresholds: %s', e)


@tracer.start_as_current_span('check_expiry_dates')
def check_expiry_dates():
    """Check stock items for expiry and send notifications.
    
    This task checks for items that are:
    1. About to expire (within warning threshold)
    2. Already expired
    
    It sends notifications for both cases.
    """
    from InvenTree.exceptions import log_error
    from InvenTree.sentry import report_exception
    from plugin.events import trigger_event
    from stock.models import StockItem
    from stock.events import StockEvents
    from common.settings import get_global_setting
    from InvenTree.helpers import current_date
    
    try:
        # Get expiry warning days setting
        warning_days = get_global_setting('STOCK_EXPIRY_WARNING_DAYS', 30)
        
        today = current_date()
        warning_date = today + datetime.timedelta(days=warning_days)
        
        # Filter for in-stock items that have expiry dates
        stock_items = StockItem.objects.exclude(expiry_date=None).filter(StockItem.IN_STOCK_FILTER)
        
        # Get expired items
        expired_items = stock_items.filter(expiry_date__lt=today)
        
        # Get about-to-expire items (not already expired)
        expiring_items = stock_items.filter(
            expiry_date__gte=today,
            expiry_date__lte=warning_date
        )
        
        # Trigger events for expired items
        expired_ids = [item.pk for item in expired_items]
        if expired_ids:
            trigger_event(
                StockEvents.STOCK_EXPIRED,
                ids=expired_ids,
            )
            
            logger.info(f"Found {len(expired_ids)} expired stock items")
        
        # Trigger events for items about to expire
        expiring_ids = [item.pk for item in expiring_items]
        if expiring_ids:
            trigger_event(
                StockEvents.STOCK_EXPIRY_WARNING,
                ids=expiring_ids,
                days=warning_days
            )
            
            logger.info(f"Found {len(expiring_ids)} stock items about to expire")
    
    except Exception as e:
        # Report error to sentry
        report_exception(e)
        
        log_error('check_expiry_dates')
        logger.exception('Failed to check stock expiry dates: %s', e)