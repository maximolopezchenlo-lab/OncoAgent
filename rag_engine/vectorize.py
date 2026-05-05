import chromadb
import chromadb.utils.embedding_functions as embedding_functions
import json
import os

def vectorize_chunks(input_dir="data/processed/chunks", db_dir="data/chroma_db"):
    # Ensure directories exist
    os.makedirs(db_dir, exist_ok=True)
    
    print("⏳ Inicializando ChromaDB local...")
    # Initialize persistent ChromaDB
    client = chromadb.PersistentClient(path=db_dir)
    
    # Use medical embedding model
    model_name = "pritamdeka/S-PubMedBert-MS-MARCO"
    print(f"🧠 Cargando modelo de embeddings: {model_name}...")
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
    
    # Create or get collection
    collection = client.get_or_create_collection(name="clinical_guidelines", embedding_function=emb_fn)
    
    if not os.path.exists(input_dir):
        print(f"⚠️ El directorio {input_dir} no existe.")
        return

    json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
    
    if not json_files:
        print(f"⚠️ No se encontraron archivos JSON en {input_dir}.")
        return

    total_chunks = 0
    
    for file in json_files:
        path = os.path.join(input_dir, file)
        print(f"📄 Indexando {file}...")
        
        with open(path, 'r', encoding='utf-8') as f:
            try:
                chunks = json.load(f)
            except json.JSONDecodeError:
                print(f"❌ Error al decodificar JSON en {file}")
                continue
        
        if not chunks:
            continue
            
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            # Generate a unique ID for each chunk
            chunk_id = f"{file.replace('.json', '')}_chunk_{i}"
            ids.append(chunk_id)
            
            # Contextualize the chunk slightly by adding the header to the content
            header = chunk.get("header", "Unknown Header")
            content = chunk.get("content", "")
            doc_text = f"Section: {header}\n\n{content}"
            documents.append(doc_text)
            
            metadatas.append({
                "source": chunk.get("source", "Unknown"),
                "page": chunk.get("page", -1),
                "header": header
            })
            
        # Add to chroma in batches
        try:
            # collection.add natively handles batching if needed, but doing it directly is usually fine for these sizes
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            total_chunks += len(ids)
        except Exception as e:
            print(f"❌ Error al añadir {file}: {e}")
            
    print(f"✅ Vectorización completada. {total_chunks} chunks indexados en ChromaDB.")
    print(f"📂 Base de datos guardada en: {db_dir}")

if __name__ == "__main__":
    vectorize_chunks()
