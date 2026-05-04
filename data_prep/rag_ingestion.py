import fitz  # PyMuPDF
import json
import os
import re
from typing import List, Dict, Optional

class OncoRAGIngestor:
    """
    Ingestor para guías clínicas oncológicas (NCCN/ESMO).
    Implementa Adaptive Semantic Chunking basado en encabezados médicos.
    """
    
    def __init__(self, output_dir: str = "processed_data"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Palabras clave para identificación de secciones semánticas
        self.headers_keywords = [
            r"Recomendaci[óo]n",
            r"Evidencia",
            r"Grado",
            r"Algoritmo",
            r"Discusi[óo]n",
            r"Tratamiento",
            r"Diagn[óo]stico",
            r"Estratificaci[óo]n"
        ]
        self.header_pattern = re.compile(f"^(?:{'|'.join(self.headers_keywords)}).*", re.IGNORECASE)

    def extract_text_semantically(self, pdf_path: str) -> List[Dict[str, str]]:
        """
        Extrae texto del PDF y lo divide en chunks semánticos basados en encabezados.
        """
        doc = fitz.open(pdf_path)
        chunks = []
        current_header = "Introducción/General"
        current_content = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text_instances = page.get_text("blocks") # (x0, y0, x1, y1, text, block_no, block_type)
            
            for block in text_instances:
                text = block[4].strip()
                if not text:
                    continue
                
                # Detectar si el bloque parece ser un encabezado médico
                if self.header_pattern.match(text) and len(text) < 100:
                    # Guardar el chunk anterior si existe
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
    # Ejemplo de uso (puede ser llamado desde la CLI)
    ingestor = OncoRAGIngestor()
    
    # Directorio de guías clínicas
    guides_dir = "clinical_guides"
    if os.path.exists(guides_dir):
        for file in os.listdir(guides_dir):
            if file.endswith(".pdf"):
                path = os.path.join(guides_dir, file)
                print(f"Procesando: {file}...")
                chunks = ingestor.extract_text_semantically(path)
                ingestor.save_chunks(chunks, file.replace(".pdf", ""))
    else:
        print(f"⚠️ El directorio {guides_dir} no existe. Crea uno y añade tus PDFs de NCCN/ESMO.")
