# Installation

PSI Coprocessor MCP connects to your AI assistant and gives it a persistent memory and reasoning layer. Once connected, your AI can track hypotheses, detect contradictions, and remember findings across sessions.

---

## Step 1 — Install `uv` (one time, free)

`uv` is a small tool that installs and runs Python programs. You only need to do this once.

**Windows:**
Open PowerShell (search "PowerShell" in the Start menu) and paste this:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```
Close and reopen PowerShell after it finishes.

**macOS / Linux:**
Open Terminal and paste:
```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Close and reopen Terminal after it finishes.

**Verify it worked:**
```sh
uvx --version
```
You should see a version number. If you get "command not found," restart your terminal.

---

## Step 2 — Connect to your AI client

Find your AI client below and follow its section.

---

### Claude Desktop

**Where is the config file?**
- **Windows:** Press `Win+R`, type `%APPDATA%\Claude`, press Enter. Open `claude_desktop_config.json` in Notepad.
- **macOS:** In Finder, press `Cmd+Shift+G`, paste `~/Library/Application Support/Claude`, press Enter. Open `claude_desktop_config.json`.

> If the file doesn't exist yet, create it. If it exists, look for the `"mcpServers"` section and add inside it.

**Paste this into the file:**
```json
{
  "mcpServers": {
    "psi-coprocessor": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP",
        "psi-coprocessor-mcp",
        "stdio"
      ]
    }
  }
}
```

**Restart Claude Desktop.** The first launch downloads the server (takes ~30 seconds). After that it starts instantly.

**Make Claude use it automatically:** Add a CLAUDE.md file to any project folder:
```markdown
At the start of every task, call psi.run.start then psi.reflect before writing code or plans.
Use project_id=[your-project-slug] consistently. Do not create files to store PSI findings — use psi.memory.commit(lane=project) instead.
```

---

### Claude Code (CLI)

Claude Code reads `CLAUDE.md` in the project folder automatically. Add the MCP to `~/.claude/claude.json` (global) or `settings.json` in the project's `.claude/` folder:

```json
{
  "mcpServers": {
    "psi-coprocessor": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP",
        "psi-coprocessor-mcp",
        "stdio"
      ],
      "type": "stdio"
    }
  }
}
```

