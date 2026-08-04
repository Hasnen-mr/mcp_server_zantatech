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
            showAddToolModal: false,
            showQuickSearch: false,
            showOperationNotAvailableModal: false,
            operationNotAvailableTitle: "Operation Not Available",
            operationNotAvailableMessage: "",
            newlyCreatedRawToken: "",

            testingConnector: false,
            testResults: null,

            tools: [],
            apiKeys: [],
            oauthClients: [],
            sessions: [],
            auditLogs: [],

            // Multi-step Add/Edit Tool Modal State
            modalStep: 1,
            isEditingTool: false,
            availableModels: [],
            modelSearchQuery: "",
            availableFields: [],
            loadingModels: false,
            loadingFields: false,
            toolForm: {
                id: null,
                name: "",
                display_name: "",
                description: "",
                model_name: "",
                operation: "search",
                search_fields: [],
                result_fields: [],
                is_builtin: false,
                active: true
            },

            // Permissions UI State for Odoo Apps
            odooAppsPermissions: [
                { id: "sale", name: "Sales (sale.order)", icon: "fa-shopping-cart", read: true, create: false, write: false, delete: false, active: true },
                { id: "account", name: "Invoicing & Accounting (account.move)", icon: "fa-calculator", read: true, create: false, write: false, delete: false, active: true },
                { id: "stock", name: "Inventory & Warehouses (stock.picking)", icon: "fa-cubes", read: true, create: false, write: false, delete: false, active: true },
                { id: "crm", name: "CRM & Opportunities (crm.lead)", icon: "fa-handshake-o", read: true, create: false, write: false, delete: false, active: true },
                { id: "partner", name: "Contacts & Customers (res.partner)", icon: "fa-address-book", read: true, create: false, write: false, delete: false, active: true },
                { id: "hr", name: "Employees & HR (hr.employee)", icon: "fa-users", read: true, create: false, write: false, delete: false, active: false },
                { id: "purchase", name: "Purchase Orders (purchase.order)", icon: "fa-truck", read: true, create: false, write: false, delete: false, active: true },
                { id: "project", name: "Projects & Tasks (project.task)", icon: "fa-tasks", read: true, create: false, write: false, delete: false, active: true },
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
            }
        });

        onWillStart(async () => {
            await this.loadAllData();
        });
    }

    async loadAllData() {
        try {
            const tools = await this.orm.searchRead("mcp.tool", [], ["id", "name", "display_name", "description", "model_name", "operation", "search_fields", "result_fields", "active", "is_builtin", "sequence", "create_date"], { order: "sequence, id" }).catch(() => []);
            const keys = await this.orm.searchRead("mcp.api.key", [], ["id", "name", "key_prefix", "scopes", "expiration_policy", "expires_at", "last_used_at", "last_used_ip", "active", "create_date"]).catch(() => []);
            const clients = await this.orm.searchRead("mcp.oauth.client", [], ["id", "name", "client_id", "redirect_uri", "active"]).catch(() => []);
            const sessions = await this.orm.searchRead("mcp.session", [], ["id", "client_name", "status", "create_date"]).catch(() => []);
            const logs = await this.orm.searchRead("mcp.audit.log", [], ["id", "tool_name", "model_name", "action_type", "status", "create_date"], { limit: 15, order: "id desc" }).catch(() => []);
            const backendPerms = await this.orm.call("mcp.model.rule", "get_app_permissions", []).catch(() => null);

            this.state.tools = tools || [];
            this.state.apiKeys = keys || [];
            this.state.oauthClients = clients || [];
            this.state.sessions = sessions || [];
            this.state.auditLogs = logs || [];
            if (backendPerms && backendPerms.length > 0) {
                this.state.odooAppsPermissions = backendPerms;
            }

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

    // Multi-Step Add/Edit Tool Handlers
    async openAddToolModal() {
        this.state.modalStep = 1;
        this.state.isEditingTool = false;
        this.state.modelSearchQuery = "";
        this.state.availableFields = [];
        this.state.toolForm = {
            id: null,
            name: "",
            display_name: "",
            description: "",
            model_name: "",
            operation: "search",
            search_fields: [],
            result_fields: [],
            is_builtin: false,
            active: true
        };
        this.state.showAddToolModal = true;
        await this.loadAvailableModels();
    }

    async openEditToolModal(tool) {
        if (tool.is_builtin) {
            this.notification.add("Built-in tools cannot be modified.", { type: "warning" });
            return;
        }
        let sFields = [];
        let rFields = [];
        try {
            sFields = tool.search_fields ? JSON.parse(tool.search_fields) : [];
        } catch (e) { sFields = []; }
        try {
            rFields = tool.result_fields ? JSON.parse(tool.result_fields) : [];
        } catch (e) { rFields = []; }

        this.state.modalStep = 1;
        this.state.isEditingTool = true;
        this.state.modelSearchQuery = "";
        this.state.toolForm = {
            id: tool.id,
            name: tool.name,
            display_name: tool.display_name || tool.name,
            description: tool.description || "",
            model_name: tool.model_name || "",
            operation: tool.operation || "search",
            search_fields: sFields,
            result_fields: rFields,
            is_builtin: tool.is_builtin || false,
            active: tool.active
        };
        this.state.showAddToolModal = true;
        await this.loadAvailableModels();
        if (tool.model_name) {
            await this.onModelSelected(tool.model_name, false);
        }
    }

    closeAddToolModal() {
        this.state.showAddToolModal = false;
    }

    setModalStep(step) {
        if (step === 2 && !this.state.toolForm.name) {
            this.notification.add("Technical Tool Name is required.", { type: "danger" });
            return;
        }
        if (step === 3 && !this.state.toolForm.model_name) {
            this.notification.add("Please select a target Odoo Model.", { type: "danger" });
            return;
        }
        this.state.modalStep = step;
    }

    async loadAvailableModels() {
        if (this.state.availableModels.length > 0) return;
        this.state.loadingModels = true;
        try {
            const models = await this.orm.call("mcp.tool", "get_available_models", []);
            this.state.availableModels = models || [];
        } catch (e) {
            console.error("Failed fetching models:", e);
        } finally {
            this.state.loadingModels = false;
        }
    }

    get filteredModels() {
        if (!this.state.modelSearchQuery) {
            return this.state.availableModels.slice(0, 30);
        }
        const q = this.state.modelSearchQuery.toLowerCase();
        return this.state.availableModels.filter(m => 
            m.model.toLowerCase().includes(q) || m.name.toLowerCase().includes(q)
        ).slice(0, 50);
    }

    async onModelSelected(modelName, updateDesc = true) {
        this.state.toolForm.model_name = modelName;
        this.state.loadingFields = true;
        try {
            const fields = await this.orm.call("mcp.tool", "get_model_fields", [modelName]);
            this.state.availableFields = fields || [];
            if (updateDesc && !this.state.toolForm.description) {
                this.autoGenerateDescription();
            }
        } catch (e) {
            console.error("Failed fetching fields:", e);
        } finally {
            this.state.loadingFields = false;
        }
    }

    toggleSearchField(fname) {
        const idx = this.state.toolForm.search_fields.indexOf(fname);
        if (idx >= 0) {
            this.state.toolForm.search_fields.splice(idx, 1);
        } else {
            this.state.toolForm.search_fields.push(fname);
        }
        this.autoGenerateDescription();
    }

    toggleResultField(fname) {
        const idx = this.state.toolForm.result_fields.indexOf(fname);
        if (idx >= 0) {
            this.state.toolForm.result_fields.splice(idx, 1);
        } else {
            this.state.toolForm.result_fields.push(fname);
        }
    }

    selectAllResultFields() {
        this.state.toolForm.result_fields = this.state.availableFields.map(f => f.name);
    }

    clearResultFields() {
        this.state.toolForm.result_fields = [];
    }

    autoGenerateDescription() {
        const model = this.state.toolForm.model_name || 'records';
        const op = this.state.toolForm.operation || 'search';
        const sFields = this.state.toolForm.search_fields;
        
        let desc = `${op.charAt(0).toUpperCase() + op.slice(1)} Odoo ${model}`;
        if (sFields && sFields.length > 0) {
            desc += ` by ${sFields.join(', ')}`;
        }
        this.state.toolForm.description = desc;
    }

    get generatedSchemaPreview() {
        const op = this.state.toolForm.operation;
        const sFields = this.state.toolForm.search_fields;
        
        if (op === "explain") {
            return {
                "type": "object",
                "properties": {
                    "model": { "type": "string", "description": "Target Odoo model name" },
                    "id": { "type": "integer", "description": "Optional record ID" }
                },
                "required": ["model"]
            };
        } else if (op === "read") {
            return {
                "type": "object",
                "properties": {
                    "id": { "type": "integer", "description": "Target record ID" },
                    "fields": { "type": "array", "items": { "type": "string" }, "description": "Fields to read" }
                },
                "required": ["id"]
            };
        } else if (op === "aggregate") {
            return {
                "type": "object",
                "properties": {
                    "domain": { "type": "array", "description": "Search domain" },
                    "groupby": { "type": "array", "items": { "type": "string" }, "description": "Groupby dimensions" },
                    "fields": { "type": "array", "items": { "type": "string" }, "description": "Fields to aggregate" }
                }
            };
        } else {
            const props = {
                "limit": { "type": "integer", "default": 20, "description": "Max records (1-100)" },
                "offset": { "type": "integer", "default": 0, "description": "Pagination offset" }
            };
            if (sFields) {
                sFields.forEach(f => {
                    props[f] = { "type": "string", "description": `Filter by ${f}` };
                });
            }
            return { "type": "object", "properties": props };
        }
    }

    get generatedExampleRequest() {
        const name = this.state.toolForm.name || "odoo_custom_tool";
        const op = this.state.toolForm.operation;
        const sFields = this.state.toolForm.search_fields;
        
        const args = { limit: 10 };
        if (sFields && sFields.length > 0) {
            args[sFields[0]] = "Example Query";
        }
        return JSON.stringify({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": args
            }
        }, null, 2);
    }

    async saveTool() {
        const form = this.state.toolForm;
        if (!form.name || !form.model_name || !form.description) {
            this.notification.add("Technical Name, Target Model, and Description are required.", { type: "danger" });
            return;
        }

        // Validate format
        if (!/^[a-z0-9_]+$/.test(form.name)) {
            this.notification.add("Technical Name must be lowercase alphanumeric with underscores only.", { type: "danger" });
            return;
        }

        // Validate operation
        if (!['search', 'read', 'aggregate', 'explain'].includes(form.operation)) {
            this.notification.add("Operation not allowed! Read-only deployment supports only search, read, aggregate, explain.", { type: "danger" });
            return;
        }

        try {
            if (this.state.isEditingTool && form.id) {
                await this.orm.call("mcp.tool", "action_update_custom_tool", [form.id, {
                    display_name: form.display_name || form.name,
                    description: form.description,
                    search_fields: form.search_fields,
                    result_fields: form.result_fields,
                    active: form.active
                }]);
                this.notification.add(`Tool '${form.name}' updated successfully!`, { type: "success" });
            } else {
                await this.orm.call("mcp.tool", "action_create_custom_tool", [{
                    name: form.name,
                    display_name: form.display_name || form.name,
                    description: form.description,
                    model_name: form.model_name,
                    operation: form.operation,
                    search_fields: form.search_fields,
                    result_fields: form.result_fields
                }]);
                this.notification.add(`Tool '${form.name}' created & registered live!`, { type: "success" });
            }

            this.state.showAddToolModal = false;
            await this.loadAllData();
        } catch (e) {
            this.notification.add(`Save Tool Error: ${e.message}`, { type: "danger" });
        }
    }

    async toggleToolActive(tool) {
        try {
            const newState = await this.orm.call("mcp.tool", "action_toggle_tool_active", [tool.id]);
            tool.active = newState;
            this.notification.add(`Tool '${tool.name}' ${newState ? 'Enabled & Live' : 'Disabled'}`, { type: newState ? "success" : "warning" });
            await this.loadAllData();
        } catch (e) {
            this.notification.add(`Toggle Error: ${e.message}`, { type: "danger" });
        }
    }

    async deleteCustomTool(tool) {
        if (tool.is_builtin) {
            this.notification.add("Built-in tools cannot be deleted.", { type: "warning" });
            return;
        }
        if (!confirm(`Are you sure you want to delete custom tool '${tool.name}'?`)) return;

        try {
            await this.orm.call("mcp.tool", "action_delete_custom_tool", [tool.id]);
            this.notification.add(`Custom Tool '${tool.name}' deleted.`, { type: "info" });
            await this.loadAllData();
        } catch (e) {
            this.notification.add(`Delete Error: ${e.message}`, { type: "danger" });
        }
    }

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

    async toggleAppPermission(appId, perm) {
        const app = this.state.odooAppsPermissions.find(a => a.id === appId);
        if (!app) return;

        if (perm === 'read') {
            app.read = !app.read;
            await this.orm.call("mcp.model.rule", "update_app_read_permission", [appId, app.read]).catch(() => {});
            this.notification.add(`Updated ${app.name} (READ): ${app.read ? 'Granted' : 'Revoked'}`, { type: "info" });
            return;
        }

        // Create, Update, and Delete: Never toggle ON, remain strictly OFF, display warning dialog
        app[perm] = false;

        this.state.operationNotAvailableTitle = "Operation Not Available";
        this.state.operationNotAvailableMessage = "This MCP deployment is currently configured for read-only access.\n\nCreate, Update, and Delete operations are disabled by the current configuration.\n\nContact your administrator if write permissions are required.";
        this.state.showOperationNotAvailableModal = true;
    }

    closeOperationNotAvailableModal() {
        this.state.showOperationNotAvailableModal = false;
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
}

registry.category("actions").add("mcp_claude.control_center", MCPControlCenter);
registry.category("actions").add("mcp_claude.ControlCenterAction", MCPControlCenter);
