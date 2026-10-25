#!/usr/bin/env python3
"""Turn a saved agent session into a terminal replay: an asciinema cast, a GIF, and an MP4.

The replay shows the developer's prompts and the agent's messages exactly as they were, in order. The agent's
tool calls between messages are summarised in one dim line each (how many, which tools, how long the turn took),
because the real session ran headless and its output was a stream of events, not a terminal. Timing is synthetic:
typing speed and pauses are chosen for a viewer, so the replay is labelled as a replay, not a recording.

    demo/replay.py hero            # reads demo/sessions/hero/, writes demo/out/hero.{cast,gif,mp4}
"""

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
COLS, ROWS = 110, 34
TYPE_DELAY, LINE_DELAY, PARA_PAUSE = 0.03, 0.045, 0.9
DIM, BOLD, BLUE, RESET = "\x1b[2m", "\x1b[1m", "\x1b[34m", "\x1b[0m"


def wrap(line, width=COLS - 2):
    words, out, cur = line.split(" "), [], ""
    for word in words:
        if cur and len(cur) + 1 + len(word) > width:
            out.append(cur); cur = word
        else:
            cur = f"{cur} {word}" if cur else word
    out.append(cur)
    return out


def plain(markdown):
    text = re.sub(r"\*\*(.+?)\*\*", lambda m: BOLD + m.group(1) + RESET, markdown)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text


class Cast:
    def __init__(self):
        self.t = 0.0
        self.events = []

    def out(self, text, delay=0.0):
        self.t += delay
        self.events.append([round(self.t, 3), "o", text])

    def typed(self, text):
        for ch in text:
            self.out(ch, TYPE_DELAY)

    def lines(self, text, prefix=""):
        for raw in text.split("\n"):
            raw = raw.rstrip()
            if not raw:
                self.out("\r\n", LINE_DELAY); continue
            for piece in wrap(plain(raw)):
                self.out(prefix + piece + "\r\n", LINE_DELAY)

    def pause(self, seconds):
        self.t += seconds


def turn_blocks(path):
    """The agent's text blocks and tool calls from one turn's stream, in order, plus the turn's duration."""
    blocks, duration = [], 0
    for line in path.read_text().splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "text" and block.get("text", "").strip():
                    blocks.append(("text", block["text"]))
                elif block.get("type") == "tool_use":
                    blocks.append(("tool", block.get("name", "?")))
        elif event.get("type") == "result":
            duration = event.get("duration_ms") or 0
    return blocks, duration


def main():
    name = sys.argv[1]
    folder = REPO / "demo" / "sessions" / name
    state = json.loads((folder / "session.json").read_text())
    cast = Cast()
    cast.out(f"{DIM}Replay of a real agent session in verification-framework-storefront-example. Words unedited; timing compressed.{RESET}\r\n\r\n", 0.5)
    for turn in state["turns"]:
        n = turn["number"]
        cast.out(f"{BLUE}{BOLD}› {RESET}", 0.6)
        cast.typed(turn["prompt"])
        cast.out("\r\n\r\n", 0.4)
        blocks, duration = turn_blocks(folder / f"turn-{n}.jsonl")
        run = []
        def flush():
            if run:
                names = Counter(run)
                summary = ", ".join(f"{k} ×{v}" for k, v in names.most_common(4))
                cast.out(f"{DIM}  ⋯ {len(run)} tool calls ({summary}){RESET}\r\n\r\n", 0.8)
                run.clear()
        for kind, payload in blocks:
            if kind == "tool":
                run.append(payload)
            else:
                flush()
                cast.lines(payload)
                cast.out("\r\n", 0.2)
                cast.pause(PARA_PAUSE)
        flush()
        minutes = max(1, round(duration / 60000)) if duration else None
        if minutes:
            cast.out(f"{DIM}  turn {n}: {minutes} min of agent time{RESET}\r\n\r\n", 0.3)
        cast.pause(1.5)
    cast.pause(3)
    out = REPO / "demo" / "out"; out.mkdir(exist_ok=True)
    cast_path = out / f"{name}.cast"
    header = {"version": 2, "width": COLS, "height": ROWS, "title": f"{name} session replay"}
    cast_path.write_text(json.dumps(header) + "\n" + "\n".join(json.dumps(e) for e in cast.events) + "\n")
    gif = out / f"{name}.gif"
    subprocess.run(["agg", "--theme", "github-light", "--font-size", "18", "--speed", "1", str(cast_path), str(gif)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(gif), "-movflags", "faststart", "-pix_fmt", "yuv420p",
                    "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", str(out / f"{name}.mp4")], check=True)
    print(f"{cast_path} ({cast.t:.0f} s), {gif}, {out / f'{name}.mp4'}")


if __name__ == "__main__":
    main()
