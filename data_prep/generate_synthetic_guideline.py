"""
Synthetic clinical guideline PDF generator for OncoAgent.
Creates structured PDFs that mimic NCCN/ESMO guideline format
for testing the RAG ingestion pipeline.

Uses reportlab for PDF generation. All content is synthetic
and for demonstration/testing purposes only.
"""

import os
from typing import List, Dict


# Synthetic guideline content organized by cancer type
SYNTHETIC_GUIDELINES: Dict[str, List[Dict[str, str]]] = {
    "lung_cancer": [
        {
            "header": "Diagnóstico",
            "content": (
                "La evaluación inicial del paciente con sospecha de cáncer de pulmón "
                "debe incluir:\n"
                "- Historia clínica completa con énfasis en factores de riesgo "
                "(tabaquismo, exposición ocupacional, historia familiar)\n"
                "- Exploración física completa\n"
                "- TC de tórax con contraste\n"
                "- Citología de esputo en pacientes con lesiones centrales\n"
                "- Broncoscopia con biopsia para lesiones centrales\n"
                "- Biopsia guiada por TC para lesiones periféricas\n"
                "- PET-CT para estadificación completa"
            ),
        },
        {
            "header": "Estratificación de Riesgo",
            "content": (
                "La estratificación del riesgo de malignidad en nódulos pulmonares "
                "solitarios se basa en los criterios de Fleischner Society:\n\n"
                "Nódulos Sólidos:\n"
                "- <6 mm: No requiere seguimiento (bajo riesgo)\n"
                "- 6-8 mm: TC de seguimiento a los 6-12 meses\n"
                "- >8 mm: Considerar PET-CT, biopsia o seguimiento a los 3 meses\n\n"
                "Factores que aumentan la probabilidad de malignidad:\n"
                "- Bordes espiculados (VPP >90%)\n"
                "- Localización en lóbulo superior\n"
                "- Crecimiento documentado\n"
                "- Antecedente de tabaquismo (>30 paquetes-año)\n"
                "- Edad >60 años"
            ),
        },
        {
            "header": "Tratamiento - Estadio I-II (Enfermedad Temprana)",
            "content": (
                "Recomendación: Resección quirúrgica es el tratamiento de elección.\n\n"
                "Opciones quirúrgicas:\n"
                "- Lobectomía (estándar de cuidado)\n"
                "- Segmentectomía (para tumores ≤2 cm periféricos)\n"
                "- Neumonectomía (si es necesaria para márgenes negativos)\n\n"
                "Quimioterapia adyuvante:\n"
                "- Estadio IA: No recomendada\n"
                "- Estadio IB (tumores >4 cm): Considerar cisplatino-vinorelbina\n"
                "- Estadio II: Cisplatino-vinorelbina × 4 ciclos (Evidencia Nivel 1A)\n\n"
                "Radioterapia:\n"
                "- SBRT para pacientes inoperables con Estadio I"
            ),
        },
        {
            "header": "Tratamiento - Estadio III (Enfermedad Localmente Avanzada)",
            "content": (
                "Recomendación: Quimioradioterapia concurrente seguida de immunoterapia.\n\n"
                "Protocolo estándar:\n"
                "1. Quimioradioterapia concurrente con cisplatino-etopósido\n"
                "2. Consolidación con durvalumab × 12 meses (Ensayo PACIFIC)\n\n"
                "Estadio IIIA resecable:\n"
                "- Considerar quimioterapia neoadyuvante + cirugía\n"
                "- Nivolumab neoadyuvante + quimioterapia (CheckMate 816)\n\n"
                "Evidencia: Durvalumab post-QRT mejora la supervivencia global "
                "a 5 años del 33.4% al 42.9% (HR 0.72, IC 95% 0.59-0.89)"
            ),
        },
        {
            "header": "Tratamiento - Estadio IV (Enfermedad Metastásica)",
            "content": (
                "Recomendación: Terapia sistémica basada en biomarcadores.\n\n"
                "Testing molecular obligatorio:\n"
                "- EGFR, ALK, ROS1, BRAF V600E, KRAS G12C, MET, RET, NTRK\n"
                "- PD-L1 (TPS) mediante inmunohistoquímica\n\n"
                "Primera línea según biomarcador:\n"
                "- EGFR mutado: Osimertinib (Evidencia 1A)\n"
                "- ALK fusión: Alectinib (Evidencia 1A)\n"
                "- PD-L1 ≥50%: Pembrolizumab monoterapia\n"
                "- PD-L1 <50%, sin drivers: Pembrolizumab + pemetrexed + platino\n"
                "- KRAS G12C: Sotorasib o adagrasib"
            ),
        },
        {
            "header": "Evidencia - Ensayos Clínicos de Referencia",
            "content": (
                "1. KEYNOTE-024: Pembrolizumab vs quimioterapia en PD-L1 ≥50%. "
                "SLP: 10.3 vs 6.0 meses (HR 0.50). SG: 30.0 vs 14.2 meses.\n"
                "2. FLAURA: Osimertinib vs gefitinib/erlotinib en EGFR+. "
                "SLP: 18.9 vs 10.2 meses (HR 0.46).\n"
                "3. ALEX: Alectinib vs crizotinib en ALK+. "
                "SLP: 34.8 vs 10.9 meses (HR 0.43).\n"
                "4. CheckMate 816: Nivolumab neoadyuvante + QT. "
                "pCR: 24.0% vs 2.2% (OR 13.94).\n"
                "5. PACIFIC: Durvalumab post-QRT en Estadio III. "
                "SG a 5 años: 42.9% vs 33.4% (HR 0.72)."
            ),
        },
    ],
    "breast_cancer": [
        {
            "header": "Diagnóstico",
            "content": (
                "Evaluación inicial ante sospecha de cáncer de mama:\n"
                "- Mamografía bilateral diagnóstica\n"
                "- Ecografía mamaria complementaria\n"
                "- RM mamaria en alto riesgo (BRCA1/2, historia familiar)\n"
                "- Biopsia con aguja gruesa (core) guiada por imagen\n"
                "- Panel inmunohistoquímico: ER, PR, HER2, Ki-67\n"
                "- Testing genómico: Oncotype DX, MammaPrint (Estadio I-II, HR+)"
            ),
        },
        {
            "header": "Estratificación por Subtipo Molecular",
            "content": (
                "Clasificación molecular y pronóstico:\n\n"
                "Luminal A (HR+/HER2-, Ki67 bajo):\n"
                "- Mejor pronóstico, responde a hormonoterapia\n"
                "- Tratamiento: Tamoxifeno o inhibidores de aromatasa\n\n"
                "Luminal B (HR+/HER2-, Ki67 alto):\n"
                "- Requiere quimioterapia adyuvante + hormonoterapia\n\n"
                "HER2-positivo:\n"
                "- Trastuzumab + pertuzumab + quimioterapia\n"
                "- T-DM1 si enfermedad residual post-neoadyuvancia\n\n"
                "Triple Negativo (TNBC):\n"
                "- Quimioterapia con antraciclina + taxano\n"
                "- Pembrolizumab neoadyuvante (KEYNOTE-522)"
            ),
        },
        {
            "header": "Tratamiento - Enfermedad Temprana",
            "content": (
                "Recomendación: Cirugía + terapia adyuvante según subtipo.\n\n"
                "Cirugía conservadora + radioterapia es equivalente a mastectomía "
                "en supervivencia global (Nivel de Evidencia 1A).\n\n"
                "Biopsia de ganglio centinela para axila clínicamente negativa.\n"
                "Disección axilar solo si ≥3 ganglios positivos.\n\n"
                "Hormonoterapia adyuvante (HR+):\n"
                "- Premenopausia: Tamoxifeno × 5-10 años\n"
                "- Postmenopausia: Letrozol/Anastrozol × 5 años\n"
                "- CDK4/6 inhibidor (abemaciclib) si alto riesgo"
            ),
        },
        {
            "header": "Evidencia - Ensayos Clínicos de Referencia",
            "content": (
                "1. KEYNOTE-522: Pembrolizumab neoadyuvante en TNBC. "
                "pCR: 64.8% vs 51.2% (delta 13.6%). SLE a 3 años mejorada.\n"
                "2. monarchE: Abemaciclib adyuvante en HR+/HER2- alto riesgo. "
                "iDFS a 4 años: 85.8% vs 79.4% (HR 0.664).\n"
                "3. CLEOPATRA: Pertuzumab + trastuzumab en HER2+ metastásico. "
                "SG: 56.5 vs 40.8 meses (HR 0.68).\n"
                "4. DESTINY-Breast04: T-DXd en HER2-low. "
                "SLP: 10.1 vs 5.4 meses (HR 0.51)."
            ),
        },
    ],
    "colorectal_cancer": [
        {
            "header": "Diagnóstico",
            "content": (
                "Evaluación diagnóstica del cáncer colorrectal:\n"
                "- Colonoscopia completa con biopsia de la lesión\n"
                "- TC de tórax/abdomen/pelvis con contraste para estadificación\n"
                "- CEA sérico basal\n"
                "- RM pélvica para cáncer de recto\n"
                "- Testing molecular: MSI/MMR, KRAS, NRAS, BRAF, HER2"
            ),
        },
        {
            "header": "Estratificación de Riesgo",
            "content": (
                "Factores pronósticos en cáncer colorrectal:\n\n"
                "Alto riesgo de recurrencia:\n"
                "- T4 (invasión de serosa o órganos adyacentes)\n"
                "- Invasión linfovascular o perineural\n"
                "- Histología pobremente diferenciada\n"
                "- <12 ganglios linfáticos examinados\n"
                "- Márgenes positivos o cercanos (<1 mm)\n"
                "- Obstrucción o perforación intestinal al diagnóstico\n\n"
                "MSI-High (dMMR):\n"
                "- Mejor pronóstico en Estadio II\n"
                "- No beneficio de 5-FU en monoterapia\n"
                "- Excelente respuesta a inmunoterapia en enfermedad avanzada"
            ),
        },
        {
            "header": "Tratamiento - Enfermedad Localizada",
            "content": (
                "Recomendación: Resección quirúrgica con márgenes adecuados.\n\n"
                "Colon:\n"
                "- Colectomía con linfadenectomía (mínimo 12 ganglios)\n"
                "- Estadio II alto riesgo: Considerar FOLFOX × 3-6 meses\n"
                "- Estadio III: FOLFOX o CAPOX × 3-6 meses (Evidencia 1A)\n\n"
                "Recto:\n"
                "- cT3/T4 o N+: Quimioradioterapia neoadyuvante (TNT preferida)\n"
                "- Total Neoadjuvant Therapy (TNT): FOLFOX × 4 → QRT → cirugía\n"
                "- Respuesta clínica completa: Considerar Watch-and-Wait"
            ),
        },
        {
            "header": "Tratamiento - Enfermedad Metastásica",
            "content": (
                "Recomendación: Terapia sistémica guiada por biomarcadores.\n\n"
                "MSI-High/dMMR:\n"
                "- Primera línea: Pembrolizumab monoterapia (KEYNOTE-177)\n"
                "- SLP: 16.5 vs 8.2 meses (HR 0.60)\n\n"
                "MSS (microsatélite estable):\n"
                "- RAS wild-type, lado izquierdo: FOLFOX/FOLFIRI + cetuximab\n"
                "- RAS wild-type, lado derecho: FOLFOX/FOLFIRI + bevacizumab\n"
                "- RAS mutado: FOLFOX/FOLFIRI + bevacizumab\n"
                "- BRAF V600E: Encorafenib + cetuximab (BEACON CRC)\n\n"
                "Metástasis hepáticas resecables:\n"
                "- Quimioterapia perioperatoria + resección hepática\n"
                "- Supervivencia a 5 años: 30-50% post-resección"
            ),
        },
        {
            "header": "Evidencia - Ensayos Clínicos de Referencia",
            "content": (
                "1. KEYNOTE-177: Pembrolizumab en CCR MSI-H primera línea. "
                "SLP: 16.5 vs 8.2 meses (HR 0.60). ORR: 43.8% vs 33.1%.\n"
                "2. BEACON CRC: Encorafenib + cetuximab en BRAF V600E. "
                "SG: 9.3 vs 5.9 meses (HR 0.61).\n"
                "3. IDEA: CAPOX × 3 meses vs 6 meses en Estadio III. "
                "No-inferioridad demostrada para bajo riesgo.\n"
                "4. RAPIDO: TNT en cáncer de recto localmente avanzado. "
                "Fallo del tratamiento: 23.7% vs 30.4% (HR 0.75)."
            ),
        },
    ],
}


