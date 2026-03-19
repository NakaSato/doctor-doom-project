/**
 * Array Map Tab Component
 * 
 * Displays thermal map of solar panel array with module inspection
 */

import { useState } from "react";
import EnhancedThermalCanvas from "@/components/thermal/EnhancedThermalCanvas";
import TempScale from "./TempScale";
import ModuleDetail from "./ModuleDetail";

interface Module {
  id: string;
  row: number;
  col: number;
  string: number;
  baseTemp: number;
  maxTemp: number;
  defects: any[];
  power: number;
  status: string;
}

interface ArrayMapTabProps {
  modules: Module[];
  selectedModule: string | null;
  onSelectModule: (id: string) => void;
  viewMode: 'thermal' | 'severity' | 'deltaT';
  colormap: string;
  showGridLabels: boolean;
  stats: {
    total: number;
    critical: number;
    major: number;
    minor: number;
    affectedModules: number;
    totalModules: number;
    maxTemp: number;
    avgTemp: number;
    performanceRatio: number;
  };
}

export default function ArrayMapTab({
  modules,
  selectedModule,
  onSelectModule,
  viewMode,
  colormap,
  showGridLabels,
  stats,
}: ArrayMapTabProps) {
  return (
    <div>
      {/* Stats Row */}
      <div style={{
        display: "flex",
        gap: 12,
        marginBottom: 24,
        flexWrap: "wrap",
        padding: "20px",
        background: "rgba(0,0,0,0.3)",
        borderRadius: 12,
        border: "1px solid rgba(255,255,255,0.05)"
      }}>
        <StatCard label="Total Defects" value={stats.total} icon="🔍" color="#FF3B30" sub={`${stats.affectedModules}/${stats.totalModules} modules`} />
        <StatCard label="Critical" value={stats.critical} icon="🚨" color="#FF3B30" />
        <StatCard label="Major" value={stats.major} icon="⚠️" color="#FF9500" />
        <StatCard label="Minor" value={stats.minor} icon="ℹ️" color="#FFCC00" />
        <StatCard label="Max Temp" value={`${stats.maxTemp}°C`} icon="🌡️" color="#FF6B35" sub={`Avg: ${stats.avgTemp}°C`} />
        <StatCard label="Performance" value={`${stats.performanceRatio}%`} icon="⚡" color={stats.performanceRatio > 85 ? "#2CB67D" : "#FF9500"} />
      </div>

      {/* View Mode Toggle */}
      <div style={{
        display: "flex",
        gap: 12,
        marginBottom: 20,
        alignItems: "center",
        flexWrap: "wrap"
      }}>
        <div style={{ fontSize: 12, color: "#888", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em" }}>
          View Mode:
        </div>
        {[
          { id: "thermal", label: "Thermal" },
          { id: "severity", label: "Severity" },
          { id: "deltaT", label: "ΔT Anomaly" },
        ].map(v => (
          <ViewModeButton
            key={v.id}
            active={viewMode === v.id}
            onClick={() => {}}
            label={v.label}
          />
        ))}
      </div>

      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
        {/* Left: Array Map */}
        <div style={{ flex: "1 1 500px" }}>
          <div style={{
            fontSize: 12,
            color: "#888",
            marginBottom: 12,
            letterSpacing: "0.08em",
            display: "flex",
            alignItems: "center",
            gap: 8
          }}>
            <span style={{ color: "#00F0FF" }}>🗺️</span>
            <span>ARRAY THERMAL MAP</span>
          </div>
          
          <EnhancedThermalCanvas
            modules={modules}
            selected={selectedModule}
            onSelect={onSelectModule}
            viewMode={viewMode}
            showLabels={showGridLabels}
          />
          
          <TempScale min={35} max={70} />
          
          {/* String Legend */}
          <div style={{
            display: "flex",
            gap: 16,
            flexWrap: "wrap",
            marginTop: 12,
            padding: "12px",
            background: "rgba(255,255,255,0.02)",
            borderRadius: 8
          }}>
            {["String 1", "String 2", "String 3", "String 4"].map((s, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  fontSize: 11,
                  color: "#aaa"
                }}
              >
                <span style={{
                  display: "inline-block",
                  width: 12,
                  height: 12,
                  borderRadius: 3,
                  background: ["#4CC9F0", "#7209B7", "#2CB67D", "#FF6B35"][i],
                  boxShadow: `0 0 10px ${["#4CC9F0", "#7209B7", "#2CB67D", "#FF6B35"][i]}60`
                }} />
                {s}
              </div>
            ))}
          </div>
        </div>

        {/* Right: Module Detail */}
        <div style={{ flex: "0 0 360px", minWidth: 320 }}>
          <ModuleDetail
            module={modules.find(m => m.id === selectedModule) || null}
            onSelectModule={onSelectModule}
          />
        </div>
      </div>
    </div>
  );
}

// Sub-components

function StatCard({ label, value, sub, color = "#00F0FF", icon }: any) {
  return (
    <div style={{
      background: "rgba(255,255,255,0.03)",
      border: "1px solid rgba(255,255,255,0.06)",
      borderRadius: 12,
      padding: "16px 18px",
      flex: 1,
      minWidth: 140,
      transition: "all 0.2s ease",
    }}>
      <div style={{
        fontSize: 11,
        color: "#888",
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        marginBottom: 8,
        display: "flex",
        alignItems: "center",
        gap: 6
      }}>
        {icon && <span style={{ fontSize: 16 }}>{icon}</span>}
        {label}
      </div>
      <div style={{
        fontSize: 28,
        fontWeight: 800,
        color,
        fontFamily: "monospace",
        letterSpacing: "-0.02em",
        textShadow: `0 0 20px ${color}40`
      }}>
        {value}
      </div>
      {sub && (
        <div style={{
          fontSize: 11,
          color: "#666",
          marginTop: 4,
          display: "flex",
          alignItems: "center",
          gap: 4
        }}>
          {sub}
        </div>
      )}
    </div>
  );
}

function ViewModeButton({ active, onClick, label }: any) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: "8px 18px",
        border: active ? "2px solid #00F0FF" : "2px solid rgba(255,255,255,0.15)",
        borderRadius: 8,
        cursor: "pointer",
        background: active ? "rgba(0,240,255,0.15)" : "rgba(255,255,255,0.02)",
        color: active ? "#00F0FF" : "#888",
        fontSize: 12,
        fontWeight: 700,
        fontFamily: "inherit",
        transition: "all 0.2s ease",
      }}
    >
      {label}
    </button>
  );
}
