import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { theme } from "./theme";

// A scene's chrome: a caption bar across the bottom and a small step counter, over whatever the scene shows.
export const Frame: React.FC<{ caption: string; step: string; children: React.ReactNode }> = ({ caption, step, children }) => {
  const frame = useCurrentFrame();
  const fade = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: theme.paper, fontFamily: theme.font, color: theme.ink }}>
      <AbsoluteFill style={{ padding: "56px 72px 150px", opacity: fade }}>{children}</AbsoluteFill>
      <div
        style={{
          position: "absolute", left: 72, right: 72, bottom: 48, display: "flex", alignItems: "center", gap: 24,
          background: "white", border: `1px solid ${theme.line}`, borderRadius: 14, padding: "20px 28px",
          boxShadow: "0 6px 24px rgba(31,35,40,0.06)", opacity: fade,
        }}
      >
        <span style={{ color: theme.accent, fontWeight: 700, fontSize: 22, letterSpacing: 1, minWidth: 90 }}>{step}</span>
        <span style={{ fontSize: 30, lineHeight: 1.3 }}>{caption}</span>
      </div>
    </AbsoluteFill>
  );
};

// A rounded, shadowed container for a video or still, kept inside the frame's content area.
export const Card: React.FC<{ children: React.ReactNode; width?: number | string }> = ({ children, width = "100%" }) => (
  <div style={{ width, margin: "0 auto", borderRadius: 16, overflow: "hidden", border: `1px solid ${theme.line}`,
    boxShadow: "0 12px 40px rgba(31,35,40,0.10)", background: "white" }}>
    {children}
  </div>
);
