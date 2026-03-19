/**
 * Enhanced ThermalCanvas Component v2.0
 * 
 * Features:
 * - Pulsing animation for critical modules
 * - Rounded corners on module cells
 * - Glow effect on selection
 * - Animated defect markers
 * - Hover tooltip
 * - Gradient background
 */

import { useState, useEffect, useCallback, useRef } from "react";
import type { DefectType } from "@/types/ml";

interface Module {
  id: string;
  row: number;
  col: number;
  status: string;
  defects: Array<{
    type: DefectType;
    x: number;
    y: number;
  }>;
  maxTemp: number;
  baseTemp: number;
}

interface ThermalCanvasProps {
  modules: Module[];
  selected: string | null;
  onSelect: (id: string) => void;
  rows?: number;
  cols?: number;
  viewMode: 'thermal' | 'severity' | 'deltaT';
  showLabels?: boolean;
}

const DEFECT_COLORS: Record<string, string> = {
  hotspot: "#FF3B30",
  cracked_cell: "#FF9500",
  snail_trail: "#FFCC00",
  delamination: "#FF6B35",
  bypass_diode: "#FF2D55",
  junction_box: "#E63946",
  connector: "#F77F00",
  string_disconnect: "#D62828",
  cabling: "#FC5A03",
  moisture: "#4CC9F0",
  pid: "#7209B7",
  soiling: "#8D6E63",
};

