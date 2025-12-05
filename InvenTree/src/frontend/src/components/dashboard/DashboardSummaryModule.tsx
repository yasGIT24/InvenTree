// [AGENT GENERATED CODE - REQUIREMENT: REQ-003]
import { useState, useMemo } from 'react';
import {
  Card,
  Group,
  Text,
  Badge,
  Loader,
  Box,
  Grid,
  Select,
  Button,
  Stack,
  Tabs,
  ScrollArea,
  ThemeIcon,
  Progress,
  ActionIcon,
  Tooltip,
} from '@mantine/core';
import {
  IconDashboard,
  IconChartBar,
  IconUsers,
  IconActivity,
  IconDownload,
  IconRefresh,
  IconCalendar,
  IconTrendingUp,
  IconTrendingDown,
} from '@tabler/icons-react';
import { DatePickerInput } from '@mantine/dates';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import { api } from '../../api';
import MetricsWidget from '../metrics/MetricsWidget';

interface DashboardStats {
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
  daily_metrics: Array<{
    date: string;
    count: number;
  }>;
}

/**
 * Dashboard Summary Module - Main dashboard component displaying key metrics and summaries.
 * This is the central dashboard interface for viewing usage metrics and system statistics.
 */
export default function DashboardSummaryModule() {
  const queryClient = useQueryClient();
  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>([
    new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
    new Date(), // today
  ]);
  const [selectedMetricType, setSelectedMetricType] = useState<string | null>(null);

  const { data: dashboardData, isLoading, error, refetch } = useQuery({
    queryKey: ['dashboard-summary', dateRange[0]?.toISOString(), dateRange[1]?.toISOString()],
    queryFn: async (): Promise<DashboardStats> => {
      const params = new URLSearchParams();
      if (dateRange[0]) params.append('start_date', dateRange[0].toISOString());
      if (dateRange[1]) params.append('end_date', dateRange[1].toISOString());
      
      const response = await api.get(`/api/common/metrics/summary/?${params}`);
      return response.data;
    },
    refetchInterval: 300000, // Refetch every 5 minutes
  });

  const metricTypeOptions = useMemo(() => {
    if (!dashboardData?.events_by_type) return [];
    return dashboardData.events_by_type.map(type => ({
      value: type.metric_type,
      label: type.metric_type.replace('_', ' ').toUpperCase(),
    }));
  }, [dashboardData]);

  const handleExportMetrics = async () => {
    try {
      const params = new URLSearchParams();
      if (dateRange[0]) params.append('start_date', dateRange[0].toISOString());
      if (dateRange[1]) params.append('end_date', dateRange[1].toISOString());
      if (selectedMetricType) params.append('metric_type', selectedMetricType);
      
      // Request export (this would typically create a background task)
      await api.post('/api/common/metrics/export/', {
        start_date: dateRange[0]?.toISOString(),
        end_date: dateRange[1]?.toISOString(),
        export_format: 'csv',
        filter_params: {
          metric_type: selectedMetricType,
        },
      });
      
      notifications.show({
        title: 'Export Started',
        message: 'Metrics export has been initiated. You will be notified when complete.',
        color: 'blue',
      });
    } catch (error) {
      notifications.show({
        title: 'Export Failed',
        message: 'Failed to start metrics export. Please try again.',
        color: 'red',
      });
    }
  };

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
    queryClient.invalidateQueries({ queryKey: ['metrics-summary'] });
    refetch();
  };

  if (isLoading) {
    return (
      <Card withBorder padding="xl" radius="md">
        <Group justify="center" py="xl">
          <Loader size="lg" />
          <Text>Loading dashboard...</Text>
        </Group>
      </Card>
    );
  }

  if (error) {
    return (
      <Card withBorder padding="xl" radius="md">
        <Group justify="center" py="xl">
          <Text c="red">Failed to load dashboard data</Text>
          <Button variant="light" onClick={handleRefresh}>
            Retry
          </Button>
        </Group>
      </Card>
    );
  }

  const totalEvents = dashboardData?.total_events || 0;
  const uniqueUsers = dashboardData?.unique_users || 0;
  const avgEventsPerUser = uniqueUsers > 0 ? Math.round(totalEvents / uniqueUsers) : 0;

  return (
    <Box>
      {/* Header */}
      <Group justify="space-between" mb="md">
        <Group>
          <ThemeIcon size="lg" variant="light">
            <IconDashboard size={20} />
          </ThemeIcon>
          <Box>
            <Text size="xl" fw={700}>Dashboard Summary</Text>
            <Text size="sm" c="dimmed">
              System usage metrics and analytics
            </Text>
          </Box>
        </Group>
        
        <Group>
          <Tooltip label="Refresh data">
            <ActionIcon variant="light" onClick={handleRefresh}>
              <IconRefresh size={16} />
            </ActionIcon>
          </Tooltip>
          
          <Button
            leftSection={<IconDownload size={16} />}
            variant="light"
            onClick={handleExportMetrics}
          >
            Export
          </Button>
        </Group>
      </Group>

      {/* Controls */}
      <Card withBorder padding="md" mb="md">
        <Group>
          <DatePickerInput
            type="range"
            label="Date Range"
            placeholder="Select date range"
            value={dateRange}
            onChange={setDateRange}
            leftSection={<IconCalendar size={16} />}
            style={{ flex: 1 }}
          />
          
          <Select
            label="Filter by Type"
            placeholder="All event types"
            data={metricTypeOptions}
            value={selectedMetricType}
            onChange={setSelectedMetricType}
            clearable
            style={{ minWidth: 200 }}
          />
        </Group>
      </Card>

      {/* Key Metrics Cards */}
      <Grid mb="md">
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card withBorder padding="md">
            <Group>
              <ThemeIcon color="blue" variant="light" size="lg">
                <IconActivity size={20} />
              </ThemeIcon>
              <Box>
                <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                  Total Events
                </Text>
                <Text size="xl" fw={700}>{totalEvents.toLocaleString()}</Text>
              </Box>
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card withBorder padding="md">
            <Group>
              <ThemeIcon color="green" variant="light" size="lg">
                <IconUsers size={20} />
              </ThemeIcon>
              <Box>
                <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                  Active Users
                </Text>
                <Text size="xl" fw={700}>{uniqueUsers.toLocaleString()}</Text>
              </Box>
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card withBorder padding="md">
            <Group>
              <ThemeIcon color="orange" variant="light" size="lg">
                <IconTrendingUp size={20} />
              </ThemeIcon>
              <Box>
                <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                  Avg Events/User
                </Text>
                <Text size="xl" fw={700}>{avgEventsPerUser}</Text>
              </Box>
            </Group>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card withBorder padding="md">
            <Group>
              <ThemeIcon color="purple" variant="light" size="lg">
                <IconChartBar size={20} />
              </ThemeIcon>
              <Box>
                <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                  Event Types
                </Text>
                <Text size="xl" fw={700}>
                  {dashboardData?.events_by_type?.length || 0}
                </Text>
              </Box>
            </Group>
          </Card>
        </Grid.Col>
      </Grid>

      {/* Main Content */}
      <Tabs defaultValue="overview">
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconDashboard size={16} />}>
            Overview
          </Tabs.Tab>
          <Tabs.Tab value="events" leftSection={<IconActivity size={16} />}>
            Events
          </Tabs.Tab>
          <Tabs.Tab value="users" leftSection={<IconUsers size={16} />}>
            Users
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="overview" pt="md">
          <Grid>
            <Grid.Col span={{ base: 12, md: 8 }}>
              <MetricsWidget
                title="Usage Overview"
                startDate={dateRange[0]?.toISOString()}
                endDate={dateRange[1]?.toISOString()}
              />
            </Grid.Col>
            
            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card withBorder padding="md">
                <Text fw={500} mb="md">Event Type Distribution</Text>
                <ScrollArea h={300}>
                  <Stack gap="xs">
                    {dashboardData?.events_by_type?.map((eventType) => {
                      const percentage = totalEvents > 0 
                        ? Math.round((eventType.count / totalEvents) * 100) 
                        : 0;
                      
                      return (
                        <Box key={eventType.metric_type}>
                          <Group justify="space-between" mb="xs">
                            <Text size="sm">
                              {eventType.metric_type.replace('_', ' ')}
                            </Text>
                            <Badge size="sm">{eventType.count}</Badge>
                          </Group>
                          <Progress 
                            value={percentage} 
                            size="sm" 
                            mb="sm"
                            color="blue"
                          />
                        </Box>
                      );
                    })}
                  </Stack>
                </ScrollArea>
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        <Tabs.Panel value="events" pt="md">
          <Card withBorder padding="md">
            <Text fw={500} mb="md">Top Events</Text>
            <ScrollArea>
              <Stack gap="sm">
                {dashboardData?.top_events?.map((event, index) => (
                  <Group key={event.event_name} justify="space-between" p="sm">
                    <Group>
                      <Text fw={500}>{index + 1}.</Text>
                      <Text>{event.event_name}</Text>
                    </Group>
                    <Badge variant="light">{event.count} events</Badge>
                  </Group>
                ))}
              </Stack>
            </ScrollArea>
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="users" pt="md">
          <Card withBorder padding="md">
            <Group justify="space-between" mb="md">
              <Text fw={500}>User Activity</Text>
              <Text size="sm" c="dimmed">
                {uniqueUsers} active users in selected period
              </Text>
            </Group>
            
            <Box p="xl" style={{ textAlign: 'center' }}>
              <Text c="dimmed">
                Detailed user analytics will be available here
              </Text>
            </Box>
          </Card>
        </Tabs.Panel>
      </Tabs>
    </Box>
  );
}