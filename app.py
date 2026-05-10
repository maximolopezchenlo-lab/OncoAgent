"""
OncoAgent — Interactive Demo for Hugging Face Spaces.

Simulates the full multi-agent oncology triage pipeline with realistic
streaming, agent node transitions, and clinical recommendations.
Runs without GPU/vLLM — pure frontend showcase.

Hardware Target: AMD Instinct MI300X (production)
Demo Mode: CPU-only simulation for HF Spaces free tier
"""

import gradio as gr
import time
from typing import Generator

# ── Design System (inline for HF Spaces portability) ──────────────────

FONTS_LINK: str = (
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Figtree:wght@400;500;600;700&'
    'family=Inter:wght@300;400;500;600&display=swap">'
)

CSS: str = """
/* OncoAgent — Clinical Dark Theme */
:root {
    --shadow-drop: none !important;
    --shadow-drop-lg: none !important;
    --shadow-inset: none !important;
    --block-shadow: none !important;
    --body-background-fill: #0f172a !important;
    --background-fill-primary: #0f172a !important;
}
html, body, gradio-app {
    background-color: #0f172a !important;
    margin: 0 !important; padding: 0 !important;
}
.gradio-container, .main, .wrap, .contain,
.gradio-container > div, footer, main {
    background: #0f172a !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    box-shadow: none !important;
}
.gradio-container {
    max-width: 960px !important;
    margin: 0 auto !important;
    border: none !important;
}
* { box-sizing: border-box; }

.gr-group, .gr-block, .gr-box, .gr-panel,
.block, .wrap, .panel { background: transparent !important; }

/* Header */
.header-bar {
    display: flex; justify-content: space-between; align-items: center;
    padding: 14px 24px;
    background: #1e293b;
    border: 1px solid #334155; border-radius: 14px;
    margin-bottom: 16px;
}
.brand-name {
    font-family: 'Figtree', sans-serif;
    font-size: 1.6rem; font-weight: 700;
    color: #f1f5f9; letter-spacing: -0.025em;
}
.hw-badge {
    background: rgba(239, 68, 68, 0.15); color: #fca5a5;
    padding: 5px 14px; border-radius: 6px;
    font-size: 0.72rem; font-weight: 600;
    letter-spacing: 0.05em;
    border: 1px solid rgba(239, 68, 68, 0.25);
}
.demo-badge {
    background: rgba(14, 165, 233, 0.15); color: #7dd3fc;
    padding: 5px 14px; border-radius: 6px;
    font-size: 0.72rem; font-weight: 600;
    letter-spacing: 0.05em;
    border: 1px solid rgba(14, 165, 233, 0.25);
}

/* Cards */
.card {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 14px !important;
    padding: 18px !important;
}
.card:hover { border-color: #475569 !important; }

/* Buttons */
.btn-primary {
    background: linear-gradient(135deg, #0ea5e9, #0284c7) !important;
    border: none !important; color: #fff !important;
    font-weight: 600 !important; border-radius: 10px !important;
    cursor: pointer !important;
    transition: transform 0.15s ease-out, box-shadow 0.15s ease-out !important;
}
.btn-primary:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(14, 165, 233, 0.4) !important;
}
.btn-demo {
    background: linear-gradient(135deg, #10b981, #059669) !important;
    border: none !important; color: #fff !important;
    font-weight: 600 !important; border-radius: 10px !important;
    cursor: pointer !important; font-size: 1rem !important;
    padding: 12px 24px !important;
    transition: transform 0.15s ease-out, box-shadow 0.15s ease-out !important;
}
.btn-demo:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4) !important;
}

/* Chat */
.gr-chatbot, [class*="chatbot"] {
    background: transparent !important;
    border: none !important; box-shadow: none !important;
}
.message {
    padding: 16px 20px !important;
    border-radius: 18px !important;
    margin-bottom: 12px !important;
    line-height: 1.7 !important;
    font-size: 0.94rem !important;
}
.message.user {
    background: rgba(14, 165, 233, 0.08) !important;
    border: 1px solid rgba(14, 165, 233, 0.15) !important;
    border-bottom-right-radius: 4px !important;
    margin-left: 15% !important;
}
.message.bot {
    background: rgba(30, 41, 59, 0.6) !important;
    border: 1px solid rgba(51, 65, 85, 0.3) !important;
    border-bottom-left-radius: 4px !important;
    margin-right: 10% !important;
    backdrop-filter: blur(12px) !important;
}

/* Safety Badges */
.badge-safe {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(16, 185, 129, 0.12); color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
    padding: 4px 12px; border-radius: 6px;
    font-weight: 600; font-size: 0.8rem;
}

/* Node Progress */
.node-step {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 0.78rem; color: #94a3b8;
    padding: 4px 10px; border-radius: 6px;
    background: rgba(14, 165, 233, 0.08);
    border: 1px solid rgba(14, 165, 233, 0.15);
    margin-right: 6px; margin-bottom: 4px;
}
.node-step.active {
    color: #38bdf8; border-color: rgba(14, 165, 233, 0.4);
    animation: pulse-node 1.5s ease-in-out infinite;
}
.node-step.done { color: #34d399; border-color: rgba(16,185,129,0.3); }
@keyframes pulse-node {
    0%, 100% { opacity: 1; } 50% { opacity: 0.5; }
}

/* Info panel */
.info-panel {
    background: rgba(14, 165, 233, 0.06);
    border: 1px solid rgba(14, 165, 233, 0.15);
    border-radius: 12px; padding: 16px;
    margin-bottom: 12px;
}

/* Textarea & inputs */
textarea, input[type="text"] {
    background: #0f172a !important;
    border: 1px solid #334155 !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
}
textarea:focus, input[type="text"]:focus {
    border-color: #0ea5e9 !important;
    outline: none !important;
}

/* Labels */
label, .gr-input-label { color: #94a3b8 !important; }

/* KPI tiles */
.kpi-row { display: flex; gap: 12px; margin-top: 12px; }
.kpi-tile {
    flex: 1; background: #1e293b; border: 1px solid #334155;
    border-radius: 10px; padding: 14px; text-align: center;
}
.kpi-label {
    font-size: 0.68rem; font-weight: 500; color: #64748b;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;
}
.kpi-value {
    font-family: 'Figtree', sans-serif;
    font-size: 1.3rem; font-weight: 700; color: #f1f5f9;
}

/* Architecture diagram */
.arch-flow {
    display: flex; align-items: center; gap: 8px;
    flex-wrap: wrap; margin: 12px 0;
}
.arch-node {
    background: #1e293b; border: 1px solid #334155;
    border-radius: 8px; padding: 8px 14px;
    font-size: 0.78rem; color: #cbd5e1;
    font-weight: 500;
}
.arch-node.highlight {
    border-color: #0ea5e9; color: #7dd3fc;
    background: rgba(14, 165, 233, 0.08);
}
.arch-arrow { color: #475569; font-size: 1.2rem; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0f172a; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }

/* Footer */
.footer-text {
    text-align: center; color: #475569;
    font-size: 0.72rem; margin-top: 20px;
    padding: 12px; border-top: 1px solid #1e293b;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
"""

