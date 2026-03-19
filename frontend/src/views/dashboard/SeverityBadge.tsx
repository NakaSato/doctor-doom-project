/**
 * Severity Badge Component
 * 
 * Displays animated severity indicator with glow effects
 */

import { useState, useEffect } from "react";

interface SeverityBadgeProps {
  severity: 'critical' | 'major' | 'minor' | 'low';
  animated?: boolean;
  size?: 'small' | 'medium' | 'large';
}

const SEVERITY_CONFIG = {
  critical: { label: "Critical", color: "#FF3B30", bg: "rgba(255,59,48,0.12)", priority: 1 },
  major: { label: "Major", color: "#FF9500", bg: "rgba(255,149,0,0.12)", priority: 2 },
  minor: { label: "Minor", color: "#FFCC00", bg: "rgba(255,204,0,0.12)", priority: 3 },
  low: { label: "Low", color: "#2CB67D", bg: "rgba(44,182,125,0.12)", priority: 4 },
};

export default function SeverityBadge({
  severity,
  animated = true,
  size = 'medium'
}: SeverityBadgeProps) {
  const [pulse, setPulse] = useState(0);
  const cfg = SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.low;

  useEffect(() => {
    if (!animated) return;
    const interval = setInterval(() => {
      setPulse(prev => (prev + 1) % 60);
    }, 50);
    return () => clearInterval(interval);
  }, [animated]);

  const pulseScale = animated && severity === 'critical'
    ? 1 + Math.sin(pulse * 0.2) * 0.1
    : 1;

  const sizeStyles = {
    small: { padding: "2px 6px", fontSize: 9 },
    medium: { padding: "3px 10px", fontSize: 10 },
    large: { padding: "4px 12px", fontSize: 12 },
  };

  return (
    <span style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 4,
      padding: sizeStyles[size].padding,
      borderRadius: 12,
      fontSize: sizeStyles[size].fontSize,
      fontWeight: 700,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
      color: cfg.color,
      background: cfg.bg,
      border: `1px solid ${cfg.color}40`,
      transform: `scale(${pulseScale})`,
      transition: "transform 0.1s",
      boxShadow: severity === 'critical' ? `0 0 10px ${cfg.color}60` : "none"
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
}
