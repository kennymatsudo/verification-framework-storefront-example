import React from "react";
import { Img, interpolate, staticFile, useCurrentFrame } from "remotion";

// A screenshot that slowly moves, so a static image still reads as a scene: it zooms toward a point of interest,
// or, when panTo is set, scrolls down so that fraction of the image's height ends up at the top of the window.
export const Still: React.FC<{ src: string; focusY?: number; zoomTo?: number; panTo?: number; width?: number; imageRatio?: number }> = ({
  src,
  focusY = 0.2,
  zoomTo = 1.15,
  panTo,
  width = 1100,
  imageRatio = 1,
}) => {
  const frame = useCurrentFrame();
  const transform =
    panTo === undefined
      ? `scale(${interpolate(frame, [0, 150], [1, zoomTo], { extrapolateRight: "clamp" })})`
      : `translateY(${-interpolate(frame, [0, 180], [0, panTo * width * imageRatio], { extrapolateRight: "clamp" })}px)`;
  return (
    <div style={{ width, margin: "0 auto", overflow: "hidden", borderRadius: 16, maxHeight: 820 }}>
      <Img src={staticFile(src)} style={{ width: "100%", transform, transformOrigin: `50% ${focusY * 100}%`, display: "block" }} />
    </div>
  );
};
