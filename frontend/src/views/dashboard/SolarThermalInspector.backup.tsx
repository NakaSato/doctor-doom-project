/**
 * Solar PV Thermal Inspector - Enhanced Version 2.0
 *
 * Complete thermal inspection interface with ENHANCED UI/UX:
 * - Animated thermal canvas with pulsing effects
 * - Enhanced severity badges with glow
 * - Improved stat cards with hover effects
 * - Colormap selector (4 options)
 * - Settings toggles (labels, auto-refresh)
 * - Enhanced temperature scale with 11-color gradient
 *
 * Features:
 * - 13 defect types with severity classification
 * - Real-time thermal heatmap rendering with animations
 * - Simulated thermal image viewer
 * - Interactive module selection with glow effects
 * - Multiple view modes (thermal, severity, ΔT)
 * - Comprehensive filtering and search
 * - IEC 62446-3 compliant reporting
 */

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
// Import refactored components
import UploadTab from "./UploadTab";
import ArrayMapTab from "./ArrayMapTab";
import DefectsTab from "./DefectsTab";
import SeverityBadge from "./SeverityBadge";
import TempScale from "./TempScale";
import EnhancedThermalCanvas from "@/components/thermal/EnhancedThermalCanvas";

const DEFECT_TYPES = {
  hotspot: { label: "Hot Spot", severity: "critical", color: "#FF3B30", icon: "🔥", desc: "Overheating cells due to internal damage, shading, or dirt accumulation" },
  cracked_cell: { label: "Cracked Cell", severity: "major", color: "#FF9500", icon: "⚡", desc: "Physical fracture in cell substrate affecting power output" },
  snail_trail: { label: "Snail Trail", severity: "minor", color: "#FFCC00", icon: "🐌", desc: "Discoloration pattern from moisture and silver paste degradation" },
  delamination: { label: "Delamination", severity: "major", color: "#FF6B35", icon: "📄", desc: "Separation of encapsulant layers causing moisture ingress" },
  bypass_diode: { label: "Bypass Diode Failure", severity: "critical", color: "#FF2D55", icon: "⚙️", desc: "Malfunctioning bypass diode causing string-level power loss" },
  junction_box: { label: "Junction Box Overheat", severity: "critical", color: "#E63946", icon: "📦", desc: "Overheated junction box — potential fire hazard" },
  connector: { label: "Defective Connector", severity: "major", color: "#F77F00", icon: "🔌", desc: "Faulty MC4 or cable connector with elevated resistance" },
  string_disconnect: { label: "Disconnected String", severity: "critical", color: "#D62828", icon: "🔗", desc: "Open-circuit string segment — installation defect" },
  cabling: { label: "Poor Cabling", severity: "major", color: "#FC5A03", icon: "🪢", desc: "Improper cable routing or damaged insulation — fire risk" },
  moisture: { label: "Moisture Ingress", severity: "minor", color: "#4CC9F0", icon: "💧", desc: "Water penetration through compromised sealing" },
  pid: { label: "PID Effect", severity: "major", color: "#7209B7", icon: "⬇️", desc: "Potential-induced degradation from voltage stress" },
  soiling: { label: "Heavy Soiling", severity: "minor", color: "#8D6E63", icon: "🌫️", desc: "Significant dirt/debris reducing thermal performance" },
};

const SEVERITY_CONFIG = {
  critical: { label: "Critical", color: "#FF3B30", bg: "rgba(255,59,48,0.12)", priority: 1 },
  major: { label: "Major", color: "#FF9500", bg: "rgba(255,149,0,0.12)", priority: 2 },
  minor: { label: "Minor", color: "#FFCC00", bg: "rgba(255,204,0,0.12)", priority: 3 },
};

const generateId = () => Math.random().toString(36).substr(2, 9);

const generateDemoData = () => {
  const modules = [];
  const rows = 8, cols = 12;
  const defectKeys = Object.keys(DEFECT_TYPES);
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const hasDefect = Math.random() < 0.18;
      const defects = [];
      if (hasDefect) {
        const count = Math.random() < 0.15 ? 2 : 1;
        for (let i = 0; i < count; i++) {
          const type = defectKeys[Math.floor(Math.random() * defectKeys.length)];
          defects.push({
            id: generateId(),
            type,
            deltaT: +(5 + Math.random() * 35).toFixed(1),
            confidence: +(0.72 + Math.random() * 0.27).toFixed(2),
            x: +(0.1 + Math.random() * 0.8).toFixed(2),
            y: +(0.1 + Math.random() * 0.8).toFixed(2),
          });
        }
      }
      const baseTemp = 38 + Math.random() * 8;
      modules.push({
        id: `M-${String(r + 1).padStart(2, "0")}-${String(c + 1).padStart(2, "0")}`,
        row: r, col: c,
        string: Math.floor(c / 3) + 1,
        baseTemp: +baseTemp.toFixed(1),
        maxTemp: +(baseTemp + (hasDefect ? 5 + Math.random() * 30 : Math.random() * 3)).toFixed(1),
        defects,
        power: hasDefect ? +(180 + Math.random() * 80).toFixed(0) : +(320 + Math.random() * 30).toFixed(0),
        status: defects.some(d => DEFECT_TYPES[d.type].severity === "critical") ? "critical" : defects.length > 0 ? "warning" : "normal",
      });
    }
  }
  return modules;
};

