import { useParams } from 'react-router-dom';
import { useModule, useModuleTelemetry, useModuleDefects } from '@/hooks/useQueries';
import ThermalViewer from '@/components/thermal/ThermalViewer';
import ModuleTelemetryChart from '@/components/charts/ModuleTelemetryChart';
import DefectList from '@/components/defects/DefectList';

function ModuleInspector() {
  const { moduleId } = useParams<{ moduleId: string }>();

  const { data: module } = useModule(moduleId!);
  const { data: telemetry } = useModuleTelemetry(moduleId!, 30);
  const { data: defects } = useModuleDefects(moduleId!);

  if (!module) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-500">Module not found</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Module Inspector
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          {module.id} - Side-by-side thermal + RGB with annotations
        </p>
      </div>

      {/* Module info */}
      <div className="card p-4 mb-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500">Rated Power</p>
            <p className="text-lg font-semibold">{module.rated_power_w}W</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Orientation</p>
            <p className="text-lg font-semibold">{module.orientation}°</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Tilt</p>
            <p className="text-lg font-semibold">{module.tilt}°</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Status</p>
            <p className="text-lg font-semibold capitalize">{module.status}</p>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 min-h-0">
        {/* Thermal viewer */}
        <div className="card overflow-hidden flex flex-col">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold">Thermal Image</h3>
          </div>
          <div className="flex-1 bg-black">
            <ThermalViewer moduleId={moduleId!} />
          </div>
        </div>

        {/* Telemetry chart */}
        <div className="card overflow-hidden flex flex-col">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold">Performance Telemetry</h3>
          </div>
          <div className="flex-1 p-4">
            <ModuleTelemetryChart data={telemetry || []} />
          </div>
        </div>
      </div>

      {/* Defects section */}
      <div className="card p-4 mt-4">
        <h3 className="font-semibold mb-4">Detected Defects</h3>
        <DefectList defects={defects || []} />
      </div>
    </div>
  );
}

export default ModuleInspector;
