import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "./theme";

export const Title: React.FC<{ line1: string; line2: string; small?: string }> = ({ line1, line2, small }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const rise = spring({ frame, fps, config: { damping: 200 } });
  const y = interpolate(rise, [0, 1], [30, 0]);
  return (
    <AbsoluteFill style={{ background: theme.paper, fontFamily: theme.font, color: theme.ink, justifyContent: "center", padding: "0 160px" }}>
      <div style={{ transform: `translateY(${y}px)`, opacity: rise }}>
        <div style={{ fontSize: 72, fontWeight: 700, lineHeight: 1.1 }}>{line1}</div>
        <div style={{ fontSize: 72, fontWeight: 700, lineHeight: 1.1, color: theme.accent }}>{line2}</div>
        {small && <div style={{ fontSize: 30, color: theme.muted, marginTop: 36, maxWidth: 1300, lineHeight: 1.4 }}>{small}</div>}
      </div>
    </AbsoluteFill>
  );
};
