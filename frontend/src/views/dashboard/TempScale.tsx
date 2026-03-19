/**
 * Temperature Scale Component
 * 
 * Displays enhanced temperature gradient scale with markers
 */

interface TempScaleProps {
  min: number;
  max: number;
  unit?: string;
}

export default function TempScale({ min, max, unit = "°C" }: TempScaleProps) {
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: 10,
      background: "rgba(255,255,255,0.02)",
      borderRadius: 8,
      padding: "12px"
    }}>
      <span style={{
        fontSize: 11,
        color: "#aaa",
        fontFamily: "monospace",
        fontWeight: 600,
        minWidth: 40
      }}>
        {min}{unit}
      </span>
      <div style={{
        flex: 1,
        height: 14,
        borderRadius: 8,
        background: "linear-gradient(to right, #000033, #000066, #000099, #0033cc, #0066ff, #00ccff, #00ff00, #ffff00, #ff9900, #ff3300, #ff0000)",
        boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
        position: "relative"
      }}>
        {/* Temperature markers */}
        {[0.25, 0.5, 0.75].map(pos => (
          <div
            key={pos}
            style={{
              position: "absolute",
              left: `${pos * 100}%`,
              top: 0,
              bottom: 0,
              width: 1,
              background: "rgba(255,255,255,0.3)"
            }}
          />
        ))}
      </div>
      <span style={{
        fontSize: 11,
        color: "#aaa",
        fontFamily: "monospace",
        fontWeight: 600,
        minWidth: 40
      }}>
        {max}{unit}
      </span>
    </div>
  );
}
