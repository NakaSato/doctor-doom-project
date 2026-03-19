import { useDashboardStats } from '@/hooks/useQueries';
import StatCard from '@/components/common/StatCard';
import RecentAlerts from '@/components/common/RecentAlerts';
import HealthScoreGauge from '@/components/charts/HealthScoreGauge';
import DefectTrendChart from '@/components/charts/DefectTrendChart';

function Dashboard() {
  const { data: stats, isLoading, error } = useDashboardStats();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin text-4xl">⏳</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card p-8 text-center">
        <p className="text-red-500">Error loading dashboard data</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Overview of your solar panel fleet
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Sites"
          value={stats?.total_sites || 0}
          icon="📍"
          trend="+2 this month"
          trendUp={true}
        />
        <StatCard
          title="Total Modules"
          value={stats?.total_modules || 0}
          icon="☀️"
          trend="+120 this month"
          trendUp={true}
        />
        <StatCard
          title="Total Defects"
          value={stats?.total_defects || 0}
          icon="⚠️"
          trend="-5 from last week"
          trendUp={true}
        />
        <StatCard
          title="Critical Issues"
          value={stats?.critical_defects || 0}
          icon="🚨"
          trend="Requires attention"
          trendUp={false}
          variant="critical"
        />
      </div>

      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Health score */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Fleet Health Score
          </h3>
          <HealthScoreGauge
            score={stats?.average_health_score || 0}
          />
        </div>

        {/* Defect trend */}
        <div className="card p-6 lg:col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Defect Trend (Last 30 Days)
          </h3>
          <DefectTrendChart />
        </div>
      </div>

      {/* Recent alerts and inspections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent alerts */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Recent Alerts
          </h3>
          <RecentAlerts alerts={stats?.recent_alerts || []} />
        </div>

        {/* Recent inspections */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Recent Inspections
          </h3>
          <div className="space-y-3">
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              No recent inspections
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
