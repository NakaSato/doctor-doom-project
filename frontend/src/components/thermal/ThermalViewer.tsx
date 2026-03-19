/**
 * Thermal Image Viewer Component
 * 
 * Displays thermal images with adjustable colormap and temperature scale.
 */

import React, { useRef, useEffect, useMemo, useState } from 'react';

interface ThermalViewerProps {
  /** Thermal data as 2D array (temperature values in °C) */
  thermalData: Float32Array | number[][];
  /** Image width */
  width: number;
  /** Image height */
  height: number;
  /** Colormap to use */
  colormap?: 'ironbow' | 'grayscale' | 'rainbow' | 'thermal';
  /** Temperature range (auto-calculated if not provided) */
  tempRange?: { min: number; max: number };
  /** Show temperature scale bar */
  showScale?: boolean;
  /** Show crosshair */
  showCrosshair?: boolean;
  /** Crosshair position */
  crosshairPos?: { x: number; y: number };
  /** On crosshair move callback */
  onCrosshairMove?: (pos: { x: number; y: number; temp: number }) => void;
  /** className for styling */
  className?: string;
}

/**
 * Convert temperature to color using ironbow colormap
 */
function ironbowColormap(value: number): [number, number, number] {
  // value is 0-1
  const r = Math.min(255, Math.max(0, value * 255 * 3 - 255));
  const g = Math.min(255, Math.max(0, value * 255 * 3 - 510));
  const b = Math.min(255, Math.max(0, value * 255 * 3));
  return [Math.round(r), Math.round(g), Math.round(b)];
}

/**
 * Convert temperature to color using grayscale colormap
 */
function grayscaleColormap(value: number): [number, number, number] {
  const gray = Math.round(value * 255);
  return [gray, gray, gray];
}

/**
 * Convert temperature to color using rainbow colormap
 */
function rainbowColormap(value: number): [number, number, number] {
  const hue = (1 - value) * 270; // Blue to Red
  const s = 1;
  const l = 0.5;
  
  // HSL to RGB conversion
  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs(((hue / 60) % 2) - 1));
  const m = l - c / 2;
  
  let r = 0, g = 0, b = 0;
  
  if (hue < 60) { r = c; g = x; b = 0; }
  else if (hue < 120) { r = x; g = c; b = 0; }
  else if (hue < 180) { r = 0; g = c; b = x; }
  else if (hue < 240) { r = 0; g = x; b = c; }
  else if (hue < 300) { r = x; g = 0; b = c; }
  else { r = c; g = 0; b = x; }
  
  return [
    Math.round((r + m) * 255),
    Math.round((g + m) * 255),
    Math.round((b + m) * 255)
  ];
}

/**
 * Convert temperature to color using thermal colormap (black-red-yellow-white)
 */
function thermalColormap(value: number): [number, number, number] {
  let r: number, g: number, b: number;
  
  if (value < 0.25) {
    // Black to Red
    const t = value * 4;
    r = t * 255;
    g = 0;
    b = 0;
  } else if (value < 0.5) {
    // Red to Yellow
    const t = (value - 0.25) * 4;
    r = 255;
    g = t * 255;
    b = 0;
  } else if (value < 0.75) {
    // Yellow to White
    const t = (value - 0.5) * 4;
    r = 255;
    g = 255;
    b = t * 255;
  } else {
    // White
    r = 255;
    g = 255;
    b = 255;
  }
  
  return [Math.round(r), Math.round(g), Math.round(b)];
}

