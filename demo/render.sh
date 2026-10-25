#!/usr/bin/env bash
# Render every demo asset from scratch: terminal tapes, the session replay, the PR stills, then the Remotion cuts
# and the README GIF. Needs vhs, agg, ffmpeg, gifski, Node, and the app's ports free. Takes about ten minutes.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p demo/out
for tape in demo/tapes/*.tape; do echo "== $tape"; vhs "$tape"; done
echo "== session replay"; demo/replay.py hero
echo "== stills"; python3 demo/stills.py
echo "== remotion"
(cd demo/video && [ -d node_modules ] || npm install --no-audit --no-fund)
(cd demo/video && npx remotion render src/index.ts Demo ../out/demo.mp4 --log=error)
(cd demo/video && npx remotion render src/index.ts ReadmeHero ../out/readme-hero.mp4 --log=error)
echo "== readme gif"
rm -rf demo/out/readme-frames && mkdir -p demo/out/readme-frames
ffmpeg -v error -y -i demo/out/readme-hero.mp4 -vf "fps=12,scale=960:-1" demo/out/readme-frames/f%04d.png
gifski -q --fps 12 --quality 80 -o demo/out/readme-hero.gif demo/out/readme-frames/f*.png
ls -la demo/out
