/**
 * Defect Overlay Component
 * 
 * Displays defect markers and bounding boxes on thermal images.
 */

import React from 'react';
import type { DefectType, SeverityLevel } from '@/types/ml';

interface DefectOverlayProps {
  /** Image width */
  width: number;
  /** Image height */
  height: number;
  /** Defects to display */
  defects: DefectMarker[];
  /** Selected defect ID */
  selectedDefectId?: number;
  /** On defect click callback */
  onDefectClick?: (defectId: number) => void;
  /** Show labels */
  showLabels?: boolean;
  /** Show confidence scores */
  showConfidence?: boolean;
}

export interface DefectMarker {
  id: number;
  type: DefectType;
  severity: SeverityLevel;
  confidence: number;
  bbox: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  temperature_delta?: number;
}

/**
 * Get color for defect severity
 */
function getSeverityColor(severity: SeverityLevel): string {
  switch (severity) {
    case 'critical':
      return '#ef4444'; // Red
    case 'high':
      return '#f97316'; // Orange
    case 'medium':
      return '#eab308'; // Yellow
    case 'low':
      return '#22c55e'; // Green
    default:
      return '#9ca3af'; // Gray
  }
}

/**
 * Get color for defect type
 */
function getDefectTypeColor(type: DefectType): string {
  const colors: Record<DefectType, string> = {
    hotspot: '#ef4444',
    cell_anomaly: '#f97316',
    delamination: '#eab308',
    diode_failure: '#dc2626',
    crack: '#7c3aed',
    soiling: '#059669',
    discoloration: '#0891b2',
    snail_track: '#06b6d4',
    burn_mark: '#b91c1c',
    corrosion: '#6b7280',
    potential_induced: '#a855f7',
    broken_cell: '#dc2626',
    normal: '#22c55e',
  };
  return colors[type] || '#9ca3af';
}

/**
 * Get defect type label
 */
function getDefectLabel(type: DefectType): string {
  const labels: Record<DefectType, string> = {
    hotspot: 'Hotspot',
    cell_anomaly: 'Cell Anomaly',
    delamination: 'Delamination',
    diode_failure: 'Diode Failure',
    crack: 'Crack',
    soiling: 'Soiling',
    discoloration: 'Discoloration',
    snail_track: 'Snail Track',
    burn_mark: 'Burn Mark',
    corrosion: 'Corrosion',
    potential_induced: 'PID',
    broken_cell: 'Broken Cell',
    normal: 'Normal',
  };
  return labels[type] || type;
}

export const DefectOverlay: React.FC<DefectOverlayProps> = ({
  width,
  height,
  defects,
  selectedDefectId,
  onDefectClick,
  showLabels = true,
  showConfidence = true,
}) => {
  return (
    <svg
      className="absolute inset-0 pointer-events-auto"
      width={width}
      height={height}
    >
      {/* Defect markers */}
      {defects.map((defect) => {
        const color = getSeverityColor(defect.severity);
        const isSelected = selectedDefectId === defect.id;
        
        return (
          <g
            key={defect.id}
            onClick={() => onDefectClick?.(defect.id)}
            className="cursor-pointer pointer-events-auto"
            style={{ opacity: isSelected ? 1 : 0.7 }}
          >
            {/* Bounding box */}
            <rect
              x={defect.bbox.x}
              y={defect.bbox.y}
              width={defect.bbox.width}
              height={defect.bbox.height}
              fill="none"
              stroke={color}
              strokeWidth={isSelected ? 3 : 2}
              strokeDasharray={isSelected ? 'none' : '4,2'}
            />
            
            {/* Corner markers */}
            <path
              d={`
                M ${defect.bbox.x} ${defect.bbox.y + 8}
                L ${defect.bbox.x} ${defect.bbox.y}
                L ${defect.bbox.x + 8} ${defect.bbox.y}
                
                M ${defect.bbox.x + defect.bbox.width - 8} ${defect.bbox.y}
                L ${defect.bbox.x + defect.bbox.width} ${defect.bbox.y}
                L ${defect.bbox.x + defect.bbox.width} ${defect.bbox.y + 8}
                
                M ${defect.bbox.x + defect.bbox.width} ${defect.bbox.y + defect.bbox.height - 8}
                L ${defect.bbox.x + defect.bbox.width} ${defect.bbox.y + defect.bbox.height}
                L ${defect.bbox.x + defect.bbox.width - 8} ${defect.bbox.y + defect.bbox.height}
                
                M ${defect.bbox.x + 8} ${defect.bbox.y + defect.bbox.height}
                L ${defect.bbox.x} ${defect.bbox.y + defect.bbox.height}
                L ${defect.bbox.x} ${defect.bbox.y + defect.bbox.height - 8}
              `}
              stroke={color}
              strokeWidth={2}
              fill="none"
            />
            
            {/* Label background */}
            {showLabels && (
              <g>
                <rect
                  x={defect.bbox.x}
                  y={defect.bbox.y - 20}
                  width={defect.bbox.width}
                  height={20}
                  fill={color}
                  fillOpacity={0.8}
                />
                
                {/* Label text */}
                <text
                  x={defect.bbox.x + 4}
                  y={defect.bbox.y - 6}
                  className="text-xs font-medium"
                  fill="white"
                  style={{ fontSize: '11px' }}
                >
                  {getDefectLabel(defect.type)}
                  {showConfidence && ` ${(defect.confidence * 100).toFixed(0)}%`}
                </text>
              </g>
            )}
            
            {/* Temperature delta badge */}
            {defect.temperature_delta && (
              <g>
                <rect
                  x={defect.bbox.x + defect.bbox.width - 60}
                  y={defect.bbox.y - 20}
                  width={56}
                  height={20}
                  fill="rgba(0,0,0,0.7)"
                />
                <text
                  x={defect.bbox.x + defect.bbox.width - 56}
                  y={defect.bbox.y - 6}
                  className="text-xs"
                  fill="white"
                  style={{ fontSize: '10px' }}
                >
                  ΔT: {defect.temperature_delta.toFixed(1)}°C
                </text>
              </g>
            )}
          </g>
        );
      })}
      
      {/* No defects message */}
      {defects.length === 0 && (
        <g>
          <rect
            x={width / 2 - 60}
            y={height / 2 - 20}
            width={120}
            height={40}
            fill="rgba(34, 197, 94, 0.8)"
            rx={8}
          />
          <text
            x={width / 2}
            y={height / 2 + 5}
            textAnchor="middle"
            className="text-sm font-medium"
            fill="white"
            style={{ fontSize: '14px' }}
          >
            ✓ No Defects Detected
          </text>
        </g>
      )}
    </svg>
  );
};

export default DefectOverlay;
