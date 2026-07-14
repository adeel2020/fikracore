import React from "react";
import { X } from "lucide-react";
import "./HoloCard.css";

interface HoloCardProps {
  title?: string;
  children: React.ReactNode;
  status?: "normal" | "danger";
  className?: string;
  style?: React.CSSProperties;
  theme?: "emerald-cut" | "aquamarine" | "holographic" | "frosted" | "matte-clay";
  onClose?: () => void; // Optional onClose callback
}

/**
 * HoloCard Component
 * Acts as a glassmorphic container for BI dashboard visualizations.
 * 
 * @param {string} title - The header text for the data panel (e.g., "Biometric Analysis")
 * @param {ReactNode} children - The actual data, chart, or UI elements to display inside
 * @param {string} status - Allows dynamic color changing based on data state (e.g., 'danger', 'normal')
 * @param {string} className - Optional Tailwind CSS classes for sizing and placement
 * @param {React.CSSProperties} style - Optional CSS inline styles passed to the container
 * @param {string} theme - Active card theme ('emerald-cut', 'aquamarine', 'holographic', 'frosted', 'matte-clay')
 * @param {Function} onClose - Triggers when the close button is clicked
 */
const HoloCard = ({ title, children, status = "normal", className = "", style = {}, theme = "emerald-cut", onClose }: HoloCardProps) => {
  // REASONING: In a BI platform, data often dictates the UI state. 
  // We can dynamically alter the glow color based on a status prop.
  // Example: If a metric drops below a threshold, the card glows red instead of cyan.
  const dynamicStyles = {
    ...style,
    borderColor: status === "danger" ? "rgba(255, 50, 50, 0.5)" : style.borderColor || "",
    boxShadow: status === "danger" ? "inset 0 0 20px rgba(255, 50, 50, 0.1)" : style.boxShadow || "",
  };

  const titleStyles = {
    color: status === "danger" ? "#ff3232" : "",
    textShadow: status === "danger" ? "0 0 8px rgba(255, 50, 50, 0.6)" : "",
  };

  return (
    <div className={`holo-container theme-${theme} ${className}`} style={dynamicStyles}>
      {/* Decorative scanline texture overlay (skip for frosted minimalistic glass) */}
      {theme !== "frosted" && <div className="holo-scanlines"></div>}

      {/* Close button option if onClose is supplied */}
      {onClose && (
        <button
          onClick={(e) => {
            e.stopPropagation(); // Avoid triggering card click transitions
            onClose();
          }}
          className="absolute top-3.5 right-3.5 text-white/40 hover:text-white transition-colors cursor-pointer pointer-events-auto z-10"
          title="Close Panel"
        >
          <X size={13} className="stroke-[2.5]" />
        </button>
      )}

      {/* Header section */}
      {title && (
        <h3 className="holo-title" style={titleStyles}>
          {title}
        </h3>
      )}

      {/* REASONING: By passing {children}, this component becomes highly reusable. 
        You can wrap a complex interactive chart or just a few <p> tags with data.
      */}
      <div className="holo-content">{children}</div>
    </div>
  );
};

export default HoloCard;
