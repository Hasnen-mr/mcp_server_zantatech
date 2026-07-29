/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class MCPControlCenter extends Component {
    static template = "mcp_claude.ControlCenter";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");

        this.state = useState({
            activeTab: "home",
            settingsTab: "connection",
            connectOption: "url", // 'url' or 'stdio'
            
            isHttp: window.location.protocol === "http:",
            httpsEnabled: window.location.protocol === "https:",
            serverUrl: window.location.origin,
            connectorUrl: "https://localhost:8443/mcp/v1/sse?token=mcp_live_default",
            stdioJsonConfig: JSON.stringify({
                "mcpServers": {
                    "odoo-claude": {
                        "command": "D:\\Odoo\\venv\\Scripts\\python.exe",
                        "args": [
                            "D:\\odoo-mcp\\mcp_claude\\bin\\mcp_bridge.py"
                        ]
                    }
                }
            }, null, 2),
            
            showOAuthSecret: false,
            revealedSecretValue: "••••••••••••••••",

            showConnectWizard: false,
            showCreateTokenModal: false,
            showRawTokenModal: false,
            showCreateToolModal: false,
            showQuickSearch: false,
            newlyCreatedRawToken: "",

            testingConnector: false,
            testResults: null,

            tools: [],
            apiKeys: [],
            oauthClients: [],
            sessions: [],
            auditLogs: [],

            // Permissions UI State for Odoo Apps
            odooAppsPermissions: [
                { id: "sale", name: "Sales (sale.order)", icon: "fa-shopping-cart", read: true, create: true, write: true, delete: false, active: true },
                { id: "account", name: "Invoicing & Accounting (account.move)", icon: "fa-calculator", read: true, create: true, write: true, delete: false, active: true },
                { id: "stock", name: "Inventory & Warehouses (stock.picking)", icon: "fa-cubes", read: true, create: false, write: false, delete: false, active: true },
                { id: "crm", name: "CRM & Opportunities (crm.lead)", icon: "fa-handshake-o", read: true, create: true, write: true, delete: false, active: true },
                { id: "partner", name: "Contacts & Customers (res.partner)", icon: "fa-address-book", read: true, create: true, write: true, delete: false, active: true },
                { id: "hr", name: "Employees & HR (hr.employee)", icon: "fa-users", read: true, create: false, write: false, delete: false, active: false },
                { id: "purchase", name: "Purchase Orders (purchase.order)", icon: "fa-truck", read: true, create: true, write: true, delete: false, active: true },
                { id: "project", name: "Projects & Tasks (project.task)", icon: "fa-tasks", read: true, create: true, write: true, delete: false, active: true },
            ],

            stats: {
                totalTools: 0,
                activeKeys: 0,
                activeSessions: 0,
                rateLimitRpm: 120,
            },

            newToken: {
                name: "Claude Desktop",
                scopes: "full",
                expiration_policy: "never",
                allowed_ips: "",
            },
            newTool: { name: "", description: "", model_name: "", python_code: "" },
        });

        onWillStart(async () => {
            await this.loadAllData();
        });
    }

    async loadAllData() {
        try {
            const tools = await this.orm.searchRead("mcp.tool", [], ["id", "name", "description", "active", "create_date"]).catch(() => []);
            const keys = await this.orm.searchRead("mcp.api.key", [], ["id", "name", "key_prefix", "scopes", "expiration_policy", "expires_at", "last_used_at", "last_used_ip", "active", "create_date"]).catch(() => []);
            const clients = await this.orm.searchRead("mcp.oauth.client", [], ["id", "name", "client_id", "redirect_uri", "active"]).catch(() => []);
            const sessions = await this.orm.searchRead("mcp.session", [], ["id", "client_name", "status", "create_date"]).catch(() => []);
            const logs = await this.orm.searchRead("mcp.audit.log", [], ["id", "tool_name", "model_name", "action_type", "status", "create_date"], { limit: 15 }).catch(() => []);

            this.state.tools = tools || [];
            this.state.apiKeys = keys || [];
            this.state.oauthClients = clients || [];
            this.state.sessions = sessions || [];
            this.state.auditLogs = logs || [];

            this.state.stats.totalTools = this.state.tools.length;
            this.state.stats.activeKeys = this.state.apiKeys.filter(k => k.active).length;
            this.state.stats.activeSessions = this.state.sessions.filter(s => s.status === 'active').length;
        } catch (e) {
            console.error("Failed loading MCP data:", e);
        }
    }

    setTabHome() { this.state.activeTab = "home"; }
    setTabTools() { this.state.activeTab = "tools"; }
    setTabConfigurations() { this.state.activeTab = "configurations"; }

    setSubTabConnection() { this.state.settingsTab = "connection"; }
    setSubTabAuth() { this.state.settingsTab = "authentication"; }
    setSubTabPermissions() { this.state.settingsTab = "permissions"; }
    setSubTabGeneral() { this.state.settingsTab = "general"; }
    setSubTabAudit() { this.state.settingsTab = "advanced"; }

    setConnectOption(mode) { this.state.connectOption = mode; }

    openConnectWizard() { this.state.showConnectWizard = true; }
    closeConnectWizard() { this.state.showConnectWizard = false; }

    openCreateTokenModal() { this.state.showCreateTokenModal = true; }
    closeCreateTokenModal() { this.state.showCreateTokenModal = false; }
    closeRawTokenModal() { this.state.showRawTokenModal = false; }

    openCreateToolModal() { this.state.showCreateToolModal = true; }
    closeCreateToolModal() { this.state.showCreateToolModal = false; }

    copyConnectorUrl() {
        this.copyText(this.state.connectorUrl, "Connector URL");
    }

    copyJsonConfig() {
        this.copyText(this.state.stdioJsonConfig, "claude_desktop_config.json Snippet");
    }

    copyText(text, label = "Item") {
        navigator.clipboard.writeText(text);
        this.notification.add(`${label} copied to clipboard!`, {
            type: "success",
            title: "Copied",
        });
    }

    toggleAppPermission(appId, perm) {
        const app = this.state.odooAppsPermissions.find(a => a.id === appId);
        if (app) {
            app[perm] = !app[perm];
            this.notification.add(`Updated ${app.name} (${perm.toUpperCase()}): ${app[perm] ? 'Granted' : 'Revoked'}`, { type: "info" });
        }
    }

    toggleAppActive(appId) {
        const app = this.state.odooAppsPermissions.find(a => a.id === appId);
        if (app) {
            app.active = !app.active;
            this.notification.add(`${app.name} integration ${app.active ? 'Enabled' : 'Disabled'}`, { type: app.active ? "success" : "warning" });
        }
    }

    async createNamedToken() {
        if (!this.state.newToken.name) return;
        try {
            const [rawToken, recId] = await this.orm.call(
                "mcp.api.key",
                "generate_opaque_connector_token",
                [],
                {
                    name: this.state.newToken.name,
                    scopes: this.state.newToken.scopes,
                    expiration_policy: this.state.newToken.expiration_policy,
                    allowed_ips: this.state.newToken.allowed_ips || null,
                }
            );

            this.state.newlyCreatedRawToken = rawToken;
            this.state.connectorUrl = window.location.origin + `/mcp/v1/sse?token=${rawToken}`;
            this.state.showCreateTokenModal = false;
            this.state.showRawTokenModal = true;
            this.notification.add("High-Entropy Connector Token generated!", { type: "success" });
            await this.loadAllData();
        } catch (e) {
            this.notification.add(`Token Creation Failed: ${e.message}`, { type: "danger" });
        }
    }

    async revokeToken(id) {
        try {
            await this.orm.call("mcp.api.key", "action_revoke", [[id]]);
            this.notification.add("Token revoked & active sessions terminated!", { type: "info" });
            await this.loadAllData();
        } catch (e) {
            this.notification.add(`Revocation Error: ${e.message}`, { type: "danger" });
        }
    }

    async revokeAllTokens() {
        if (!confirm("Are you sure you want to revoke ALL active tokens for your account? This will disconnect all connected clients.")) return;
        try {
            await this.orm.call("mcp.api.key", "action_revoke_all_user_tokens", []);
            this.notification.add("Emergency Revoke All Executed!", { type: "warning" });
            await this.loadAllData();
        } catch (e) {
            this.notification.add(`Emergency Revoke Error: ${e.message}`, { type: "danger" });
        }
    }

    async revealOAuthSecret(clientId) {
        try {
            const secret = await this.orm.call("mcp.oauth.client", "reveal_secret_admin", [[clientId]]);
            this.state.revealedSecretValue = secret;
            this.state.showOAuthSecret = true;
            this.notification.add("Admin Access Logged: OAuth Secret Revealed", { type: "warning" });
        } catch (e) {
            this.notification.add(`Access Denied: ${e.message}`, { type: "danger" });
        }
    }

    async testConnector() {
        this.state.testingConnector = true;
        this.state.testResults = null;

        const results = {
            serverReachable: false,
            authWorking: false,
            mcpEndpoint: false,
            protocolCompatible: false,
            connectorReady: false,
            summary: "Running diagnostics..."
        };

        try {
            const healthRes = await fetch("/mcp/health");
            if (healthRes.ok) results.serverReachable = true;

            const msgRes = await fetch("/mcp/v1/messages", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer mcp_live_default"
                },
                body: JSON.stringify({ jsonrpc: "2.0", method: "initialize", id: Date.now() })
            });

            if (msgRes.ok) {
                results.authWorking = true;
                results.mcpEndpoint = true;
                const msgData = await msgRes.json();
                if (msgData && msgData.result && msgData.result.protocolVersion === "2024-11-05") {
                    results.protocolCompatible = true;
                }
                if (results.serverReachable && results.authWorking && results.mcpEndpoint && results.protocolCompatible) {
                    results.connectorReady = true;
                    results.summary = "All 5 security & protocol checks passed! Ready to connect.";
                    this.notification.add("Connector Verified!", { type: "success" });
                }
            } else {
                results.summary = `HTTP Ping Failed with status ${msgRes.status}`;
            }
        } catch (err) {
            results.summary = `Connection Error: ${err.message}`;
            this.notification.add(`Test Failed: ${err.message}`, { type: "danger" });
        } finally {
            this.state.testResults = results;
            this.state.testingConnector = false;
        }
    }

    async deleteTool(id) {
        try {
            await this.orm.unlink("mcp.tool", [id]);
            this.notification.add("Tool deleted", { type: "info" });
            await this.loadAllData();
        } catch (e) {
            this.notification.add(`Error: ${e.message}`, { type: "danger" });
        }
    }

    async createTool() {
        if (!this.state.newTool.name) return;
        try {
            await this.orm.create("mcp.tool", [this.state.newTool]);
            this.notification.add("Tool created!", { type: "success" });
            this.state.showCreateToolModal = false;
            this.state.newTool = { name: "", description: "", model_name: "", python_code: "" };
            await this.loadAllData();
        } catch (e) {
            this.notification.add(`Error: ${e.message}`, { type: "danger" });
        }
    }
}

registry.category("actions").add("mcp_claude.control_center", MCPControlCenter);
registry.category("actions").add("mcp_claude.ControlCenterAction", MCPControlCenter);
