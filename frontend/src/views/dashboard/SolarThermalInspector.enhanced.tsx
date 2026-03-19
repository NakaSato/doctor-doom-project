import { useState, useEffect, useCallback, useRef, useMemo } from "react";

// Keep existing DEFECT_TYPES and SEVERITY_CONFIG from your original code
const DEFECT_TYPES = {
  hotspot: { label: "Hot Spot", severity: "critical", color: "#FF3B30", icon: "🔥", desc: "Overheating cells" },
  cracked_cell: { label: "Cracked Cell", severity: "major", color: "#FF9500", icon: "⚡", desc: "Physical fracture" },
  snail_trail: { label: "Snail Trail", severity: "minor", color: "#FFCC00", icon: "🐌", desc: "Discoloration pattern" },
  delamination: { label: "Delamination", severity: "major", color: "#FF6B35", icon: "📄", desc: "Layer separation" },
  bypass_diode: { label: "Bypass Diode Failure", severity: "critical", color: "#FF2D55", icon: "⚙️", desc: "Diode malfunction" },
  junction_box: { label: "Junction Box Overheat", severity: "critical", color: "#E63946", icon: "📦", desc: "Fire hazard" },
  connector: { label: "Defective Connector", severity: "major", color: "#F77F00", icon: "🔌", desc: "High resistance" },
  string_disconnect: { label: "Disconnected String", severity: "critical", color: "#D62828", icon: "🔗", desc: "Open circuit" },
  cabling: { label: "Poor Cabling", severity: "major", color: "#FC5A03", icon: "🪢", desc: "Fire risk" },
  moisture: { label: "Moisture Ingress", severity: "minor", color: "#4CC9F0", icon: "💧", desc: "Water penetration" },
  pid: { label: "PID Effect", severity: "major", color: "#7209B7", icon: "⬇️", desc: "Voltage stress" },
  soiling: { label: "Heavy Soiling", severity: "minor", color: "#8D6E63", icon: "🌫️", desc: "Dirt/debris" },
};

const SEVERITY_CONFIG = {
  critical: { label: "Critical", color: "#FF3B30", bg: "rgba(255,59,48,0.12)", priority: 1 },
  major: { label: "Major", color: "#FF9500", bg: "rgba(255,149,0,0.12)", priority: 2 },
  minor: { label: "Minor", color: "#FFCC00", bg: "rgba(255,204,0,0.12)", priority: 3 },
};

// Keep your existing generateId, generateDemoData, generateInspectionData functions
const generateId = () => Math.random().toString(36).substr(2, 9);
const generateDemoData = () => { /* your existing code */ return []; };
const generateInspectionData = () => { /* your existing code */ return { modules: [] }; };

// ENHANCED COMPONENTS WITH NEW STYLING

