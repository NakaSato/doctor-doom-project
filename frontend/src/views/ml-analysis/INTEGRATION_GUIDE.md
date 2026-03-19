# Frontend ↔ Backend Integration Guide

## Overview

This guide shows how to use the ML Inference integration in the React frontend.

## Quick Start

### 1. Start Backend Services

```bash
# From project root
docker compose up -d ml-inference api-gateway

# Check health
curl http://localhost:8001/health
```

### 2. Configure Frontend

Create `frontend/.env`:

```bash
VITE_API_URL=http://localhost:8000/api/v1
VITE_ML_SERVICE_URL=http://localhost:8001
```

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Open ML Analysis Dashboard

Navigate to: `http://localhost:3000/ml-analysis`

---

## Components

### ThermalViewer

Display thermal images with adjustable colormap.

```tsx
import ThermalViewer from '@/components/thermal/ThermalViewer';

function MyComponent() {
  const thermalData = new Float32Array(640 * 512); // Your temperature data
  
  return (
    <ThermalViewer
      thermalData={thermalData}
      width={640}
      height={512}
      colormap="ironbow"
      showScale
      showCrosshair
      onCrosshairMove={({ x, y, temp }) => {
        console.log(`Position: ${x},${y}, Temp: ${temp.toFixed(1)}°C`);
      }}
    />
  );
}
```

**Props:**
- `thermalData`: Float32Array or number[][] of temperature values
- `width`, `height`: Image dimensions
- `colormap`: 'ironbow' | 'grayscale' | 'rainbow' | 'thermal'
- `tempRange`: Optional { min, max } (auto-calculated if not provided)
- `showScale`: Show temperature scale bar
- `showCrosshair`: Show interactive crosshair
- `onCrosshairMove`: Callback when crosshair moves

---

### DefectOverlay

Display defect markers on thermal images.

```tsx
import DefectOverlay, { type DefectMarker } from '@/components/defects/DefectOverlay';

const defects: DefectMarker[] = [
  {
    id: 1,
    type: 'hotspot',
    severity: 'critical',
    confidence: 0.95,
    bbox: { x: 300, y: 200, width: 100, height: 80 },
    temperature_delta: 28.5,
  },
];

function MyComponent() {
  return (
    <div className="relative">
      <ThermalViewer thermalData={data} width={640} height={512} />
      <DefectOverlay
        width={640}
        height={512}
        defects={defects}
        onDefectClick={(id) => console.log('Clicked defect:', id)}
      />
    </div>
  );
}
```

**Props:**
- `width`, `height`: Image dimensions
- `defects`: Array of DefectMarker
- `selectedDefectId`: Currently selected defect
- `onDefectClick`: Callback when defect is clicked
- `showLabels`: Show defect labels
- `showConfidence`: Show confidence scores

---

## Hooks

### useAnalyzeModule

Submit thermal image for analysis.

```tsx
import { useAnalyzeModule } from '@/hooks/useML';

function AnalysisButton() {
  const analyze = useAnalyzeModule();
  
  const handleAnalyze = () => {
    analyze.mutate({
      module_id: 'mod_001',
      inspection_id: 'insp_001',
      image_id: 'img_001',
      thermal_data: base64ImageData,
      metadata: {
        ambient_temp: 35.0,
        irradiance: 850,
      },
    }, {
      onSuccess: (result) => {
        console.log('Defect:', result.defect_type);
        console.log('Severity:', result.severity);
        console.log('Confidence:', result.confidence);
      },
    });
  };
  
  return (
    <Button onClick={handleAnalyze} disabled={analyze.isPending}>
      {analyze.isPending ? 'Analyzing...' : 'Analyze'}
    </Button>
  );
}
```

---

### usePipelineInfo

Get ML pipeline information.

```tsx
import { usePipelineInfo } from '@/hooks/useML';

function PipelineStatus() {
  const { data, isLoading } = usePipelineInfo();
  
  if (isLoading) return <div>Loading...</div>;
  
  return (
    <div>
      {data.stages.map(stage => (
        <div key={stage.id}>
          {stage.name}: {stage.latency_ms}ms
        </div>
      ))}
      <div>Total: {data.total_latency_ms}ms</div>
    </div>
  );
}
```

---

### useMLHealth

Check ML service health status.

```tsx
import { useMLHealth } from '@/hooks/useML';

function HealthIndicator() {
  const { data, isLoading } = useMLHealth(30000); // Refresh every 30s
  
  if (isLoading) return <div>Checking...</div>;
  
  return (
    <Badge variant={data.status === 'healthy' ? 'default' : 'destructive'}>
      {data.status === 'healthy' ? '✓' : '✗'} ML Service
    </Badge>
  );
}
```

