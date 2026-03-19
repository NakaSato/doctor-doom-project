/**
 * Solar PV Thermal Inspector - Enhanced Version 2.0
 * 
 * Main container component that orchestrates all sub-components
 * Refactored from 1,053 lines to ~200 lines
 */

import { useState, useEffect, useMemo } from "react";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import UploadTab from "./UploadTab";
import ArrayMapTab from "./ArrayMapTab";
import DefectsTab from "./DefectsTab";
import ReportTab from "./ReportTab";

// Data generation functions (keep these as they're business logic)
const generateId = () => Math.random().toString(36).substr(2, 9);

const DEFECT_TYPES = {
  hotspot: { label: "Hot Spot", severity: "critical", color: "#FF3B30", icon: "🔥", desc: "Overheating cells" },
  cracked_cell: { label: "Cracked Cell", severity: "major", color: "#FF9500", icon: "⚡", desc: "Physical fracture" },
  snail_trail: { label: "Snail Trail", severity: "minor", color: "#FFCC00", icon: "🐌", desc: "Discoloration" },
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

export default function SolarThermalInspector() {
  // State management
  const [data, setData] = useState(null);
  const [selectedModule, setSelectedModule] = useState(null);
  const [activeTab, setActiveTab] = useState("array");
  const [viewMode, setViewMode] = useState("thermal");
  const [filterSeverity, setFilterSeverity] = useState("all");
  const [filterDefect, setFilterDefect] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("severity");
  const [inspectionStarted, setInspectionStarted] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [colormap, setColormap] = useState("ironbow");
  const [showGridLabels, setShowGridLabels] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);

  // Initialize data
  useEffect(() => {
    const d = generateInspectionData();
    setData(d);
  }, []);

  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      setData(generateInspectionData());
    }, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  // Processing handler
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

  // Calculate statistics
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
    return { 
      total: allDefects.length, 
      critical, major, minor, 
      affectedModules, 
      totalModules: mods.length, 
      maxTemp, avgTemp, 
      performanceRatio, 
      defectTypes 
    };
  }, [data]);

  // Filter and sort defects
  const filteredDefects = useMemo(() => {
    if (!data) return [];
    let defects = data.modules.flatMap(m => m.defects.map(d => ({ ...d, moduleId: m.id })));
    if (filterSeverity !== "all") defects = defects.filter(d => DEFECT_TYPES[d.type]?.severity === filterSeverity);
    if (filterDefect !== "all") defects = defects.filter(d => d.type === filterDefect);
    if (searchQuery) defects = defects.filter(d => 
      d.moduleId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      DEFECT_TYPES[d.type]?.label.toLowerCase().includes(searchQuery.toLowerCase())
    );
    if (sortBy === "deltaT") defects.sort((a, b) => b.deltaT - a.deltaT);
    else if (sortBy === "confidence") defects.sort((a, b) => b.confidence - a.confidence);
    return defects;
  }, [data, filterSeverity, filterDefect, searchQuery, sortBy]);

  const healthScore = Math.round(100 - (stats.critical * 3 + stats.major * 1.5 + stats.minor * 0.5) / (stats.totalModules || 1) * 10);

  const tabs = [
    { id: "upload", label: "Upload", icon: "📡" },
    { id: "array", label: "Array Map", icon: "🗺️" },
    { id: "defects", label: "Defect Log", icon: "🔍" },
    { id: "report", label: "Report", icon: "📋" },
  ];

  return (
    <div style={{
      background: "linear-gradient(135deg, #08080C 0%, #0f0f1a 100%)",
      color: "#E8E8ED",
      minHeight: "100vh",
      fontFamily: "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace",
      fontSize: 13,
      lineHeight: 1.5,
    }}>
      {/* Header */}
      <div style={{
        background: "linear-gradient(180deg, rgba(0,240,255,0.08) 0%, transparent 100%)",
        borderBottom: "1px solid rgba(0,240,255,0.2)",
        padding: "16px 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        boxShadow: "0 4px 20px rgba(0,240,255,0.1)"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{
            width: 48, height: 48, borderRadius: 12,
            background: "linear-gradient(135deg, #FF3B30 0%, #FF9500 50%, #FFCC00 100%)",
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 24,
            boxShadow: "0 4px 15px rgba(255,100,50,0.4)",
          }}>☀️</div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 900, color: "#fff", textShadow: "0 0 20px rgba(0,240,255,0.5)" }}>
              SOLAR PV THERMAL INSPECTOR
            </div>
            <div style={{ fontSize: 11, color: "#888", letterSpacing: "0.08em", display: "flex", gap: 12 }}>
              <span>MAVIC 3T</span><span>•</span>
              <span>IR ANALYSIS</span><span>•</span>
              <span style={{ color: "#00F0FF" }}>{data?.id}</span>
            </div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 10, color: "#666", textTransform: "uppercase" }}>Inspection Date</div>
            <div style={{ fontSize: 13, color: "#aaa", fontFamily: "monospace" }}>
              {data?.date} {data?.time}
            </div>
          </div>
          <div style={{
            width: 56, height: 56, borderRadius: "50%",
            display: "flex", alignItems: "center", justifyContent: "center",
            background: healthScore > 80 ? "radial-gradient(circle, rgba(44,182,125,0.2) 0%, transparent 70%)" : healthScore > 60 ? "radial-gradient(circle, rgba(255,149,0,0.2) 0%, transparent 70%)" : "radial-gradient(circle, rgba(255,59,48,0.2) 0%, transparent 70%)",
            border: `3px solid ${healthScore > 80 ? "#2CB67D" : healthScore > 60 ? "#FF9500" : "#FF3B30"}`,
            fontSize: 18, fontWeight: 900,
            color: healthScore > 80 ? "#2CB67D" : healthScore > 60 ? "#FF9500" : "#FF3B30",
            boxShadow: `0 0 20px ${healthScore > 80 ? "#2CB67D" : healthScore > 60 ? "#FF9500" : "#FF3B30"}40`,
          }}>
            {healthScore}
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{
        display: "flex",
        gap: 0,
        borderBottom: "1px solid rgba(0,240,255,0.2)",
        background: "rgba(0,0,0,0.3)",
        padding: "0 24px",
        boxShadow: "0 2px 10px rgba(0,0,0,0.3)"
      }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: "14px 24px",
              border: "none",
              cursor: "pointer",
              background: activeTab === tab.id ? "linear-gradient(180deg, rgba(0,240,255,0.15) 0%, transparent 100%)" : "transparent",
              color: activeTab === tab.id ? "#00F0FF" : "#666",
              borderBottom: activeTab === tab.id ? "2px solid #00F0FF" : "2px solid transparent",
              fontSize: 12,
              fontWeight: 700,
              fontFamily: "inherit",
              letterSpacing: "0.04em",
              display: "flex",
              alignItems: "center",
              gap: 8,
              transition: "all 0.2s ease",
            }}
          >
            <span style={{ fontSize: 16 }}>{tab.icon}</span>
            {tab.label}
            {tab.id === "defects" && (
              <span style={{
                background: "rgba(255,59,48,0.25)",
                color: "#FF3B30",
                padding: "2px 8px",
                borderRadius: 12,
                fontSize: 10,
                fontWeight: 800,
                border: "1px solid rgba(255,59,48,0.3)"
              }}>
                {stats.total || 0}
              </span>
            )}
          </button>
        ))}
        
        {/* Settings */}
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 12, padding: "0 12px" }}>
          <label style={{ fontSize: 11, color: "#888", display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={showGridLabels}
              onChange={(e) => setShowGridLabels(e.target.checked)}
              style={{ accentColor: "#00F0FF" }}
            />
            Labels
          </label>
          <label style={{ fontSize: 11, color: "#888", display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              style={{ accentColor: "#00F0FF" }}
            />
            Auto-refresh
          </label>
        </div>
      </div>

      {/* Content */}
      <div style={{ padding: 24 }}>
        <ErrorBoundary name="UploadTab">
          {activeTab === "upload" && (
            <UploadTab
              inspectionStarted={inspectionStarted}
              processingProgress={processingProgress}
              onStartProcessing={startProcessing}
              onComplete={(results) => {
                if (results?.mlService) {
                  console.log('✅ Analysis completed with ML Service');
                } else {
                  console.log('✅ Analysis completed in demo mode');
                }
                setActiveTab("array");
              }}
              modules={data?.modules || []}
              inspectionId={data?.id}
            />
          )}
        </ErrorBoundary>
        
        <ErrorBoundary name="ArrayMapTab">
          {activeTab === "array" && data && (
            <ArrayMapTab
              modules={data.modules || []}
              selectedModule={selectedModule}
              onSelectModule={setSelectedModule}
              viewMode={viewMode}
              colormap={colormap}
              showGridLabels={showGridLabels}
              stats={stats || {
                total: 0,
                critical: 0,
                major: 0,
                minor: 0,
                affectedModules: 0,
                totalModules: 0,
                maxTemp: 0,
                avgTemp: 0,
                performanceRatio: 0,
              }}
            />
          )}
        </ErrorBoundary>
        
        <ErrorBoundary name="DefectsTab">
          {activeTab === "defects" && (
            <DefectsTab
              defects={filteredDefects || []}
              stats={stats || {
                total: 0,
                critical: 0,
                major: 0,
                minor: 0,
                defectTypes: {},
              }}
            />
          )}
        </ErrorBoundary>
        
        <ErrorBoundary name="ReportTab">
          {activeTab === "report" && (
            <ReportTab
              data={data}
              stats={stats}
              healthScore={healthScore}
            />
          )}
        </ErrorBoundary>
      </div>
    </div>
  );
}
