"""
OncoAgent — Clinical Triage Dashboard (UI Module).

Provides a Gradio-based interface for the multi-agent oncological
triage system. Designed following WCAG AA accessibility standards
with a clinical-grade dark theme optimized for healthcare professionals.
"""

import os
import time
import psutil
import random
import gradio as gr
from typing import Dict, Any, List, Tuple, Optional
from dotenv import load_dotenv

# Import our LangGraph engine
from agents.graph import build_oncoagent_graph

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# SVG Icon Library (replaces emoji usage per ui-ux-pro-max checklist)
# ---------------------------------------------------------------------------
ICONS: Dict[str, str] = {
    "patient": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    "edit": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/></svg>',
    "play": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>',
    "clock": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "shield": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "database": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
    "cpu": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>',
    "book": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
    "globe": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    "graph": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "refresh": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>',
    "check": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    "alert": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f87171" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
}


# ---------------------------------------------------------------------------
# Custom CSS — Clinical Dark Theme
# Design System: Figtree/Inter, Slate-900 bg, Sky-500 accent, WCAG AA+
# ---------------------------------------------------------------------------
# Google Fonts loaded via HTML <link> tag (Gradio 6 blocks @import in CSS)
FONTS_LINK = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap">' 

CSS = """
/* ── Base ────────────────────────────────────────────────────────────── */
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
    background-color: #0f172a !important;
    background-image: none !important;
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
/* Kill any white bleed outside container */
* { box-sizing: border-box; }

/* Force dark on ALL Gradio internal wrappers */
.gr-group, .gr-block, .gr-box, .gr-panel, .gr-form,
.block, .wrap, .panel, form, .gap, .gr-padded,
[class*="svelte-"], .tabitem, .tab-content {
    background: transparent !important;
    border-color: #334155 !important;
}

/* Secondary / default buttons */
button.secondary, button[variant="secondary"],
.gr-button-secondary, button:not(.btn-primary):not(.selected) {
    background: #1e293b !important;
    color: #e2e8f0 !important;
    border: 1px solid #334155 !important;
}
button.secondary:hover, button[variant="secondary"]:hover {
    background: #334155 !important;
}

/* ── Cards ───────────────────────────────────────────────────────────── */
.card {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 12px !important;
    padding: 20px !important;
    transition: border-color 0.2s ease-out, box-shadow 0.2s ease-out !important;
}
.card:hover {
    border-color: #475569 !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
}

/* ── Header ──────────────────────────────────────────────────────────── */
.header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    margin-bottom: 20px;
}
.brand-name {
    font-family: 'Figtree', sans-serif;
    font-size: 1.75rem;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: -0.025em;
}
.hw-badge {
    background: rgba(239, 68, 68, 0.15);
    color: #fca5a5;
    padding: 5px 14px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    border: 1px solid rgba(239, 68, 68, 0.25);
}

/* ── Section Titles ──────────────────────────────────────────────────── */
.section-title {
    font-family: 'Figtree', sans-serif;
    font-size: 0.875rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── KPI Tiles ───────────────────────────────────────────────────────── */
.kpi-tile {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    transition: border-color 0.2s ease-out;
}
.kpi-tile:hover { border-color: #0ea5e9; }
.kpi-label {
    font-size: 0.7rem;
    font-weight: 500;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
}
.kpi-value {
    font-family: 'Figtree', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #f1f5f9;
}

/* ── Primary Action Button ───────────────────────────────────────────── */
.btn-primary {
    background: linear-gradient(135deg, #0ea5e9, #0284c7) !important;
    border: none !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    border-radius: 8px !important;
    cursor: pointer !important;
    transition: transform 0.15s ease-out, box-shadow 0.15s ease-out !important;
}
.btn-primary:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(14, 165, 233, 0.4) !important;
}
.btn-primary:active { transform: translateY(0) !important; }

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

/* ── Telemetry Grid ──────────────────────────────────────────────────── */
.telemetry-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
}
.telemetry-item {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 10px;
    text-align: center;
}
.telemetry-label { font-size: 0.65rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; }
.telemetry-value { font-family: 'Figtree', sans-serif; font-size: 1rem; font-weight: 600; color: #e2e8f0; }
.telemetry-status { font-size: 0.65rem; color: #10b981; }

/* ── Tabs ────────────────────────────────────────────────────────────── */
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
.tabitem, .tab-content, [class*="tabitem"] {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-top: none !important;
    border-radius: 0 0 12px 12px !important;
}

/* ── Input Fields ────────────────────────────────────────────────────── */
textarea, input[type="text"], .gr-text-input {
    background: #0f172a !important;
    border: 1px solid #334155 !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.2s ease-out !important;
}
textarea:focus, input[type="text"]:focus {
    border-color: #0ea5e9 !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15) !important;
}

/* ── Status Bar ──────────────────────────────────────────────────────── */
.status-bar {
    font-size: 0.75rem;
    color: #64748b;
    padding: 8px 0;
    border-top: 1px solid #1e293b;
    margin-top: 12px;
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


# ---------------------------------------------------------------------------
# Initialize Graph
# ---------------------------------------------------------------------------
agent_graph = build_oncoagent_graph()


def generate_patient_id() -> str:
    """Generate a randomized patient session identifier."""
    return f"PT-{random.randint(1000, 9999)}"


# ---------------------------------------------------------------------------
# Core Triage Function
# ---------------------------------------------------------------------------
def run_triage(
    clinical_text: str,
    patient_id: str,
    tier_override: str,
) -> Tuple[str, Dict[str, str], str, str, str, str]:
    """Execute the multi-agent triage graph and format results.

    Args:
        clinical_text: Raw clinical notes from the user.
        patient_id: Session identifier for memory isolation.
        tier_override: Model tier selection (auto / 9b / 27b).

    Returns:
        Tuple of (summary_md, stats_dict, sources_md, graph_md, api_md, status).
    """
    if not clinical_text.strip():
        return "Please enter a clinical case.", {}, "", "", "", ""
    if not patient_id.strip():
        patient_id = "PT-UNKNOWN"

    start_time: float = time.time()

    try:
        final_state = agent_graph.invoke(
            {
                "clinical_text": clinical_text,
                "manual_override": tier_override if tier_override != "auto" else None,
                "errors": [],
            },
            config={"configurable": {"thread_id": patient_id}},
        )
    except Exception as e:
        return f"Error running triage: {str(e)}", {}, "", "", "", ""

    latency: float = time.time() - start_time

    # Extract results
    recommendation: str = final_state.get(
        "formatted_recommendation",
        final_state.get("clinical_recommendation", "No recommendation generated."),
    )
    safety_status: str = final_state.get("safety_status", "Unknown")
    is_safe: bool = final_state.get("is_safe", False)
    confidence: float = final_state.get("rag_confidence", 0.0)
    sources: List[str] = final_state.get("rag_sources", [])
    graph_context: List[str] = final_state.get("graph_rag_context", [])
    api_context: List[str] = final_state.get("api_evidence_context", [])
    critic_feedback: List[str] = final_state.get("critic_feedback", [])

    # Format summary with clean badges (no emojis)
    if is_safe:
        safety_badge = f"<span class='badge-safe'>{ICONS['check']} Clinically Safe</span>"
    else:
        safety_badge = f"<span class='badge-unsafe'>{ICONS['alert']} Review Required</span>"

    summary_md = f"### Decision Status: {safety_badge}\n\n"
    summary_md += f"{recommendation}\n\n---\n"
    summary_md += f"**Safety Audit:** {safety_status}\n"

    if critic_feedback:
        summary_md += "\n<div class='critic-card'><strong>Critic Iterations:</strong><br/>"
        summary_md += "<br/>".join([f"— {fb}" for fb in critic_feedback])
        summary_md += "</div>"

    # Format evidence tabs
    sources_md = (
        "### Medical Guidelines (NCCN / ESMO)\n\n" + "\n".join(sources)
        if sources
        else "No guideline sources retrieved."
    )
    graph_md = (
        "### Clinical Knowledge Graph\n\n"
        + "\n".join([f"- {item}" for item in graph_context])
        if graph_context
        else "No graph relations extracted."
    )
    api_md = (
        "### Real-Time Evidence (CIViC & ClinicalTrials)\n\n"
        + "\n".join([f"- {item}" for item in api_context])
        if api_context
        else "No real-time API evidence found."
    )

    stats: Dict[str, str] = {
        "Confidence": f"{confidence * 100:.1f}%",
        "Sources": str(len(sources)),
    }

    status_msg = f"Triage completed for {patient_id}"
    return summary_md, stats, sources_md, graph_md, api_md, status_msg



# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
theme = gr.themes.Soft(
    primary_hue="sky",
    secondary_hue="slate",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
)

# ---------------------------------------------------------------------------
# UI Layout
# ---------------------------------------------------------------------------
with gr.Blocks(title="OncoAgent — Clinical Triage") as demo:

    # ── Font Loader + Header ────────────────────────────────────────
    gr.HTML(FONTS_LINK)
    gr.HTML(
        "<div class='header-bar'>"
        "<span class='brand-name'>OncoAgent</span>"
        "<span class='hw-badge'>AMD Instinct MI300X</span>"
        "</div>"
    )

    with gr.Row():
        # ── LEFT SIDEBAR ─────────────────────────────────────────────
        with gr.Column(scale=1):

            # Session Controls
            with gr.Column(elem_classes="card"):
                gr.HTML("<div class='section-title'>Session</div>")
                patient_id_input = gr.Textbox(
                    label="Patient ID",
                    value=generate_patient_id,
                    interactive=True,
                    info="Unique session for memory isolation",
                )
                tier_override_input = gr.Dropdown(
                    label="Model Tier",
                    choices=["auto", "9b", "27b"],
                    value="auto",
                    info="Auto-routes based on case complexity",
                )

            # Clinical Input
            with gr.Column(elem_classes="card"):
                gr.HTML("<div class='section-title'>Clinical Case</div>")
                case_input = gr.Textbox(
                    placeholder="Enter clinical notes, pathology reports, or genomic variants...",
                    lines=8,
                    label=None,
                    show_label=False,
                )
                with gr.Row():
                    clear_btn = gr.Button("Clear", variant="secondary")
                    triage_btn = gr.Button(
                        "Send to OncoAgent",
                        elem_classes="btn-primary",
                        variant="primary",
                    )


        # ── RIGHT MAIN PANEL ──────────────────────────────────────────
        with gr.Column(scale=2):

            # KPI Row
            with gr.Row():

                with gr.Column(elem_classes="kpi-tile", min_width=120):
                    gr.HTML(
                        "<div class='kpi-label'>Confidence</div>"
                        "<div class='kpi-value' id='kpi-confidence'>—</div>"
                    )
                    confidence_val = gr.Label(label="Confidence", visible=False)
                with gr.Column(elem_classes="kpi-tile", min_width=120):
                    gr.HTML(
                        "<div class='kpi-label'>Evidence Sources</div>"
                        "<div class='kpi-value' id='kpi-sources'>—</div>"
                    )
                    sources_val = gr.Label(label="Sources", visible=False)

            # Results
            with gr.Column(elem_classes="card"):
                gr.HTML("<div class='section-title'>Analysis Results</div>")
                output_summary = gr.Markdown(
                    "Awaiting clinical input. System will process through triage stages."
                )
                status_box = gr.Markdown(
                    "<div class='status-bar'>System ready.</div>",
                    elem_id="status-box",
                )

            # Evidence Tabs
            with gr.Tabs(elem_classes="card"):
                with gr.Tab(f"Guidelines"):
                    output_sources = gr.Markdown(
                        "NCCN and ESMO guideline evidence will appear here."
                    )
                with gr.Tab("Knowledge Graph"):
                    output_graph = gr.Markdown(
                        "Knowledge graph connections will appear here."
                    )
                with gr.Tab("API Evidence"):
                    output_api = gr.Markdown(
                        "Real-time data from CIViC and ClinicalTrials.gov will appear here."
                    )

    # ── Interaction Logic ─────────────────────────────────────────────
    def process_and_update(
        text: str, pid: str, tier: str
    ) -> Tuple[str, str, str, str, str, str, str, str]:
        """Run triage and fan out results to all UI components."""
        summary, stats, sources, graph, api, status = run_triage(text, pid, tier)
        return (
            summary,
            stats.get("Confidence", "—") if isinstance(stats, dict) else "—",
            str(stats.get("Sources", "—")) if isinstance(stats, dict) else "—",
            sources,
            graph,
            api,
            f"<div class='status-bar'>{status}</div>",
        )

    triage_btn.click(
        fn=process_and_update,
        inputs=[case_input, patient_id_input, tier_override_input],
        outputs=[
            output_summary,
            confidence_val,
            sources_val,
            output_sources,
            output_graph,
            output_api,
            status_box,
        ],
    )

    clear_btn.click(
        lambda: [
            "",
            generate_patient_id(),
            "auto",
            "",
            "—",
            "—",
            "",
            "",
            "",
            "<div class='status-bar'>System ready.</div>",
        ],
        outputs=[
            case_input,
            patient_id_input,
            tier_override_input,
            output_summary,
            confidence_val,
            sources_val,
            output_sources,
            output_graph,
            output_api,
            status_box,
        ],
    )

# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        theme=theme,
        css=CSS,
    )
