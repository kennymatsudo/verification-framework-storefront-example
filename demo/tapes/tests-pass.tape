# Scene 1: "done, tests pass". The discount PR's description and its green unit tests, before anything verifies it.
Output demo/out/tests-pass.mp4
Output demo/out/tests-pass.gif
Set Shell zsh
Set FontSize 18
Set Width 1400
Set Height 820
Set Padding 24
Set Theme "Catppuccin Latte"
Set TypingSpeed 35ms

Hide
Type "cd ~/projects/storefront && setopt interactive_comments && git switch -q discount-codes && clear"
Enter
Sleep 1s
Show
Type "gh pr view 2 | sed -n '1,4p;/## Test plan/,$p'"
Enter
Sleep 5s
Type "clear"
Enter
Type "# The tests the PR says it ran:"
Enter
Type "uv run pytest -q -p no:warnings"
Enter
Sleep 4s
Type "# Green. Does the feature work?"
Enter
Sleep 3s
Hide
Type "git switch -q main"
Enter
Sleep 1s
