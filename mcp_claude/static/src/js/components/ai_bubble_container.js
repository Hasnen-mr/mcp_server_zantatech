/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { AIBubbleTrigger } from "@mcp_claude/js/components/ai_bubble_trigger";
import { AIChatWindow } from "@mcp_claude/js/components/ai_chat_window";

export class AIBubbleContainer extends Component {
    static template = "mcp_claude.AIBubbleContainer";
    static components = { AIBubbleTrigger, AIChatWindow };

    setup() {
        this.state = useState({
            isOpen: false,
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
