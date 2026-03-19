/**
 * Module Detail Component
 * 
 * Displays detailed information about a selected module
 */

import SeverityBadge from "./SeverityBadge";

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

interface ModuleDetailProps {
  module: Module | null;
  onSelectModule: (id: string) => void;
}

export default function ModuleDetail({ module, onSelectModule }: ModuleDetailProps) {
  if (!module) {
    return (
      <div style={{
        background: "rgba(255,255,255,0.02)",
        border: "2px dashed rgba(255,255,255,0.1)",
        borderRadius: 12,
        padding: 60,
        textAlign: "center",
        transition: "all 0.3s"
      }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>🔍</div>
        <div style={{ fontSize: 14, color: "#aaa", marginBottom: 8 }}>
          Select a module to inspect
        </div>
        <div style={{ fontSize: 12, color: "#666" }}>
          Click any cell in the thermal map
        </div>
      </div>
    );
  }

  return (
    <div style={{
      background: "rgba(255,255,255,0.03)",
      border: "1px solid rgba(0,240,255,0.2)",
      borderRadius: 12,
      padding: 20,
      boxShadow: "0 4px 20px rgba(0,240,255,0.1)"
    }}>
      {/* Header */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: 16,
        paddingBottom: 12,
        borderBottom: "1px solid rgba(255,255,255,0.1)"
      }}>
        <div style={{
          fontSize: 18,
          fontWeight: 900,
          color: "#fff",
          fontFamily: "monospace"
        }}>
          {module.id}
        </div>
        <SeverityBadge
          severity={module.status === "critical" ? "critical" : module.status === "warning" ? "major" : "minor"}
        />
      </div>

      {/* Thermal Image Placeholder */}
      <div style={{
        width: "100%",
        height: 240,
        background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
        borderRadius: 8,
        marginBottom: 16,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "#888",
        fontSize: 12
      }}>
        📷 Thermal Image
      </div>

      {/* Module Info Grid */}
      <div style={{
        marginTop: 16,
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 10
      }}>
        <InfoCard label="Base Temp" value={`${module.baseTemp}°C`} />
        <InfoCard label="Max Temp" value={`${module.maxTemp}°C`} highlight={module.maxTemp > 55} />
        <InfoCard label="ΔT" value={`${(module.maxTemp - module.baseTemp).toFixed(1)}°C`} />
        <InfoCard label="Power Est." value={`${module.power}W`} />
        <InfoCard label="String" value={`#${module.string}`} />
        <InfoCard label="Position" value={`R${module.row + 1} C${module.col + 1}`} />
      </div>

      {/* Defects */}
      {module.defects.length > 0 ? (
        <div style={{ marginTop: 20 }}>
          <div style={{
            fontSize: 11,
            color: "#888",
            letterSpacing: "0.08em",
            marginBottom: 12,
            textTransform: "uppercase",
            display: "flex",
            alignItems: "center",
            gap: 6
          }}>
            <span>🔍</span> Detected Defects ({module.defects.length})
          </div>
          {module.defects.map((d: any) => (
            <DefectItem key={d.id} defect={d} />
          ))}
        </div>
      ) : (
        <div style={{
          textAlign: "center",
          padding: 30,
          color: "#2CB67D",
          fontSize: 13,
          background: "rgba(44,182,125,0.1)",
          borderRadius: 10,
          border: "1px solid rgba(44,182,125,0.2)"
        }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>✓</div>
          No defects detected
          <div style={{ fontSize: 11, color: "#888", marginTop: 4 }}>
            Module operating normally
          </div>
        </div>
      )}
    </div>
  );
}

// Sub-components

function InfoCard({ label, value, highlight = false }: any) {
  return (
    <div style={{
      padding: "10px",
      background: "rgba(255,255,255,0.02)",
      borderRadius: 8,
      border: "1px solid rgba(255,255,255,0.05)"
    }}>
      <div style={{ fontSize: 10, color: "#888", textTransform: "uppercase", marginBottom: 4 }}>
        {label}
      </div>
      <div style={{
        fontSize: 14,
        fontWeight: 700,
        color: highlight ? "#FF3B30" : "#fff",
        fontFamily: "monospace"
      }}>
        {value}
      </div>
    </div>
  );
}

function DefectItem({ defect }: any) {
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

  const DEFECT_ICONS: Record<string, string> = {
    hotspot: "🔥",
    cracked_cell: "⚡",
    snail_trail: "🐌",
    delamination: "📄",
    bypass_diode: "⚙️",
    junction_box: "📦",
    connector: "🔌",
    string_disconnect: "🔗",
    cabling: "🪢",
    moisture: "💧",
    pid: "⬇️",
    soiling: "🌫️",
  };

  return (
    <div
      style={{
        background: "rgba(255,255,255,0.03)",
        border: `1px solid ${DEFECT_COLORS[defect.type] || "#333"}30`,
        borderRadius: 10,
        padding: "12px",
        marginBottom: 10,
        transition: "all 0.2s"
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateX(4px)";
        e.currentTarget.style.borderColor = DEFECT_COLORS[defect.type] + "60";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "translateX(0)";
        e.currentTarget.style.borderColor = DEFECT_COLORS[defect.type] + "30";
      }}
    >
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center"
      }}>
        <span style={{
          fontSize: 13,
          fontWeight: 800,
          color: DEFECT_COLORS[defect.type] || "#fff",
          display: "flex",
          alignItems: "center",
          gap: 6
        }}>
          <span>{DEFECT_ICONS[defect.type] || "⚠️"}</span>
          {defect.label || defect.type}
        </span>
        <SeverityBadge severity={defect.severity || "minor"} />
      </div>
      <div style={{
        display: "flex",
        gap: 16,
        marginTop: 10,
        fontSize: 11,
        color: "#aaa",
        fontFamily: "monospace"
      }}>
        <span>
          ΔT: <span style={{ color: "#FF6B35", fontWeight: 700 }}>{defect.deltaT}°C</span>
        </span>
        <span>
          Conf: <span style={{ color: "#00F0FF", fontWeight: 700 }}>{(defect.confidence * 100).toFixed(0)}%</span>
        </span>
      </div>
    </div>
  );
}
