import { useRef, useEffect, useState } from 'react';
import Map from 'mapbox-gl';
import { DeckGL } from '@deck.gl/react';
import { ScatterplotLayer } from '@deck.gl/layers';
import { useSites, useDefects } from '@/hooks/useQueries';
import { useSelectionStore } from '@/stores/selectionStore';
import type { Site, Defect } from '@/types';

// Mapbox token - replace with your own
const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || '';

function ArrayMap() {
  const [viewState, setViewState] = useState({
    longitude: 100.5,
    latitude: 13.7,
    zoom: 10,
  });

  const { data: sites = [] } = useSites();
  const { data: defects = [] } = useDefects();
  const { setSelectedSite, setSelectedDefect } = useSelectionStore();

  const mapRef = useRef<Map | null>(null);

  // Site layers
  const siteLayer = new ScatterplotLayer({
    id: 'sites',
    data: sites.map((site) => ({
      position: site.location.coordinates[0] as [number, number],
      radius: 200,
      name: site.name,
      moduleCount: site.module_count,
    })),
    getPosition: (d: unknown) => (d as { position: [number, number] }).position,
    getRadius: (d: unknown) => (d as { radius: number }).radius,
    getFillColor: [245, 158, 11, 200],
    pickable: true,
    onClick: (info: { object: { name: string } }) => {
      const site = sites.find((s) => s.name === info.object.name);
      if (site) setSelectedSite(site);
    },
  });

  // Defect heatmap layer
  const defectLayer = new HeatmapLayer({
    id: 'defects',
    data: defects
      .filter((d) => d.location)
      .map((d) => ({
        position: d.location!.coordinates[0] as [number, number],
        weight: d.severity === 'critical' ? 5 : d.severity === 'high' ? 3 : 1,
      })),
    getPosition: (d: unknown) => (d as { position: [number, number] }).position,
    getWeight: (d: unknown) => (d as { weight: number }).weight,
    radiusPixels: 50,
    colorRange: [
      [1, 152, 189],
      [73, 227, 206],
      [216, 254, 181],
      [254, 237, 177],
      [254, 173, 154],
      [209, 55, 78],
    ],
    pickable: true,
    onClick: (info: { object: { position: [number, number] } }) => {
      // Find nearest defect
      const nearestDefect = defects.find(
        (d) =>
          d.location &&
          Math.abs(d.location.coordinates[0][0] - info.object.position[0]) <
            0.001
      );
      if (nearestDefect) setSelectedDefect(nearestDefect);
    },
  });

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Array Map
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Interactive thermal heatmap with module-level drill-down
        </p>
      </div>

      {/* Map container */}
      <div className="flex-1 card overflow-hidden relative">
        {!MAPBOX_TOKEN && (
          <div className="absolute top-4 left-4 z-10 card p-4 bg-yellow-100 dark:bg-yellow-900/30">
            <p className="text-sm text-yellow-800 dark:text-yellow-400">
              ⚠️ Mapbox token not configured. Set VITE_MAPBOX_TOKEN in .env
            </p>
          </div>
        )}

        <DeckGL
          initialViewState={viewState}
          controller={true}
          layers={[siteLayer, defectLayer]}
          onViewStateChange={({ viewState }) => setViewState(viewState)}
        >
          {MAPBOX_TOKEN && (
            <Map
              mapboxAccessToken={MAPBOX_TOKEN}
              mapStyle="mapbox://styles/mapbox/satellite-v9"
            />
          )}
        </DeckGL>

        {/* Legend */}
        <div className="absolute bottom-4 right-4 card p-4 bg-white/90 dark:bg-gray-800/90">
          <h4 className="text-sm font-medium mb-2">Defect Severity</h4>
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-green-500 rounded" />
              <span className="text-xs">Low</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-yellow-500 rounded" />
              <span className="text-xs">Medium</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-orange-500 rounded" />
              <span className="text-xs">High</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-red-500 rounded" />
              <span className="text-xs">Critical</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ArrayMap;
