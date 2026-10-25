# Scene 5: the instruments by hand. Starts the stack through the harness, asks the probe three questions, shows its help, stops.
Output demo/out/instruments.mp4
Output demo/out/instruments.gif
Set Shell zsh
Set FontSize 18
Set Width 1400
Set Height 820
Set Padding 24
Set Theme "Catppuccin Latte"
Set TypingSpeed 40ms

Hide
Type "cd ~/projects/storefront && clear"
Enter
Sleep 500ms
Show

Type "# Every instrument is a plain command in the repo. Start the stack the way the harness does:"
Enter
Type `python3 .agents/skills/verify-storefront/scripts/framework/vf.py start --until "python3 .agents/skills/verify-storefront/scripts/doctor.py" -- .agents/skills/verify-storefront/scripts/serve.sh`
Enter
Sleep 6s
Type "clear"
Enter
Type "# A probe reads the databases directly. It never asks the app."
Enter
Type "python3 .agents/skills/verify-storefront/scripts/probe.py cart"
Enter
Sleep 2500ms
Type "python3 .agents/skills/verify-storefront/scripts/probe.py order 1"
Enter
Sleep 3s
Type "python3 .agents/skills/verify-storefront/scripts/probe.py charge $(python3 .agents/skills/verify-storefront/scripts/probe.py order 1 | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"charge_id\"])')"
Enter
Sleep 3500ms
Type "clear"
Enter
Type "python3 .agents/skills/verify-storefront/scripts/probe.py --help"
Enter
Sleep 5s
Type "python3 .agents/skills/verify-storefront/scripts/framework/vf.py stop"
Enter
Sleep 2s
