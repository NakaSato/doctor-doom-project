import { useState } from 'react';
import { useInspections } from '@/hooks/useQueries';
import { useSelectionStore } from '@/stores/selectionStore';
import ComparisonChart from '@/components/charts/ComparisonChart';
import { format } from 'date-fns';

function ComparisonView() {
  const { data: inspections = [] } = useInspections();
  const { comparisonItems, addToComparison, removeFromComparison, comparisonMode } =
    useSelectionStore();

  const [selectedInspections, setSelectedInspections] = useState<string[]>([]);

  const handleToggleInspection = (inspectionId: string) => {
    if (selectedInspections.includes(inspectionId)) {
      setSelectedInspections(selectedInspections.filter((id) => id !== inspectionId));
    } else if (selectedInspections.length < 3) {
      setSelectedInspections([...selectedInspections, inspectionId]);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Comparison View
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Before/after overlays across inspection dates for degradation tracking
        </p>
      </div>

      {/* Inspection selector */}
      <div className="card p-4 mb-4">
        <h3 className="font-semibold mb-3">Select Inspections to Compare</h3>
        <div className="flex flex-wrap gap-2">
          {inspections.map((inspection) => (
            <button
              key={inspection.id}
              onClick={() => handleToggleInspection(inspection.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedInspections.includes(inspection.id)
                  ? 'bg-primary-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              {format(new Date(inspection.started_at), 'MMM dd, yyyy')}
              {selectedInspections.includes(inspection.id) && (
                <span className="ml-2">×</span>
              )}
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
          Select up to 3 inspections to compare
        </p>
      </div>

      {/* Comparison content */}
      {selectedInspections.length >= 2 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 min-h-0">
          {/* Performance comparison */}
          <div className="card p-4">
            <h3 className="font-semibold mb-4">Performance Comparison</h3>
            <ComparisonChart
              inspectionIds={selectedInspections}
              metric="power_output"
            />
          </div>

          {/* Defect count comparison */}
          <div className="card p-4">
            <h3 className="font-semibold mb-4">Defect Count Comparison</h3>
            <ComparisonChart
              inspectionIds={selectedInspections}
              metric="defect_count"
            />
          </div>

          {/* Thermal comparison */}
          <div className="card p-4 lg:col-span-2">
            <h3 className="font-semibold mb-4">Average Temperature by String</h3>
            <ComparisonChart
              inspectionIds={selectedInspections}
              metric="temperature"
            />
          </div>
        </div>
      ) : (
        <div className="card p-8 flex-1 flex items-center justify-center">
          <div className="text-center">
            <span className="text-6xl">📊</span>
            <p className="text-gray-500 dark:text-gray-400 mt-4">
              Select at least 2 inspections to compare
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default ComparisonView;
