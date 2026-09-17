# Regenerate with: vhs docs/demo.tape   (brew install vhs)
Output docs/.frames/
Set Shell bash
Set FontSize 15
Set Width 1120
Set Height 600
Set Padding 18
Set Theme "Catppuccin Mocha"
Set TypingSpeed 35ms

Hide
Type "source docs/demo-setup.sh; clear"
Enter
Show

Type "# The promise: a read-only analytics helper"
Enter
Type "sed -n '8,22p' examples/demo/analytics-helper/agent-assurance.yaml"
Enter
Sleep 2.5s
Type "# The evidence: what the repo's config actually grants"
Enter
Type "agent-assurance scan examples/demo/analytics-helper | grep -E 'AA-00|Promise|Blast'"
Enter
Sleep 3s
Type "clear"
Enter
Type "# A pull request adds a GitHub MCP server (write + token)"
Enter
Type "agent-assurance diff examples/demo/analytics-helper /tmp/pr-head --fail-on-delta"
Enter
Sleep 6s
Type "echo exit=$?"
Enter
Sleep 2.5s

# Note: VHS 0.x + ffmpeg 9 fail to encode the GIF directly on macOS; frames are
# written to docs/.frames/ and assembled with:
#   ffmpeg -framerate 50 -i docs/.frames/frame-text-%05d.png \
#     -vf "fps=10,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=64[p];[s1][p]paletteuse=dither=none" docs/demo.gif
