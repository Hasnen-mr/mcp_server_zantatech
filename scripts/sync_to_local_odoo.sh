#!/usr/bin/env bash
# Copy mcp_claude from this git repo into the local Odoo custom_addons folder.
# Edit code here in mcp_server/, commit with git, then run this script.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODULE_SRC="$REPO_ROOT/mcp_claude"
LOCAL_DEV="${LOCAL_DEV:-$REPO_ROOT/../.local-dev}"
ADDONS_DIR="$LOCAL_DEV/custom_addons"
TARGET="$ADDONS_DIR/mcp_claude"

if [[ ! -d "$MODULE_SRC" ]]; then
  echo "ERROR: Module not found: $MODULE_SRC"
  exit 1
fi

mkdir -p "$ADDONS_DIR"
rsync -a --delete \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  "$MODULE_SRC/" "$TARGET/"

echo "Synced: $MODULE_SRC -> $TARGET"
echo "Restart Odoo to load changes, for example:"
echo "  cd $LOCAL_DEV && bash restart.sh"
echo "Or upgrade only MCP:"
echo "  cd $LOCAL_DEV && DB_NAME=twilio_test MODULES=mcp_claude bash restart.sh"
