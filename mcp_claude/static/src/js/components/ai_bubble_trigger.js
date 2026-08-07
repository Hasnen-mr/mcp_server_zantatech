/** @odoo-module **/

import { Component } from "@odoo/owl";

export class AIBubbleTrigger extends Component {
    static template = "mcp_claude.AIBubbleTrigger";
    static props = {
        onClick: Function,
        isOpen: Boolean,
    };
}
