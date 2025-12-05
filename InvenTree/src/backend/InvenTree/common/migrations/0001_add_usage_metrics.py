# [AGENT GENERATED CODE - REQUIREMENT: REQ-001]
# Generated migration for UsageMetrics model

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('common', '0029_auto_20241201_0000'),  # Adjust to latest existing migration
    ]

    operations = [
        migrations.CreateModel(
            name='UsageMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True, help_text='When the metric was recorded', verbose_name='Timestamp')),
                ('metric_type', models.CharField(choices=[('api_call', 'API Call'), ('page_view', 'Page View'), ('user_action', 'User Action'), ('system_event', 'System Event'), ('export_event', 'Export Event'), ('report_generation', 'Report Generation')], db_index=True, help_text='Type of metric being tracked', max_length=20, verbose_name='Metric Type')),
                ('event_name', models.CharField(db_index=True, help_text='Name or identifier of the event', max_length=255, verbose_name='Event Name')),
                ('module', models.CharField(blank=True, help_text='System module where event occurred', max_length=100, verbose_name='Module')),
                ('url_path', models.CharField(blank=True, help_text='URL path for web-based events', max_length=500, verbose_name='URL Path')),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address of the client', null=True, verbose_name='IP Address')),
                ('user_agent', models.TextField(blank=True, help_text='User agent string from client', verbose_name='User Agent')),
                ('duration_ms', models.PositiveIntegerField(blank=True, help_text='Duration of the event in milliseconds', null=True, verbose_name='Duration (ms)')),
                ('data_size_bytes', models.PositiveIntegerField(blank=True, help_text='Size of data processed in bytes', null=True, verbose_name='Data Size (bytes)')),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional metric data as JSON', verbose_name='Metadata')),
                ('user', models.ForeignKey(blank=True, help_text='User associated with this metric', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Usage Metric',
                'verbose_name_plural': 'Usage Metrics',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='usagemetrics',
            index=models.Index(fields=['timestamp', 'metric_type'], name='common_usag_timesta_8a9c91_idx'),
        ),
        migrations.AddIndex(
            model_name='usagemetrics',
            index=models.Index(fields=['user', 'timestamp'], name='common_usag_user_id_4b2c73_idx'),
        ),
        migrations.AddIndex(
            model_name='usagemetrics',
            index=models.Index(fields=['event_name', 'timestamp'], name='common_usag_event_n_7d8e42_idx'),
        ),
    ]