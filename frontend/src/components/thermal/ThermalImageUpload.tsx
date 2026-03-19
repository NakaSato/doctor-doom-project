/**
 * Thermal Image Upload Component - Multi-Image Support
 * 
 * Handles drag-and-drop upload of multiple R-JPEG thermal images
 * Supports batch processing with progress tracking
 */

import { useState, useCallback, useRef } from "react";
import { parseRJpeg, getTemperatureStats } from "@/utils/thermalParser";

interface ThermalImageUploadProps {
  onImageLoaded: (data: ThermalUploadData) => void;
  onImagesLoaded?: (data: ThermalUploadData[]) => void;
  onClear?: () => void;
  acceptedFormats?: string[];
  maxFileSize?: number;
  allowMultiple?: boolean;
  maxImages?: number;
}

export interface ThermalUploadData {
  file: File;
  fileName: string;
  width: number;
  height: number;
  temperatureStats: {
    min: number;
    max: number;
    avg: number;
  };
  previewUrl: string;
  timestamp: string;
  id: string;
  processingStatus: 'pending' | 'processing' | 'completed' | 'error';
  errorMessage?: string;
}

export default function ThermalImageUpload({
  onImageLoaded,
  onImagesLoaded,
  onClear,
  acceptedFormats = ['.rjpeg', '.jpg', '.jpeg', '.tiff', '.tif'],
  maxFileSize = 50 * 1024 * 1024, // 50MB
  allowMultiple = true,
  maxImages = 20,
}: ThermalImageUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadedImages, setUploadedImages] = useState<ThermalUploadData[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const generateId = () => `IMG-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  const processThermalImage = useCallback(async (file: File): Promise<ThermalUploadData | null> => {
    try {
      // Validate file size
      if (file.size > maxFileSize) {
        throw new Error(`File too large. Maximum size is ${maxFileSize / 1024 / 1024}MB`);
      }

      // Validate file type
      const extension = file.name.toLowerCase().split('.').pop();
      if (extension && !acceptedFormats.includes(`.${extension}`)) {
        throw new Error(`Unsupported file format`);
      }

      // Parse thermal image
      const thermalData = await parseRJpeg(file);
      const stats = getTemperatureStats(thermalData.rawTemps);

      // Create preview URL
      const previewUrl = URL.createObjectURL(file);

      const imageData: ThermalUploadData = {
        file,
        fileName: file.name,
        width: thermalData.width,
        height: thermalData.height,
        temperatureStats: {
          min: Math.round(stats.min * 10) / 10,
          max: Math.round(stats.max * 10) / 10,
          avg: Math.round(stats.avg * 10) / 10,
        },
        previewUrl,
        timestamp: new Date().toISOString(),
        id: generateId(),
        processingStatus: 'completed' as const,
      };

      return imageData;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to process image';
      console.error('Image processing error:', err);
      
      return {
        file,
        fileName: file.name,
        width: 640,
        height: 512,
        temperatureStats: { min: 0, max: 0, avg: 0 },
        previewUrl: URL.createObjectURL(file),
        timestamp: new Date().toISOString(),
        id: generateId(),
        processingStatus: 'error' as const,
        errorMessage,
      };
    }
  }, [acceptedFormats, maxFileSize]);

  const processFiles = useCallback(async (files: FileList | File[]) => {
    setIsProcessing(true);
    setError(null);

    const fileArray = Array.from(files);
    const remainingSlots = maxImages - uploadedImages.length;
    const filesToProcess = fileArray.slice(0, remainingSlots);

    if (filesToProcess.length === 0) {
      setError(`Maximum ${maxImages} images allowed`);
      setIsProcessing(false);
      return;
    }

    // Process all files in parallel
    const results = await Promise.all(
      filesToProcess.map(file => processThermalImage(file))
    );

    const validResults = results.filter((r): r is ThermalUploadData => r !== null);
    
    // Update state
    setUploadedImages(prev => [...prev, ...validResults]);

    // Notify parent
    validResults.forEach(result => {
      onImageLoaded(result);
    });

    if (onImagesLoaded) {
      onImagesLoaded([...uploadedImages, ...validResults]);
    }

    setIsProcessing(false);

    if (fileArray.length > filesToProcess.length) {
      setError(`Only ${filesToProcess.length} of ${fileArray.length} images were processed (max ${maxImages})`);
    }
  }, [processThermalImage, onImageLoaded, onImagesLoaded, uploadedImages, maxImages]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  }, []);

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      processFiles(files);
    }
  }, [processFiles]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      processFiles(files);
    }
  }, [processFiles]);

  const handleClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleRemoveImage = useCallback((id: string) => {
    setUploadedImages(prev => {
      const image = prev.find(img => img.id === id);
      if (image) {
        URL.revokeObjectURL(image.previewUrl);
      }
      const filtered = prev.filter(img => img.id !== id);
      if (onImagesLoaded) {
        onImagesLoaded(filtered);
      }
      if (filtered.length === 0 && onClear) {
        onClear();
      }
      return filtered;
    });
  }, [onImagesLoaded, onClear]);

  const handleClearAll = useCallback(() => {
    uploadedImages.forEach(img => URL.revokeObjectURL(img.previewUrl));
    setUploadedImages([]);
    if (onClear) {
      onClear();
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [uploadedImages, onClear]);

  const totalImages = uploadedImages.length;
  const errorCount = uploadedImages.filter(img => img.processingStatus === 'error').length;
  const successCount = uploadedImages.filter(img => img.processingStatus === 'completed').length;

  return (
    <div style={{ width: "100%" }}>
      {/* Upload Area */}
      <div
        onDragEnter={handleDragIn}
        onDragLeave={handleDragOut}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleClick}
        style={{
          border: `2px dashed ${isDragging ? "#00F0FF" : "rgba(0,240,255,0.3)"}`,
          borderRadius: 16,
          padding: isProcessing ? 40 : 60,
          textAlign: "center",
          cursor: isProcessing ? "wait" : "pointer",
          background: isDragging
            ? "rgba(0,240,255,0.1)"
            : "linear-gradient(135deg, rgba(0,240,255,0.05) 0%, transparent 100%)",
          transition: "all 0.3s ease",
          marginBottom: 24,
          opacity: isProcessing ? 0.7 : 1,
          pointerEvents: isProcessing ? "none" : "auto",
        }}
      >
        {isProcessing ? (
          <>
            <div style={{ fontSize: 48, marginBottom: 16, animation: "spin 1s linear infinite" }}>⏳</div>
            <div style={{ fontSize: 16, fontWeight: 800, marginBottom: 8, color: "#fff" }}>
              Processing {totalImages} image{totalImages !== 1 ? 's' : ''}...
            </div>
            <div style={{ fontSize: 12, color: "#888" }}>
              Extracting temperature data from all images
            </div>
          </>
        ) : (
          <>
            <div style={{ fontSize: 48, marginBottom: 16 }}>📡</div>
            <div style={{ fontSize: 16, fontWeight: 800, marginBottom: 8, color: "#fff" }}>
              {allowMultiple ? 'Drop multiple R-JPEG images here' : 'Drop R-JPEG thermal image here'}
            </div>
            <div style={{ fontSize: 12, color: "#888" }}>
              Supports DJI Mavic 3T, FLIR cameras (640×512 LWIR)
            </div>
            {allowMultiple && (
              <div style={{ fontSize: 11, color: "#00F0FF", marginTop: 8, fontWeight: 700 }}>
                📸 Upload up to {maxImages} images at once
              </div>
            )}
            <div style={{ fontSize: 11, color: "#666", marginTop: 12 }}>
              or click to browse files
            </div>
          </>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept={acceptedFormats.join(',')}
          onChange={handleFileInput}
          multiple={allowMultiple}
          style={{ display: "none" }}
        />
      </div>

      {/* Image Grid */}
      {uploadedImages.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <div style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 12,
          }}>
            <div style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>
              📷 Uploaded Images ({totalImages})
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              {errorCount > 0 && (
                <span style={{ fontSize: 11, color: "#FF3B30", fontWeight: 700 }}>
                  ⚠️ {errorCount} error{errorCount !== 1 ? 's' : ''}
                </span>
              )}
              <button
                onClick={handleClearAll}
                style={{
                  padding: "6px 12px",
                  background: "rgba(255,59,48,0.2)",
                  border: "1px solid rgba(255,59,48,0.3)",
                  borderRadius: 6,
                  color: "#FF3B30",
                  fontSize: 11,
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                ✕ CLEAR ALL
              </button>
            </div>
          </div>

          <div style={{
            display: "grid",
            gridTemplateColumns: `repeat(auto-fill, minmax(200px, 1fr))`,
            gap: 12,
          }}>
            {uploadedImages.map((img) => (
              <ImageCard
                key={img.id}
                data={img}
                onRemove={() => handleRemoveImage(img.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Summary Stats */}
      {uploadedImages.length > 0 && (
        <div style={{
          padding: "16px",
          background: "rgba(0,240,255,0.05)",
          border: "1px solid rgba(0,240,255,0.2)",
          borderRadius: 8,
          marginBottom: 16,
        }}>
          <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
            <StatItem label="Total Images" value={totalImages.toString()} color="#00F0FF" />
            <StatItem label="Successful" value={successCount.toString()} color="#2CB67D" />
            <StatItem label="Errors" value={errorCount.toString()} color="#FF3B30" />
            {successCount > 0 && (
              <>
                <StatItem 
                  label="Avg Temp (Overall)" 
                  value={`${(uploadedImages.filter(i => i.processingStatus === 'completed').reduce((sum, img) => sum + img.temperatureStats.avg, 0) / successCount).toFixed(1)}°C`}
                  color="#FFCC00"
                />
                <StatItem 
                  label="Max Temp" 
                  value={`${Math.max(...uploadedImages.filter(i => i.processingStatus === 'completed').map(img => img.temperatureStats.max))}°C`}
                  color="#FF3B30"
                />
              </>
            )}
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div style={{
          marginTop: 16,
          padding: "12px 16px",
          background: "rgba(255,59,48,0.1)",
          border: "1px solid rgba(255,59,48,0.3)",
          borderRadius: 8,
          color: "#FF3B30",
          fontSize: 12,
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}>
          <span>⚠️</span>
          {error}
        </div>
      )}

      {/* Supported Formats */}
      <div style={{
        marginTop: 16,
        fontSize: 11,
        color: "#666",
        textAlign: "center",
      }}>
        Supported formats: {acceptedFormats.join(', ')} • Max size: {maxFileSize / 1024 / 1024}MB
        {allowMultiple && ` • Max ${maxImages} images`}
      </div>
    </div>
  );
}

// Image Card Component
function ImageCard({ data, onRemove }: { data: ThermalUploadData; onRemove: () => void }) {
  const isError = data.processingStatus === 'error';
  const isProcessing = data.processingStatus === 'processing';

  return (
    <div style={{
      position: "relative",
      background: "rgba(0,0,0,0.3)",
      borderRadius: 8,
      border: `1px solid ${isError ? "rgba(255,59,48,0.3)" : "rgba(0,240,255,0.2)"}`,
      overflow: "hidden",
      transition: "all 0.2s",
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.transform = "translateY(-2px)";
      e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.3)";
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.transform = "translateY(0)";
      e.currentTarget.style.boxShadow = "none";
    }}
    >
      {/* Preview Image */}
      <div style={{ position: "relative" }}>
        <img
          src={data.previewUrl}
          alt={data.fileName}
          style={{
            width: "100%",
            height: 120,
            objectFit: "cover",
            opacity: isError ? 0.5 : 1,
          }}
        />
        
        {/* Status Overlay */}
        {isError && (
          <div style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(255,59,48,0.7)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#fff",
            fontSize: 24,
          }}>
            ⚠️
          </div>
        )}
        
        {isProcessing && (
          <div style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.7)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}>
            <div style={{ fontSize: 24, animation: "spin 1s linear infinite" }}>⏳</div>
          </div>
        )}

        {/* Remove Button */}
        <button
          onClick={onRemove}
          style={{
            position: "absolute",
            top: 6,
            right: 6,
            width: 24,
            height: 24,
            borderRadius: "50%",
            background: "rgba(0,0,0,0.7)",
            border: "1px solid rgba(255,255,255,0.3)",
            color: "#fff",
            fontSize: 14,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 0.2s",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "rgba(255,59,48,0.8)";
            e.currentTarget.style.borderColor = "#FF3B30";
          }}
        >
          ✕
        </button>
      </div>

      {/* Info */}
      <div style={{ padding: 10 }}>
        <div style={{
          fontSize: 11,
          fontWeight: 700,
          color: "#fff",
          marginBottom: 4,
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}>
          {data.fileName}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "#888" }}>
          <span>{data.width}×{data.height}</span>
          <span style={{ color: isError ? "#FF3B30" : "#00F0FF" }}>
            {isError ? '❌ Error' : `✓ ${data.temperatureStats.avg}°C`}
          </span>
        </div>
      </div>
    </div>
  );
}

// Stat Item Component
function StatItem({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div>
      <div style={{ fontSize: 10, color: "#888", textTransform: "uppercase", marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 18, fontWeight: 800, color, fontFamily: "monospace" }}>
        {value}
      </div>
    </div>
  );
}
