"""
OncoAgent — Conversational Clinical Copilot (UI Module).

Provides a ChatGPT-style Gradio interface for the multi-agent
oncological triage system. Uses LangGraph streaming to show
real-time agent progress and prevent UI freezing.
"""

import os
import time
import random
import logging
import gradio as gr
from typing import Dict, Any, List, Tuple, Optional, Generator
from dotenv import load_dotenv

from agents.graph import build_oncoagent_graph
from ui.styles import CSS, FONTS_LINK

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SVG Icon Library
# ---------------------------------------------------------------------------
ICONS: Dict[str, str] = {
    "check": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    "alert": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f87171" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
}

# Node display names for streaming progress
NODE_LABELS: Dict[str, str] = {
    "router": "Routing case",
    "ingestion": "Extracting clinical entities",
    "corrective_rag": "Retrieving NCCN/ESMO guidelines",
    "specialist": "Generating clinical recommendation",
    "critic": "Validating medical safety",
    "hitl_gate": "Assessing acuity level",
    "formatter": "Formatting final report",
    "fallback": "Generating safe fallback response",
}

# ---------------------------------------------------------------------------
# Initialize Graph
# ---------------------------------------------------------------------------
agent_graph = build_oncoagent_graph()


def generate_patient_id() -> str:
    """Generate a randomized patient session identifier."""
    return f"PT-{random.randint(1000, 9999)}"


# ---------------------------------------------------------------------------
# Streaming Triage (replaces blocking invoke)
# ---------------------------------------------------------------------------
def stream_triage(
    clinical_text: str,
    patient_id: str,
    tier_override: str,
) -> Generator[Tuple[str, str, Dict[str, str]], None, None]:
    """Stream through LangGraph nodes, yielding progress and final result.

    Args:
        clinical_text: Raw clinical notes from the user.
        patient_id: Session identifier for memory isolation.
        tier_override: Model tier selection (auto / 9b / 27b).

    Yields:
        Tuples of (node_name, progress_markdown, partial_state).
    """
    if not clinical_text.strip():
        yield ("done", "Please enter a clinical case.", {})
        return
    if not patient_id.strip():
        patient_id = "PT-UNKNOWN"

    input_state: Dict[str, Any] = {
        "clinical_text": clinical_text,
        "messages": [("user", clinical_text)],
        "manual_override": tier_override if tier_override != "auto" else None,
        "errors": [],
    }
    config: Dict[str, Any] = {
        "configurable": {"thread_id": patient_id},
    }

    accumulated_state: Dict[str, Any] = {}

    try:
        for event in agent_graph.stream(
            input_state, config=config, stream_mode="updates"
        ):
            for node_name, node_output in event.items():
                label = NODE_LABELS.get(node_name, node_name)
                yield (node_name, f"**{label}**...", node_output)
                if isinstance(node_output, dict):
                    accumulated_state.update(node_output)
    except Exception as e:
        logger.error("Graph streaming error: %s", e, exc_info=True)
        yield ("error", f"Error: {str(e)}", {})
        return

    yield ("done", "Complete", accumulated_state)


def format_final_response(state: Dict[str, Any]) -> str:
    """Format the accumulated state into a readable clinical response."""
    recommendation: str = state.get(
        "formatted_recommendation",
        state.get("clinical_recommendation", "No recommendation generated."),
    )
    safety_status: str = state.get("safety_status", "Unknown")
    is_safe: bool = state.get("is_safe", False)
    critic_feedback = state.get("critic_feedback", [])

    if is_safe:
        badge = f"<span class='badge-safe'>{ICONS['check']} Clinically Safe</span>"
    else:
        badge = f"<span class='badge-unsafe'>{ICONS['alert']} Review Required</span>"

    md = f"### Decision Status: {badge}\n\n"
    md += f"{recommendation}\n\n---\n"
    md += f"**Safety Audit:** {safety_status}\n"

    if critic_feedback:
        if isinstance(critic_feedback, list):
            items = critic_feedback
        else:
            items = [str(critic_feedback)]
        md += "\n<div class='critic-card'><strong>Critic Iterations:</strong><br/>"
        md += "<br/>".join([f"— {fb}" for fb in items])
        md += "</div>"

    return md


