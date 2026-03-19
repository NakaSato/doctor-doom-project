import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, ComposedChart } from 'recharts';
import { format } from 'date-fns';

interface DefectTrendChartProps {
  data?: Array<{ date: string; count: number }>;
}

function DefectTrendChart({ data }: DefectTrendChartProps) {
  // Mock data if not provided
  const chartData =
    data ||
    Array.from({ length: 30 }, (_, i) => ({
      date: format(new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000), 'MMM dd'),
      count: Math.floor(Math.random() * 10),
      critical: Math.floor(Math.random() * 3),
    }));

  return (
    <ResponsiveContainer width="100%" height={250}>
      <ComposedChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis
          dataKey="date"
          stroke="#9CA3AF"
          tick={{ fontSize: 10 }}
          interval={5}
        />
        <YAxis stroke="#9CA3AF" tick={{ fontSize: 12 }} />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1F2937',
            border: '1px solid #374151',
            borderRadius: '8px',
          }}
          labelStyle={{ color: '#F3F4F6' }}
        />
        <Area
          type="monotone"
          dataKey="critical"
          fill="#EF4444"
          fillOpacity={0.3}
          stroke="#EF4444"
          name="Critical"
        />
        <Line
          type="monotone"
          dataKey="count"
          stroke="#F59E0B"
          strokeWidth={2}
          dot={false}
          name="Total Defects"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export default DefectTrendChart;