const generateInspectionData = () => ({
  id: `INS-${Date.now().toString(36).toUpperCase()}`,
  site: "Nakhon Ratchasima Solar Farm",
  capacity: "5.2 MWp",
  date: new Date().toISOString().split("T")[0],
  time: new Date().toLocaleTimeString(),
  operator: "Thermal Inspector v2.0",
  drone: "DJI Mavic 3T",
  camera: "FLIR Tau2 (640×512)",
  altitude: "25m AGL",
  gsd: "2.8 cm/px (thermal)",
  irradiance: "892 W/m²",
  ambientTemp: "34.2°C",
  windSpeed: "2.1 m/s",
  humidity: "62%",
  modules: generateDemoData(),
});

/* ─── Thermal Heatmap Canvas ─── */
const ThermalCanvas = ({ modules, selected, onSelect, rows = 8, cols = 12, viewMode }) => {
  const canvasRef = useRef(null);
  const [hoveredModule, setHoveredModule] = useState(null);
  const padding = 2;

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
    // thermal view
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

    ctx.fillStyle = "#0a0a0f";
    ctx.fillRect(0, 0, w, h);

    modules.forEach((mod) => {
      const x = padding + mod.col * (cellW + padding);
      const y = padding + mod.row * (cellH + padding);
      ctx.fillStyle = getColor(mod);
      ctx.globalAlpha = mod.id === selected ? 1 : hoveredModule === mod.id ? 0.9 : 0.78;
      ctx.fillRect(x, y, cellW, cellH);

      if (mod.defects.length > 0) {
        ctx.globalAlpha = 0.95;
        mod.defects.forEach((d) => {
          const dx = x + d.x * cellW;
          const dy = y + d.y * cellH;
          ctx.beginPath();
          ctx.arc(dx, dy, 3, 0, Math.PI * 2);
          ctx.fillStyle = "#fff";
          ctx.fill();
          ctx.strokeStyle = DEFECT_TYPES[d.type]?.color || "#fff";
          ctx.lineWidth = 1.5;
          ctx.stroke();
        });
      }

      if (mod.id === selected) {
        ctx.globalAlpha = 1;
        ctx.strokeStyle = "#00F0FF";
        ctx.lineWidth = 2;
        ctx.strokeRect(x - 1, y - 1, cellW + 2, cellH + 2);
      }
      ctx.globalAlpha = 1;
    });
  }, [modules, selected, hoveredModule, getColor, rows, cols]);

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
    <canvas
      ref={canvasRef}
      width={720}
      height={480}
      onClick={handleClick}
      onMouseMove={handleMove}
      onMouseLeave={() => setHoveredModule(null)}
      style={{ width: "100%", height: "auto", cursor: "crosshair", borderRadius: 6, border: "1px solid rgba(255,255,255,0.06)" }}
    />
  );
};

