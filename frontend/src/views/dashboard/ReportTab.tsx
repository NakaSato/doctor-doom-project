/**
 * Report Tab Component (Stub)
 * 
 * Placeholder for inspection report
 * TODO: Implement full report functionality
 */

interface ReportTabProps {
  data: any;
  stats: any;
  healthScore: number;
}

export default function ReportTab({ data, stats, healthScore }: ReportTabProps) {
  if (!data) return null;

  return (
    <div style={{
      background: "rgba(255,255,255,0.03)",
      border: "1px solid rgba(0,240,255,0.2)",
      borderRadius: 12,
      padding: 32,
      maxWidth: 900,
      margin: "0 auto"
    }}>
      <div style={{ textAlign: "center", marginBottom: 32 }}>
        <div style={{ fontSize: 12, color: "#00F0FF", letterSpacing: "0.15em", marginBottom: 12, fontWeight: 800 }}>
          THERMOGRAPHIC INSPECTION REPORT
        </div>
        <div style={{ fontSize: 26, fontWeight: 900, color: "#fff", marginBottom: 8 }}>
          {data.site}
        </div>
        <div style={{ fontSize: 13, color: "#888", fontFamily: "monospace" }}>
          Inspection ID: <span style={{ color: "#00F0FF" }}>{data.id}</span> • {data.date}
        </div>
      </div>

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(4, 1fr)",
        gap: 16,
        marginBottom: 24
      }}>
        <StatBox label="Critical" value={stats.critical} color="#FF3B30" />
        <StatBox label="Major" value={stats.major} color="#FF9500" />
        <StatBox label="Minor" value={stats.minor} color="#FFCC00" />
        <StatBox label="Healthy" value={stats.totalModules - stats.affectedModules} color="#2CB67D" />
      </div>

      <div style={{
        background: "rgba(0,0,0,0.3)",
        borderRadius: 12,
        padding: 24,
        textAlign: "center"
      }}>
        <div style={{ fontSize: 11, color: "#888", marginBottom: 8 }}>Array Health Score</div>
        <div style={{
          fontSize: 48,
          fontWeight: 900,
          color: healthScore > 80 ? "#2CB67D" : healthScore > 60 ? "#FF9500" : "#FF3B30",
        }}>
          {healthScore}<span style={{ fontSize: 18, color: "#888" }}>/100</span>
        </div>
      </div>

      <div style={{
        marginTop: 32,
        padding: 24,
        background: "rgba(44,182,125,0.1)",
        borderRadius: 12,
        border: "1px solid rgba(44,182,125,0.2)",
        textAlign: "center"
      }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>✅</div>
        <div style={{ fontSize: 14, color: "#2CB67D", fontWeight: 700 }}>
          Report generation coming soon
        </div>
        <div style={{ fontSize: 12, color: "#888", marginTop: 8 }}>
          Full IEC 62446-3 compliant reports will be available in the next update
        </div>
      </div>
    </div>
  );
}

function StatBox({ label, value, color }: any) {
  return (
    <div style={{
      background: `${color}08`,
      borderRadius: 8,
      padding: 16,
      textAlign: "center",
      border: `1px solid ${color}30`
    }}>
      <div style={{ fontSize: 28, fontWeight: 900, color, marginBottom: 4 }}>
        {value}
      </div>
      <div style={{ fontSize: 10, color: "#888", textTransform: "uppercase", fontWeight: 700 }}>
        {label}
      </div>
    </div>
  );
}
