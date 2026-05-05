import os
import sys
import gradio as gr

# Ensure the parent directory is in the sys.path to import agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.graph import build_oncoagent_graph

# i18n Dictionary
I18N = {
    "en": {
        "title": "OncoAgent: Clinical Oncology Decision Support",
        "description": "An AI-powered multi-agent system providing evidence-based triage and treatment recommendations using ESMO/NCCN guidelines on AMD ROCm architecture.",
        "input_label": "Clinical History / Patient Presentation",
        "input_placeholder": "E.g., 65-year-old male presenting with Stage III colon cancer, KRAS mutated...",
        "submit_btn": "Generate Recommendation",
        "clear_btn": "Clear",
        "output_entities": "Extracted Entities",
        "output_recommendation": "Clinical Recommendation",
        "output_status": "Safety Validation Status",
        "phi_warning": "⚠️ PHI Detected! Patient data was anonymized for safety.",
    },
    "es": {
        "title": "OncoAgent: Soporte de Decisión en Oncología Clínica",
        "description": "Un sistema multi-agente impulsado por IA que proporciona recomendaciones de tratamiento basadas en guías ESMO/NCCN, optimizado para arquitectura AMD ROCm.",
        "input_label": "Historia Clínica / Presentación del Paciente",
        "input_placeholder": "Ej., Hombre de 65 años con cáncer de colon en Estadio III, mutación KRAS...",
        "submit_btn": "Generar Recomendación",
        "clear_btn": "Limpiar",
        "output_entities": "Entidades Extraídas",
        "output_recommendation": "Recomendación Clínica",
        "output_status": "Estado de Validación de Seguridad",
        "phi_warning": "⚠️ PHI Detectado! Los datos del paciente fueron anonimizados por seguridad.",
    }
}

# Current Language setting
LANG = "en"  # Change to "es" for local presentation

def process_clinical_case(text: str):
    if not text.strip():
        return "Please enter a clinical history.", "", ""
    
    try:
        app = build_oncoagent_graph()
        initial_state = {"clinical_text": text}
        
        # Invoke LangGraph workflow with strict recursion limit
        final_state = app.invoke(initial_state, config={"recursion_limit": 5})
        
        # Format Extracted Entities
        entities = final_state.get("extracted_entities", {})
        entities_str = "\n".join(f"- **{k.replace('_', ' ').title()}**: {v}" for k, v in entities.items())
        
        if final_state.get("phi_detected"):
            entities_str = f"**{I18N[LANG]['phi_warning']}**\n\n" + entities_str
            
        # Get Recommendation
        recommendation = final_state.get("clinical_recommendation", "N/A")
        
        # Get Sources
        sources = final_state.get("rag_sources", [])
        sources_list_str = "\n".join(sources) if sources else "No sources retrieved."
        
        rag_confidence = final_state.get("rag_confidence", 0.0)
        retrieval_count = final_state.get("rag_retrieval_count", 0)
        
        metrics_str = f"📊 **RAG Confidence Score:** {rag_confidence} | 📚 **Sources Retrieved:** {retrieval_count}\n\n"
        sources_str = metrics_str + sources_list_str
        
        # Get Safety Status
        safety_status = final_state.get("safety_status", "Unknown")
        is_safe = final_state.get("is_safe", False)
        
        status_icon = "✅" if is_safe else "❌"
        status_str = f"{status_icon} **{safety_status}**"
        
        return entities_str, sources_str, recommendation, status_str
        
    except Exception as e:
        return f"Error processing request: {str(e)}", "", "", ""

def create_ui():
    lang_dict = I18N[LANG]
    
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue")) as ui:
        gr.Markdown(f"# {lang_dict['title']}")
        gr.Markdown(lang_dict['description'])
        
        with gr.Row():
            with gr.Column(scale=1):
                clinical_input = gr.Textbox(
                    label=lang_dict["input_label"],
                    placeholder=lang_dict["input_placeholder"],
                    lines=10
                )
                with gr.Row():
                    clear_btn = gr.Button(lang_dict["clear_btn"])
                    submit_btn = gr.Button(lang_dict["submit_btn"], variant="primary")
            
            with gr.Column(scale=1):
                status_output = gr.Markdown(label=lang_dict["output_status"])
                entities_output = gr.Markdown(label=lang_dict["output_entities"])
                sources_output = gr.Markdown(label=lang_dict.get("output_sources", "Sources / Fuentes"))
                recommendation_output = gr.Markdown(label=lang_dict["output_recommendation"])
                
        submit_btn.click(
            fn=process_clinical_case,
            inputs=clinical_input,
            outputs=[entities_output, sources_output, recommendation_output, status_output]
        )
        
        clear_btn.click(
            fn=lambda: ("", "", "", ""),
            inputs=None,
            outputs=[clinical_input, entities_output, sources_output, recommendation_output, status_output]
        )
        
    return ui

if __name__ == "__main__":
    ui = create_ui()
    # Share=True allows external testing if needed, though local execution is 0.0.0.0
    ui.launch(server_name="0.0.0.0", server_port=7860, share=False)
