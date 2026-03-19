/**
 * ML Analysis Dashboard Page
 * 
 * Upload thermal images and analyze them for defects.
 */

import React, { useState, useCallback } from 'react';
import { useAnalyzeModule, usePipelineInfo, useMLHealth } from '@/hooks/useML';
import ThermalViewer from '@/components/thermal/ThermalViewer';
import DefectOverlay from '@/components/defects/DefectOverlay';
import type { DefectMarker } from '@/components/defects/DefectOverlay';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Upload, Activity, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

const MLAnalysisDashboard: React.FC = () => {
  const [thermalData, setThermalData] = useState<Float32Array | null>(null);
  const [imageSize, setImageSize] = useState({ width: 640, height: 512 });
  const [selectedDefect, setSelectedDefect] = useState<number | null>(null);
  const [colormap, setColormap] = useState<'ironbow' | 'grayscale' | 'rainbow' | 'thermal'>('ironbow');
  
  const analyzeMutation = useAnalyzeModule();
  const pipelineInfo = usePipelineInfo();
  const healthStatus = useMLHealth();
  
  // Handle file upload
  const handleFileUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    try {
      // Read file as array buffer
      const arrayBuffer = await file.arrayBuffer();
      const floatArray = new Float32Array(arrayBuffer);
      
      // For demo, assume 640x512 resolution
      setThermalData(floatArray);
      setImageSize({ width: 640, height: 512 });
      
      // Run analysis
      analyzeMutation.mutate({
        module_id: 'mod_demo_001',
        inspection_id: 'insp_demo_001',
        image_id: file.name,
        thermal_data: btoa(String.fromCharCode(...new Uint8Array(arrayBuffer))),
        metadata: {
          ambient_temp: 35.0,
          irradiance: 850,
        },
      });
    } catch (error) {
      console.error('Failed to load thermal image:', error);
    }
  }, [analyzeMutation]);
  
  // Generate sample defects for demo
  const defects: DefectMarker[] = analyzeMutation.data ? [
    {
      id: 1,
      type: analyzeMutation.data.defect_type as any,
      severity: analyzeMutation.data.severity,
      confidence: analyzeMutation.data.confidence,
      bbox: {
        x: 300,
        y: 200,
        width: 100,
        height: 80,
      },
      temperature_delta: analyzeMutation.data.temperature_delta,
    },
  ] : [];
  
  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">ML Thermal Analysis</h1>
          <p className="text-muted-foreground">
            Upload thermal images for automated defect detection
          </p>
        </div>
        
        {/* Health Status */}
        <Badge variant={healthStatus.data?.status === 'healthy' ? 'default' : 'destructive'}>
          {healthStatus.data?.status === 'healthy' ? (
            <CheckCircle className="w-3 h-3 mr-1" />
          ) : (
            <AlertCircle className="w-3 h-3 mr-1" />
          )}
          ML Service: {healthStatus.data?.status || 'checking...'}
        </Badge>
      </div>
      
      {/* Pipeline Info */}
      {pipelineInfo.data && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              ML Pipeline
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              {pipelineInfo.data.stages.map((stage) => (
                <div key={stage.id} className="text-center p-3 bg-muted rounded-lg">
                  <div className="font-semibold">Stage {stage.id}</div>
                  <div className="text-sm text-muted-foreground">{stage.name}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {stage.latency_ms}ms
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 text-sm text-muted-foreground">
              Total Latency: {pipelineInfo.data.total_latency_ms}ms |
              Model Size: {pipelineInfo.data.total_model_size_mb} MB
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Upload Area */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Thermal Image</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <label htmlFor="thermal-upload">
              <div className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md cursor-pointer hover:bg-primary/90">
                <Upload className="w-4 h-4" />
                Upload .npy or Raw File
              </div>
            </label>
            <input
              id="thermal-upload"
              type="file"
              accept=".npy,.raw,.bin"
              onChange={handleFileUpload}
              className="hidden"
            />
            <span className="text-sm text-muted-foreground">
              Supports NumPy .npy or raw float32 binary files
            </span>
          </div>
          
          {analyzeMutation.isPending && (
            <div className="flex items-center gap-2 mt-4 text-muted-foreground">
              <Loader2 className="w-4 h-4 animate-spin" />
              Analyzing thermal image...
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Analysis Results */}
      {analyzeMutation.data && (
        <Card>
          <CardHeader>
            <CardTitle>Analysis Results</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="p-3 bg-muted rounded-lg">
                <div className="text-sm text-muted-foreground">Defect Type</div>
                <div className="text-lg font-semibold capitalize">
                  {analyzeMutation.data.defect_type}
                </div>
              </div>
              <div className="p-3 bg-muted rounded-lg">
                <div className="text-sm text-muted-foreground">Severity</div>
                <div className="text-lg font-semibold capitalize">
                  {analyzeMutation.data.severity}
                </div>
              </div>
              <div className="p-3 bg-muted rounded-lg">
                <div className="text-sm text-muted-foreground">Confidence</div>
                <div className="text-lg font-semibold">
                  {(analyzeMutation.data.confidence * 100).toFixed(1)}%
                </div>
              </div>
            </div>
            
            {analyzeMutation.data.recommendations.length > 0 && (
              <Alert>
                <AlertDescription>
                  <strong>Recommendation:</strong> {analyzeMutation.data.recommendations[0].description}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}
      
      {/* Thermal Viewer */}
      {thermalData && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Thermal Image</CardTitle>
              <div className="flex gap-2">
                <Button
                  variant={colormap === 'ironbow' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setColormap('ironbow')}
                >
                  Ironbow
                </Button>
                <Button
                  variant={colormap === 'grayscale' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setColormap('grayscale')}
                >
                  Grayscale
                </Button>
                <Button
                  variant={colormap === 'rainbow' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setColormap('rainbow')}
                >
                  Rainbow
                </Button>
                <Button
                  variant={colormap === 'thermal' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setColormap('thermal')}
                >
                  Thermal
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="relative">
              <ThermalViewer
                thermalData={thermalData}
                width={imageSize.width}
                height={imageSize.height}
                colormap={colormap}
                showScale
                showCrosshair
              />
              <DefectOverlay
                width={imageSize.width}
                height={imageSize.height}
                defects={defects}
                selectedDefectId={selectedDefect || undefined}
                onDefectClick={setSelectedDefect}
              />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default MLAnalysisDashboard;
