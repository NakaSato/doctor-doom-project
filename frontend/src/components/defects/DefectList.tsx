import type { Defect } from '@/types';
import { formatDistanceToNow } from 'date-fns';

interface DefectListProps {
  defects: Defect[];
}

function DefectList({ defects }: DefectListProps) {
  if (defects.length === 0) {
    return (
      <p className="text-gray-500 dark:text-gray-400 text-sm">
        No defects detected for this module
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {defects.map((defect) => (
        <div
          key={defect.id}
          className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
        >
          <div className="flex items-center space-x-3">
            <span
              className={`w-3 h-3 rounded-full ${
                defect.severity === 'critical'
                  ? 'bg-red-500'
                  : defect.severity === 'high'
                  ? 'bg-orange-500'
                  : defect.severity === 'medium'
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
              }`}
            />
            <div>
              <p className="font-medium text-gray-900 dark:text-white capitalize">
                {defect.defect_type}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                ΔT: +{defect.temperature_delta.toFixed(1)}°C •{' '}
                {(defect.confidence * 100).toFixed(0)}% confidence
              </p>
            </div>
          </div>
          <div className="text-right">
            <span className={`badge-${defect.severity}`}>
              {defect.severity}
            </span>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {formatDistanceToNow(new Date(defect.detected_at), {
                addSuffix: true,
              })}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default DefectList;
