/**
 * Upload Tab Component
 * 
 * Handles thermal image upload and ML analysis
 * Integrated with real ML Inference Service
 * Supports multi-image batch upload
 */

import { useState, useEffect } from "react";
import { useMLServiceHealth, useArrayAnalysis } from "@/hooks/useMLService";
import type { MLAnalysisRequest } from "@/services/mlService";
import ThermalImageUpload, { type ThermalUploadData } from "@/components/thermal/ThermalImageUpload";

interface UploadTabProps {
  inspectionStarted: boolean;
  processingProgress: number;
  onStartProcessing: () => void;
  onComplete: (results?: any) => void;
  modules?: any[];
  inspectionId?: string;
}

export default function UploadTab({
  inspectionStarted,
  processingProgress,
  onStartProcessing,
  onComplete,
  modules = [],
  inspectionId,
}: UploadTabProps) {
  const [useRealML, setUseRealML] = useState(false);
  const [uploadedImages, setUploadedImages] = useState<ThermalUploadData[]>([]);
  
  // Check ML service health (with error handling)
  const { data: mlServiceHealthy, error: mlError } = useMLServiceHealth(5000);
  const { analyzeArray, isLoading: isAnalyzing, error: analyzeError } = useArrayAnalysis();

  // Log errors
  useEffect(() => {
    if (mlError) {
      console.warn('ML Service health check failed:', mlError);
    }
    if (analyzeError) {
      console.error('ML Analysis error:', analyzeError);
    }
  }, [mlError, analyzeError]);

  const handleImageLoaded = (data: ThermalUploadData) => {
    setUploadedImages(prev => [...prev, data]);
    console.log('✅ Thermal image loaded:', data.fileName);
    console.log('📊 Temperature stats:', data.temperatureStats);
  };

  const handleImagesLoaded = (data: ThermalUploadData[]) => {
    setUploadedImages(data);
    console.log(`✅ ${data.length} thermal images loaded`);
  };

  const handleClear = () => {
    setUploadedImages([]);
    console.log('🗑️ All images cleared');
  };

  const handleStartAnalysis = async () => {
    onStartProcessing();
    
    // Always use demo mode if ML service is not healthy or not enabled
    const shouldUseML = useRealML && mlServiceHealthy && modules.length > 0;
    
    if (shouldUseML) {
      // Use real ML service with uploaded images
      try {
        const requests: MLAnalysisRequest[] = modules.map((mod, idx) => {
          // Cycle through uploaded images if fewer images than modules
          const image = uploadedImages[idx % uploadedImages.length];
          
          return {
            module_id: mod.id,
            inspection_id: inspectionId || `INS-${Date.now()}`,
            image_id: image?.id || `IMG-${mod.id}-${Date.now()}`,
            thermal_data: image?.previewUrl,
            metadata: {
              drone_model: "DJI Mavic 3T",
              camera_model: "FLIR Tau2",
              altitude: 25,
              irradiance: 892,
              ambient_temp: 34.2,
              ...image && {
                image_width: image.width,
                image_height: image.height,
                min_temp: image.temperatureStats.min,
                max_temp: image.temperatureStats.max,
              },
            },
          };
        });
        
        await analyzeArray(requests, (progress, current, total) => {
          console.log(`Analyzing: ${current}/${total} (${progress.toFixed(0)}%)`);
        });
        
        onComplete({ 
          mlService: true, 
          thermalImages: uploadedImages,
          imageCount: uploadedImages.length,
        });
      } catch (error) {
        console.error('ML analysis failed, falling back to demo mode:', error);
        // Fall back to demo mode
        startDemoProcessing();
      }
    } else {
      // Use demo mode
      startDemoProcessing();
    }
  };

  const startDemoProcessing = () => {
    let p = 0;
    const interval = setInterval(() => {
      p += Math.random() * 8 + 2;
      if (p >= 100) {
        p = 100;
        clearInterval(interval);
        onComplete({ mlService: false, thermalImages: uploadedImages });
      }
    }, 200);
  };

  if (!inspectionStarted) {
    return (
      <div style={{ maxWidth: 800, margin: "0 auto" }}>
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{ fontSize: 20, fontWeight: 900, marginBottom: 8, color: "#fff" }}>
            Thermal Image Upload
          </div>
          <div style={{ fontSize: 12, color: "#888" }}>
            Import RJPEG thermal images from DJI Mavic 3T
          </div>
          
          {/* ML Service Status */}
          <div style={{
            marginTop: 16,
            padding: "10px 16px",
            background: mlServiceHealthy ? "rgba(44,182,125,0.1)" : "rgba(255,59,48,0.1)",
            border: `1px solid ${mlServiceHealthy ? "#2CB67D" : "#FF3B30"}30`,
            borderRadius: 8,
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            fontSize: 12,
          }}>
            <div style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: mlServiceHealthy ? "#2CB67D" : "#FF3B30",
              animation: mlServiceHealthy ? "none" : "pulse 2s infinite",
            }} />
            <span style={{ color: mlServiceHealthy ? "#2CB67D" : "#FF3B30", fontWeight: 700 }}>
              ML Service: {mlServiceHealthy ? "ONLINE" : "OFFLINE"}
            </span>
            <span style={{ color: "#888" }}>
              {mlServiceHealthy ? "http://localhost:8001" : "Using demo mode"}
            </span>
          </div>
        </div>

        {/* Thermal Image Upload Component */}
        <ThermalImageUpload 
          onImageLoaded={handleImageLoaded}
          onImagesLoaded={handleImagesLoaded}
          onClear={handleClear}
          allowMultiple={true}
          maxImages={20}
        />

        {/* Use Real ML Toggle */}
        <div style={{
          marginBottom: 20,
          marginTop: 20,
          padding: "12px 16px",
          background: "rgba(0,240,255,0.05)",
          border: "1px solid rgba(0,240,255,0.2)",
          borderRadius: 8,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}>
          <div style={{ fontSize: 12, color: "#aaa" }}>
            <div style={{ fontWeight: 700, color: "#fff", marginBottom: 4 }}>Use Real ML Service</div>
            <div style={{ fontSize: 11, color: "#888" }}>Send thermal data to ML inference server for analysis</div>
          </div>
          <label style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            cursor: "pointer",
            opacity: mlServiceHealthy ? 1 : 0.5,
          }}>
            <input
              type="checkbox"
              checked={useRealML && mlServiceHealthy}
              onChange={(e) => setUseRealML(e.target.checked)}
              disabled={!mlServiceHealthy}
              style={{ accentColor: "#00F0FF", width: 18, height: 18 }}
            />
            <span style={{ fontSize: 12, color: useRealML && mlServiceHealthy ? "#00F0FF" : "#888", fontWeight: 700 }}>
              {mlServiceHealthy ? (useRealML ? "ENABLED" : "DISABLED") : "UNAVAILABLE"}
            </span>
          </label>
        </div>

        <button
          onClick={handleStartAnalysis}
          disabled={isAnalyzing || uploadedImages.length === 0}
          style={{
            width: "100%",
            padding: "18px",
            border: "none",
            borderRadius: 12,
            cursor: (uploadedImages.length === 0 || isAnalyzing) ? "not-allowed" : "pointer",
            background: (uploadedImages.length === 0 || isAnalyzing)
              ? "linear-gradient(135deg, #666 0%, #888 100%)"
              : "linear-gradient(135deg, #00F0FF 0%, #0080FF 100%)",
            color: "#000",
            fontSize: 14,
            fontWeight: 900,
            fontFamily: "inherit",
            letterSpacing: "0.08em",
            boxShadow: (uploadedImages.length === 0 || isAnalyzing) ? "none" : "0 4px 20px rgba(0,240,255,0.4)",
            opacity: (uploadedImages.length === 0 || isAnalyzing) ? 0.7 : 1,
          }}
        >
          {uploadedImages.length === 0 ? "📷 UPLOAD IMAGES FIRST" : 
           isAnalyzing ? "⏳ ANALYZING WITH ML SERVICE..." : `▶ ANALYZE ${uploadedImages.length} IMAGE${uploadedImages.length !== 1 ? 'S' : ''} WITH ML`}
        </button>
      </div>
    );
  }

  if (processingProgress < 100) {
    return (
      <div style={{ padding: 60 }}>
        <div style={{
          fontSize: 16,
          fontWeight: 800,
          marginBottom: 24,
          textAlign: "center",
          color: "#fff"
        }}>
          Processing Thermal Data...
        </div>
        <div style={{
          background: "rgba(0,0,0,0.5)",
          borderRadius: 12,
          height: 12,
          overflow: "hidden",
          marginBottom: 20,
          border: "1px solid rgba(255,255,255,0.1)"
        }}>
          <div style={{
            width: `${processingProgress}%`,
            height: "100%",
            borderRadius: 12,
            transition: "width 0.3s ease",
            background: "linear-gradient(90deg, #00F0FF 0%, #0080FF 50%, #00F0FF 100%)",
          }} />
        </div>
        <div style={{
          fontSize: 12,
          color: "#888",
          textAlign: "center",
          fontFamily: "monospace"
        }}>
          {processingProgress < 20 ? "Loading radiometric data..." :
           processingProgress < 40 ? "Calibrating emissivity..." :
           processingProgress < 60 ? "Running CNN classification..." :
           processingProgress < 80 ? "Computing ΔT anomaly..." :
           "Generating report..."}
          {" "}<span style={{ color: "#00F0FF", fontWeight: 700 }}>{Math.round(processingProgress)}%</span>
        </div>
      </div>
    );
  }

  return (
    <div style={{ textAlign: "center", padding: 60 }}>
      <div style={{ fontSize: 64, marginBottom: 16 }}>✅</div>
      <div style={{ fontSize: 20, fontWeight: 900, marginBottom: 8, color: "#fff" }}>
        Analysis Complete
      </div>
      <div style={{ fontSize: 14, color: "#888", marginBottom: 32 }}>
        Click below to view results
      </div>
      <button
        onClick={onComplete}
        style={{
          padding: "14px 40px",
          border: "2px solid #00F0FF",
          borderRadius: 12,
          cursor: "pointer",
          background: "transparent",
          color: "#00F0FF",
          fontSize: 13,
          fontWeight: 800,
          fontFamily: "inherit",
        }}
      >
        VIEW RESULTS →
      </button>
    </div>
  );
}