def generate_guideline_pdf(
    cancer_type: str,
    output_dir: str = "data/clinical_guides",
) -> str:
    """
    Generates a synthetic clinical guideline PDF for testing the RAG pipeline.
    Uses reportlab if available, falls back to PyMuPDF (fitz) plain text PDF.

    Args:
        cancer_type: Key from SYNTHETIC_GUIDELINES dict.
        output_dir: Directory to save the generated PDF.

    Returns:
        Absolute path to the generated PDF file.
    """
    if cancer_type not in SYNTHETIC_GUIDELINES:
        raise ValueError(
            f"Unknown cancer type '{cancer_type}'. "
            f"Available: {list(SYNTHETIC_GUIDELINES.keys())}"
        )

    sections = SYNTHETIC_GUIDELINES[cancer_type]
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"synthetic_guideline_{cancer_type}.pdf")

    try:
        _generate_with_reportlab(cancer_type, sections, output_path)
    except ImportError:
        _generate_with_fitz(cancer_type, sections, output_path)

    print(f"✅ Generated synthetic guideline PDF → {output_path}")
    return os.path.abspath(output_path)


def _generate_with_reportlab(
    cancer_type: str,
    sections: List[Dict[str, str]],
    output_path: str,
) -> None:
    """Generate PDF using reportlab for richer formatting."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "GuidelineTitle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=20,
    )
    header_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=16,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "BodyText",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
    )

    elements: list = []
    title = cancer_type.replace("_", " ").title()
    elements.append(Paragraph(f"Guía Clínica Sintética: {title}", title_style))
    elements.append(
        Paragraph(
            "DOCUMENTO SINTÉTICO - Solo para validación del pipeline OncoAgent",
            styles["Italic"],
        )
    )
    elements.append(Spacer(1, 0.3 * inch))

    for section in sections:
        elements.append(Paragraph(section["header"], header_style))
        # Convert newlines to <br/> for reportlab
        content_html = section["content"].replace("\n", "<br/>")
        elements.append(Paragraph(content_html, body_style))
        elements.append(Spacer(1, 0.2 * inch))

    doc.build(elements)


def _generate_with_fitz(
    cancer_type: str,
    sections: List[Dict[str, str]],
    output_path: str,
) -> None:
    """Fallback: Generate plain-text PDF using PyMuPDF (fitz)."""
    import fitz  # PyMuPDF

    doc = fitz.open()
    title = cancer_type.replace("_", " ").title()

    for section in sections:
        page = doc.new_page()
        text = f"{section['header']}\n\n{section['content']}"
        text_rect = fitz.Rect(50, 50, 550, 750)
        page.insert_textbox(text_rect, text, fontsize=11, fontname="helv")

    # Add a title page at the beginning
    title_page = doc.new_page(pno=0)
    title_rect = fitz.Rect(50, 200, 550, 400)
    title_page.insert_textbox(
        title_rect,
        f"Guía Clínica Sintética: {title}\n\n"
        "DOCUMENTO SINTÉTICO\nSolo para validación del pipeline OncoAgent",
        fontsize=16,
        fontname="helv",
        align=1,  # Center
    )

    doc.save(output_path)
    doc.close()


def generate_all_guidelines(output_dir: str = "data/clinical_guides") -> List[str]:
    """
    Generates synthetic guideline PDFs for all cancer types.

    Returns:
        List of absolute paths to generated PDF files.
    """
    paths: List[str] = []
    for cancer_type in SYNTHETIC_GUIDELINES:
        path = generate_guideline_pdf(cancer_type, output_dir)
        paths.append(path)
    return paths


if __name__ == "__main__":
    generated = generate_all_guidelines()
    print(f"\n🚀 Generated {len(generated)} synthetic guideline PDFs:")
    for p in generated:
        print(f"   → {p}")