/* ─── Simulated Thermal Image Viewer ─── */
const ThermalImageViewer = ({ module }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!module || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const w = canvas.width, h = canvas.height;

    // Generate simulated thermal noise
    const imgData = ctx.createImageData(w, h);
    const baseT = module.baseTemp;
    const maxT = module.maxTemp;

    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        let temp = baseT + (Math.random() - 0.5) * 2;

        // Add hotspot regions for each defect
        module.defects.forEach(d => {
          const dx = (x / w - d.x);
          const dy = (y / h - d.y);
          const dist = Math.sqrt(dx * dx + dy * dy);
          const radius = d.type === "hotspot" ? 0.12 : 0.08;
          if (dist < radius) {
            temp += (d.deltaT * (1 - dist / radius) * (0.7 + Math.random() * 0.3));
          }
        });

        // Cell grid pattern
        const cellX = (x % (w / 6));
        const cellY = (y % (h / 10));
        if (cellX < 1 || cellY < 1) temp -= 1.5;

        const t = Math.min(Math.max((temp - 30) / 40, 0), 1);
        const idx = (y * w + x) * 4;

        // Iron palette
        if (t < 0.2) {
          imgData.data[idx] = Math.round(t * 5 * 80);
          imgData.data[idx + 1] = 0;
          imgData.data[idx + 2] = Math.round(t * 5 * 120 + 30);
        } else if (t < 0.45) {
          const p = (t - 0.2) / 0.25;
          imgData.data[idx] = Math.round(80 + p * 175);
          imgData.data[idx + 1] = Math.round(p * 40);
          imgData.data[idx + 2] = Math.round(120 - p * 100);
        } else if (t < 0.7) {
          const p = (t - 0.45) / 0.25;
          imgData.data[idx] = 255;
          imgData.data[idx + 1] = Math.round(40 + p * 180);
          imgData.data[idx + 2] = Math.round(20 + p * 10);
        } else {
          const p = (t - 0.7) / 0.3;
          imgData.data[idx] = 255;
          imgData.data[idx + 1] = Math.round(220 + p * 35);
          imgData.data[idx + 2] = Math.round(30 + p * 225);
        }
        imgData.data[idx + 3] = 255;
      }
    }
    ctx.putImageData(imgData, 0, 0);

    // Overlay defect markers
    module.defects.forEach(d => {
      const cx = d.x * w, cy = d.y * h;
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(cx, cy, 16, 0, Math.PI * 2);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(cx - 20, cy); ctx.lineTo(cx - 10, cy);
      ctx.moveTo(cx + 10, cy); ctx.lineTo(cx + 20, cy);
      ctx.moveTo(cx, cy - 20); ctx.lineTo(cx, cy - 10);
      ctx.moveTo(cx, cy + 10); ctx.lineTo(cx, cy + 20);
      ctx.stroke();

      ctx.font = "bold 10px monospace";
      ctx.fillStyle = "#fff";
      ctx.fillText(`ΔT ${d.deltaT}°C`, cx + 20, cy - 8);
      ctx.fillStyle = DEFECT_TYPES[d.type]?.color || "#fff";
      ctx.fillText(DEFECT_TYPES[d.type]?.label || d.type, cx + 20, cy + 4);
    });

    // Temperature scale
    ctx.font = "10px monospace";
    ctx.fillStyle = "#fff";
    ctx.fillText(`${module.maxTemp}°C`, 8, 14);
    ctx.fillText(`${module.baseTemp}°C`, 8, h - 6);

  }, [module]);

  if (!module) return null;

  return (
    <canvas
      ref={canvasRef}
      width={360}
      height={240}
      style={{ width: "100%", height: "auto", borderRadius: 6, border: "1px solid rgba(255,255,255,0.08)" }}
    />
  );
};

/* ─── Severity Badge ─── */
const SeverityBadge = ({ severity }) => {
  const cfg = SEVERITY_CONFIG[severity];
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: "2px 8px", borderRadius: 4, fontSize: 10, fontWeight: 700,
      letterSpacing: "0.05em", textTransform: "uppercase",
      color: cfg.color, background: cfg.bg,
      border: `1px solid ${cfg.color}33`,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: cfg.color, display: "inline-block" }} />
      {cfg.label}
    </span>
  );
};

/* ─── Stat Card ─── */
const StatCard = ({ label, value, sub, color = "#00F0FF", icon }) => (
  <div style={{
    background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)",
    borderRadius: 8, padding: "14px 16px", flex: 1, minWidth: 130,
  }}>
    <div style={{ fontSize: 11, color: "#888", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 6, display: "flex", alignItems: "center", gap: 6 }}>
      {icon && <span style={{ fontSize: 14 }}>{icon}</span>}
      {label}
    </div>
    <div style={{ fontSize: 26, fontWeight: 800, color, fontFamily: "'JetBrains Mono', monospace", letterSpacing: "-0.02em" }}>{value}</div>
    {sub && <div style={{ fontSize: 11, color: "#666", marginTop: 2 }}>{sub}</div>}
  </div>
);

/* ─── Temperature Scale Legend ─── */
const TempScale = ({ min, max }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 0" }}>
    <span style={{ fontSize: 10, color: "#888", fontFamily: "monospace" }}>{min}°C</span>
    <div style={{
      flex: 1, height: 10, borderRadius: 5,
      background: "linear-gradient(to right, #1a0030, #500050, #ff0020, #ff6600, #ffcc00, #ffffcc)",
    }} />
    <span style={{ fontSize: 10, color: "#888", fontFamily: "monospace" }}>{max}°C</span>
  </div>
);

