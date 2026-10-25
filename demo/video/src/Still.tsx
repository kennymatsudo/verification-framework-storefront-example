import React from "react";
import { Img, interpolate, staticFile, useCurrentFrame } from "remotion";

// A screenshot that slowly drifts and zooms toward a point of interest, so a static image still reads as a scene.
export const Still: React.FC<{ src: string; focusY?: number; zoomTo?: number; width?: number }> = ({ src, focusY = 0.2, zoomTo = 1.15, width = 1100 }) => {
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, 150], [1, zoomTo], { extrapolateRight: "clamp" });
  return (
    <div style={{ width, margin: "0 auto", overflow: "hidden", borderRadius: 16, maxHeight: 820 }}>
      <Img src={staticFile(src)} style={{ width: "100%", transform: `scale(${scale})`, transformOrigin: `50% ${focusY * 100}%`, display: "block" }} />
    </div>
  );
};
