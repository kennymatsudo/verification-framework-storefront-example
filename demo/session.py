#!/usr/bin/env python3
"""Run one turn of a headless agent session in this repo, with the verification framework loaded as a plugin.

Every demo scene that involves the agent goes through here, so a run is reproducible: the prompt, the model, the
session ID, and the agent's final message are saved under demo/sessions/<name>/. Resume a session with --resume to
answer the question its last message ended on.

    demo/session.py setup "/verification-framework:vf Set up verification for this app."
    demo/session.py setup --resume "Yes, commit it."
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FRAMEWORK = Path(os.environ.get("VF_FRAMEWORK", Path.home() / "projects" / "verification-framework"))
SESSIONS = REPO / "demo" / "sessions"
DEFAULT_MODEL = "claude-opus-5-5"
# Headless acceptEdits mode still prompts for writes under .claude/, where Claude Code loads project skills from and
# where the harness lives, so those paths are allowed by rule.
ALLOWED_TOOLS = ["Read", "Glob", "Grep", "Bash", "Edit", "Write", "MultiEdit", "NotebookEdit", "Agent", "Skill", "TodoWrite", "WebFetch",
                 "Edit(.claude/skills/**)", "Write(.claude/skills/**)"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="session name; its turns are saved under demo/sessions/<name>/")
    parser.add_argument("prompt")
    parser.add_argument("--resume", action="store_true", help="continue the session named, answering its last question")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-turns", type=int, default=150)
    args = parser.parse_args()

    folder = SESSIONS / args.name
    folder.mkdir(parents=True, exist_ok=True)
    state_path = folder / "session.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {"turns": []}
    if args.resume and not state.get("session_id"):
        sys.exit(f"no session to resume under {folder}")

    command = ["claude", "-p", args.prompt, "--output-format", "stream-json", "--verbose",
               "--plugin-dir", str(FRAMEWORK), "--add-dir", str(FRAMEWORK),
               "--permission-mode", "acceptEdits", "--allowedTools", *ALLOWED_TOOLS,
               "--disallowedTools", "AskUserQuestion", "--max-turns", str(args.max_turns), "--model", args.model]
    if args.resume:
        command += ["--resume", state["session_id"]]
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)

    turn_number = len(state["turns"]) + 1
    stream_path = folder / f"turn-{turn_number}.jsonl"
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with stream_path.open("w") as stream:
        result = subprocess.run(command, cwd=REPO, env=env, stdout=stream, stderr=subprocess.PIPE, text=True, stdin=subprocess.DEVNULL)

    final_text, session_id, cost, error = "", state.get("session_id"), 0.0, None
    for line in stream_path.read_text().splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "system" and event.get("subtype") == "init":
            session_id = event.get("session_id") or session_id
        elif event.get("type") == "result":
            session_id = event.get("session_id") or session_id
            final_text = event.get("result") or ""
            cost = event.get("total_cost_usd") or 0.0
            if event.get("is_error") or event.get("subtype", "success") != "success":
                error = event.get("subtype") or "error"
    if result.returncode and not final_text:
        error = f"claude exited {result.returncode}: {result.stderr.strip()[:800]}"

    state["session_id"] = session_id
    state["model"] = args.model
    state["turns"].append({"number": turn_number, "prompt": args.prompt, "started": started, "cost_usd": cost, "error": error})
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    (folder / f"turn-{turn_number}.md").write_text(f"# Turn {turn_number}\n\n**Prompt:** {args.prompt}\n\n{final_text}\n")

    print(final_text)
    if error:
        print(f"\n[error: {error}]", file=sys.stderr)
        sys.exit(1)
    print(f"\n[session {session_id}, turn {turn_number}, ${cost:.2f}]", file=sys.stderr)


if __name__ == "__main__":
    main()
