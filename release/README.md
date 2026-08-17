# MCP Claude Integration for Odoo — Release Packages & Installers

This release package contains ready-to-use, version-specific MCP Claude modules and automated installers for **Odoo 17**, **Odoo 18**, and **Odoo 19**.

---

## 📁 Release Directory Structure

```text
release/
  ├── installer/
  │   ├── install_windows.ps1    # Automated PowerShell installer for Windows
  │   ├── install_windows.bat    # Windows double-click launcher
  │   └── install_mac.sh         # Automated Shell installer for macOS / Linux
  ├── packages/
  │   ├── mcp_claude_17.0.zip    # Module package tailored for Odoo 17
  │   ├── mcp_claude_18.0.zip    # Module package tailored for Odoo 18
  │   └── mcp_claude_19.0.zip    # Module package tailored for Odoo 19
  └── README.md
```

---

## 🚀 Quick Automated Installation

### Windows Users
1. Double-click **`installer/install_windows.bat`**  
   *(or right-click `install_windows.ps1` and select **Run with PowerShell**)*.
2. Select your Odoo installation directory from the auto-detected list (or enter custom path).
3. The installer will auto-detect your Odoo version (17, 18, or 19), extract the matching `mcp_claude` package into `custom_addons`, update `odoo.conf`, and install required Python packages (`PyJWT`, `requests`, `cryptography`).

### macOS / Linux Users
1. Open Terminal and navigate to the `release/` directory.
2. Run:
   ```bash
   chmod +x installer/install_mac.sh
   ./installer/install_mac.sh
   ```
3. Follow the interactive prompts to detect/select your Odoo folder and complete installation.

---

## 🛠️ Manual Installation (Alternative)

If you prefer installing manually:

1. Identify your Odoo version:
   * **Odoo 17:** Use `packages/mcp_claude_17.0.zip`
   * **Odoo 18:** Use `packages/mcp_claude_18.0.zip`
   * **Odoo 19:** Use `packages/mcp_claude_19.0.zip`
2. Extract the matching `.zip` package into your Odoo `custom_addons` folder.
3. Ensure the extracted folder is named **`mcp_claude`** and contains `__manifest__.py` directly at its root:
   ```text
   custom_addons/mcp_claude/__manifest__.py
   ```
4. Verify `addons_path` in your `odoo.conf` includes the `custom_addons` directory.
5. Install Python dependencies:
   ```bash
   pip install PyJWT requests cryptography
   ```

---

## 📲 Enabling the Module in Odoo

1. Restart your Odoo server.
2. Log into Odoo as an Administrator.
3. Go to **Settings** $\rightarrow$ scroll down and click **Activate Developer Mode**.
4. Navigate to the **Apps** menu.
5. Click **Update Apps List** in the top navigation bar.
6. Search for **`MCP Claude`** in the search bar.
7. Click **Activate** (or Install).
8. Open **MCP Claude** $\rightarrow$ **Control Center** to set up your API keys and configuration profiles.
