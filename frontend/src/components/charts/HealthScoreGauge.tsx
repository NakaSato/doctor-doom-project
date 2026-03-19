import { ResponsiveContainer, RadialBarChart, RadialBar, PolarGrid, PolarAngleAxis } from 'recharts';

interface HealthScoreGaugeProps {
  score: number;
}

function HealthScoreGauge({ score }: HealthScoreGaugeProps) {
  const data = [
    { name: 'Score', value: score, fill: score >= 80 ? '#22c55e' : score >= 60 ? '#f59e0b' : '#ef4444' },
  ];

  return (
    <div className="flex flex-col items-center">
      <div className="w-48 h-48">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            innerRadius="80%"
            outerRadius="100%"
            barSize={40}
            data={data}
            startAngle={90}
            endAngle={-270}
          >
            <PolarGrid gridType="circle" />
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
            <RadialBar
              background
              dataKey="value"
              cornerRadius={20}
            />
          </RadialBarChart>
        </ResponsiveContainer>
      </div>
      <div className="text-center -mt-32">
        <p className="text-4xl font-bold">{score.toFixed(0)}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400">out of 100</p>
      </div>
      <div className="mt-4 text-center">
        <p
          className={`text-sm font-medium ${
            score >= 80
              ? 'text-green-500'
              : score >= 60
              ? 'text-yellow-500'
              : 'text-red-500'
          }`}
        >
          {score >= 80 ? 'Excellent' : score >= 60 ? 'Good' : 'Needs Attention'}
        </p>
      </div>
    </div>
  );
}

export default HealthScoreGauge;