---

## API Client

### Direct API Usage

```tsx
import { analyzeModule, getDefectTypes } from '@/services/ml';

// Analyze image
const result = await analyzeModule({
  module_id: 'mod_001',
  inspection_id: 'insp_001',
  image_id: 'img_001',
  thermal_data: base64Data,
  metadata: { ambient_temp: 35.0 },
});

// Get defect types
const defectTypes = await getDefectTypes();
console.log(defectTypes);
```

---

## Types

```tsx
import type {
  DefectType,
  SeverityLevel,
  AnalysisRequest,
  AnalysisResult,
  Recommendation,
} from '@/types/ml';

// Defect types
type DefectType = 'hotspot' | 'cell_anomaly' | 'delamination' | ...;

// Severity levels
type SeverityLevel = 'low' | 'medium' | 'high' | 'critical';

// Analysis result
interface AnalysisResult {
  module_id: string;
  defect_type: DefectType;
  severity: SeverityLevel;
  severity_score: number;
  confidence: number;
  temperature_delta: number;
  affected_cells: number[];
  recommendations: Recommendation[];
  processing_time_ms: number;
}
```

---

## Example: Complete Analysis Flow

```tsx
import React, { useState } from 'react';
import { useAnalyzeModule, usePipelineInfo } from '@/hooks/useML';
import ThermalViewer from '@/components/thermal/ThermalViewer';
import DefectOverlay from '@/components/defects/DefectOverlay';
import { Button } from '@/components/ui/button';

function ThermalAnalysis() {
  const [thermalData, setThermalData] = useState<Float32Array | null>(null);
  const analyze = useAnalyzeModule();
  const pipelineInfo = usePipelineInfo();
  
  const handleUpload = async (file: File) => {
    const arrayBuffer = await file.arrayBuffer();
    const floatArray = new Float32Array(arrayBuffer);
    setThermalData(floatArray);
    
    // Run analysis
    analyze.mutate({
      module_id: 'mod_001',
      inspection_id: 'insp_001',
      image_id: file.name,
      thermal_data: btoa(String.fromCharCode(...new Uint8Array(arrayBuffer))),
    });
  };
  
  const defects = analyze.data ? [{
    id: 1,
    type: analyze.data.defect_type,
    severity: analyze.data.severity,
    confidence: analyze.data.confidence,
    bbox: { x: 300, y: 200, width: 100, height: 80 },
    temperature_delta: analyze.data.temperature_delta,
  }] : [];
  
  return (
    <div>
      <input
        type="file"
        accept=".npy,.raw"
        onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
      />
      
      {thermalData && (
        <div className="relative">
          <ThermalViewer thermalData={thermalData} width={640} height={512} />
          <DefectOverlay width={640} height={512} defects={defects} />
        </div>
      )}
      
      {analyze.data && (
        <div>
          <h3>Results</h3>
          <p>Defect: {analyze.data.defect_type}</p>
          <p>Severity: {analyze.data.severity}</p>
          <p>Confidence: {(analyze.data.confidence * 100).toFixed(1)}%</p>
        </div>
      )}
    </div>
  );
}
```

---

## Testing

### Run Frontend Tests

```bash
cd frontend
npm run test
```

### Test with Backend

```bash
# Start backend
docker compose up -d ml-inference

# Start frontend
npm run dev

# Open browser to http://localhost:3000/ml-analysis
```

### Upload Test Data

```bash
# Generate sample thermal data
cd services/ml-inference
uv run python scripts/generate_sample_images.py --output-dir ../frontend/public/test_data

# Upload the .npy file in the frontend
```

---

## Troubleshooting

### "Failed to fetch" error

**Cause:** Backend not running or CORS issue

**Solution:**
```bash
# Check backend is running
curl http://localhost:8001/health

# Check CORS in frontend .env
VITE_API_URL=http://localhost:8000/api/v1
```

### Image not displaying

**Cause:** Wrong data format

**Solution:**
- Ensure thermal data is Float32Array
- Check width/height match data length
- Verify temperature values are reasonable (20-80°C)

### Defects not showing

**Cause:** Analysis failed or no defects detected

**Solution:**
- Check `analyzeMutation.error` for errors
- Verify backend logs: `docker logs ml-inference`
- Check if defect coordinates are within image bounds

---

## Resources

- [ML Service API Docs](http://localhost:8001/docs)
- [Thermal Viewer Component](../../src/components/thermal/ThermalViewer.tsx)
- [Defect Overlay Component](../../src/components/defects/DefectOverlay.tsx)
- [ML Hooks](../../src/hooks/useML.ts)
