import { Composition } from "remotion";
import { Demo, DEMO_FPS, demoDurationInFrames } from "./Demo";
import { ReadmeHero, README_DURATION } from "./ReadmeHero";

export const Root = () => (
  <>
    <Composition
      id="Demo"
      component={Demo}
      durationInFrames={demoDurationInFrames}
      fps={DEMO_FPS}
      width={1920}
      height={1080}
    />
    <Composition
      id="ReadmeHero"
      component={ReadmeHero}
      durationInFrames={README_DURATION}
      fps={DEMO_FPS}
      width={1280}
      height={720}
    />
  </>
);