# ── Demo Case Data ────────────────────────────────────────────────────

DEMO_CASE: str = (
    "55-year-old female patient presents with postmenopausal bleeding. "
    "Ultrasound shows an endometrial thickening of 12mm. "
    "The endometrial biopsy report confirms Grade 1 endometrioid "
    "adenocarcinoma. No evidence of myometrial invasion on MRI. "
    "CA-125 within normal limits. Patient has BMI of 32 and "
    "controlled type 2 diabetes."
)

# Simulated agent outputs — based on real NCCN Uterine guidelines
DEMO_STEPS: list = [
    {
        "node": "🔀 Router Agent",
        "delay": 0.8,
        "output": (
            "**Classification:** Oncological case detected.\n\n"
            "- **Cancer Type:** Endometrial (Uterine)\n"
            "- **Confidence:** 0.96\n"
            "- **Routing Decision:** → Specialist Agent (Tier 2 — Qwen3.6-27B)\n"
            "- **Rationale:** Confirmed histopathology requires advanced reasoning."
        ),
    },
    {
        "node": "🔍 Clinical Extraction",
        "delay": 1.0,
        "output": (
            "**Extracted Clinical Entities:**\n\n"
            "| Field | Value |\n"
            "|---|---|\n"
            "| Age | 55 years |\n"
            "| Sex | Female |\n"
            "| Chief Complaint | Postmenopausal bleeding |\n"
            "| Imaging | Endometrial thickening 12mm (US) |\n"
            "| MRI | No myometrial invasion |\n"
            "| Pathology | **Grade 1 endometrioid adenocarcinoma** |\n"
            "| Biomarker | CA-125 normal |\n"
            "| Comorbidities | BMI 32, T2DM (controlled) |\n"
            "| FIGO Stage | Likely IA (pending surgical staging) |"
        ),
    },
    {
        "node": "📚 Corrective RAG",
        "delay": 1.5,
        "output": (
            "**Retrieval Results** — NCCN Uterine Cancer Guidelines v2.2025\n\n"
            "- 📄 **Source:** `uterine.pdf` — Pages 12-18 (Endometrioid Adenocarcinoma)\n"
            "- 🎯 **Bi-Encoder Score:** 0.89 | **Cross-Encoder Score:** 0.94\n"
            "- ✅ **Distance Gate:** PASSED (threshold: 0.65)\n"
            "- 📊 **Chunks Retrieved:** 6 / 2,847 total\n\n"
            "**Key Guideline Excerpts:**\n"
            "> *\"For Grade 1 endometrioid adenocarcinoma confined to the endometrium "
            "(Stage IA), total hysterectomy with bilateral salpingo-oophorectomy "
            "(TH/BSO) is the primary treatment. Lymph node assessment should be "
            "considered based on institutional protocols.\"*\n\n"
            "> *\"Sentinel lymph node mapping is preferred over comprehensive "
            "lymphadenectomy for clinically uterine-confined disease.\"*"
        ),
    },
    {
        "node": "🧠 Specialist Agent",
        "delay": 2.0,
        "output": (
            "**OncoAgent — Clinical Recommendation**\n\n"
            "---\n\n"
            "## 📋 Clinical Summary\n\n"
            "55-year-old postmenopausal female with biopsy-confirmed Grade 1 "
            "endometrioid adenocarcinoma. MRI shows no myometrial invasion. "
            "Tumor markers within normal limits. Comorbidities include obesity "
            "(BMI 32) and controlled T2DM.\n\n"
            "## 🔬 Diagnostic Findings\n\n"
            "- **Histology:** Endometrioid adenocarcinoma, Grade 1 (well-differentiated)\n"
            "- **Probable FIGO Stage:** IA — disease confined to endometrium\n"
            "- **Myometrial Invasion:** Not detected on MRI\n"
            "- **Lymphovascular Space Invasion (LVSI):** Not reported\n\n"
            "## 💊 Treatment Recommendation\n\n"
            "**Primary Treatment (NCCN Category 1):**\n"
            "1. **Total Hysterectomy with Bilateral Salpingo-Oophorectomy (TH/BSO)**\n"
            "   - Minimally invasive approach (laparoscopic/robotic) preferred\n"
            "   - Consider peritoneal washings at time of surgery\n\n"
            "2. **Sentinel Lymph Node (SLN) Mapping**\n"
            "   - Preferred over comprehensive lymphadenectomy\n"
            "   - Per NCCN institutional SLN algorithm\n\n"
            "**Adjuvant Therapy Considerations:**\n"
            "- If final pathology confirms Stage IA, Grade 1: **Observation only**\n"
            "- No adjuvant radiation or chemotherapy indicated for this stage\n"
            "- If upstaged post-surgery: Refer to NCCN adjuvant guidelines\n\n"
            "## ⚠️ Additional Considerations\n\n"
            "- **Obesity Management:** BMI 32 — perioperative risk optimization recommended\n"
            "- **Diabetes Control:** HbA1c target < 7% pre-surgery\n"
            "- **Genetic Counseling:** Consider Lynch syndrome screening "
            "(immunohistochemistry for MMR proteins or MSI testing)\n"
            "- **Fertility Preservation:** Not applicable (postmenopausal)\n\n"
            "## 📚 Evidence Level\n\n"
            "- **NCCN Evidence Category:** 1 (High-level evidence, uniform consensus)\n"
            "- **Guideline Source:** NCCN Uterine Neoplasms v2.2025, Pages 12-18\n"
            "- **RAG Confidence:** 0.94 (Cross-Encoder validated)"
        ),
    },
    {
        "node": "✅ Critic (Reflexion Loop)",
        "delay": 1.0,
        "output": (
            "**Critic Validation — PASSED ✅**\n\n"
            "| Check | Status |\n"
            "|---|---|\n"
            "| Clinical Summary present | ✅ |\n"
            "| Diagnostic Findings present | ✅ |\n"
            "| Treatment Recommendation present | ✅ |\n"
            "| Evidence/Citations present | ✅ |\n"
            "| Diagnostic Rigor (biopsy confirmed) | ✅ |\n"
            "| Anti-Hallucination (RAG-grounded) | ✅ |\n"
            "| PHI Sanitization | ✅ |\n\n"
            "**Verdict:** Recommendation is clinically grounded and safe for review.\n\n"
            "---\n"
            "### Decision Status: "
            "<span class='badge-safe'>"
            "✅ Clinically Validated"
            "</span>"
        ),
    },
]


