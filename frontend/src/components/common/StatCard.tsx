interface StatCardProps {
  title: string;
  value: number | string;
  icon: string;
  trend?: string;
  trendUp?: boolean;
  variant?: 'default' | 'critical';
}

function StatCard({
  title,
  value,
  icon,
  trend,
  trendUp,
  variant = 'default',
}: StatCardProps) {
  return (
    <div
      className={`card p-6 ${
        variant === 'critical' ? 'border-l-4 border-l-red-500' : ''
      }`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
            {title}
          </p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            {value}
          </p>
          {trend && (
            <p
              className={`text-sm mt-2 ${
                trendUp
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-red-600 dark:text-red-400'
              }`}
            >
              {trend}
            </p>
          )}
        </div>
        <div className="text-4xl">{icon}</div>
      </div>
    </div>
  );
}

export default StatCard;
