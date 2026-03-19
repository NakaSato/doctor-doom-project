/**
 * Defects Tab Component
 * 
 * Displays defect list with filtering and sorting
 */

import { useState, useMemo } from "react";
import SeverityBadge from "./SeverityBadge";

interface Defect {
  id: string;
  type: string;
  severity: string;
  deltaT: number;
  confidence: number;
  moduleId: string;
}

interface DefectsTabProps {
  defects: Defect[];
  stats: {
    defectTypes: Record<string, number>;
  };
}

const DEFECT_TYPES: Record<string, { label: string; color: string; icon: string }> = {
  hotspot: { label: "Hot Spot", color: "#FF3B30", icon: "🔥" },
  cracked_cell: { label: "Cracked Cell", color: "#FF9500", icon: "⚡" },
  snail_trail: { label: "Snail Trail", color: "#FFCC00", icon: "🐌" },
  delamination: { label: "Delamination", color: "#FF6B35", icon: "📄" },
  bypass_diode: { label: "Bypass Diode Failure", color: "#FF2D55", icon: "⚙️" },
  junction_box: { label: "Junction Box Overheat", color: "#E63946", icon: "📦" },
  connector: { label: "Defective Connector", color: "#F77F00", icon: "🔌" },
  string_disconnect: { label: "Disconnected String", color: "#D62828", icon: "🔗" },
  cabling: { label: "Poor Cabling", color: "#FC5A03", icon: "🪢" },
  moisture: { label: "Moisture Ingress", color: "#4CC9F0", icon: "💧" },
  pid: { label: "PID Effect", color: "#7209B7", icon: "⬇️" },
  soiling: { label: "Heavy Soiling", color: "#8D6E63", icon: "🌫️" },
};