def _node_progress_html(current_idx: int) -> str:
    """Generate the agent pipeline progress bar HTML."""
    nodes = ["Router", "Extraction", "RAG", "Specialist", "Critic"]
    icons = ["🔀", "🔍", "📚", "🧠", "✅"]
    parts = []
    for i, (name, icon) in enumerate(zip(nodes, icons)):
        if i < current_idx:
            cls = "done"
        elif i == current_idx:
            cls = "active"
        else:
            cls = ""
        parts.append(f"<span class='node-step {cls}'>{icon} {name}</span>")
        if i < len(nodes) - 1:
            parts.append("<span style='color:#475569;'>→</span>")
    return " ".join(parts)


def run_demo() -> Generator:
    """Simulate the full OncoAgent pipeline with streaming."""
    history = []

    # Step 1: User message appears
    history.append({"role": "user", "content": DEMO_CASE})
    yield history

    time.sleep(0.5)

    # Step 2: Stream each agent node
    for step_idx, step in enumerate(DEMO_STEPS):
        node_name = step["node"]
        delay = step["delay"]
        output = step["output"]

        # Build progress bar
        progress = _node_progress_html(step_idx)

        # Start with node header + progress
        header = f"### {node_name}\n{progress}\n\n"

        # Stream the output character by character (in chunks for speed)
        full_text = header
        chunk_size = 8
        for i in range(0, len(output), chunk_size):
            full_text += output[i:i + chunk_size]
            # Update the last bot message
            display_history = history.copy()
            display_history.append({"role": "assistant", "content": full_text})
            yield display_history
            time.sleep(0.015)

        # Finalize this step
        history.append({"role": "assistant", "content": full_text})
        yield history

        # Pause between nodes
        time.sleep(delay * 0.3)

    # Final summary message
    time.sleep(0.3)
    final_msg = (
        "---\n\n"
        "### 🏁 Pipeline Complete\n\n"
        "<div class='kpi-row'>"
        "<div class='kpi-tile'><div class='kpi-label'>Agents Used</div>"
        "<div class='kpi-value'>5</div></div>"
        "<div class='kpi-tile'><div class='kpi-label'>RAG Sources</div>"
        "<div class='kpi-value'>6</div></div>"
        "<div class='kpi-tile'><div class='kpi-label'>Confidence</div>"
        "<div class='kpi-value'>0.94</div></div>"
        "<div class='kpi-tile'><div class='kpi-label'>Safety</div>"
        "<div class='kpi-value'>✅</div></div>"
        "</div>\n\n"
        "<div style='margin-top:12px; font-size:0.8rem; color:#64748b;'>"
        "⚡ In production, this pipeline runs on AMD Instinct™ MI300X with "
        "vLLM (PagedAttention) serving Qwen3.5-9B + Qwen3.6-27B models. "
        "This demo simulates the agent flow for showcase purposes."
        "</div>"
    )
    history.append({"role": "assistant", "content": final_msg})
    yield history


