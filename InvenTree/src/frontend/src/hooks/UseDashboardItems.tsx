import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { identifierString } from '@lib/functions/Conversion';
import { api } from '../App';
import type { DashboardWidgetProps } from '../components/dashboard/DashboardWidget';
import DashboardWidgetLibrary from '../components/dashboard/DashboardWidgetLibrary';
import { useInvenTreeContext } from '../components/plugins/PluginContext';
import {
  type PluginUIFeature,
  PluginUIFeatureType
} from '../components/plugins/PluginUIFeature';
import RemoteComponent from '../components/plugins/RemoteComponent';
import { useGlobalSettingsState } from '../states/SettingsStates';
import { useUserState } from '../states/UserState';

interface DashboardLibraryProps {
  items: DashboardWidgetProps[];
  loaded: boolean;
  error: any;
}

/**
 * Custom hook to load available dashboard items.
 *
 * - Loads from library of "builtin" dashboard items
 * - Loads plugin-defined dashboard items (via the API)
 */
export function useDashboardItems(): DashboardLibraryProps {
  const user = useUserState();
  const globalSettings = useGlobalSettingsState();

  const pluginsEnabled: boolean = useMemo(
    () => globalSettings.isSet('ENABLE_PLUGINS_INTERFACE'),
    [globalSettings]
  );

  const builtin = DashboardWidgetLibrary();

  const pluginQuery = useQuery({
    enabled: pluginsEnabled,
    queryKey: ['plugin-dashboard-items', user],
    refetchOnMount: true,
    queryFn: async () => {
      if (!pluginsEnabled) {
        return Promise.resolve([]);
      }

      const url = apiUrl(ApiEndpoints.plugin_ui_features_list, undefined, {
        feature_type: PluginUIFeatureType.dashboard
      });

      return api.get(url).then((response: any) => response.data);
    }
  });

  // Cache the context data which is delivered to the plugins
  const inventreeContext = useInvenTreeContext();

  const pluginDashboardItems: DashboardWidgetProps[] = useMemo(() => {
    return (
      pluginQuery?.data?.map((item: PluginUIFeature) => {
        const pluginContext = {
          ...inventreeContext,
          context: item.context
        };

        return {
          label: identifierString(`p-${item.plugin_name}-${item.key}`),
          title: item.title,
          description: item.description,
          minWidth: item.options?.width ?? 2,
          minHeight: item.options?.height ?? 1,
          render: () => {
            return (
              <RemoteComponent
                source={item.source}
                defaultFunctionName='renderDashboardItem'
                context={pluginContext}
              />
            );
          }
        };
      }) ?? []
    );
  }, [pluginQuery.data, inventreeContext]);

  // [AGENT GENERATED CODE - REQUIREMENT: REQ-001, REQ-003] 
  const metricsItems: DashboardWidgetProps[] = useMemo(() => {
    return [
      {
        label: 'metrics-summary',
        title: 'Usage Metrics Summary',
        description: 'Summary of system usage metrics and analytics',
        widgetType: 'summary',
        enabled: true,
        minWidth: 4,
        minHeight: 2,
        render: () => {
          // Dynamic import to avoid circular dependencies
          return import('../components/dashboard/DashboardSummaryModule').then(
            (module) => module.default()
          );
        }
      },
      {
        label: 'metrics-widget-compact',
        title: 'Usage Metrics (Compact)',
        description: 'Compact view of recent usage metrics',
        widgetType: 'metrics',
        enabled: true,
        minWidth: 2,
        minHeight: 1,
        metricsConfig: {
          refreshInterval: 300000, // 5 minutes
          dateRange: 7 // last 7 days
        },
        render: () => {
          return import('../components/metrics/MetricsWidget').then(
            (module) => module.default({ 
              compact: true,
              title: 'Recent Activity'
            })
          );
        }
      },
      {
        label: 'metrics-widget-detailed',
        title: 'Usage Metrics (Detailed)',
        description: 'Detailed view of usage metrics with breakdowns',
        widgetType: 'metrics',
        enabled: true,
        minWidth: 3,
        minHeight: 2,
        metricsConfig: {
          refreshInterval: 300000, // 5 minutes
          dateRange: 30 // last 30 days
        },
        render: () => {
          return import('../components/metrics/MetricsWidget').then(
            (module) => module.default({ 
              compact: false,
              title: 'Usage Analytics'
            })
          );
        }
      }
    ];
  }, []);

  const items: DashboardWidgetProps[] = useMemo(() => {
    const widgets = [...builtin, ...pluginDashboardItems, ...metricsItems];

    return widgets.filter((item) => item.enabled ?? true);
  }, [builtin, pluginDashboardItems, metricsItems]);

  const loaded: boolean = useMemo(() => {
    if (pluginsEnabled) {
      return (
        !pluginQuery.isFetching &&
        !pluginQuery.isLoading &&
        pluginQuery.isFetched &&
        pluginQuery.isSuccess
      );
    } else {
      return true;
    }
  }, [pluginsEnabled, pluginQuery]);

  return {
    items: items,
    loaded: loaded,
    error: pluginQuery.error
  };
}
