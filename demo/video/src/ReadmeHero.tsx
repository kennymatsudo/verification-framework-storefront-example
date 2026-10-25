import React from "react";
import { AbsoluteFill, OffthreadVideo, Sequence, staticFile } from "remotion";
import { Card } from "./Frame";
import { Still } from "./Still";
import { theme } from "./theme";
import { Title } from "./Title";
import { DEMO_FPS } from "./Demo";

// The README's short loop: the claim, the catch, the clip. Rendered at 1280x720 and turned into a GIF afterwards.
const s = (seconds: number) => Math.round(seconds * DEMO_FPS);
export const README_DURATION = s(3 + 5 + 6);

export const ReadmeHero: React.FC = () => (
  <AbsoluteFill style={{ background: theme.paper, fontFamily: theme.font }}>
    <Sequence from={0} durationInFrames={s(3)}>
      <Title line1="Done, tests pass." line2="Does it work?" />
    </Sequence>
    <Sequence from={s(3)} durationInFrames={s(5)}>
      <AbsoluteFill style={{ padding: 36 }}>
        <Still src="out/stills/pr2-collapsed.png" focusY={0.1} zoomTo={1.1} width={900} />
      </AbsoluteFill>
    </Sequence>
    <Sequence from={s(8)} durationInFrames={s(6)}>
      <AbsoluteFill style={{ padding: 36 }}>
        <Card width={1000}>
          <OffthreadVideo src={staticFile("out/pr4-demo.mp4")} startFrom={s(2)} style={{ width: "100%", display: "block" }} muted />
        </Card>
      </AbsoluteFill>
    </Sequence>
  </AbsoluteFill>
);
