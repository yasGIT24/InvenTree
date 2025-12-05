// [AGENT GENERATED CODE - REQUIREMENT: REQ-001, REQ-003]
import { useMemo } from 'react';
import { Card, Group, Text, Badge, Loader, Box } from '@mantine/core';
import { IconChartBar, IconTrendingUp, IconClock, IconUsers } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../api';

interface MetricsData {
  total_events: number;
  unique_users: number;
  events_by_type: Array<{
    metric_type: string;
    count: number;
  }>;
  top_events: Array<{
    event_name: string;
    count: number;
  }>;
}

interface MetricsWidgetProps {
  title?: string;
  startDate?: string;
  endDate?: string;
  userId?: number;
  compact?: boolean;
}

/**
 * Metrics widget component for displaying usage statistics.
 * This component fetches and displays metrics data in a dashboard widget format.
 */
export default function MetricsWidget({
  title = 'Usage Metrics',
  startDate,
  endDate,
  userId,
  compact = false,
}: MetricsWidgetProps) {
  
  const { data: metricsData, isLoading, error } = useQuery({
    queryKey: ['metrics-summary', startDate, endDate, userId],
    queryFn: async (): Promise<MetricsData> => {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (userId) params.append('user_id', userId.toString());
      
      const response = await api.get(`/api/common/metrics/summary/?${params}`);
      return response.data;
    },
    refetchInterval: 300000, // Refetch every 5 minutes
  });

  const topEventTypes = useMemo(() => {
    if (!metricsData?.events_by_type) return [];
    return metricsData.events_by_type
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);
  }, [metricsData]);

  const topEvents = useMemo(() => {
    if (!metricsData?.top_events) return [];
    return metricsData.top_events.slice(0, 5);
  }, [metricsData]);

  if (isLoading) {
    return (
      <Card withBorder padding="md">
        <Group justify="center" py="xl">
          <Loader size="sm" />
          <Text size="sm" c="dimmed">Loading metrics...</Text>
        </Group>
      </Card>
    );
  }

  if (error) {
    return (
      <Card withBorder padding="md">
        <Group justify="center" py="xl">
          <Text size="sm" c="red">Failed to load metrics</Text>
        </Group>
      </Card>
    );
  }

  if (compact) {
    return (
      <Card withBorder padding="sm">
        <Group justify="space-between" mb="xs">
          <Text fw={500} size="sm">{title}</Text>
          <IconChartBar size={16} />
        </Group>
        
        <Group justify="space-between">
          <Box>
            <Text size="lg" fw={700}>{metricsData?.total_events || 0}</Text>
            <Text size="xs" c="dimmed">Events</Text>
          </Box>
          <Box>
            <Text size="lg" fw={700}>{metricsData?.unique_users || 0}</Text>
            <Text size="xs" c="dimmed">Users</Text>
          </Box>
        </Group>
      </Card>
    );
  }

  return (
    <Card withBorder padding="md">
      <Group justify="space-between" mb="md">
        <Text fw={500}>{title}</Text>
        <IconChartBar size={20} />
      </Group>

      {/* Summary Stats */}
      <Group mb="md" grow>
        <Card withBorder padding="xs">
          <Group>
            <IconTrendingUp size={20} color="blue" />
            <Box>
              <Text size="xl" fw={700}>{metricsData?.total_events || 0}</Text>
              <Text size="xs" c="dimmed">Total Events</Text>
            </Box>
          </Group>
        </Card>
        
        <Card withBorder padding="xs">
          <Group>
            <IconUsers size={20} color="green" />
            <Box>
              <Text size="xl" fw={700}>{metricsData?.unique_users || 0}</Text>
              <Text size="xs" c="dimmed">Unique Users</Text>
            </Box>
          </Group>
        </Card>
      </Group>

      {/* Top Event Types */}
      {topEventTypes.length > 0 && (
        <Box mb="md">
          <Text size="sm" fw={500} mb="xs">Top Event Types</Text>
          {topEventTypes.map((eventType, index) => (
            <Group key={eventType.metric_type} justify="space-between" mb="xs">
              <Badge variant="light" size="sm">
                {eventType.metric_type.replace('_', ' ')}
              </Badge>
              <Text size="sm" fw={500}>{eventType.count}</Text>
            </Group>
          ))}
        </Box>
      )}

      {/* Top Events */}
      {topEvents.length > 0 && (
        <Box>
          <Text size="sm" fw={500} mb="xs">Most Frequent Events</Text>
          {topEvents.map((event, index) => (
            <Group key={event.event_name} justify="space-between" mb="xs">
              <Text size="xs" c="dimmed" truncate style={{ maxWidth: '60%' }}>
                {event.event_name}
              </Text>
              <Badge variant="outline" size="xs">{event.count}</Badge>
            </Group>
          ))}
        </Box>
      )}
    </Card>
  );
}