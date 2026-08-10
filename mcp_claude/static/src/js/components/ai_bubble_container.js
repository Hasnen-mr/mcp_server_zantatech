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
            if (this.state.isHiddenOnClaude) {
                this.state.isOpen = false;
            }
        };

        this._onToggleWindow = (ev) => {
            if (this.state.isHiddenOnClaude) return;
            this.state.isOpen = !this.state.isOpen;
        };

        this._onCloseWindow = (ev) => {
            this.state.isOpen = false;
        };

        this._onClickOutside = (ev) => {
            if (!this.state.isOpen) return;
            const target = ev.target;
            if (!target) return;

            // Check if click target is inside chat window, bubble trigger button, or systray button
            const insideChatWindow = target.closest && target.closest(".o_mcp_ai_chat_window");
            const insideBubbleTrigger = target.closest && target.closest(".o_mcp_ai_bubble_trigger");
            const insideSystrayBtn = target.closest && target.closest(".o_mcp_ai_systray_btn");

            if (!insideChatWindow && !insideBubbleTrigger && !insideSystrayBtn) {
                this.state.isOpen = false;
            }
        };

        this._onKeyDown = (ev) => {
            if (this.state.isOpen && (ev.key === "Escape" || ev.key === "Esc")) {
                this.state.isOpen = false;
            }
        };

        window.addEventListener("mcp_tab_changed", this._onTabChange);
        window.addEventListener("toggle_mcp_ai_window", this._onToggleWindow);
        window.addEventListener("close_mcp_ai_window", this._onCloseWindow);
        document.addEventListener("pointerdown", this._onClickOutside);
        document.addEventListener("keydown", this._onKeyDown);

        onWillUnmount(() => {
            window.removeEventListener("mcp_tab_changed", this._onTabChange);
            window.removeEventListener("toggle_mcp_ai_window", this._onToggleWindow);
            window.removeEventListener("close_mcp_ai_window", this._onCloseWindow);
            document.removeEventListener("pointerdown", this._onClickOutside);
            document.removeEventListener("keydown", this._onKeyDown);
        });
    }

    toggleWindow() {
        if (this.state.isHiddenOnClaude) return;
        this.state.isOpen = !this.state.isOpen;
    }

    closeWindow() {
        this.state.isOpen = false;
    }
}

registry.category("main_components").add("AIBubbleContainer", {
    Component: AIBubbleContainer,
});