def handle_user_message(
    message: str,
    history: list,
) -> Generator:
    """Handle custom user messages with a simulated response."""
    if not message.strip():
        yield history
        return

    history = history or []
    history.append({"role": "user", "content": message})
    yield history

    time.sleep(0.5)

    # Simulated response for any custom input
    response = (
        "### 🔀 Router Agent\n\n"
        "**Note:** This is a demo environment running on HF Spaces "
        "without GPU acceleration.\n\n"
        "In the **production deployment** on AMD Instinct™ MI300X, "
        "your clinical case would be processed through our full "
        "5-agent pipeline:\n\n"
        "1. **Router** — Classifies oncological vs. non-oncological\n"
        "2. **Clinical Extraction** — Extracts structured entities\n"
        "3. **Corrective RAG** — Retrieves from NCCN/ESMO guidelines\n"
        "4. **Specialist** — Generates evidence-based recommendation\n"
        "5. **Critic (Reflexion)** — Validates safety and completeness\n\n"
        "👉 Click **▶ View Demo** to see a complete simulated triage "
        "with the endometrial cancer case.\n\n"
        "🔗 **Production:** Deploy with `docker compose up` on MI300X hardware.\n"
        "📖 **Source:** [GitHub](https://github.com/maximolopezchenlo-lab/OncoAgent)"
    )

    # Stream it
    partial = ""
    chunk_size = 12
    for i in range(0, len(response), chunk_size):
        partial += response[i:i + chunk_size]
        display = history.copy()
        display.append({"role": "assistant", "content": partial})
        yield display
        time.sleep(0.01)

    history.append({"role": "assistant", "content": response})
    yield history


