# Odoo MCP Server (`mcp_claude`)

Enterprise Model Context Protocol (MCP) server for Odoo — connect Claude, Cursor, ChatGPT, VS Code and other AI clients.

**Git repo:** https://github.com/Hasnen-mr/mcp_server_zantatech  
**Branches:** `17.0`, `18.0`, `19.0`  
**Module technical name:** `mcp_claude`

## Where to edit code

Always change code in this repository:

```
mcp_server/mcp_claude/
```

Use `git add`, `git commit`, and `git push` from **`mcp_server/`** only.

Do **not** commit from `.local-dev/custom_addons/` — that folder is a runtime copy for local Docker Odoo.

## Local Odoo workflow

After you change code here, copy the module into local Odoo addons:

```bash
bash scripts/sync_to_local_odoo.sh
```

Then restart / upgrade:

```bash
cd ../.local-dev
DB_NAME=twilio_test MODULES=mcp_claude bash restart.sh
```

## Repo layout

- `mcp_claude/` — Odoo module (edit here)
- `scripts/sync_to_local_odoo.sh` — copy module to `.local-dev/custom_addons/`
- `docs/` — architecture and API notes
- `tests/` — test helpers

## Python dependencies

```
pyjwt>=2.8.0
cryptography>=42.0.0
jsonschema>=4.21.0
requests>=2.31.0
```

Install in the Odoo container (or bake into your local Docker image).
