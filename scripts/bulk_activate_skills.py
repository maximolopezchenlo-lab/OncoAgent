import os
import shutil
import re

# Source and Destination
SOURCE_DIR = "temp_skills_repo/skills"
DEST_DIR = ".oncoagent/active_skills"

# Keywords for "even a minimum" utility
KEYWORDS = [
    "ai", "llm", "agent", "graph", "rag", "langchain", "llama", "hugging", "torch", "model",
    "med", "health", "onco", "clinic", "science", "bio", "patient", "evidence",
    "python", "script", "code", "refactor", "debug", "test", "audit", "security",
    "performance", "gpu", "amd", "rocm", "cuda", "memory", "optimize",
    "doc", "paper", "write", "latex", "markdown", "log", "report", "whitepaper",
    "ui", "ux", "frontend", "gradio", "streamlit", "react", "design", "css",
    "cloud", "docker", "deployment", "job", "pipeline", "ops", "git",
    "data", "extract", "pdf", "json", "parquet", "vector", "database",
    "math", "logic", "reasoning", "prompt", "eval", "metric"
]

def analyze_and_activate():
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)
        
    skills = os.listdir(SOURCE_DIR)
    activated_count = 0
    
    print(f"Analyzing {len(skills)} skills...")
    
    for skill_name in skills:
        skill_path = os.path.join(SOURCE_DIR, skill_name)
        if not os.path.isdir(skill_path):
            continue
            
        skill_md_path = os.path.join(skill_path, "SKILL.md")
        if not os.path.exists(skill_md_path):
            continue
            
        # Check name first
        useful = any(kw in skill_name.lower() for kw in KEYWORDS)
        
        if not useful:
            # Check content (first 1000 chars)
            try:
                with open(skill_md_path, 'r', encoding='utf-8') as f:
                    content = f.read(1000).lower()
                    useful = any(kw in content for kw in KEYWORDS)
            except:
                pass
                
        if useful:
            # Create subfolder and copy SKILL.md
            target_skill_dir = os.path.join(DEST_DIR, skill_name)
            if not os.path.exists(target_skill_dir):
                os.makedirs(target_skill_dir)
                shutil.copy(skill_md_path, os.path.join(target_skill_dir, "SKILL.md"))
                activated_count += 1
                
    print(f"Activation complete. {activated_count} skills added to {DEST_DIR}.")

if __name__ == "__main__":
    analyze_and_activate()