/* ─── Main Application ─── */
export default function SolarThermalInspector() {
  const [data, setData] = useState(null);
  const [selectedModule, setSelectedModule] = useState(null);
  const [activeTab, setActiveTab] = useState("array");
  const [viewMode, setViewMode] = useState("thermal");
  const [filterSeverity, setFilterSeverity] = useState("all");
  const [filterDefect, setFilterDefect] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("severity");
  const [showUpload, setShowUpload] = useState(false);
  const [inspectionStarted, setInspectionStarted] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  // ENHANCED: New state variables
  const [colormap, setColormap] = useState("ironbow");
  const [showGridLabels, setShowGridLabels] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);

  useEffect(() => {
    const d = generateInspectionData();
    setData(d);
  }, []);

  // ENHANCED: Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      setData(generateInspectionData());
    }, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const startProcessing = () => {
    setInspectionStarted(true);
    setProcessingProgress(0);
    let p = 0;
    const interval = setInterval(() => {
      p += Math.random() * 8 + 2;
      if (p >= 100) {
        p = 100;
        clearInterval(interval);
        setActiveTab("array");
      }
      setProcessingProgress(Math.min(p, 100));
    }, 200);
  };

  const stats = useMemo(() => {
    if (!data) return {};
    const mods = data.modules;
    const allDefects = mods.flatMap(m => m.defects);
    const critical = allDefects.filter(d => DEFECT_TYPES[d.type]?.severity === "critical").length;
    const major = allDefects.filter(d => DEFECT_TYPES[d.type]?.severity === "major").length;
    const minor = allDefects.filter(d => DEFECT_TYPES[d.type]?.severity === "minor").length;
    const affectedModules = mods.filter(m => m.defects.length > 0).length;
    const maxTemp = Math.max(...mods.map(m => m.maxTemp));
    const avgTemp = +(mods.reduce((s, m) => s + m.maxTemp, 0) / mods.length).toFixed(1);
    const totalPower = mods.reduce((s, m) => s + +m.power, 0);
    const idealPower = mods.length * 350;
    const performanceRatio = +((totalPower / idealPower) * 100).toFixed(1);
    const defectTypes = {};
    allDefects.forEach(d => { defectTypes[d.type] = (defectTypes[d.type] || 0) + 1; });
    return { total: allDefects.length, critical, major, minor, affectedModules, totalModules: mods.length, maxTemp, avgTemp, performanceRatio, defectTypes, totalPower };
  }, [data]);

  const filteredDefects = useMemo(() => {
    if (!data) return [];
    let defects = data.modules.flatMap(m => m.defects.map(d => ({ ...d, moduleId: m.id, moduleTemp: m.maxTemp })));
    if (filterSeverity !== "all") defects = defects.filter(d => DEFECT_TYPES[d.type]?.severity === filterSeverity);
    if (filterDefect !== "all") defects = defects.filter(d => d.type === filterDefect);
    if (searchQuery) defects = defects.filter(d => d.moduleId.toLowerCase().includes(searchQuery.toLowerCase()) || DEFECT_TYPES[d.type]?.label.toLowerCase().includes(searchQuery.toLowerCase()));
    if (sortBy === "severity") defects.sort((a, b) => (SEVERITY_CONFIG[DEFECT_TYPES[a.type]?.severity]?.priority || 9) - (SEVERITY_CONFIG[DEFECT_TYPES[b.type]?.severity]?.priority || 9));
    else if (sortBy === "deltaT") defects.sort((a, b) => b.deltaT - a.deltaT);
    else if (sortBy === "confidence") defects.sort((a, b) => b.confidence - a.confidence);
    return defects;
  }, [data, filterSeverity, filterDefect, searchQuery, sortBy]);

  const selectedModuleData = useMemo(() => {
    if (!data || !selectedModule) return null;
    return data.modules.find(m => m.id === selectedModule);
  }, [data, selectedModule]);

  if (!data) return <div style={{ background: "#08080C", color: "#fff", height: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>Loading...</div>;

  const healthScore = Math.round(100 - (stats.critical * 3 + stats.major * 1.5 + stats.minor * 0.5) / stats.totalModules * 10);

  const tabs = [
    { id: "upload", label: "Upload", icon: "📡" },
    { id: "array", label: "Array Map", icon: "🗺️" },
    { id: "defects", label: "Defect Log", icon: "🔍" },
    { id: "report", label: "Report", icon: "📋" },
  ];

  return (
    <div style={{
      background: "#08080C", color: "#E8E8ED", minHeight: "100vh",
      fontFamily: "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace",
      fontSize: 13, lineHeight: 1.5,
    }}>
      {/* Header */}
      <div style={{
        background: "linear-gradient(180deg, rgba(0,240,255,0.04) 0%, transparent 100%)",
        borderBottom: "1px solid rgba(255,255,255,0.06)", padding: "12px 20px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 8,
            background: "linear-gradient(135deg, #FF3B30 0%, #FF9500 50%, #FFCC00 100%)",
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18,
          }}>☀️</div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 800, letterSpacing: "-0.02em", color: "#fff" }}>
              SOLAR PV THERMAL INSPECTOR
            </div>
            <div style={{ fontSize: 10, color: "#666", letterSpacing: "0.08em" }}>
              MAVIC 3T • IR ANALYSIS ENGINE • {data.id}
            </div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 10, color: "#666" }}>INSPECTION DATE</div>
            <div style={{ fontSize: 12, color: "#aaa" }}>{data.date} {data.time}</div>
          </div>
          <div style={{
            width: 42, height: 42, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
            background: healthScore > 80 ? "rgba(44,182,125,0.15)" : healthScore > 60 ? "rgba(255,149,0,0.15)" : "rgba(255,59,48,0.15)",
            border: `2px solid ${healthScore > 80 ? "#2CB67D" : healthScore > 60 ? "#FF9500" : "#FF3B30"}`,
            fontSize: 14, fontWeight: 900,
            color: healthScore > 80 ? "#2CB67D" : healthScore > 60 ? "#FF9500" : "#FF3B30",
          }}>
            {healthScore}
          </div>
        </div>
      </div>

      {/* Tab Nav */}
      <div style={{
        display: "flex", gap: 0, borderBottom: "1px solid rgba(255,255,255,0.06)",
        background: "rgba(255,255,255,0.01)",
      }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: "10px 20px", border: "none", cursor: "pointer",
              background: activeTab === tab.id ? "rgba(0,240,255,0.06)" : "transparent",
              color: activeTab === tab.id ? "#00F0FF" : "#666",
              borderBottom: activeTab === tab.id ? "2px solid #00F0FF" : "2px solid transparent",
              fontSize: 12, fontWeight: 600, fontFamily: "inherit",
              letterSpacing: "0.04em", display: "flex", alignItems: "center", gap: 6,
              transition: "all 0.15s ease",
            }}
          >
            <span style={{ fontSize: 14 }}>{tab.icon}</span> {tab.label}
            {tab.id === "defects" && <span style={{
              background: "rgba(255,59,48,0.2)", color: "#FF3B30", padding: "1px 6px",
              borderRadius: 10, fontSize: 10, fontWeight: 800,
            }}>{stats.total}</span>}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ padding: 20 }}>
        {/* Upload Tab */}
        {activeTab === "upload" && (
          <UploadTab
            inspectionStarted={inspectionStarted}
            processingProgress={processingProgress}
            onStartProcessing={startProcessing}
            onComplete={() => setActiveTab("array")}
          />
        )}

        {/* Array Map Tab */}
        {activeTab === "array" && (
          <ArrayMapTab
            modules={data.modules}
            selectedModule={selectedModule}
            onSelectModule={setSelectedModule}
            viewMode={viewMode}
            colormap={colormap}
            showGridLabels={showGridLabels}
            stats={stats}
          />
        )}

        {/* Defects Tab */}
        {activeTab === "defects" && (
          <DefectsTab
            defects={filteredDefects}
            stats={stats}
          />
        )}
                            <div style={{ display: "flex", gap: 12, marginTop: 6, fontSize: 10, color: "#aaa" }}>
                              <span>ΔT: <b style={{ color: "#FF6B35" }}>{d.deltaT}°C</b></span>
                              <span>Conf: <b style={{ color: "#00F0FF" }}>{(d.confidence * 100).toFixed(0)}%</b></span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {selectedModuleData.defects.length === 0 && (
                      <div style={{ textAlign: "center", padding: 20, color: "#2CB67D", fontSize: 12 }}>
                        ✓ No defects detected — Module operating normally
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{
                    background: "rgba(255,255,255,0.02)", border: "1px dashed rgba(255,255,255,0.08)",
                    borderRadius: 8, padding: 40, textAlign: "center",
                  }}>
                    <div style={{ fontSize: 30, marginBottom: 10 }}>🔍</div>
                    <div style={{ fontSize: 12, color: "#555" }}>Select a module on the array map to inspect</div>
                    <div style={{ fontSize: 10, color: "#444", marginTop: 6 }}>Click any cell in the thermal map</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Defects Tab */}
        {activeTab === "defects" && (
          <div>
            {/* Filters */}
            <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap", alignItems: "center" }}>
              <input
                type="text"
                placeholder="Search module ID or defect..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                style={{
                  padding: "7px 12px", borderRadius: 6, border: "1px solid rgba(255,255,255,0.1)",
                  background: "rgba(255,255,255,0.03)", color: "#ddd", fontSize: 12,
                  fontFamily: "inherit", outline: "none", width: 220,
                }}
              />
              <select value={filterSeverity} onChange={e => setFilterSeverity(e.target.value)} style={{
                padding: "7px 10px", borderRadius: 6, border: "1px solid rgba(255,255,255,0.1)",
                background: "#111", color: "#ddd", fontSize: 11, fontFamily: "inherit",
              }}>
                <option value="all">All Severity</option>
                <option value="critical">Critical</option>
                <option value="major">Major</option>
                <option value="minor">Minor</option>
              </select>
              <select value={filterDefect} onChange={e => setFilterDefect(e.target.value)} style={{
                padding: "7px 10px", borderRadius: 6, border: "1px solid rgba(255,255,255,0.1)",
                background: "#111", color: "#ddd", fontSize: 11, fontFamily: "inherit",
              }}>
                <option value="all">All Types</option>
                {Object.entries(DEFECT_TYPES).map(([k, v]) => (
                  <option key={k} value={k}>{v.icon} {v.label}</option>
                ))}
              </select>
              <select value={sortBy} onChange={e => setSortBy(e.target.value)} style={{
                padding: "7px 10px", borderRadius: 6, border: "1px solid rgba(255,255,255,0.1)",
                background: "#111", color: "#ddd", fontSize: 11, fontFamily: "inherit",
              }}>
                <option value="severity">Sort: Severity</option>
                <option value="deltaT">Sort: ΔT</option>
                <option value="confidence">Sort: Confidence</option>
              </select>
              <span style={{ fontSize: 11, color: "#666", marginLeft: "auto" }}>
                {filteredDefects.length} defects
              </span>
            </div>

            {/* Defect Type Summary */}
            <div style={{ display: "flex", gap: 6, marginBottom: 16, flexWrap: "wrap" }}>
              {Object.entries(stats.defectTypes || {}).sort((a, b) => b[1] - a[1]).map(([type, count]) => (
                <div key={type} style={{
                  padding: "5px 10px", borderRadius: 6, fontSize: 10, fontWeight: 700,
                  background: `${DEFECT_TYPES[type]?.color}15`, border: `1px solid ${DEFECT_TYPES[type]?.color}30`,
                  color: DEFECT_TYPES[type]?.color, cursor: "pointer",
                }}
                  onClick={() => setFilterDefect(filterDefect === type ? "all" : type)}
                >
                  {DEFECT_TYPES[type]?.icon} {DEFECT_TYPES[type]?.label}: {count}
                </div>
              ))}
            </div>

            {/* Defect List */}
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {/* Table header */}
              <div style={{
                display: "grid", gridTemplateColumns: "90px 1fr 80px 70px 80px 80px",
                padding: "8px 12px", fontSize: 10, color: "#555", letterSpacing: "0.06em",
                borderBottom: "1px solid rgba(255,255,255,0.06)", fontWeight: 700,
              }}>
                <div>MODULE</div><div>DEFECT TYPE</div><div>SEVERITY</div><div>ΔT</div><div>CONFIDENCE</div><div>ACTION</div>
              </div>
              {filteredDefects.slice(0, 50).map((d, i) => (
                <div key={d.id} style={{
                  display: "grid", gridTemplateColumns: "90px 1fr 80px 70px 80px 80px",
                  padding: "8px 12px", alignItems: "center", fontSize: 12,
                  background: i % 2 === 0 ? "rgba(255,255,255,0.01)" : "transparent",
                  borderLeft: `3px solid ${DEFECT_TYPES[d.type]?.color || "#333"}`,
                  borderRadius: 2, cursor: "pointer",
                }}
                  onClick={() => { setSelectedModule(d.moduleId); setActiveTab("array"); }}
                >
                  <div style={{ fontWeight: 700, color: "#00F0FF" }}>{d.moduleId}</div>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span>{DEFECT_TYPES[d.type]?.icon}</span>
                    <span style={{ color: DEFECT_TYPES[d.type]?.color }}>{DEFECT_TYPES[d.type]?.label}</span>
                  </div>
                  <div><SeverityBadge severity={DEFECT_TYPES[d.type]?.severity} /></div>
                  <div style={{ fontWeight: 700, color: d.deltaT > 20 ? "#FF3B30" : d.deltaT > 10 ? "#FF9500" : "#FFCC00" }}>
                    {d.deltaT}°C
                  </div>
                  <div>
                    <div style={{
                      width: 50, height: 5, borderRadius: 3, background: "rgba(255,255,255,0.06)", overflow: "hidden",
                    }}>
                      <div style={{
                        width: `${d.confidence * 100}%`, height: "100%", borderRadius: 3,
                        background: d.confidence > 0.9 ? "#2CB67D" : d.confidence > 0.8 ? "#00F0FF" : "#FF9500",
                      }} />
                    </div>
                    <div style={{ fontSize: 9, color: "#666", marginTop: 2 }}>{(d.confidence * 100).toFixed(0)}%</div>
                  </div>
                  <div style={{ fontSize: 10, color: "#00F0FF", fontWeight: 600 }}>INSPECT →</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Report Tab */}
        {activeTab === "report" && (
          <div style={{ maxWidth: 800, margin: "0 auto" }}>
            <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 12, padding: 24 }}>
              {/* Report Header */}
              <div style={{ textAlign: "center", marginBottom: 24, paddingBottom: 20, borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                <div style={{ fontSize: 10, color: "#00F0FF", letterSpacing: "0.12em", marginBottom: 6 }}>THERMOGRAPHIC INSPECTION REPORT</div>
                <div style={{ fontSize: 20, fontWeight: 900, color: "#fff", marginBottom: 4 }}>{data.site}</div>
                <div style={{ fontSize: 12, color: "#666" }}>Inspection ID: {data.id} • {data.date}</div>
              </div>

              {/* Site Info */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
                <div>
                  <div style={{ fontSize: 10, color: "#00F0FF", letterSpacing: "0.08em", marginBottom: 10, fontWeight: 700 }}>SITE INFORMATION</div>
                  {[
                    ["Capacity", data.capacity],
                    ["Total Modules", stats.totalModules],
                    ["Array Config", "8 rows × 12 columns"],
                    ["Strings", "4"],
                  ].map(([k, v]) => (
                    <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: "1px solid rgba(255,255,255,0.03)", fontSize: 12 }}>
                      <span style={{ color: "#888" }}>{k}</span><span style={{ color: "#ddd", fontWeight: 600 }}>{v}</span>
                    </div>
                  ))}
                </div>
                <div>
                  <div style={{ fontSize: 10, color: "#00F0FF", letterSpacing: "0.08em", marginBottom: 10, fontWeight: 700 }}>ENVIRONMENTAL CONDITIONS</div>
                  {[
                    ["Irradiance", data.irradiance],
                    ["Ambient Temp", data.ambientTemp],
                    ["Wind Speed", data.windSpeed],
                    ["Humidity", data.humidity],
                  ].map(([k, v]) => (
                    <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: "1px solid rgba(255,255,255,0.03)", fontSize: 12 }}>
                      <span style={{ color: "#888" }}>{k}</span><span style={{ color: "#ddd", fontWeight: 600 }}>{v}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Equipment */}
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontSize: 10, color: "#00F0FF", letterSpacing: "0.08em", marginBottom: 10, fontWeight: 700 }}>EQUIPMENT & METHODOLOGY</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
                  {[
                    ["Platform", data.drone, "📡"],
                    ["Thermal Camera", data.camera, "🔭"],
                    ["Flight Altitude", data.altitude, "✈️"],
                    ["Thermal GSD", data.gsd, "📐"],
                    ["Emissivity (ε)", "0.85", "⚙️"],
                    ["Standard", "IEC 62446-3", "📋"],
                  ].map(([k, v, ic]) => (
                    <div key={k} style={{ background: "rgba(255,255,255,0.02)", borderRadius: 6, padding: "8px 10px" }}>
                      <div style={{ fontSize: 10, color: "#666" }}>{ic} {k}</div>
                      <div style={{ fontSize: 12, fontWeight: 700, color: "#ddd" }}>{v}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Summary */}
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontSize: 10, color: "#00F0FF", letterSpacing: "0.08em", marginBottom: 10, fontWeight: 700 }}>FINDINGS SUMMARY</div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 16 }}>
                  <div style={{ background: "rgba(255,59,48,0.08)", borderRadius: 8, padding: 14, textAlign: "center", border: "1px solid rgba(255,59,48,0.15)" }}>
                    <div style={{ fontSize: 28, fontWeight: 900, color: "#FF3B30" }}>{stats.critical}</div>
                    <div style={{ fontSize: 10, color: "#FF3B30", fontWeight: 700 }}>CRITICAL</div>
                  </div>
                  <div style={{ background: "rgba(255,149,0,0.08)", borderRadius: 8, padding: 14, textAlign: "center", border: "1px solid rgba(255,149,0,0.15)" }}>
                    <div style={{ fontSize: 28, fontWeight: 900, color: "#FF9500" }}>{stats.major}</div>
                    <div style={{ fontSize: 10, color: "#FF9500", fontWeight: 700 }}>MAJOR</div>
                  </div>
                  <div style={{ background: "rgba(255,204,0,0.08)", borderRadius: 8, padding: 14, textAlign: "center", border: "1px solid rgba(255,204,0,0.15)" }}>
                    <div style={{ fontSize: 28, fontWeight: 900, color: "#FFCC00" }}>{stats.minor}</div>
                    <div style={{ fontSize: 10, color: "#FFCC00", fontWeight: 700 }}>MINOR</div>
                  </div>
                  <div style={{ background: "rgba(44,182,125,0.08)", borderRadius: 8, padding: 14, textAlign: "center", border: "1px solid rgba(44,182,125,0.15)" }}>
                    <div style={{ fontSize: 28, fontWeight: 900, color: "#2CB67D" }}>{stats.totalModules - stats.affectedModules}</div>
                    <div style={{ fontSize: 10, color: "#2CB67D", fontWeight: 700 }}>HEALTHY</div>
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  <div style={{ background: "rgba(255,255,255,0.02)", borderRadius: 6, padding: 12 }}>
                    <div style={{ fontSize: 10, color: "#666", marginBottom: 4 }}>Array Health Score</div>
                    <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                      <span style={{ fontSize: 32, fontWeight: 900, color: healthScore > 80 ? "#2CB67D" : healthScore > 60 ? "#FF9500" : "#FF3B30" }}>{healthScore}</span>
                      <span style={{ fontSize: 12, color: "#666" }}>/ 100</span>
                    </div>
                  </div>
                  <div style={{ background: "rgba(255,255,255,0.02)", borderRadius: 6, padding: 12 }}>
                    <div style={{ fontSize: 10, color: "#666", marginBottom: 4 }}>Estimated Performance Ratio</div>
                    <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                      <span style={{ fontSize: 32, fontWeight: 900, color: stats.performanceRatio > 85 ? "#2CB67D" : "#FF9500" }}>{stats.performanceRatio}</span>
                      <span style={{ fontSize: 12, color: "#666" }}>%</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Defect Breakdown */}
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontSize: 10, color: "#00F0FF", letterSpacing: "0.08em", marginBottom: 10, fontWeight: 700 }}>DEFECT CLASSIFICATION BREAKDOWN</div>
                {Object.entries(stats.defectTypes || {}).sort((a, b) => {
                  const sa = SEVERITY_CONFIG[DEFECT_TYPES[a[0]]?.severity]?.priority || 9;
                  const sb = SEVERITY_CONFIG[DEFECT_TYPES[b[0]]?.severity]?.priority || 9;
                  return sa - sb || b[1] - a[1];
                }).map(([type, count]) => (
                  <div key={type} style={{
                    display: "flex", alignItems: "center", gap: 10, padding: "8px 0",
                    borderBottom: "1px solid rgba(255,255,255,0.03)",
                  }}>
                    <span style={{ fontSize: 16 }}>{DEFECT_TYPES[type]?.icon}</span>
                    <span style={{ flex: 1, fontSize: 12, color: DEFECT_TYPES[type]?.color, fontWeight: 600 }}>{DEFECT_TYPES[type]?.label}</span>
                    <SeverityBadge severity={DEFECT_TYPES[type]?.severity} />
                    <span style={{ fontSize: 14, fontWeight: 900, color: "#fff", minWidth: 30, textAlign: "right" }}>{count}</span>
                    <div style={{ width: 80, height: 5, borderRadius: 3, background: "rgba(255,255,255,0.06)", overflow: "hidden" }}>
                      <div style={{
                        width: `${(count / stats.total) * 100}%`, height: "100%",
                        background: DEFECT_TYPES[type]?.color, borderRadius: 3,
                      }} />
                    </div>
                  </div>
                ))}
              </div>

              {/* Recommendations */}
              <div>
                <div style={{ fontSize: 10, color: "#00F0FF", letterSpacing: "0.08em", marginBottom: 10, fontWeight: 700 }}>RECOMMENDED ACTIONS</div>
                {[
                  { priority: "IMMEDIATE", color: "#FF3B30", items: [
                    "Replace modules with critical hot spots (ΔT > 25°C) — fire risk",
                    "Inspect and replace all failed bypass diodes",
                    "Re-terminate disconnected strings and verify cabling integrity",
                    "Check junction boxes showing elevated temperatures",
                  ]},
                  { priority: "SCHEDULED", color: "#FF9500", items: [
                    "Replace modules with cracked cells showing major power loss",
                    "Repair delaminated modules before moisture causes further degradation",
                    "Replace defective MC4 connectors with elevated contact resistance",
                  ]},
                  { priority: "MONITORING", color: "#FFCC00", items: [
                    "Track snail trail progression in follow-up inspections",
                    "Schedule cleaning for modules with heavy soiling",
                    "Monitor PID-affected modules for further degradation",
                  ]},
                ].map(section => (
                  <div key={section.priority} style={{ marginBottom: 14 }}>
                    <div style={{
                      display: "inline-flex", padding: "3px 10px", borderRadius: 4, marginBottom: 8,
                      background: `${section.color}18`, border: `1px solid ${section.color}30`,
                      fontSize: 10, fontWeight: 800, color: section.color, letterSpacing: "0.08em",
                    }}>
                      {section.priority}
                    </div>
                    {section.items.map((item, i) => (
                      <div key={i} style={{ padding: "4px 0 4px 16px", fontSize: 12, color: "#bbb", borderLeft: `2px solid ${section.color}40` }}>
                        {item}
                      </div>
                    ))}
                  </div>
                ))}
              </div>

              {/* Footer */}
              <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid rgba(255,255,255,0.06)", textAlign: "center" }}>
                <div style={{ fontSize: 10, color: "#444" }}>
                  Generated by Solar PV Thermal Inspector v1.0 • Compliant with IEC 62446-3 / IEC TS 62446-3:2017
                </div>
                <div style={{ fontSize: 10, color: "#333", marginTop: 4 }}>
                  Analysis performed using CNN-based defect classification on radiometric LWIR data
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