export default function DefectsTab({ defects, stats }: DefectsTabProps) {
  const [filterSeverity, setFilterSeverity] = useState("all");
  const [filterDefect, setFilterDefect] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("severity");

  const filteredDefects = useMemo(() => {
    let result = [...defects];
    
    if (filterSeverity !== "all") {
      result = result.filter(d => DEFECT_TYPES[d.type]?.severity === filterSeverity);
    }
    if (filterDefect !== "all") {
      result = result.filter(d => d.type === filterDefect);
    }
    if (searchQuery) {
      result = result.filter(d =>
        d.moduleId.toLowerCase().includes(searchQuery.toLowerCase()) ||
        DEFECT_TYPES[d.type]?.label.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    if (sortBy === "deltaT") result.sort((a, b) => b.deltaT - a.deltaT);
    else if (sortBy === "confidence") result.sort((a, b) => b.confidence - a.confidence);
    
    return result;
  }, [defects, filterSeverity, filterDefect, searchQuery, sortBy]);

  return (
    <div>
      {/* Filters */}
      <div style={{
        display: "flex",
        gap: 12,
        marginBottom: 20,
        flexWrap: "wrap",
        alignItems: "center",
        padding: "16px",
        background: "rgba(0,0,0,0.3)",
        borderRadius: 12,
        border: "1px solid rgba(255,255,255,0.05)"
      }}>
        <input
          type="text"
          placeholder="Search module ID or defect..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          style={{
            padding: "10px 16px",
            borderRadius: 8,
            border: "1px solid rgba(255,255,255,0.15)",
            background: "rgba(255,255,255,0.03)",
            color: "#fff",
            fontSize: 12,
            fontFamily: "inherit",
            outline: "none",
            width: 260,
          }}
        />
        <select
          value={filterSeverity}
          onChange={e => setFilterSeverity(e.target.value)}
          style={{
            padding: "10px 14px",
            borderRadius: 8,
            border: "1px solid rgba(255,255,255,0.15)",
            background: "rgba(0,0,0,0.5)",
            color: "#fff",
            fontSize: 12,
            fontFamily: "inherit",
            cursor: "pointer",
          }}
        >
          <option value="all">All Severity</option>
          <option value="critical">Critical</option>
          <option value="major">Major</option>
          <option value="minor">Minor</option>
        </select>
        <select
          value={filterDefect}
          onChange={e => setFilterDefect(e.target.value)}
          style={{
            padding: "10px 14px",
            borderRadius: 8,
            border: "1px solid rgba(255,255,255,0.15)",
            background: "rgba(0,0,0,0.5)",
            color: "#fff",
            fontSize: 12,
            fontFamily: "inherit",
            cursor: "pointer",
          }}
        >
          <option value="all">All Types</option>
          {Object.entries(DEFECT_TYPES).map(([k, v]) => (
            <option key={k} value={k}>{v.icon} {v.label}</option>
          ))}
        </select>
        <select
          value={sortBy}
          onChange={e => setSortBy(e.target.value)}
          style={{
            padding: "10px 14px",
            borderRadius: 8,
            border: "1px solid rgba(255,255,255,0.15)",
            background: "rgba(0,0,0,0.5)",
            color: "#fff",
            fontSize: 12,
            fontFamily: "inherit",
            cursor: "pointer",
          }}
        >
          <option value="severity">Sort: Severity</option>
          <option value="deltaT">Sort: ΔT</option>
          <option value="confidence">Sort: Confidence</option>
        </select>
        <span style={{
          fontSize: 12,
          color: "#888",
          marginLeft: "auto",
          fontFamily: "monospace",
          fontWeight: 700
        }}>
          <span style={{ color: "#00F0FF" }}>{filteredDefects.length}</span> defects
        </span>
      </div>

      {/* Defect Type Summary */}
      <div style={{
        display: "flex",
        gap: 8,
        marginBottom: 20,
        flexWrap: "wrap"
      }}>
        {Object.entries(stats.defectTypes || {}).sort((a, b) => b[1] - a[1]).map(([type, count]) => (
          <div
            key={type}
            style={{
              padding: "8px 14px",
              borderRadius: 8,
              fontSize: 11,
              fontWeight: 700,
              background: `${DEFECT_TYPES[type]?.color}15`,
              border: `1px solid ${DEFECT_TYPES[type]?.color}40`,
              color: DEFECT_TYPES[type]?.color,
              cursor: "pointer",
              transition: "all 0.2s",
              display: "flex",
              alignItems: "center",
              gap: 6
            }}
            onClick={() => setFilterDefect(filterDefect === type ? "all" : type)}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "translateY(-2px)";
              e.currentTarget.style.background = `${DEFECT_TYPES[type]?.color}25`;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "translateY(0)";
              e.currentTarget.style.background = `${DEFECT_TYPES[type]?.color}15`;
            }}
          >
            <span>{DEFECT_TYPES[type]?.icon}</span>
            {DEFECT_TYPES[type]?.label}
            <span style={{
              background: `${DEFECT_TYPES[type]?.color}30`,
              padding: "2px 8px",
              borderRadius: 6,
              marginLeft: 4
            }}>
              {count}
            </span>
          </div>
        ))}
      </div>

      {/* Defect List */}
      <div style={{
        display: "flex",
        flexDirection: "column",
        gap: 6,
        background: "rgba(0,0,0,0.2)",
        borderRadius: 12,
        padding: "16px",
        border: "1px solid rgba(255,255,255,0.05)"
      }}>
        <div style={{
          display: "grid",
          gridTemplateColumns: "100px 1fr 90px 80px 90px 90px",
          padding: "12px 16px",
          fontSize: 11,
          color: "#888",
          letterSpacing: "0.08em",
          borderBottom: "1px solid rgba(0,240,255,0.2)",
          fontWeight: 800,
          textTransform: "uppercase"
        }}>
          <div>Module</div>
          <div>Defect Type</div>
          <div>Severity</div>
          <div>ΔT</div>
          <div>Confidence</div>
          <div>Action</div>
        </div>
        {filteredDefects.slice(0, 50).map((d, i) => (
          <div
            key={d.id}
            style={{
              display: "grid",
              gridTemplateColumns: "100px 1fr 90px 80px 90px 90px",
              padding: "14px 16px",
              alignItems: "center",
              fontSize: 12,
              background: i % 2 === 0 ? "rgba(255,255,255,0.02)" : "transparent",
              borderLeft: `4px solid ${DEFECT_TYPES[d.type]?.color || "#333"}`,
              borderRadius: 8,
              cursor: "pointer",
              transition: "all 0.2s"
            }}
          >
            <div style={{ fontWeight: 800, color: "#00F0FF", fontFamily: "monospace" }}>
              {d.moduleId}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 14 }}>{DEFECT_TYPES[d.type]?.icon}</span>
              <span style={{ color: DEFECT_TYPES[d.type]?.color, fontWeight: 700 }}>
                {DEFECT_TYPES[d.type]?.label}
              </span>
            </div>
            <div>
              <SeverityBadge severity={d.severity as any} animated={false} />
            </div>
            <div style={{
              fontWeight: 700,
              color: d.deltaT > 20 ? "#FF3B30" : d.deltaT > 10 ? "#FF9500" : "#FFCC00",
              fontFamily: "monospace"
            }}>
              {d.deltaT}°C
            </div>
            <div>
              <div style={{
                width: 70,
                height: 6,
                borderRadius: 4,
                background: "rgba(255,255,255,0.1)",
                overflow: "hidden",
              }}>
                <div style={{
                  width: `${d.confidence * 100}%`,
                  height: "100%",
                  borderRadius: 4,
                  background: d.confidence > 0.9
                    ? "linear-gradient(90deg, #2CB67D, #00F0FF)"
                    : d.confidence > 0.8
                    ? "linear-gradient(90deg, #FF9500, #FFCC00)"
                    : "linear-gradient(90deg, #FF3B30, #FF6B35)",
                }} />
              </div>
              <div style={{ fontSize: 10, color: "#888", marginTop: 4, fontFamily: "monospace" }}>
                {(d.confidence * 100).toFixed(0)}%
              </div>
            </div>
            <div style={{ fontSize: 11, color: "#00F0FF", fontWeight: 800, cursor: "pointer" }}>
              INSPECT →
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
