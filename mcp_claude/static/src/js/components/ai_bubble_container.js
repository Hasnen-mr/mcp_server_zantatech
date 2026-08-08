/** @odoo-module **/

import { Component, useState, onWillStart, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { AIBubbleTrigger } from "@mcp_claude/js/components/ai_bubble_trigger";
import { AIChatWindow } from "@mcp_claude/js/components/ai_chat_window";

export class AIBubbleContainer extends Component {
    static template = "mcp_claude.AIBubbleContainer";
    static components = { AIBubbleTrigger, AIChatWindow };

    setup() {
        const activeTab = localStorage.getItem("mcp_active_tab") || "dashboard";
        this.state = useState({
            isOpen: false,
            isHiddenOnClaude: activeTab === "claude",
        });

        this._onTabChange = (ev) => {
            const currentTab = (ev.detail && ev.detail.tab) || localStorage.getItem("mcp_active_tab");
            this.state.isHiddenOnClaude = (currentTab === "claude");
        };

        window.addEventListener("mcp_tab_changed", this._onTabChange);

        onWillUnmount(() => {
            window.removeEventListener("mcp_tab_changed", this._onTabChange);
        });
    }

    toggleWindow() {
        this.state.isOpen = !this.state.isOpen;
    }

    closeWindow() {
        this.state.isOpen = false;
    }
}

registry.category("main_components").add("AIBubbleContainer", {
    Component: AIBubbleContainer,
});