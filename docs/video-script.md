# Launch video script (≈75 s)

Format: screen recording of a terminal + the GitHub PR, voice-over. English for the launch; a Spanish version of the voice-over is at the end. Use `/brag` or any editor; the shots below are what matters.

| # | Shot (what is on screen) | Voice-over | s |
|---|---|---|---|
| 1 | Black screen, one line types out: `autonomy: 2  # a human approves actions` | "Your AI agent has a job description. Read the CRM. Don't send email. Ask before acting." | 6 |
| 2 | `.mcp.json` in an editor; a hand adds a `github` server with a token | "Then someone adds a tool. Nobody reads the diff. Now it can push code and it holds a token." | 8 |
| 3 | The PR page: red check, the bot comment scrolls into view (`docs/pr-comment.png`) | "Agent Assurance turns the job description into a promise — and checks every change against it. Promise broken: `github.write` grants write, not declared. File and line." | 12 |
| 4 | Terminal: `agent-assurance scan .` on a repo; the *Sources scanned* table | "It reads what your repo actually grants: MCP servers for Claude Code, Cursor, Gemini, VS Code — and Claude Code permissions. Whatever it doesn't understand, it says so. Unknown is never silent." | 12 |
| 5 | `.claude/settings.json`: `"allow": ["Bash(*)"]` highlighted; report line *runs without human approval, but declared autonomy is L2* | "It knows the difference between a tool and a person. An `allow` rule doesn't add a power — it removes the human. That breaks a promise too." | 11 |
| 6 | Claude Code session: the agent calls `would_break` before editing; answer *WOULD BREAK THE PROMISE* | "And the agent can ask first. Would this break the promise? — before it touches a file." | 8 |
| 7 | Terminal: `agent-assurance attest . -o aa-attestation.json`; JSON with `subject`, `sha256`, `git.commit` | "Every run leaves evidence: what the agent could do, at which commit, signed. The record auditors ask for." | 9 |
| 8 | Logo card: **agent-assurance** · *Declare what your agent may do. Verify it on every change.* · `pipx install agent-assurance` · OWASP Agentic Top 10 · no LLM in the verdict | "Deterministic. Open source. No LLM in the verdict. Declare what your agent may do — and hold it to its word." | 9 |

## For friends (Spanish, 20 s)

"Es como la etiqueta de ingredientes de un agente de IA, pero comprobada. Escribes lo que tu agente puede hacer, y en cada cambio del código el sistema mira si sigue siendo verdad. Si alguien le da un poder que no estaba prometido —enviar correos, tocar GitHub, actuar sin que un humano apruebe— lo para y dice exactamente dónde. Y deja un recibo firmado de lo que podía hacer en cada versión."

## Three words

**Promises, verified. Evidence, signed.**
