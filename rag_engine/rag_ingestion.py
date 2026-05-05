import fitz  # PyMuPDF
import json
import os
import re
from typing import List, Dict, Optional

class OncoRAGIngestor:
    """
    Ingestor para guías clínicas oncológicas (NCCN/ESMO).
    Implementa Adaptive Semantic Chunking basado en encabezados médicos en inglés.
    """
    
    def __init__(self, output_dir: str = "processed_data"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Palabras clave para identificación de secciones semánticas en inglés (Guías reales)
        self.headers_keywords = [
            r"Recommendation",
            r"Recommendations",
            r"Evidence",
            r"Algorithm",
            r"Discussion",
            r"Treatment",
            r"Diagnosis",
            r"Workup",
            r"Staging",
            r"Follow-Up",
            r"Principles",
            r"Pathology",
            r"Systemic Therapy"
        ]
        self.header_pattern = re.compile(f"^(?:{'|'.join(self.headers_keywords)}).*", re.IGNORECASE)

        # Patrones para sanitización de textos (Eliminar rastro de NCCN)
        self.nccn_patterns = [
            re.compile(r"National Comprehensive Cancer Network", re.IGNORECASE),
            re.compile(r"NCCN Guidelines", re.IGNORECASE),
            re.compile(r"NCCN\.org", re.IGNORECASE),
            re.compile(r"\bNCCN\b", re.IGNORECASE)
        ]

    def sanitize_text(self, text: str) -> str:
        """Reemplaza rastros de la marca original por términos genéricos de guías oncológicas."""
        sanitized = text
        for pattern in self.nccn_patterns:
            sanitized = pattern.sub("Oncology Guidelines", sanitized)
        return sanitized

    def extract_text_semantically(self, pdf_path: str) -> List[Dict[str, str]]:
        """
        Extrae texto del PDF nativo respetando el orden visual con PyMuPDF
        y lo divide en chunks semánticos basados en encabezados médicos.
        """
        doc = fitz.open(pdf_path)
        chunks = []
        current_header = "Introduction / General"
        current_content = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text_instances = page.get_text("blocks") # Extrae respetando el orden lógico de lectura (x0, y0, x1, y1, text, block_no, block_type)
            
            for block in text_instances:
                text = block[4].strip()
                if not text:
                    continue
                
                # Sanitizar el texto
                text = self.sanitize_text(text)
                
                # Detectar si el bloque parece ser un encabezado médico relevante
                if self.header_pattern.match(text) and len(text) < 120:
                    # Guardar el chunk anterior si existe y tiene contenido válido
                    if current_content:
                        chunks.append({
                            "header": current_header,
                            "content": "\n".join(current_content),
                            "source": os.path.basename(pdf_path),
                            "page": page_num + 1
                        })
                    current_header = text
                    current_content = []
                else:
                    current_content.append(text)
        
        # Añadir el último chunk
        if current_content:
            chunks.append({
                "header": current_header,
                "content": "\n".join(current_content),
                "source": os.path.basename(pdf_path),
                "page": len(doc)
            })
            
        return chunks

    def save_chunks(self, chunks: List[Dict[str, str]], filename: str):
        """Guarda los chunks procesados en un archivo JSON."""
        output_path = os.path.join(self.output_dir, f"{filename}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=4)
        print(f"✅ Guardados {len(chunks)} chunks en {output_path}")

if __name__ == "__main__":
    # Iniciar pipeline de ingesta
    ingestor = OncoRAGIngestor(output_dir="data/processed/nccn_chunks")
    
    # Directorio de guías clínicas
    guides_dir = "data/clinical_guides/nccn"
    
    if os.path.exists(guides_dir):
        pdf_files = []
        for root, dirs, files in os.walk(guides_dir):
            for file in files:
                if file.endswith(".pdf"):
                    pdf_files.append(os.path.join(root, file))
                    
        if not pdf_files:
            print(f"⚠️ El directorio {guides_dir} está vacío. Agrega los PDFs.")
            
        for path in pdf_files:
            file = os.path.basename(path)
            # Filtro riguroso: Excluir PDFs diseñados para pacientes
            if "patient" in file.lower() or "_pat" in file.lower() or "patient" in path.lower():
                print(f"⏭️  Omitiendo guía para pacientes (riesgo de baja densidad médica): {file}")
                continue
                
            print(f"⏳ Procesando: {file}...")
            try:
                chunks = ingestor.extract_text_semantically(path)
                ingestor.save_chunks(chunks, file.replace(".pdf", ""))
            except Exception as e:
                print(f"❌ Error procesando {file}: {e}")
    else:
        print(f"⚠️ El directorio {guides_dir} no existe. Crea uno y añade tus PDFs de NCCN/ESMO.")