const ThermalCanvas = ({ modules, selected, onSelect, rows = 8, cols = 12, viewMode, showLabels = false }) => {
  const canvasRef = useRef(null);
  const [hoveredModule, setHoveredModule] = useState(null);
  const [animationFrame, setAnimationFrame] = useState(0);
  const padding = 2;

  // Pulsing animation for critical modules
  useEffect(() => {
    const interval = setInterval(() => {
      setAnimationFrame(prev => (prev + 1) % 60);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  const getColor = useCallback((mod) => {
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

      // Defect indicators with animation
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
          ctx.strokeStyle = DEFECT_TYPES[d.type]?.color || "#fff";
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

  const handleClick = (e) => {
    const canvas = canvasRef.current;
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

  const handleMove = (e) => {
    const canvas = canvasRef.current;
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
};

// Keep your existing ThermalImageViewer, SeverityBadge, StatCard, TempScale components
// Just add enhanced styling with shadows, hover effects, and animations

const SeverityBadge = ({ severity, animated = true }) => {
  const cfg = SEVERITY_CONFIG[severity];
  const [pulse, setPulse] = useState(0);
  
  useEffect(() => {
    if (!animated) return;
    const interval = setInterval(() => {
      setPulse(prev => (prev + 1) % 60);
    }, 50);
    return () => clearInterval(interval);
  }, [animated]);
  
  const pulseScale = animated && severity === "critical" ? 1 + Math.sin(pulse * 0.2) * 0.1 : 1;
  
  return (
    <span style={{
      display: "inline-flex", 
      alignItems: "center", 
      gap: 4,
      padding: "3px 10px", 
      borderRadius: 12, 
      fontSize: 10, 
      fontWeight: 700,
      letterSpacing: "0.05em", 
      textTransform: "uppercase",
      color: cfg.color, 
      background: cfg.bg,
      border: `1px solid ${cfg.color}40`,
      transform: `scale(${pulseScale})`,
      transition: "transform 0.1s",
      boxShadow: severity === "critical" ? `0 0 10px ${cfg.color}60` : "none"
    }}>
      <span style={{ 
        width: 6, 
        height: 6, 
        borderRadius: "50%", 
        background: cfg.color,
      }} />
      {cfg.label}
    </span>
  );
};

const StatCard = ({ label, value, sub, color = "#00F0FF", icon, trend }) => {
  const [hovered, setHovered] = useState(false);
  
  return (
    <div 
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
        border: `1px solid ${hovered ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.06)"}`,
        borderRadius: 12, 
        padding: "16px 18px", 
        flex: 1, 
        minWidth: 140,
        transition: "all 0.2s ease",
        cursor: "default",
        transform: hovered ? "translateY(-2px)" : "none",
        boxShadow: hovered ? "0 4px 12px rgba(0,0,0,0.3)" : "none"
      }}
    >
      <div style={{ fontSize: 11, color: "#888", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
        {icon && <span style={{ fontSize: 16 }}>{icon}</span>}
        {label}
      </div>
      <div style={{ fontSize: 28, fontWeight: 800, color, fontFamily: "monospace", letterSpacing: "-0.02em", textShadow: `0 0 20px ${color}40` }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 11, color: "#666", marginTop: 4, display: "flex", alignItems: "center", gap: 4 }}>
        {trend && <span style={{ color: trend > 0 ? "#2CB67D" : trend < 0 ? "#FF3B30" : "#888", fontWeight: 600 }}>{trend > 0 ? "↑" : trend < 0 ? "↓" : "→"} {Math.abs(trend)}%</span>}
        {sub}
      </div>}
    </div>
  );
};

const TempScale = ({ min, max }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 0", background: "rgba(255,255,255,0.02)", borderRadius: 8, padding: "12px" }}>
    <span style={{ fontSize: 11, color: "#aaa", fontFamily: "monospace", fontWeight: 600, minWidth: 40 }}>{min}°C</span>
    <div style={{ flex: 1, height: 14, borderRadius: 8, background: "linear-gradient(to right, #000033, #000066, #000099, #0033cc, #0066ff, #00ccff, #00ff00, #ffff00, #ff9900, #ff3300, #ff0000)", boxShadow: "0 2px 8px rgba(0,0,0,0.3)", position: "relative" }}>
      {[0.25, 0.5, 0.75].map(pos => (
        <div key={pos} style={{ position: "absolute", left: `${pos * 100}%`, top: 0, bottom: 0, width: 1, background: "rgba(255,255,255,0.3)" }} />
      ))}
    </div>
    <span style={{ fontSize: 11, color: "#aaa", fontFamily: "monospace", fontWeight: 600, minWidth: 40 }}>{max}°C</span>
  </div>
);

const ColormapSelector = ({ value, onChange }) => {
  const colormaps = [
    { id: "ironbow", label: "Ironbow", colors: ["#000030", "#ff0000", "#ffff00", "#ffffff"] },
    { id: "rainbow", label: "Rainbow", colors: ["#0000ff", "#00ffff", "#00ff00", "#ffff00", "#ff0000"] },
    { id: "grayscale", label: "Grayscale", colors: ["#000000", "#808080", "#ffffff"] },
    { id: "thermal", label: "Thermal", colors: ["#000000", "#ff0000", "#ffff00", "#ffffff"] },
  ];
  
  return (
    <div style={{ display: "flex", gap: 8 }}>
      {colormaps.map(cm => (
        <button
          key={cm.id}
          onClick={() => onChange(cm.id)}
          style={{
            padding: "6px 14px",
            border: value === cm.id ? "2px solid #00F0FF" : "2px solid rgba(255,255,255,0.15)",
            borderRadius: 6,
            background: value === cm.id ? "rgba(0,240,255,0.15)" : "transparent",
            color: value === cm.id ? "#00F0FF" : "#888",
            fontSize: 11,
            fontWeight: 700,
            fontFamily: "inherit",
            cursor: "pointer",
            transition: "all 0.2s",
            display: "flex",
            alignItems: "center",
            gap: 6
          }}
        >
          <div style={{ display: "flex", gap: 1 }}>
            {cm.colors.map((c, i) => (
              <div key={i} style={{ width: 8, height: 8, borderRadius: 2, background: c }} />
            ))}
          </div>
          {cm.label}
        </button>
      ))}
    </div>
  );
};

// Main component - use your existing SolarThermalInspector with these enhancements:
// 1. Add colormap state: const [colormap, setColormap] = useState("ironbow");
// 2. Add showGridLabels state: const [showGridLabels, setShowGridLabels] = useState(false);
// 3. Add autoRefresh state: const [autoRefresh, setAutoRefresh] = useState(false);
// 4. Pass these props to the enhanced components
// 5. Add CSS animations in a <style> tag

export default function SolarThermalInspector() {
  // Use your existing component logic
  // Just replace the components with the enhanced versions above
  
  const [colormap, setColormap] = useState("ironbow");
  const [showGridLabels, setShowGridLabels] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  
  // ... rest of your existing component code
  
  return (
    <div style={{
      background: "linear-gradient(135deg, #08080C 0%, #0f0f1a 100%)",
      color: "#E8E8ED", 
      minHeight: "100vh",
      fontFamily: "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace",
    }}>
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.7; transform: scale(1.1); }
        }
      `}</style>
      
      {/* Use your existing JSX, just: */}
      {/* 1. Replace ThermalCanvas with enhanced version */}
      {/* 2. Replace SeverityBadge with animated version */}
      {/* 3. Replace StatCard with hover effects version */}
      {/* 4. Add ColormapSelector component */}
      {/* 5. Add settings toggles for showGridLabels and autoRefresh */}
      
      {/* Your existing content */}
    </div>
  );
}
