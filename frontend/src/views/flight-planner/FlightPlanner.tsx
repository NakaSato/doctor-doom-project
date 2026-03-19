import { useRef, useState } from 'react';
import Map from 'mapbox-gl';
import MapboxDraw from '@mapbox/mapbox-gl-draw';
import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css';
import { useSites } from '@/hooks/useQueries';
import { useUIStore } from '@/stores/uiStore';

// Mapbox token - replace with your own
const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || '';

function FlightPlanner() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);
  const drawRef = useRef<MapboxDraw | null>(null);

  const { data: sites = [] } = useSites();
  const { addToast } = useUIStore();

  const [flightParams, setFlightParams] = useState({
    altitude: 50,
    speed: 5,
    overlap: 80,
    sidelap: 60,
  });

  const [waypoints, setWaypoints] = useState<Array<{ lat: number; lng: number }>>([]);

  const initMap = () => {
    if (!mapContainerRef.current || !MAPBOX_TOKEN) return;

    mapRef.current = new Map({
      container: mapContainerRef.current,
      style: 'mapbox://styles/mapbox/satellite-v9',
      center: [100.5, 13.7],
      zoom: 12,
      accessToken: MAPBOX_TOKEN,
    });

    drawRef.current = new MapboxDraw({
      displayControlsDefault: false,
      controls: {
        polygon: true,
        trash: true,
      },
    });

    mapRef.current.addControl(drawRef.current);
  };

  const generateWaypoints = () => {
    if (!drawRef.current) return;

    const data = drawRef.current.getAll();
    if (data.features.length === 0) {
      addToast({
        type: 'warning',
        title: 'No area selected',
        message: 'Draw a polygon on the map first',
      });
      return;
    }

    // Generate waypoints based on survey area
    const newWaypoints = [];
    const bounds = data.features[0].bbox;
    if (bounds) {
      const [minLng, minLat, maxLng, maxLat] = bounds;
      const step = 0.001; // Approx 100m

      for (let lat = minLat; lat <= maxLat; lat += step) {
        const lng = lat % (step * 2) === 0 ? minLng : maxLng;
        newWaypoints.push({ lat, lng });
      }
    }

    setWaypoints(newWaypoints);
    addToast({
      type: 'success',
      title: 'Waypoints generated',
      message: `${newWaypoints.length} waypoints created`,
    });
  };

  const exportMission = () => {
    const mission = {
      waypoints,
      ...flightParams,
      created_at: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(mission, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mission_${new Date().getTime()}.json`;
    a.click();
    URL.revokeObjectURL(url);

    addToast({
      type: 'success',
      title: 'Mission exported',
      message: 'Flight plan downloaded',
    });
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Flight Planner
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Define survey area on map, auto-generate waypoint mission
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 flex-1 min-h-0">
        {/* Map */}
        <div className="card lg:col-span-3 overflow-hidden relative">
          {!MAPBOX_TOKEN && (
            <div className="absolute top-4 left-4 z-10 card p-4 bg-yellow-100 dark:bg-yellow-900/30">
              <p className="text-sm text-yellow-800 dark:text-yellow-400">
                ⚠️ Mapbox token not configured. Set VITE_MAPBOX_TOKEN in .env
              </p>
            </div>
          )}
          <div
            ref={mapContainerRef}
            className="w-full h-full"
            onLoad={initMap}
          />
        </div>

        {/* Flight parameters */}
        <div className="card p-4 space-y-4">
          <h3 className="font-semibold">Flight Parameters</h3>

          <div>
            <label className="block text-sm font-medium mb-1">
              Altitude (m)
            </label>
            <input
              type="number"
              value={flightParams.altitude}
              onChange={(e) =>
                setFlightParams({ ...flightParams, altitude: Number(e.target.value) })
              }
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Speed (m/s)
            </label>
            <input
              type="number"
              value={flightParams.speed}
              onChange={(e) =>
                setFlightParams({ ...flightParams, speed: Number(e.target.value) })
              }
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Overlap (%)
            </label>
            <input
              type="number"
              value={flightParams.overlap}
              onChange={(e) =>
                setFlightParams({ ...flightParams, overlap: Number(e.target.value) })
              }
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Sidelap (%)
            </label>
            <input
              type="number"
              value={flightParams.sidelap}
              onChange={(e) =>
                setFlightParams({ ...flightParams, sidelap: Number(e.target.value) })
              }
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
            />
          </div>

          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={initMap}
              className="w-full btn-outline mb-2"
            >
              Initialize Map
            </button>
            <button
              onClick={generateWaypoints}
              className="w-full btn-primary mb-2"
            >
              Generate Waypoints
            </button>
            <button
              onClick={exportMission}
              className="w-full btn-secondary"
              disabled={waypoints.length === 0}
            >
              Export Mission
            </button>
          </div>

          {/* Waypoint count */}
          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Waypoints: {waypoints.length}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Est. flight time: {Math.round(waypoints.length * 0.5)} min
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default FlightPlanner;
