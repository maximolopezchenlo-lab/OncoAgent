import os
import json
import re
import pymupdf4llm
import networkx as nx
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedOncoIngestor:
    """
    Advanced Ingestor for SOTA RAG.
    - Uses pymupdf4llm for Markdown table preservation.
    - Builds a basic Knowledge Graph (GraphRAG) using NetworkX.
    """
    
    def __init__(self, output_dir: str = "data/processed/sota_chunks", graph_path: str = "data/processed/knowledge_graph.gml"):
        self.output_dir = output_dir
        self.graph_path = graph_path
        self.graph = nx.Graph()
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Keywords for entity extraction (Basic regex-based GraphRAG)
        self.drugs = ["pembrolizumab", "nivolumab", "erlotinib", "afatinib", "osimertinib", "gefitinib", "alectinib", "brigatinib", "lorlatinib", "trastuzumab", "pertuzumab", "lapatinib", "neratinib", "t-dm1", "paclitaxel", "docetaxel", "carboplatin", "cisplatin", "gemcitabine", "pemetrexed", "bevacizumab", "ramucirumab", "atezolizumab", "durvalumab"]
        self.mutations = ["egfr", "alk", "ros1", "braf", "kras", "nras", "her2", "pd-l1", "msi-h", "dmmr", "pik3ca", "esr1", "brca1", "brca2", "ret", "met", "ntrk"]
        self.conditions = ["nsclc", "sclc", "breast cancer", "colon cancer", "rectal cancer", "melanoma", "adenocarcinoma", "squamous cell carcinoma"]

    def extract_and_graph(self, pdf_path: str):
        """
        Converts PDF to Markdown and updates the Knowledge Graph.
        """
        filename = os.path.basename(pdf_path)
        logger.info(f"⏳ Processing {filename} with SOTA Markdown extraction...")
        
        # 1. Convert PDF to Markdown (preserves tables!)
        md_text = pymupdf4llm.to_markdown(pdf_path)
        
        # 2. Simple Semantic Chunking (split by headers)
        # We look for # or ## headers in markdown
        chunks = []
        current_chunk = []
        current_header = "Intro"
        
        for line in md_text.split("\n"):
            if line.startswith("#"):
                if current_chunk:
                    content = "\n".join(current_chunk)
                    chunks.append({
                        "header": current_header,
                        "content": content,
                        "source": filename
                    })
                    self._update_graph(content, filename)
                current_header = line.strip("# ").strip()
                current_chunk = []
            else:
                current_chunk.append(line)
        
        # Save last chunk
        if current_chunk:
            content = "\n".join(current_chunk)
            chunks.append({
                "header": current_header,
                "content": content,
                "source": filename
            })
            self._update_graph(content, filename)
            
        # 3. Save chunks
        output_path = os.path.join(self.output_dir, f"{filename.replace('.pdf', '')}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=4)
        
        logger.info(f"✅ Saved {len(chunks)} Markdown chunks for {filename}")

    def _update_graph(self, text: str, source: str):
        """
        Updates the NetworkX graph by extracting clinical entities.
        """
        text_lower = text.lower()
        
        found_drugs = [d for d in self.drugs if d in text_lower]
        found_mutations = [m for m in self.mutations if m in text_lower]
        found_conditions = [c for c in self.conditions if c in text_lower]
        
        # Add nodes and edges
        for d in found_drugs:
            self.graph.add_node(d, type="drug")
            for m in found_mutations:
                self.graph.add_node(m, type="mutation")
                self.graph.add_edge(d, m, relation="targets", source=source)
            for c in found_conditions:
                self.graph.add_node(c, type="condition")
                self.graph.add_edge(d, c, relation="treats", source=source)
        
        for m in found_mutations:
            for c in found_conditions:
                self.graph.add_edge(m, c, relation="associated_with", source=source)

    def save_graph(self):
        """
        Saves the graph to disk.
        """
        # Save as GML for better compatibility with graph tools, or JSON for simplicity
        nx.write_gml(self.graph, self.graph_path)
        logger.info(f"🕸️ Knowledge Graph saved to {self.graph_path} ({len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges)")

if __name__ == "__main__":
    ingestor = AdvancedOncoIngestor()
    
    guides_dir = "data/clinical_guides"
    target_files = ["nscl.pdf", "breast.pdf", "colon.pdf", "hcc.pdf"]
    
    if os.path.exists(guides_dir):
        for root, dirs, files in os.walk(guides_dir):
            for file in files:
                if file in target_files and "patient" not in file.lower():
                    pdf_path = os.path.join(root, file)
                    ingestor.extract_and_graph(pdf_path)
        
        ingestor.save_graph()
    else:
        logger.warning(f"Directory {guides_dir} not found.")
