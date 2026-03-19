import type { Alert } from '@/types';
import { formatDistanceToNow } from 'date-fns';

interface RecentAlertsProps {
  alerts: Alert[];
}

function RecentAlerts({ alerts }: RecentAlertsProps) {
  if (alerts.length === 0) {
    return (
      <p className="text-gray-500 dark:text-gray-400 text-sm">
        No recent alerts
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
        >
          <span
            className={`text-lg ${
              alert.severity === 'critical'
                ? 'text-red-500'
                : alert.severity === 'high'
                ? 'text-orange-500'
                : alert.severity === 'medium'
                ? 'text-yellow-500'
                : 'text-green-500'
            }`}
          >
            {alert.severity === 'critical'
              ? '🚨'
              : alert.severity === 'high'
              ? '⚠️'
              : 'ℹ️'}
          </span>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
              {alert.title}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
              {alert.message}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
              {formatDistanceToNow(new Date(alert.created_at), {
                addSuffix: true,
              })}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default RecentAlerts;