export default function ThermalCanvas({
  modules,
  selected,
  onSelect,
  rows = 8,
  cols = 12,
  viewMode,
  showLabels = false,
}: ThermalCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hoveredModule, setHoveredModule] = useState<string | null>(null);
  const [animationFrame, setAnimationFrame] = useState(0);
  const padding = 2;

  // Pulsing animation
  useEffect(() => {
    const interval = setInterval(() => {
      setAnimationFrame(prev => (prev + 1) % 60);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  const getColor = useCallback((mod: Module) => {
    if (viewMode === "severity") {
      if (mod.status === "critical") return "#FF3B30";
      if (mod.status === "warning") return "#FF9500";
      return "#2CB67D";
    }
    if (viewMode === "deltaT") {
      const delta = mod.maxTemp - mod.baseTemp;
      const t = Math.min(delta / 35, 1);
      if (t < 0.25) return `rgb(${Math.round(40 + t * 4 * 80)}, ${Math.round(120 + t * 4 * 60)}, 200)`;
      if (t < 0.5) return `rgb(${Math.round(120 + (t - 0.25) * 4 * 135)}, ${Math.round(180 - (t - 0.25) * 4 * 40)}, ${Math.round(200 - (t - 0.25) * 4 * 150)})`;
      if (t < 0.75) return `rgb(255, ${Math.round(140 - (t - 0.5) * 4 * 80)}, ${Math.round(50 - (t - 0.5) * 4 * 50)})`;
      return `rgb(255, ${Math.round(60 - (t - 0.75) * 4 * 60)}, 0)`;
    }
    const t = Math.min((mod.maxTemp - 35) / 30, 1);
    const r = Math.min(255, Math.round(t * 510));
    const g = Math.round(t < 0.5 ? t * 2 * 180 : (1 - t) * 2 * 180);
    const b = Math.round(Math.max(0, (1 - t * 2) * 255));
    return `rgb(${r},${g},${b})`;
  }, [viewMode]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const w = canvas.width, h = canvas.height;
    const cellW = (w - padding * (cols + 1)) / cols;
    const cellH = (h - padding * (rows + 1)) / rows;

    // Gradient background
    const gradient = ctx.createLinearGradient(0, 0, 0, h);
    gradient.addColorStop(0, "#0a0a0f");
    gradient.addColorStop(1, "#0f0f1a");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, w, h);

    modules.forEach((mod) => {
      const x = padding + mod.col * (cellW + padding);
      const y = padding + mod.row * (cellH + padding);
      
      // Pulsing alpha for critical modules
      let alpha = mod.id === selected ? 1 : hoveredModule === mod.id ? 0.9 : 0.78;
      if (mod.status === "critical" && !selected) {
        alpha += Math.sin(animationFrame * 0.1) * 0.1;
        alpha = Math.max(0.6, Math.min(1, alpha));
      }
      
      ctx.fillStyle = getColor(mod);
      ctx.globalAlpha = alpha;
      
      // Rounded rectangle
      const radius = 3;
      ctx.beginPath();
      ctx.moveTo(x + radius, y);
      ctx.lineTo(x + cellW - radius, y);
      ctx.quadraticCurveTo(x + cellW, y, x + cellW, y + radius);
      ctx.lineTo(x + cellW, y + cellH - radius);
      ctx.quadraticCurveTo(x + cellW, y + cellH, x + cellW - radius, y + cellH);
      ctx.lineTo(x + radius, y + cellH);
      ctx.quadraticCurveTo(x, y + cellH, x, y + cellH - radius);
      ctx.lineTo(x, y + radius);
      ctx.quadraticCurveTo(x, y, x + radius, y);
      ctx.closePath();
      ctx.fill();

      // Animated defect markers
      if (mod.defects.length > 0) {
        ctx.globalAlpha = 0.95;
        mod.defects.forEach((d, idx) => {
          const dx = x + d.x * cellW;
          const dy = y + d.y * cellH;
          const pulseSize = 3 + Math.sin(animationFrame * 0.2 + idx) * 1;
          ctx.beginPath();
          ctx.arc(dx, dy, pulseSize, 0, Math.PI * 2);
          ctx.fillStyle = "#fff";
          ctx.fill();
          ctx.strokeStyle = DEFECT_COLORS[d.type] || "#fff";
          ctx.lineWidth = 2;
          ctx.stroke();
        });
      }

      // Selection glow
      if (mod.id === selected) {
        ctx.globalAlpha = 1;
        ctx.shadowColor = "#00F0FF";
        ctx.shadowBlur = 15;
        ctx.strokeStyle = "#00F0FF";
        ctx.lineWidth = 3;
        ctx.stroke();
        ctx.shadowBlur = 0;
      }
      
      // Labels
      if (showLabels) {
        ctx.globalAlpha = 1;
        ctx.fillStyle = "#fff";
        ctx.font = "10px monospace";
        ctx.textAlign = "center";
        ctx.fillText(mod.id, x + cellW / 2, y + cellH / 2);
      }
      ctx.globalAlpha = 1;
    });
  }, [modules, selected, hoveredModule, getColor, rows, cols, showLabels, animationFrame]);

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const mx = (e.clientX - rect.left) * scaleX;
    const my = (e.clientY - rect.top) * scaleY;
    const cellW = (canvas.width - padding * (cols + 1)) / cols;
    const cellH = (canvas.height - padding * (rows + 1)) / rows;
    const col = Math.floor((mx - padding) / (cellW + padding));
    const row = Math.floor((my - padding) / (cellH + padding));
    const mod = modules.find(m => m.row === row && m.col === col);
    if (mod) onSelect(mod.id);
  };

  const handleMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const mx = (e.clientX - rect.left) * scaleX;
    const my = (e.clientY - rect.top) * scaleY;
    const cellW = (canvas.width - padding * (cols + 1)) / cols;
    const cellH = (canvas.height - padding * (rows + 1)) / rows;
    const col = Math.floor((mx - padding) / (cellW + padding));
    const row = Math.floor((my - padding) / (cellH + padding));
    const mod = modules.find(m => m.row === row && m.col === col);
    setHoveredModule(mod ? mod.id : null);
  };

  return (
    <div style={{ position: "relative" }}>
      <canvas
        ref={canvasRef}
        width={720}
        height={480}
        onClick={handleClick}
        onMouseMove={handleMove}
        onMouseLeave={() => setHoveredModule(null)}
        style={{ 
          width: "100%", 
          height: "auto", 
          cursor: "crosshair", 
          borderRadius: 8, 
          border: "1px solid rgba(255,255,255,0.1)",
          boxShadow: "0 4px 20px rgba(0,0,0,0.3)"
        }}
      />
      {hoveredModule && (
        <div style={{
          position: "absolute",
          bottom: "10px",
          left: "10px",
          background: "rgba(0,0,0,0.8)",
          padding: "8px 12px",
          borderRadius: 6,
          fontSize: "11px",
          color: "#fff",
          fontFamily: "monospace",
          pointerEvents: "none"
        }}>
          {hoveredModule}
        </div>
      )}
    </div>
  );
}
