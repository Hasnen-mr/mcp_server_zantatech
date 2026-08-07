/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { AIBubbleTrigger } from "@mcp_claude/js/components/ai_bubble_trigger";
import { AIChatWindow } from "@mcp_claude/js/components/ai_chat_window";

export class AIBubbleContainer extends Component {
    static template = "mcp_claude.AIBubbleContainer";
    static components = { AIBubbleTrigger, AIChatWindow };

    setup() {
        const savedState = localStorage.getItem("mcp_ai_window_open") === "true";
        this.state = useState({
            isOpen: savedState,
        });
    }

    toggleWindow() {
        this.state.isOpen = !this.state.isOpen;
        localStorage.setItem("mcp_ai_window_open", this.state.isOpen);
    }

    closeWindow() {
        this.state.isOpen = false;
        localStorage.setItem("mcp_ai_window_open", false);
    }
}

// Register globally in Odoo 18 main_components registry
registry.category("main_components").add("AIBubbleContainer", {
    Component: AIBubbleContainer,
});
