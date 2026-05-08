"""
OncoAgent — CSS Design System Module.

Centralizes all styling for the Gradio UI. Implements a ChatGPT-style
dark theme with glassmorphism, WCAG AA accessibility, and fixes for
Gradio component transparency bugs.
"""

# Google Fonts loaded via HTML <link> tag (Gradio 6 blocks @import in CSS)
FONTS_LINK: str = (
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Figtree:wght@400;500;600;700&'
    'family=Inter:wght@300;400;500;600&display=swap">'
)

CSS: str = """
/* ══════════════════════════════════════════════════════════════════════
   OncoAgent — Clinical Dark Theme (ChatGPT-style PROMAX)
   Design: Figtree/Inter, Slate-900 bg, Sky-500 accent, WCAG AA+
   ══════════════════════════════════════════════════════════════════════ */

/* ── Reset & Base ────────────────────────────────────────────────────── */
:root {
    --shadow-drop: none !important;
    --shadow-drop-lg: none !important;
    --shadow-inset: none !important;
    --block-shadow: none !important;
    --container-shadow: none !important;
    --body-background-fill: #0f172a !important;
    --background-fill-primary: #0f172a !important;
}
html, body, gradio-app {
    background-color: #0f172a !important;
    background-image: none !important;
    box-shadow: none !important;
    margin: 0 !important;
    padding: 0 !important;
}
.gradio-container, .main, .wrap, .contain,
.gradio-container > div, footer, #__next, #app, main {
    background: #0f172a !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    box-shadow: none !important;
}
.gradio-container {
    max-width: 1440px !important;
    overflow-x: hidden !important;
    margin: 0 auto !important;
    border: none !important;
}
* { box-sizing: border-box; }

/* Force transparent on layout wrappers, but NOT on inputs/tabs */
.gr-group, .gr-block, .gr-box, .gr-panel,
.block, .wrap, .panel, .gap, .gr-padded {
    background: transparent !important;
    border-color: #334155 !important;
}

/* Base background for inputs/forms to fix transparency */
.gr-form, .gr-dropdown, .gr-input, .gr-textbox, .gr-padded, .gr-group {
    background: #1e293b !important;
    background-color: #1e293b !important;
    border-radius: 10px !important;
}

/* Chat Action Buttons */
.chat-action-btn {
    border-radius: 10px !important;
    font-size: 1.2rem !important;
    padding: 10px !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    min-width: 50px !important;
}
.chat-action-btn:hover {
    transform: translateY(-2px) !important;
}

/* ── Header Bar ──────────────────────────────────────────────────────── */
.header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 24px;
    background: #1e293b; /* Solid background to fix transparency */
    border: 1px solid #334155;
    border-radius: 14px;
    margin-bottom: 16px;
}
.brand-name {
    font-family: 'Figtree', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: -0.025em;
}
.hw-badge {
    background: rgba(239, 68, 68, 0.15);
    color: #fca5a5;
    padding: 5px 14px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    border: 1px solid rgba(239, 68, 68, 0.25);
}/* ── Sidebar Column ──────────────────────────────────────────────────── */
.sidebar-column {
    background: #0f172a !important;
    gap: 16px !important;
}

/* ── Cards ────────────────────────────────────────────────────────────── */
.card {
    --block-background-fill: #1e293b !important;
    --background-fill-primary: #1e293b !important;
    --background-fill-secondary: #1e293b !important;
    background: #1e293b !important; /* Solid background */
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 14px !important;
    padding: 18px !important;
    transition: border-color 0.2s ease-out !important;
}
.card > .gr-block, .card > .gr-box, .card .gr-form, .card .gr-group,
.card .gr-padded, .card .gr-block, .card .gr-box, .card .gr-row, .card .gr-col {
    background: #1e293b !important;
    background-color: #1e293b !important;
    border: none !important;
}
.card:hover { border-color: #475569 !important; }

/* ── Chat Input Row & Buttons ────────────────────────────────────────── */
.chat-input-row {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 24px !important;
    padding: 8px 12px !important;
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    margin-top: 10px !important;
}
.chat-input-row .gr-box, .chat-input-row textarea, .chat-input-row input {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
}

.btn-send {
    background: #0ea5e9 !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    padding: 0 !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    font-size: 1.1rem !important;
    border: none !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 2px 8px rgba(14, 165, 233, 0.3) !important;
}
.btn-send:hover {
    transform: translateY(-2px) !important;
    background: #38bdf8 !important;
    box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4) !important;
}


/* ── Section Titles ──────────────────────────────────────────────────── */
.section-title {
    font-family: 'Figtree', sans-serif;
    font-size: 0.8rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── KPI Tiles ───────────────────────────────────────────────────────── */
.kpi-tile {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 10px;
    padding: 14px;
    text-align: center;
    transition: border-color 0.2s ease-out;
}
.kpi-tile:hover { border-color: #0ea5e9 !important; }
.kpi-label {
    font-size: 0.68rem; font-weight: 500; color: #64748b;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;
}
.kpi-value {
    font-family: 'Figtree', sans-serif;
    font-size: 1.4rem; font-weight: 700; color: #f1f5f9;
}

/* ── Primary Button ──────────────────────────────────────────────────── */
.btn-primary {
    background: linear-gradient(135deg, #0ea5e9, #0284c7) !important;
    border: none !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    border-radius: 10px !important;
    cursor: pointer !important;
    transition: transform 0.15s ease-out, box-shadow 0.15s ease-out !important;
}
.btn-primary:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(14, 165, 233, 0.4) !important;
}
.btn-primary:active { transform: translateY(0) !important; }

/* ── Secondary Button ────────────────────────────────────────────────── */
button.secondary, button[variant="secondary"],
.gr-button-secondary, button:not(.btn-primary):not(.selected) {
    background: #1e293b !important;
    color: #e2e8f0 !important;
    border: 1px solid #334155 !important;
}
button.secondary:hover, button[variant="secondary"]:hover {
    background: #334155 !important;
}

/* ── Dropdown / Selector Fix (CRITICAL: Gradio 6 transparency) ───────── */
/* The select element itself */
select, .gr-dropdown select,
[data-testid="dropdown"] select,
.single-select, .multiselect, .gr-dropdown {
    background: #1e293b !important;
    background-color: #1e293b !important;
    color: #e2e8f0 !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    -webkit-appearance: none !important;
    appearance: none !important;
}
select:focus, .gr-dropdown select:focus {
    border-color: #0ea5e9 !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15) !important;
}
/* The dropdown popup/list */
ul.options, .options, .options-wrap,
[data-testid="dropdown"] ul,
.dropdown-content, .gr-dropdown ul,
[class*="dropdown"] ul, [class*="dropdown"] li,
[class*="listbox"], [role="listbox"],
[class*="dropdown-menu"], [class*="select-dropdown"] {
    background: #1e293b !important;
    background-color: #1e293b !important;
    color: #e2e8f0 !important;
    border: 1px solid #475569 !important;
    border-radius: 8px !important;
    z-index: 9999 !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4) !important;
}
ul.options li, .options li,
[role="option"], [class*="dropdown"] li {
    background: #1e293b !important;
    color: #e2e8f0 !important;
    padding: 8px 12px !important;
}
ul.options li.selected, ul.options li:hover,
.options li.selected, .options li:hover,
[role="option"]:hover, [role="option"][aria-selected="true"] {
    background-color: #334155 !important;
    color: #f1f5f9 !important;
}

/* ── Labels (Gradio 6 uses sky color by default, fix for dark) ────────── */
label, .gr-input-label, .label-wrap,
label span, .gr-group label {
    color: #94a3b8 !important;
}
.gr-input-label .text-lg, .label-wrap span {
    color: #cbd5e1 !important;
    font-weight: 500 !important;
}
/* Info text under inputs */
.gr-input-label .text-xs, [class*="info"], .info-text {
    color: #64748b !important;
    font-size: 0.75rem !important;
}

/* ── Safety Badges ───────────────────────────────────────────────────── */
.badge-safe {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(16, 185, 129, 0.12);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
    padding: 4px 12px; border-radius: 6px;
    font-weight: 600; font-size: 0.8rem;
}
.badge-unsafe {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(239, 68, 68, 0.12);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
    padding: 4px 12px; border-radius: 6px;
    font-weight: 600; font-size: 0.8rem;
}

/* ── Critic Feedback Card ────────────────────────────────────────────── */
.critic-card {
    background: rgba(245, 158, 11, 0.06);
    border-left: 3px solid #f59e0b;
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
    margin-top: 16px;
    font-size: 0.85rem;
    color: #cbd5e1;
}
.critic-card strong { color: #fbbf24; }

/* ── Tabs ────────────────────────────────────────────────────────────── */
.tab-nav, .tabs, [role="tablist"] {
    background: transparent !important;
    border-bottom: 1px solid #334155 !important;
}
.tab-nav button, .tabs button, button[role="tab"],
[class*="tab"] button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    color: #94a3b8 !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    transition: color 0.15s ease-out !important;
    cursor: pointer !important;
}
.tab-nav button.selected, .tabs button.selected,
button[role="tab"][aria-selected="true"],
button[role="tab"].selected {
    color: #0ea5e9 !important;
    border-bottom: 2px solid #0ea5e9 !important;
    background: transparent !important;
}
/* Tab content panels — force dark */
.tabitem, .tab-content, [class*="tabitem"],
[role="tabpanel"], .tab-content > div {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-top: none !important;
    border-radius: 0 0 12px 12px !important;
    color: #e2e8f0 !important;
}
/* Markdown inside tabs */
.tabitem .markdown-text, .tabitem .prose,
[role="tabpanel"] p, [role="tabpanel"] .markdown-text {
    color: #cbd5e1 !important;
}

/* ── Input Fields ────────────────────────────────────────────────────── */
textarea, input[type="text"], .gr-text-input {
    background: #0f172a !important;
    border: 1px solid #334155 !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.2s ease-out !important;
}
textarea:focus, input[type="text"]:focus {
    border-color: #0ea5e9 !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15) !important;
}

/* ── Chatbot ─────────────────────────────────────────────────────────── */
.gr-chatbot, [class*="chatbot"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
.message {
    padding: 14px 18px !important;
    border-radius: 14px !important;
    margin-bottom: 10px !important;
    border: 1px solid rgba(255, 255, 255, 0.04) !important;
    background: rgba(30, 41, 59, 0.55) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    line-height: 1.6 !important;
    font-size: 0.92rem !important;
}
.message.user {
    background: rgba(14, 165, 233, 0.08) !important;
    border-color: rgba(14, 165, 233, 0.18) !important;
    border-bottom-right-radius: 4px !important;
}
.message.bot {
    background: rgba(30, 41, 59, 0.55) !important;
    border-color: rgba(51, 65, 85, 0.4) !important;
    border-bottom-left-radius: 4px !important;
}

/* ── Status Bar ──────────────────────────────────────────────────────── */
.status-bar {
    font-size: 0.75rem;
    color: #64748b;
    padding: 8px 0;
    border-top: 1px solid #1e293b;
    margin-top: 8px;
}

/* ── Node Progress Indicator ─────────────────────────────────────────── */
.node-step {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 0.78rem; color: #94a3b8;
    padding: 4px 10px; border-radius: 6px;
    background: rgba(14, 165, 233, 0.08);
    border: 1px solid rgba(14, 165, 233, 0.15);
    margin-right: 6px; margin-bottom: 4px;
}
.node-step.active {
    color: #38bdf8;
    border-color: rgba(14, 165, 233, 0.4);
    animation: pulse-node 1.5s ease-in-out infinite;
}
.node-step.done { color: #34d399; border-color: rgba(16,185,129,0.3); }

@keyframes pulse-node {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* ── Accessibility: Focus Rings ──────────────────────────────────────── */
*:focus-visible {
    outline: 2px solid #0ea5e9 !important;
    outline-offset: 2px !important;
}

/* ── Reduced Motion ──────────────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
"""
