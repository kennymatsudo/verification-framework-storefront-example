import React from "react";
import { OffthreadVideo, Sequence, staticFile } from "remotion";
import { Card, Frame } from "./Frame";
import { Still } from "./Still";
import { Title } from "./Title";

export const DEMO_FPS = 30;
const s = (seconds: number) => Math.round(seconds * DEMO_FPS);

// Each scene: what it shows, for how long, and the one sentence under it. Offsets into a video are in seconds.
type Scene =
  | { kind: "title"; seconds: number; line1: string; line2: string; small?: string }
  | { kind: "video"; seconds: number; src: string; from?: number; step: string; caption: string; width?: number | string }
  | { kind: "still"; seconds: number; src: string; step: string; caption: string; focusY?: number; zoomTo?: number; panTo?: number; imageRatio?: number };

export const scenes: Scene[] = [
  { kind: "title", seconds: 4, line1: "Your agent says done, tests pass.", line2: "Does the feature work?" },
  { kind: "video", seconds: 14, src: "out/tests-pass.mp4", step: "1 / 6", caption: "A teammate's pull request. Confident description, 14 green unit tests." },
  { kind: "still", seconds: 7, src: "out/stills/pr2-collapsed.png", step: "2 / 6", caption: "The harness ran it on the real app. One problem: the card was charged full price while the order stored the discount.", focusY: 0.12, zoomTo: 1.12 },
  { kind: "still", seconds: 8, src: "out/stills/pr2-expanded.png", step: "2 / 6", caption: "It read the payments ledger, not the app's own answer, and it names the break the check was shown to fail on.", panTo: 0.12, imageRatio: 4208 / 1272 },
  { kind: "video", seconds: 56, src: "out/calibration.mp4", from: 30, step: "3 / 6", caption: "Calibration: the same check has to fail on a copy broken on purpose before its passes count." },
  { kind: "video", seconds: 15, src: "out/pr4-demo.mp4", step: "4 / 6", caption: "Every screen check records. A passing run is cut into the pull request's clip.", width: 1300 },
  { kind: "video", seconds: 28, src: "out/instruments.mp4", from: 14, step: "5 / 6", caption: "The instruments stay in the repo. A probe reads the database and never asks the app." },
  { kind: "video", seconds: 42, src: "out/hero.mp4", step: "6 / 6", caption: "One prompt builds a feature. Before it says done, the agent previews the proof and asks what the requirements left open." },
  { kind: "video", seconds: 30, src: "out/hero.mp4", from: 99, step: "6 / 6", caption: "It refused to attach a clip that showed nothing, fixed that, re-proved every check, and opened the pull request." },
  { kind: "title", seconds: 6, line1: "Verified, Failed, or Not verified.", line2: "Computed from the record, never written by the agent.", small: "github.com/kennymatsudo/verification-framework  ·  example: verification-framework-storefront-example" },
];

export const demoDurationInFrames = scenes.reduce((sum, scene) => sum + s(scene.seconds), 0);

const SceneView: React.FC<{ scene: Scene }> = ({ scene }) => {
  if (scene.kind === "title") return <Title line1={scene.line1} line2={scene.line2} small={scene.small} />;
  if (scene.kind === "still") {
    return (
      <Frame step={scene.step} caption={scene.caption}>
        <Still src={scene.src} focusY={scene.focusY} zoomTo={scene.zoomTo} panTo={scene.panTo} imageRatio={scene.imageRatio} />
      </Frame>
    );
  }
  return (
    <Frame step={scene.step} caption={scene.caption}>
      <Card width={scene.width ?? "100%"}>
        <OffthreadVideo src={staticFile(scene.src)} startFrom={s(scene.from ?? 0)} style={{ width: "100%", display: "block" }} muted />
      </Card>
    </Frame>
  );
};

export const Demo: React.FC = () => {
  let at = 0;
  return (
    <>
      {scenes.map((scene, index) => {
        const from = at;
        at += s(scene.seconds);
        return (
          <Sequence key={index} from={from} durationInFrames={s(scene.seconds)}>
            <SceneView scene={scene} />
          </Sequence>
        );
      })}
    </>
  );
};
