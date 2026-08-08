/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, useRef } from "@odoo/owl";
import { useService, useBus } from "@web/core/utils/hooks";
import { routerBus } from "@web/core/browser/router";
import { AIChatSkeleton } from "@mcp_claude/js/components/ai_chat_skeleton";

export class AIChatWindow extends Component {
    static template = "mcp_claude.AIChatWindow";
    static components = { AIChatSkeleton };
    static props = {
        onClose: Function,
    };

    setup() {
        this.aiService = useService("ai_chat_service");
        this.notification = useService("notification");
        this.chatBodyRef = useRef("chatBody");
        
        this.isUserScrolledUp = false;
        this.navDebounceTimer = null;
        this.fastLoadTimer = null;
        this.isSwitchingContext = false;
        this.activeAbortController = null;

        // Map to preserve unsent prompt draft text per conversation/scope
        this.draftPrompts = {};

        this.state = useState({
            initialLoading: true,        // Full skeleton on first component mount
            isSwitchingThread: false,     // Semi-transparent overlay on context switch
            sending: false,
            promptText: "",
            history: [],
            activeModel: null,
            activeResId: null,
            activeScope: "global",
            activeConvId: null,
            title: "MCP Claude AI Bubble",
            capabilities: null,
        });

        // Single-tick debounced event listeners for Odoo Action Manager and URL Router
        useBus(this.env.bus, "ACTION_MANAGER:UPDATE", (ev) => this.handleEvent("ACTION_MANAGER:UPDATE", ev));
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", (ev) => this.handleEvent("ACTION_MANAGER:UI-UPDATED", ev));
        useBus(routerBus, "ROUTE_CHANGE", (ev) => this.handleEvent("ROUTE_CHANGE", ev));

        onWillStart(async () => {
            await this.loadChat(null, true);
        });

        onMounted(() => {
            this.scrollToBottom(true);
        });
    }

    handleEvent(eventName, ev) {
        const context = this.aiService.collectActiveContext();
        const newModel = context.resModel || null;
        const newResId = context.resId || null;

        // Single-tick debounce (120ms) to coalesce rapid navigation clicks
        if (this.navDebounceTimer) {
            clearTimeout(this.navDebounceTimer);
        }
        this.navDebounceTimer = setTimeout(() => {
            this.onNavigationChange(eventName, newModel, newResId);
        }, 120);
    }

    async onNavigationChange(triggerEvent, newModel, newResId) {
        // Enforce Global Scope Baseline: Do not switch AI conversation threads on view navigation
        return;
    }

    async loadChat(forcedScope = null, isInitial = false) {
        // 1. Abort any active in-flight HTTP RPC request to prevent backend load & race conditions
        if (this.activeAbortController) {
            this.activeAbortController.abort();
            this.activeAbortController = null;
        }

        // Create new AbortController for this request
        const abortController = new AbortController();
        this.activeAbortController = abortController;

        // 2. Preserve draft input for previous conversation ID
        if (this.state.activeConvId && this.state.promptText) {
            this.draftPrompts[this.state.activeConvId] = this.state.promptText;
        }

        if (isInitial) {
            this.state.initialLoading = true;
        } else {
            // <100ms Fast Load Bypassing: Start 100ms timer before showing skeleton overlay
            if (this.fastLoadTimer) clearTimeout(this.fastLoadTimer);
            this.fastLoadTimer = setTimeout(() => {
                if (this.activeAbortController === abortController) {
                    this.state.isSwitchingThread = true; // Show semi-transparent skeleton overlay
                }
            }, 100);
        }

        try {
            const scope = "global";

            // Fetch thread data with AbortSignal
            const res = await this.aiService.initChat(
                "global",
                null,
                null,
                null,
                abortController.signal
            );

            // If request was aborted by newer navigation, exit without mutating UI state
            if (res && res.aborted) {
                return;
            }

            // Atomic Synchronous State Mutation (Single OWL Render Cycle)
            if (res && res.success) {
                this.state.activeScope = "global";
                this.state.activeConvId = res.conversation_id;
                this.state.history = res.history || [];
                this.state.title = res.title || "MCP Claude AI Bubble";
                this.state.capabilities = res.capabilities || null;

                // Restore preserved draft prompt for new conversation
                this.state.promptText = this.draftPrompts[res.conversation_id] || "";
            } else if (!res) {
                this.notification.add("Failed to initialize AI Chat session. Please try again.", { type: "warning" });
            }
        } catch (err) {
            console.error("[AIChatWindow loadChat Error]", err);
        } finally {
            if (this.fastLoadTimer) clearTimeout(this.fastLoadTimer);
            this.state.initialLoading = false;
            this.state.isSwitchingThread = false;
            if (this.activeAbortController === abortController) {
                this.activeAbortController = null;
            }
            this.scrollToBottom(true);
        }
    }

    async setScope(scope) {
        return;
    }

    onScroll(ev) {
        const el = ev.target;
        const threshold = 60;
        const isAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight <= threshold;
        this.isUserScrolledUp = !isAtBottom;
    }

    scrollToBottom(force = false) {
        setTimeout(() => {
            if (!this.chatBodyRef.el) return;
            if (force || !this.isUserScrolledUp) {
                this.chatBodyRef.el.scrollTop = this.chatBodyRef.el.scrollHeight;
            }
        }, 50);
    }

    async onSendMessage() {
        const text = (this.state.promptText || "").trim();
        if (!text || this.state.sending) return;

        this.state.sending = true;
        this.state.promptText = "";
        if (this.state.activeConvId) {
            delete this.draftPrompts[this.state.activeConvId];
        }

        this.isUserScrolledUp = false;
        
        // Optimistic User Message
        this.state.history.push({
            id: Date.now(),
            role: "user",
            content: text,
            block_type: "markdown"
        });

        this.scrollToBottom(true);

        const res = await this.aiService.sendMessage(text);
        if (res && res.success) {
            if (res.response_block) {
                this.state.history.push({
                    id: Date.now() + 1,
                    role: "assistant",
                    content: res.response_block.content,
                    block_type: res.response_block.block_type || "markdown"
                });
            }
        } else {
            this.state.history.push({
                id: Date.now() + 1,
                role: "assistant",
                content: `Error: ${res.error || "Failed to generate response"}`,
                block_type: "error"
            });
        }
        this.state.sending = false;
        this.scrollToBottom();
    }

    onKeyDown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.onSendMessage();
        }
    }
}
