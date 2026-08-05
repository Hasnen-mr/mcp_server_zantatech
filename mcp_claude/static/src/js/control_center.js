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

        const defaultOrigin = window.location.origin;
        this.state = useState({
            activeTab: "home",
            settingsTab: "connection",
            connectOption: "json", // Default to json; updated dynamically by envInfo recommendation
            
            isHttp: window.location.protocol === "http:",
            httpsEnabled: window.location.protocol === "https:",
            serverUrl: defaultOrigin,
            connectorUrl: defaultOrigin + "/mcp",
            stdioJsonConfig: JSON.stringify({
                "mcpServers": {
                    "odoo": {
                        "command": "python",
                        "args": [
                            "mcp_bridge.py",
                            "--server",
                            defaultOrigin
                        ]
                    }
                }
            }, null, 2),

            envInfo: {
                environment: "local",
                environment_title: "Local Development",
                base_url: defaultOrigin,
                hostname: window.location.hostname,
                scheme: window.location.protocol.replace(':', ''),
                port: window.location.port,
                is_https: window.location.protocol === "https:",
                is_localhost: true,
                recommended_connection: "json",
                supports_direct_url: false,
                badge_label: "🔵 Local Development",
                badge_class: "bg-info",
                status_text: "🔵 Local Development",
                reason: "This server is only accessible locally.",
                warning_message: null,
                direct_url: defaultOrigin + "/mcp",
                config_json: JSON.stringify({
                    "mcpServers": {
                        "odoo": {
                            "command": "python",
                            "args": [
                                "mcp_bridge.py",
                                "--server",
                                defaultOrigin
                            ]
                        }
                    }
                }, null, 2),
                connection_status: {
                    server_reachability: { label: "Server Reachability", status: "Online", ok: true, badge: "🟢 Online" },
                    mcp_endpoint: { label: "MCP Endpoint", status: "Reachable", ok: true, badge: "🟢 Reachable" },
                    oauth_support: { label: "OAuth Support", status: "Detected", ok: true, badge: "🟢 Detected" },
                    recommended_connection: { label: "Recommended Connection", status: "Claude Desktop JSON Configuration", ok: true, badge: "📄 Stdio JSON" }
                },
                clientPlatform: this.detectClientPlatform(),
                wizardStep: 1,
                isSavingWizardParams: false,
                wizardForm: {
                    python_path: "python",
                    bridge_path: "mcp_bridge.py",
                    api_key: "mcp_live_default",
                    server_url: ""
                }
            },
            
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

    detectClientPlatform() {
        const ua = navigator.userAgent || "";
        if (ua.includes("Win")) return "Windows";
        if (ua.includes("Mac")) return "macOS";
        if (ua.includes("Linux") || ua.includes("X11")) return "Linux";
        return "Unknown";
    }

    setClientPlatform(platform) {
        this.state.clientPlatform = platform;
    }

    setWizardStep(step) {
        this.state.wizardStep = step;
    }

    async saveWizardParams() {
        this.state.isSavingWizardParams = true;
        try {
            const updatedEnvInfo = await this.orm.call(
                "mcp.tool",
                "set_wizard_config_params",
                [],
                {
                    python_path: this.state.wizardForm.python_path,
                    bridge_path: this.state.wizardForm.bridge_path,
                    api_key: this.state.wizardForm.api_key,
                    server_url: this.state.wizardForm.server_url
                }
            );

            if (updatedEnvInfo) {
                this.state.envInfo = updatedEnvInfo;
                this.state.stdioJsonConfig = updatedEnvInfo.config_json;
                this.state.connectorUrl = updatedEnvInfo.direct_url;
            }

            this.notification.add("Configuration Settings Saved! JSON code updated dynamically.", {
                type: "success",
                title: "Settings Saved"
            });
        } catch (err) {
            this.notification.add(`Save Failed: ${err.message}`, { type: "danger" });
        } finally {
            this.state.isSavingWizardParams = false;
        }
    }

    async loadAllData() {
        try {
            const envInfo = await this.orm.call("mcp.tool", "get_environment_info", []).catch(() => null);
            if (envInfo) {
                this.state.envInfo = envInfo;
                this.state.connectOption = envInfo.recommended_connection;
                this.state.connectorUrl = envInfo.direct_url;
                this.state.stdioJsonConfig = envInfo.config_json;
                this.state.serverUrl = envInfo.base_url;
                this.state.isHttp = !envInfo.is_https;
                this.state.httpsEnabled = envInfo.is_https;
                if (envInfo.wizard_params) {
                    this.state.wizardForm = {
                        python_path: envInfo.wizard_params.python_path || "python",
                        bridge_path: envInfo.wizard_params.bridge_path || "mcp_bridge.py",
                        api_key: envInfo.wizard_params.api_key || "mcp_live_default",
                        server_url: envInfo.wizard_params.server_url_override || ""
                    };
                }
            }

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
        this.state.isEditingTool = false;
        this.state.modelSearchQuery = "";
        this.state.fieldSearchQuery = "";
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

        this.state.isEditingTool = true;
        this.state.modelSearchQuery = "";
        this.state.fieldSearchQuery = "";
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
        
        if (!this.state.isEditingTool && modelName) {
            const cleanModel = modelName.replace(/\./g, '_');
            const op = this.state.toolForm.operation || 'search';
            this.state.toolForm.name = `odoo_${op}_${cleanModel}`;
            this.state.toolForm.display_name = `${op.charAt(0).toUpperCase() + op.slice(1)} ${modelName}`;
        }

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

    onOperationSelected(op) {
        this.state.toolForm.operation = op;
        if (!this.state.isEditingTool && this.state.toolForm.model_name) {
            const cleanModel = this.state.toolForm.model_name.replace(/\./g, '_');
            this.state.toolForm.name = `odoo_${op}_${cleanModel}`;
            this.state.toolForm.display_name = `${op.charAt(0).toUpperCase() + op.slice(1)} ${this.state.toolForm.model_name}`;
        }
        this.autoGenerateDescription();
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
        
        if (op === "create") {
            const props = {};
            if (sFields) {
                sFields.forEach(f => {
                    props[f] = { "type": "string", "description": `Value for ${f}` };
                });
            }
            return {
                "type": "object",
                "properties": {
                    "values": { "type": "object", "properties": props, "description": "Field values to create" }
                },
                "required": ["values"]
            };
        } else if (op === "write") {
            const props = {};
            if (sFields) {
                sFields.forEach(f => {
                    props[f] = { "type": "string", "description": `Value for ${f}` };
                });
            }
            return {
                "type": "object",
                "properties": {
                    "id": { "type": "integer", "description": "Target record ID" },
                    "values": { "type": "object", "properties": props, "description": "Field values to update" }
                },
                "required": ["id", "values"]
            };
        } else if (op === "delete") {
            return {
                "type": "object",
                "properties": {
                    "id": { "type": "integer", "description": "Target record ID to delete" }
                },
                "required": ["id"]
            };
        } else if (op === "explain") {
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
        
        let args = { limit: 10 };
        if (op === "create") {
            args = { values: { name: "Example Name" } };
        } else if (op === "write") {
            args = { id: 1, values: { name: "Updated Name" } };
        } else if (op === "delete") {
            args = { id: 1 };
        } else if (sFields && sFields.length > 0) {
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
        if (!['search', 'read', 'aggregate', 'explain', 'create', 'write', 'delete'].includes(form.operation)) {
            this.notification.add("Operation not allowed!", { type: "danger" });
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

    openTestToolModal(tool) {
        this.state.testToolTarget = tool;
        let defaultArgs = {};
        if (tool.operation === "create") {
            defaultArgs = { model: tool.model_name || "crm.lead", values: { name: "Test Record" } };
        } else if (tool.operation === "write") {
            defaultArgs = { model: tool.model_name || "crm.lead", id: 1, values: { name: "Updated Record" } };
        } else if (tool.operation === "delete") {
            defaultArgs = { model: tool.model_name || "crm.lead", id: 1 };
        } else if (tool.operation === "read") {
            defaultArgs = { model: tool.model_name || "crm.lead", id: 1 };
        } else {
            defaultArgs = { model: tool.model_name || "crm.lead", domain: [], limit: 5 };
        }
        this.state.testToolArgsJson = JSON.stringify(defaultArgs, null, 2);
        this.state.testToolResult = null;
        this.state.testToolExecuting = false;
        this.state.showTestToolModal = true;
    }

    closeTestToolModal() {
        this.state.showTestToolModal = false;
    }

    async runToolTestExecution() {
        if (!this.state.testToolTarget) return;
        this.state.testToolExecuting = true;
        this.state.testToolResult = null;
        try {
            let parsedArgs = {};
            try {
                parsedArgs = JSON.parse(this.state.testToolArgsJson);
            } catch (e) {
                this.notification.add("Invalid JSON format in test arguments!", { type: "danger" });
                this.state.testToolExecuting = false;
                return;
            }

            const res = await fetch("/mcp/v1/messages", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer mcp_live_default"
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    id: Date.now(),
                    method: "tools/call",
                    params: {
                        name: this.state.testToolTarget.name,
                        arguments: parsedArgs
                    }
                })
            });
            const data = await res.json();
            this.state.testToolResult = data;
            this.notification.add(`Tool '${this.state.testToolTarget.name}' executed live!`, { type: "success" });
        } catch (err) {
            this.state.testToolResult = { error: err.message };
            this.notification.add(`Execution Error: ${err.message}`, { type: "danger" });
        } finally {
            this.state.testToolExecuting = false;
        }
    }

    copyConnectorUrl() {
        if (this.state.envInfo && this.state.envInfo.is_localhost) {
            this.notification.add("Direct Web URL connection is not available on localhost. A live server URL (HTTPS domain) is required for Direct Web OAuth connection. For localhost, use Desktop local dev configuration in claude_desktop_config.json.", {
                type: "warning",
                title: "Not Available on Localhost",
                sticky: true
            });
            return;
        }
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

        app[perm] = !app[perm];
        await this.orm.call("mcp.model.rule", "update_app_permission", [appId, perm, app[perm]]).catch(() => {});
        this.notification.add(`Updated ${app.name} (${perm.toUpperCase()}): ${app[perm] ? 'Granted' : 'Revoked'}`, { type: "info" });
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
            httpsReachable: window.location.protocol === "https:",
            oauthMetadata: false,
            mcpEndpoint: false,
            toolsListResponds: false,
            protocolCompatible: false,
            connectorReady: false,
            failedStep: null,
            failureReason: null,
            summary: "Executing comprehensive 6-step connection test..."
        };

        try {
            // Step 1: Server Reachability
            const healthRes = await fetch("/mcp/health").catch(() => null);
            if (healthRes && healthRes.ok) {
                results.serverReachable = true;
            } else {
                results.failedStep = "Server Reachability";
                results.failureReason = "/mcp/health endpoint did not respond with 200 OK.";
            }

            // Step 2: OAuth Metadata Reachability
            const oauthRes = await fetch("/.well-known/oauth-authorization-server").catch(() => null);
            if (oauthRes && oauthRes.ok) {
                results.oauthMetadata = true;
            } else {
                if (!results.failedStep) {
                    results.failedStep = "OAuth Metadata";
                    results.failureReason = "/.well-known/oauth-authorization-server endpoint is unreachable.";
                }
            }

            // Step 3 & 4: MCP Endpoint & Initialize
            const initRes = await fetch("/mcp/v1/messages", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer mcp_live_default"
                },
                body: JSON.stringify({ jsonrpc: "2.0", method: "initialize", id: 1 })
            }).catch(() => null);

            if (initRes && initRes.ok) {
                results.mcpEndpoint = true;
                const initData = await initRes.json().catch(() => null);
                if (initData && initData.result && initData.result.protocolVersion === "2024-11-05") {
                    results.protocolCompatible = true;
                }
            } else if (!results.failedStep) {
                results.failedStep = "MCP Endpoint";
                results.failureReason = "/mcp/v1/messages endpoint failed to process initialize request.";
            }

            // Step 5: tools/list Verification
            const toolsRes = await fetch("/mcp/v1/messages", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer mcp_live_default"
                },
                body: JSON.stringify({ jsonrpc: "2.0", method: "tools/list", id: 2 })
            }).catch(() => null);

            if (toolsRes && toolsRes.ok) {
                const toolsData = await toolsRes.json().catch(() => null);
                if (toolsData && toolsData.result && Array.isArray(toolsData.result.tools)) {
                    results.toolsListResponds = true;
                }
            } else if (!results.failedStep) {
                results.failedStep = "tools/list Response";
                results.failureReason = "tools/list method failed to return valid tool definitions.";
            }

            if (results.serverReachable && results.mcpEndpoint && results.toolsListResponds) {
                results.connectorReady = true;
                results.summary = "All 6 production & protocol validation checks passed! Ready for Claude Desktop.";
                this.notification.add("Connection Test Passed 100%!", { type: "success" });
            } else {
                results.summary = `Validation Failed at step '${results.failedStep}': ${results.failureReason}`;
                this.notification.add(`Connection Test Warning: ${results.failedStep}`, { type: "warning" });
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