def extract_evidence(state: Dict[str, Any]) -> Tuple[str, str, str]:
    """Extract evidence tabs content from state."""
    sources: List[str] = state.get("rag_sources", [])
    graph_ctx: List[str] = state.get("graph_rag_context", [])
    api_ctx: List[str] = state.get("api_evidence_context", [])

    sources_md = (
        "### Medical Guidelines (NCCN / ESMO)\n\n" + "\n".join(sources)
        if sources
        else "No guideline sources retrieved."
    )
    graph_md = (
        "### Clinical Knowledge Graph\n\n"
        + "\n".join([f"- {item}" for item in graph_ctx])
        if graph_ctx
        else "No graph relations extracted."
    )
    api_md = (
        "### Real-Time Evidence (CIViC & ClinicalTrials)\n\n"
        + "\n".join([f"- {item}" for item in api_ctx])
        if api_ctx
        else "No real-time API evidence found."
    )
    return sources_md, graph_md, api_md


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
# UI Layout — ChatGPT-style
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
        # ── LEFT SIDEBAR ────────────────────────────────────────────
        with gr.Column(scale=1, min_width=280, elem_classes="sidebar-column"):
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
                new_session_btn = gr.Button("↻ New Session", variant="secondary", size="sm")

            # KPI Row
            with gr.Row():
                with gr.Column(elem_classes="kpi-tile", min_width=100):
                    gr.HTML(
                        "<div class='kpi-label'>Confidence</div>"
                        "<div class='kpi-value' id='kpi-confidence'>—</div>"
                    )
                    confidence_val = gr.Label(label="Confidence", visible=False)
                with gr.Column(elem_classes="kpi-tile", min_width=100):
                    gr.HTML(
                        "<div class='kpi-label'>Sources</div>"
                        "<div class='kpi-value' id='kpi-sources'>—</div>"
                    )
                    sources_val = gr.Label(label="Sources", visible=False)

            # Evidence Tabs
            with gr.Tabs(elem_classes="card"):
                with gr.Tab("Guidelines"):
                    output_sources = gr.Markdown(
                        "NCCN and ESMO guideline evidence will appear here."
                    )
                with gr.Tab("Knowledge Graph"):
                    output_graph = gr.Markdown(
                        "Knowledge graph connections will appear here."
                    )
                with gr.Tab("API Evidence"):
                    output_api = gr.Markdown(
                        "Real-time data from CIViC and ClinicalTrials.gov."
                    )

            # Status
            with gr.Column(elem_classes="card"):
                gr.HTML("<div class='section-title'>System Status</div>")
                status_box = gr.Markdown(
                    "<div class='status-bar'>System ready.</div>",
                    elem_id="status-box",
                )

        # ── MAIN CHAT AREA ──────────────────────────────────────────
        with gr.Column(scale=3):
            with gr.Column(elem_classes="card", min_width=600):
                chatbot = gr.Chatbot(
                    label="OncoAgent",
                    show_label=False,
                    elem_classes="gr-chatbot",
                    height=620,
                )
                case_input = gr.Textbox(
                    placeholder="Describe the clinical case or ask a follow-up question...",
                    show_label=False,
                    container=False,
                    submit_btn="↑",
                    elem_classes="chat-input-integrated"
                )

    # ── Interaction Logic (Streaming) ─────────────────────────────────
    def process_and_stream(
        history: List[Dict[str, str]], text: str, pid: str, tier: str,
    ):
        """Stream triage results to UI, updating step-by-step."""
        if not text.strip():
            yield (
                history, "", "—", "—", "", "", "",
                "<div class='status-bar'>System ready.</div>",
            )
            return

        history = history + [
            {"role": "user", "content": text},
            {"role": "assistant", "content": ""},
        ]

        # Show immediate loading state
        yield (
            history, "", "—", "—",
            "Retrieving NCCN/ESMO guidelines...",
            "Building knowledge graph...",
            "Querying real-time evidence...",
            "<div class='status-bar'>Processing triage via LangGraph...</div>",
        )

        accumulated: Dict[str, Any] = {}
        for node_name, progress, node_output in stream_triage(text, pid, tier):
            if isinstance(node_output, dict):
                accumulated.update(node_output)

            if node_name == "done":
                break
            if node_name == "error":
                history[-1]["content"] = f"**Error:** {progress}"
                yield (
                    history, "", "—", "—", "", "", "",
                    f"<div class='status-bar'>{progress}</div>",
                )
                return

            label = NODE_LABELS.get(node_name, node_name)
            status_html = f"<div class='status-bar'><span class='node-step active'>{label}</span></div>"
            history[-1]["content"] = f"*Processing: {label}...*"
            yield (
                history, "", "—", "—",
                "Retrieving NCCN/ESMO guidelines...",
                "Building knowledge graph...",
                "Querying real-time evidence...",
                status_html,
            )

        # Final render
        final_md = format_final_response(accumulated)
        history[-1]["content"] = final_md

        sources_md, graph_md, api_md = extract_evidence(accumulated)

        conf = accumulated.get("rag_confidence", 0.0)
        src_count = len(accumulated.get("rag_sources", []))

        yield (
            history,
            "",
            f"{conf * 100:.1f}%" if conf else "—",
            str(src_count) if src_count else "—",
            sources_md,
            graph_md,
            api_md,
            f"<div class='status-bar'>Triage completed for {pid}</div>",
        )

    outputs = [
        chatbot, case_input, confidence_val, sources_val,
        output_sources, output_graph, output_api, status_box,
    ]
    inputs = [chatbot, case_input, patient_id_input, tier_override_input]

    case_input.submit(fn=process_and_stream, inputs=inputs, outputs=outputs)

    new_session_btn.click(
        lambda: (
            [], "", generate_patient_id(), "auto", "—", "—",
            "", "", "",
            "<div class='status-bar'>System ready.</div>",
        ),
        outputs=[
            chatbot, case_input, patient_id_input, tier_override_input,
            confidence_val, sources_val,
            output_sources, output_graph, output_api, status_box,
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
