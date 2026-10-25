# Scene 3: calibration. The checkout check passes on the real code, then fails on a scratch copy where the charge is
# broken on purpose, and status.md records the break. Everything on screen is the harness's own commands.
Output demo/out/calibration.mp4
Output demo/out/calibration.gif
Set Shell zsh
Set FontSize 18
Set Width 1400
Set Height 820
Set Padding 24
Set Theme "Catppuccin Latte"
Set TypingSpeed 35ms

Hide
Type `cd ~/projects/storefront && setopt interactive_comments && H=.agents/skills/verify-storefront && vf() { python3 $H/scripts/framework/vf.py "$@"; } && vf start --until "python3 $H/scripts/doctor.py" -- $H/scripts/serve.sh && clear`
Enter
Sleep 8s
Show

Type "# The checkout check on the real app:"
Enter
Type "vf run -- python3 $H/scripts/checks/checkout.py | tail -4"
Enter
Sleep 16s
Type "clear"
Enter
Type "# Now break it on purpose, in a throwaway copy the harness makes:"
Enter
Type "vf break start storefront"
Enter
Sleep 7s
Type `WT=$(vf break status | sed -n 's/.*open on \([^,]*\),.*/\1/p')`
Enter
Type `sed -i '' 's/payments.charge(total_cents, card_number/payments.charge(lines[0]["line_cents"], card_number/' $WT/shop/main.py && git -C $WT diff | grep '^[-+] '`
Enter
Sleep 3s
Type "clear"
Enter
Type "# Same check, broken copy. It must fail, or it proves nothing:"
Enter
Type `vf break run storefront "checkout.pay: charge the first line only" -- python3 $H/scripts/framework/vf.py run -- python3 $H/scripts/checks/checkout.py | grep -E "^(FAIL|Break)"`
Enter
Sleep 18s
Type "vf break end storefront | tail -1"
Enter
Sleep 7s
Type "clear"
Enter
Type "# The verdict is computed from the records, never written by the agent:"
Enter
Type `vf status >/dev/null; grep 'checkout.pay' $H/status.md | cut -c1-170`
Enter
Sleep 6s
Hide
Type "vf stop"
Enter
Sleep 2s