**Make it auto-use:** Create `CLAUDE.md` in your project root (see [auto-use template](#auto-use-template)).

---

### Cursor

**Where is the config file?**
- **Per project:** Create `.cursor/mcp.json` in your project folder.
- **Global (all projects):** `~/.cursor/mcp.json`

**Paste this:**
```json
{
  "mcpServers": {
    "psi-coprocessor": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP",
        "psi-coprocessor-mcp",
        "stdio"
      ]
    }
  }
}
```

**Restart Cursor.** You should see "psi-coprocessor" listed in Settings → MCP.

**Make it auto-use:** Create `.cursor/rules/psi-coprocessor.md` in your project:
```markdown
You have access to the psi-coprocessor MCP. At the start of every non-trivial task, call psi.run.start then psi.reflect before writing code or proposing a plan. Use psi.memory.commit(lane=project) to store findings. Do not create files to record PSI state.
```

---

### Windsurf (Codeium)

**Where is the config file?**
- **Windows:** `%USERPROFILE%\.codeium\windsurf\mcp_config.json`
- **macOS/Linux:** `~/.codeium/windsurf/mcp_config.json`

You can also open it from Windsurf: click the MCP icon in the Cascade panel → Configure.

**Paste this:**
```json
{
  "mcpServers": {
    "psi-coprocessor": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP",
        "psi-coprocessor-mcp",
        "stdio"
      ]
    }
  }
}
```

**Restart Windsurf.**

**Make it auto-use:** Create `.windsurfrules` in your project root (see [auto-use template](#auto-use-template)).

---

### OpenCode

**Where is the config file?**
- **Global:** `~/.config/opencode/opencode.json`
- **Per project:** `opencode.json` in your project folder

**Paste this (or add the `"mcp"` section if the file already exists):**
```json
{
  "mcp": {
    "psi-coprocessor": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP",
        "psi-coprocessor-mcp",
        "stdio"
      ]
    }
  }
}
```

**Make it auto-use:** Create `AGENTS.md` in your project (see [auto-use template](#auto-use-template)). OpenCode also reads `CLAUDE.md`.

---

### Codex CLI (OpenAI)

**Install Codex CLI first:** `npm install -g @openai/codex`

**Where is the config file?**
- **Global:** `~/.codex/config.toml` (create it if it doesn't exist)
- **Per project:** `.codex/config.toml`

**Paste this:**
```toml
[mcp_servers.psi-coprocessor]
command = "uvx"
args = [
  "--from",
  "git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP",
  "psi-coprocessor-mcp",
  "stdio"
]
```

**Make it auto-use:** Create `AGENTS.md` in your project (see [auto-use template](#auto-use-template)).

---

### Gemini CLI

**Install Gemini CLI first:** `npm install -g @google/gemini-cli`

**Where is the config file?**
- **Global:** `~/.gemini/settings.json`
- **Per project:** `.gemini/settings.json`

**Paste this:**
```json
{
  "mcpServers": {
    "psi-coprocessor": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP",
        "psi-coprocessor-mcp",
        "stdio"
      ]
    }
  }
}
```

**Make it auto-use:** Create `GEMINI.md` in your project (see [auto-use template](#auto-use-template)).

---

### LM Studio

LM Studio supports MCP servers starting with version 0.3.17. Make sure you're on a recent version (Help → Check for Updates).

**Where is the config file?**
- **Windows:** `%USERPROFILE%\.lmstudio\mcp.json`
- **macOS/Linux:** `~/.lmstudio/mcp.json`

You can also access it from inside LM Studio: Settings → Program tab → Edit mcp.json.

**Paste this:**
```json
{
  "mcpServers": {
    "psi-coprocessor": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP",
        "psi-coprocessor-mcp",
        "stdio"
      ]
    }
  }
}
```

**Restart LM Studio.**

**Make it auto-use:** LM Studio doesn't read project files, so you need to add a system prompt to your model/assistant configuration. Copy and paste the template from [`examples/system_prompt.md`](../examples/system_prompt.md) into your model's system prompt field.

---

### Jan AI

Jan supports MCP via its settings UI (requires enabling experimental features first).

1. Open Jan → Settings → General → Advanced → Enable experimental features.
2. Go to Settings → MCP Servers → Add Server.
3. Fill in:
   - **Name:** `psi-coprocessor`
   - **Command:** `uvx`
   - **Arguments:** `--from git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP psi-coprocessor-mcp stdio`
4. Toggle the server on.
5. In Settings → MCP Servers, enable "Allow All MCP Tool Permission."

**Make it auto-use:** Jan doesn't read project files. Paste the system prompt template from [`examples/system_prompt.md`](../examples/system_prompt.md) into your assistant's system prompt.

---

### Qwen (via Ollama or LM Studio)

Qwen models running via **Ollama** do not support MCP natively. Use one of these options instead:

**Option A — Run Qwen via LM Studio** (easiest): Load your Qwen model in LM Studio and follow the LM Studio instructions above.

**Option B — Run Qwen via Open WebUI**: Open WebUI supports MCP tool servers. Connect the PSI HTTP server:
1. Start PSI in HTTP mode: `uvx --from git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP psi-coprocessor-mcp http --port 8765`
2. In Open WebUI, go to Settings → Tools → Add MCP Server → URL: `http://127.0.0.1:8765/mcp`

In either case, paste the system prompt from [`examples/system_prompt.md`](../examples/system_prompt.md) into your model's system prompt.

---

### Continue.dev (VS Code / JetBrains extension)

**Where is the config file?**
- `~/.continue/config.yaml` (global, preferred)
- `.continue/config.yaml` (per project)

**Add this to your config.yaml:**
```yaml
mcpServers:
  - name: psi-coprocessor
    type: stdio
    command: uvx
    args:
      - --from
      - git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP
      - psi-coprocessor-mcp
      - stdio
```

---

## Auto-Use Template

For clients that read a project instruction file (Claude Code, Cursor, Windsurf, OpenCode, Codex, Gemini CLI), create the appropriate file in your project root with this content.

**Claude Code → `CLAUDE.md`**
**Codex CLI / OpenCode → `AGENTS.md`**
**Gemini CLI → `GEMINI.md`**
**Windsurf → `.windsurfrules`**
**Cursor → `.cursor/rules/psi.md`**

Content to paste (replace `my_project` with your project slug):
```markdown
## PSI Coprocessor

You have access to the psi-coprocessor MCP. Use it as your persistent reasoning layer.

**Every non-trivial task:**
1. Call `psi.run.start(title="...", scope="...", mode="construction", project_id="my_project")`
2. Call `psi.reflect(task="...", draft_answer="...", run_id="<from step 1>", project_id="my_project")`
3. Before finishing: call `psi.compliance.check(run_id="...")`

**Do not create markdown files to record PSI findings.** Use `psi.memory.commit(lane="project", ...)` instead.

**Modes:** survey (explore), construction (implement), audit (review), repair (fix), closure (wrap up).
```

For **LM Studio, Jan AI, Qwen, and other chat-based clients**, use the ready-made system prompt in [`examples/system_prompt.md`](../examples/system_prompt.md).

---

## Running the HTTP Server (for multi-client or Open WebUI setups)

If you want multiple clients to share one PSI server, or if your client only supports HTTP MCP:

```sh
uvx --from git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP psi-coprocessor-mcp http --port 8765
```

Connect clients to: `http://127.0.0.1:8765/mcp`

This server must stay running in a terminal window while you use your AI client. PSI state is stored in SQLite on disk — restarting the server is safe and does not lose data.

---

## Updating

PSI updates automatically the first time you run it after `main` gets new commits. To force an immediate update:

```sh
uvx --refresh --from git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP psi-coprocessor-mcp diagnose
```

Then restart your AI client. Your run history and database are not affected.

---

## Verifying the Connection

After connecting, ask your AI: *"What PSI tools do you have available?"* It should list tools starting with `psi.`. If it doesn't know about PSI tools, double-check the config file and restart the client.

For a deeper check:
```sh
uvx --from git+https://github.com/ahmiershadowman-commits/Progressive-Structural-Illumination-MCP psi-coprocessor-mcp diagnose
```

---

## Data Storage

PSI state lives in a local SQLite file. Nothing is sent to the cloud.

| Platform | Default location |
|---|---|
| Windows | `%LOCALAPPDATA%\psi-coprocessor-mcp\psi.db` |
| macOS/Linux | `~/.psi-coprocessor-mcp/psi.db` |

Override with the `PSI_MCP_DATA_DIR` environment variable.

---

## Troubleshooting

**"uv: command not found" after installing**
Close and reopen your terminal, then try again. On Windows, you may need to restart your computer.

**First startup is slow**
Normal — `uvx` is downloading and caching the server the first time. Subsequent starts are instant.

**"Permission denied" on Windows with OneDrive**
Run: `$env:UV_LINK_MODE = "copy"` before the `uvx` command, or move the PSI data folder outside OneDrive.

**Tools aren't appearing in the AI client**
- Confirm `uvx --version` works in your terminal
- Check that your config file has no JSON syntax errors (trailing commas, missing quotes)
- Restart the client completely (not just reload)
- Run `uvx ... psi-coprocessor-mcp diagnose` to confirm the server starts

**The AI doesn't use PSI tools proactively**
Add the [auto-use template](#auto-use-template) to the appropriate file in your project, or paste the [system prompt](../examples/system_prompt.md) into your client's system prompt field.