export const ThermalViewer: React.FC<ThermalViewerProps> = ({
  thermalData,
  width,
  height,
  colormap = 'ironbow',
  tempRange,
  showScale = true,
  showCrosshair = true,
  crosshairPos,
  onCrosshairMove,
  className = '',
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [localCrosshair, setLocalCrosshair] = useState<{ x: number; y: number } | null>(null);
  
  // Calculate temperature range
  const calculatedRange = useMemo(() => {
    if (tempRange) return tempRange;
    
    let min = Infinity;
    let max = -Infinity;
    
    for (let i = 0; i < thermalData.length; i++) {
      const val = typeof thermalData[i] === 'number' ? thermalData[i] : (thermalData as number[][])[i][0];
      if (val < min) min = val;
      if (val > max) max = val;
    }
    
    return { min, max };
  }, [thermalData, tempRange]);
  
  // Get colormap function
  const getColormap = (value: number) => {
    switch (colormap) {
      case 'grayscale':
        return grayscaleColormap(value);
      case 'rainbow':
        return rainbowColormap(value);
      case 'thermal':
        return thermalColormap(value);
      case 'ironbow':
      default:
        return ironbowColormap(value);
    }
  };
  
  // Render thermal image
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Create image data
    const imageData = ctx.createImageData(width, height);
    const data = imageData.data;
    
    // Fill pixel data
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const idx = y * width + x;
        const temp = typeof thermalData[idx] === 'number' 
          ? thermalData[idx] as number
          : (thermalData as number[][])[y]?.[x] || 0;
        
        // Normalize temperature to 0-1
        const normalized = (temp - calculatedRange.min) / (calculatedRange.max - calculatedRange.min);
        const clamped = Math.max(0, Math.min(1, normalized));
        
        // Get color from colormap
        const [r, g, b] = getColormap(clamped);
        
        // Set pixel
        const pixelIdx = (y * width + x) * 4;
        data[pixelIdx] = r;
        data[pixelIdx + 1] = g;
        data[pixelIdx + 2] = b;
        data[pixelIdx + 3] = 255; // Alpha
      }
    }
    
    ctx.putImageData(imageData, 0, 0);
  }, [thermalData, width, height, calculatedRange, colormap]);
  
  // Handle mouse move for crosshair
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || !onCrosshairMove) return;
    
    const rect = canvasRef.current.getBoundingClientRect();
    const x = Math.floor((e.clientX - rect.left) / rect.width * width);
    const y = Math.floor((e.clientY - rect.top) / rect.height * height);
    
    const idx = y * width + x;
    const temp = typeof thermalData[idx] === 'number'
      ? thermalData[idx] as number
      : (thermalData as number[][])[y]?.[x] || 0;
    
    setLocalCrosshair({ x, y });
    onCrosshairMove({ x, y, temp });
  };
  
  const handleMouseLeave = () => {
    setLocalCrosshair(null);
  };
  
  const currentCrosshair = crosshairPos || localCrosshair;
  
  return (
    <div className={`relative inline-block ${className}`}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="block max-w-full"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      />
      
      {/* Crosshair */}
      {showCrosshair && currentCrosshair && (
        <svg
          className="absolute inset-0 pointer-events-none"
          width={width}
          height={height}
        >
          <line
            x1={currentCrosshair.x}
            y1={0}
            x2={currentCrosshair.x}
            y2={height}
            stroke="white"
            strokeWidth={1}
            strokeDasharray="4,4"
          />
          <line
            x1={0}
            y1={currentCrosshair.y}
            x2={width}
            y2={currentCrosshair.y}
            stroke="white"
            strokeWidth={1}
            strokeDasharray="4,4"
          />
        </svg>
      )}
      
      {/* Temperature scale */}
      {showScale && (
        <div className="absolute right-2 top-2 bottom-2 w-8 bg-black/50 rounded">
          <div className="h-full w-full relative">
            {/* Gradient bar */}
            <div
              className="absolute inset-0 rounded"
              style={{
                background: `linear-gradient(to bottom,
                  rgb(${getColormap(1).join(',')}),
                  rgb(${getColormap(0).join(',')}))
                `,
              }}
            />
            
            {/* Temperature labels */}
            <div className="absolute -right-12 top-0 text-xs text-white">
              {calculatedRange.max.toFixed(1)}°C
            </div>
            <div className="absolute -right-12 bottom-0 text-xs text-white">
              {calculatedRange.min.toFixed(1)}°C
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ThermalViewer;
