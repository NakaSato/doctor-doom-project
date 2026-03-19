import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface ComparisonChartProps {
  inspectionIds: string[];
  metric: 'power_output' | 'defect_count' | 'temperature';
}

function ComparisonChart({ inspectionIds, metric }: ComparisonChartProps) {
  // Mock data - in real implementation, fetch from API
  const data = inspectionIds.map((id) => ({
    inspection: id.slice(0, 8),
    value: Math.random() * 100,
  }));

  const getMetricLabel = () => {
    switch (metric) {
      case 'power_output':
        return 'Power Output (W)';
      case 'defect_count':
        return 'Number of Defects';
      case 'temperature':
        return 'Avg Temperature (°C)';
    }
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis dataKey="inspection" stroke="#9CA3AF" />
        <YAxis stroke="#9CA3AF" />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1F2937',
            border: '1px solid #374151',
            borderRadius: '8px',
          }}
        />
        <Legend />
        <Bar dataKey="value" fill="#F59E0B" name={getMetricLabel()} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export default ComparisonChart;
