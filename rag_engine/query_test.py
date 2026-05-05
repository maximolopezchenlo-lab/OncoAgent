import chromadb
import chromadb.utils.embedding_functions as embedding_functions

def test_query(query: str = "What is the recommended treatment for advanced HCC?"):
    db_dir = "data/chroma_db"
    
    print("⏳ Inicializando ChromaDB local...")
    client = chromadb.PersistentClient(path=db_dir)
    
    model_name = "pritamdeka/S-PubMedBert-MS-MARCO"
    print(f"🧠 Cargando modelo de embeddings: {model_name}...")
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
    
    collection = client.get_collection(name="clinical_guidelines", embedding_function=emb_fn)
    
    print(f"❓ Buscando: '{query}'")
    results = collection.query(
        query_texts=[query],
        n_results=3
    )
    
    print("\n🔍 Resultados principales:")
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        distance = results['distances'][0][i]
        print(f"\n--- Resultado {i+1} (Distancia: {distance:.4f}) ---")
        print(f"📄 Fuente: {meta.get('source', 'Unknown')} (Página: {meta.get('page', 'Unknown')})")
        print(f"🏷️ Sección: {meta.get('header', 'Unknown')}")
        print(f"📝 Extracto:\n{doc[:300]}...")

if __name__ == "__main__":
    test_query()
