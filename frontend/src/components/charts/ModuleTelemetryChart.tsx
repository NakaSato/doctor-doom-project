import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { TelemetryPoint } from '@/types';
import { format } from 'date-fns';

interface ModuleTelemetryChartProps {
  data: TelemetryPoint[];
}

function ModuleTelemetryChart({ data }: ModuleTelemetryChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-500">No telemetry data available</p>
      </div>
    );
  }

  const chartData = data.map((point) => ({
    ...point,
    formattedTime: format(new Date(point.timestamp), 'MMM dd'),
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis
          dataKey="formattedTime"
          stroke="#9CA3AF"
          tick={{ fontSize: 12 }}
        />
        <YAxis yAxisId="left" stroke="#9CA3AF" tick={{ fontSize: 12 }} />
        <YAxis
          yAxisId="right"
          orientation="right"
          stroke="#9CA3AF"
          tick={{ fontSize: 12 }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1F2937',
            border: '1px solid #374151',
            borderRadius: '8px',
          }}
          labelStyle={{ color: '#F3F4F6' }}
        />
        <Legend />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="temperature"
          stroke="#EF4444"
          strokeWidth={2}
          dot={false}
          name="Temperature (°C)"
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="power_output_w"
          stroke="#F59E0B"
          strokeWidth={2}
          dot={false}
          name="Power (W)"
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="efficiency"
          stroke="#22C55E"
          strokeWidth={2}
          dot={false}
          name="Efficiency"
          tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export default ModuleTelemetryChart;
