"""Background tasks for the exporting app."""

from django.contrib.auth.models import User
from django.test.client import RequestFactory

import structlog

from common.models import DataOutput

logger = structlog.get_logger('inventree')


def export_data(
    view_class,
    user_id: int,
    query_params: dict,
    plugin_key: str,
    export_format: str,
    export_context: dict,
    output_id: int,
):
    """Perform the data export task using the provided parameters.

    Arguments:
        view_class: The class of the view to export data from
        user_id: The ID of the user who requested the export
        query_params: Query parameters for the export
        plugin_key: The key for the export plugin
        export_format: The output format for the export
        export_context: Additional options for the export
        output_id: The ID of the DataOutput instance to write to

    This function is designed to be called by the background task,
    to avoid blocking the web server.
    """
    from plugin import registry

    if (plugin := registry.get_plugin(plugin_key, active=True)) is None:
        logger.warning("export_data: Plugin '%s' not found", plugin_key)
        return

    if (user := User.objects.filter(pk=user_id).first()) is None:
        logger.warning('export_data: User not found: %d', user_id)
        return

    if (output := DataOutput.objects.filter(pk=output_id).first()) is None:
        logger.warning('export_data: Output object not found: %d', output_id)
        return

    # Recreate the request object - this is required for the view to function correctly
    # Note that the request object cannot be pickled, so we need to recreate it here
    request = RequestFactory()
    request.user = user
    request.query_params = query_params

    view = view_class()
    view.request = request
    view.args = getattr(view, 'args', ())
    view.kwargs = getattr(view, 'kwargs', {})
    view.format_kwarg = getattr(view, 'format_kwarg', None)

    view.export_data(plugin, export_format, export_context, output)


# [AGENT GENERATED CODE - REQUIREMENT: REQ-001, REQ-002]
def export_metrics_data(
    user_id: int,
    start_date: str,
    end_date: str,
    export_format: str,
    filter_params: dict,
    output_id: int,
):
    """Export usage metrics data to various formats.
    
    Arguments:
        user_id: The ID of the user who requested the export
        start_date: Start date for metrics export (ISO format)
        end_date: End date for metrics export (ISO format)  
        export_format: The output format (csv, excel, json, etc.)
        filter_params: Additional filter parameters
        output_id: The ID of the DataOutput instance to write to
    """
    from datetime import datetime
    from django.utils import timezone
    import json
    import csv
    import io
    from common.models import UsageMetrics, DataOutput
    
    logger.info(f"Starting metrics export for user {user_id}")
    
    # Get user and output objects
    if (user := User.objects.filter(pk=user_id).first()) is None:
        logger.warning('export_metrics_data: User not found: %d', user_id)
        return
        
    if (output := DataOutput.objects.filter(pk=output_id).first()) is None:
        logger.warning('export_metrics_data: Output object not found: %d', output_id)
        return
    
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Build queryset
        queryset = UsageMetrics.objects.filter(
            timestamp__gte=start_dt,
            timestamp__lte=end_dt
        )
        
        # Apply additional filters
        if filter_params.get('metric_type'):
            queryset = queryset.filter(metric_type=filter_params['metric_type'])
        if filter_params.get('user_filter'):
            queryset = queryset.filter(user_id=filter_params['user_filter'])
        if filter_params.get('module'):
            queryset = queryset.filter(module=filter_params['module'])
            
        # Order by timestamp
        queryset = queryset.order_by('-timestamp')
        
        # Export based on format
        if export_format.lower() == 'csv':
            content = _export_metrics_csv(queryset)
            content_type = 'text/csv'
            filename = f'metrics_export_{start_date}_{end_date}.csv'
            
        elif export_format.lower() == 'json':
            content = _export_metrics_json(queryset)
            content_type = 'application/json'
            filename = f'metrics_export_{start_date}_{end_date}.json'
            
        elif export_format.lower() == 'excel':
            content = _export_metrics_excel(queryset)
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f'metrics_export_{start_date}_{end_date}.xlsx'
            
        else:
            logger.error(f"Unsupported export format: {export_format}")
            return
            
        # Save to DataOutput
        from django.core.files.base import ContentFile
        output.data.save(filename, ContentFile(content))
        output.complete = True
        output.save()
        
        logger.info(f"Metrics export completed: {filename}")
        
        # Record the export as a metric
        UsageMetrics.record_metric(
            metric_type=UsageMetrics.MetricType.EXPORT_EVENT,
            event_name='metrics_export',
            user=user,
            module='data_exporter',
            metadata={
                'export_format': export_format,
                'start_date': start_date,
                'end_date': end_date,
                'record_count': queryset.count(),
                'filename': filename
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting metrics data: {e}")
        output.complete = True
        output.error_message = str(e)
        output.save()


def _export_metrics_csv(queryset):
    """Export metrics to CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Timestamp', 'User', 'Metric Type', 'Event Name', 'Module',
        'URL Path', 'IP Address', 'Duration (ms)', 'Data Size (bytes)', 'Metadata'
    ])
    
    # Write data rows
    for metric in queryset:
        writer.writerow([
            metric.timestamp.isoformat(),
            metric.user.username if metric.user else '',
            metric.metric_type,
            metric.event_name,
            metric.module,
            metric.url_path,
            metric.ip_address,
            metric.duration_ms,
            metric.data_size_bytes,
            json.dumps(metric.metadata) if metric.metadata else ''
        ])
    
    return output.getvalue().encode('utf-8')


def _export_metrics_json(queryset):
    """Export metrics to JSON format."""
    data = []
    for metric in queryset:
        data.append({
            'timestamp': metric.timestamp.isoformat(),
            'user': metric.user.username if metric.user else None,
            'user_id': metric.user.id if metric.user else None,
            'metric_type': metric.metric_type,
            'event_name': metric.event_name,
            'module': metric.module,
            'url_path': metric.url_path,
            'ip_address': metric.ip_address,
            'duration_ms': metric.duration_ms,
            'data_size_bytes': metric.data_size_bytes,
            'metadata': metric.metadata
        })
    
    return json.dumps(data, indent=2).encode('utf-8')


def _export_metrics_excel(queryset):
    """Export metrics to Excel format."""
    try:
        import pandas as pd
        from io import BytesIO
        
        # Convert queryset to dataframe
        data = []
        for metric in queryset:
            data.append({
                'Timestamp': metric.timestamp,
                'User': metric.user.username if metric.user else '',
                'Metric Type': metric.metric_type,
                'Event Name': metric.event_name,
                'Module': metric.module,
                'URL Path': metric.url_path,
                'IP Address': metric.ip_address,
                'Duration (ms)': metric.duration_ms,
                'Data Size (bytes)': metric.data_size_bytes,
                'Metadata': json.dumps(metric.metadata) if metric.metadata else ''
            })
        
        df = pd.DataFrame(data)
        
        # Export to Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Metrics', index=False)
        
        return output.getvalue()
        
    except ImportError:
        # Fallback to CSV if pandas/openpyxl not available
        logger.warning("pandas/openpyxl not available, falling back to CSV export")
        return _export_metrics_csv(queryset)