# ── Build the UI ──────────────────────────────────────────────────────

HEADER_HTML: str = """
<div class="header-bar">
    <div style="display:flex; align-items:center; gap:12px;">
        <span class="brand-name">🧬 OncoAgent</span>
        <span class="demo-badge">INTERACTIVE DEMO</span>
    </div>
    <div style="display:flex; gap:8px; align-items:center;">
        <span class="hw-badge">AMD INSTINCT™ MI300X</span>
        <span class="hw-badge">ROCm 7.2</span>
    </div>
</div>
"""

INFO_HTML: str = """
<div class="info-panel">
    <div style="font-size:0.95rem; font-weight:600; color:#e2e8f0; margin-bottom:8px;">
        🏥 Multi-Agent Oncology Triage System
    </div>
    <div style="font-size:0.82rem; color:#94a3b8; line-height:1.6;">
        OncoAgent uses a <strong style="color:#7dd3fc;">5-agent LangGraph pipeline</strong>
        to analyze clinical cases against <strong style="color:#7dd3fc;">NCCN/ESMO guidelines</strong>
        with built-in safety validation and anti-hallucination guardrails.
    </div>
    <div class="arch-flow">
        <span class="arch-node highlight">🔀 Router</span>
        <span class="arch-arrow">→</span>
        <span class="arch-node">🔍 Extraction</span>
        <span class="arch-arrow">→</span>
        <span class="arch-node">📚 Corrective RAG</span>
        <span class="arch-arrow">→</span>
        <span class="arch-node">🧠 Specialist</span>
        <span class="arch-arrow">→</span>
        <span class="arch-node">✅ Critic</span>
    </div>
    <div style="font-size:0.72rem; color:#64748b; margin-top:8px;">
        ⚡ Production: Qwen3.5-9B (Tier 1) + Qwen3.6-27B (Tier 2) via vLLM PagedAttention
        &nbsp;|&nbsp; 📄 162 NCCN + 16 ESMO guidelines indexed
    </div>
</div>
"""

FOOTER_HTML: str = """
<div class="footer-text">
    🧬 OncoAgent — AMD Developer Hackathon 2026<br>
    Built with LangGraph · vLLM · Gradio · ROCm 7.2<br>
    <a href="https://github.com/maximolopezchenlo-lab/OncoAgent"
       style="color:#0ea5e9; text-decoration:none;" target="_blank">
       GitHub Repository</a>
    &nbsp;·&nbsp;
    <span style="color:#64748b;">100% Open Source · Apache 2.0</span>
</div>
"""


with gr.Blocks(
    css=CSS,
    head=FONTS_LINK,
    title="OncoAgent — Oncology Triage Demo",
    theme=gr.themes.Base(),
) as demo:
    # Header
    gr.HTML(HEADER_HTML)
    gr.HTML(INFO_HTML)

    # Chat
    chatbot = gr.Chatbot(
        type="messages",
        label="Clinical Triage Chat",
        height=520,
        show_label=False,
        show_copy_button=True,
        render_markdown=True,
        elem_classes=["card"],
    )

    # Controls
    with gr.Row():
        with gr.Column(scale=3):
            txt = gr.Textbox(
                placeholder="Enter a clinical case or click '▶ View Demo'...",
                show_label=False,
                lines=2,
                max_lines=5,
            )
        with gr.Column(scale=1, min_width=180):
            demo_btn = gr.Button(
                "▶ View Demo",
                elem_classes=["btn-demo"],
                size="lg",
            )

    with gr.Row():
        send_btn = gr.Button("Send", elem_classes=["btn-primary"], size="sm")
        clear_btn = gr.Button("🗑 Clear", variant="secondary", size="sm")

    # Footer
    gr.HTML(FOOTER_HTML)

    # ── Event Handlers ────────────────────────────────────────────────

    demo_btn.click(
        fn=run_demo,
        inputs=None,
        outputs=chatbot,
    )

    send_btn.click(
        fn=handle_user_message,
        inputs=[txt, chatbot],
        outputs=chatbot,
    ).then(lambda: "", outputs=txt)

    txt.submit(
        fn=handle_user_message,
        inputs=[txt, chatbot],
        outputs=chatbot,
    ).then(lambda: "", outputs=txt)

    clear_btn.click(lambda: [], outputs=chatbot)


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
