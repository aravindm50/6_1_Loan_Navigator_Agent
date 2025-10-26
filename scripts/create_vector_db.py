from chromadb import HttpClient
from chromadb.utils import embedding_functions
import glob, fitz, os
from dotenv import load_dotenv

load_dotenv()

def create_vector_chromadb():
    # -----------------------------
    # 1️⃣ Connect to remot"""  """e Chroma server
    # -----------------------------
    chroma_host = os.getenv("CHROMA_URL")  # Cloud Run URL
    print(chroma_host)
    client = HttpClient(host=chroma_host)

    # -----------------------------
    # 2️⃣ Embedding function
    # -----------------------------
    ef = embedding_functions.SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")

    # -----------------------------
    # 3️⃣ Create collection
    # -----------------------------
    # HttpClient does not directly integrate embedding functions, so embeddings
    # are usually handled before calling `add` if needed
    collection_name = "policy_docs"
    try:
        collection = client.get_collection(name=collection_name)

    except:
        print("creating the collection of chroma db")
        collection = client.create_collection(name=collection_name, embedding_function=ef)

    # -----------------------------
    # 4️⃣ Upload PDFs
    # -----------------------------
    for file_path in glob.glob("data/policy_docs/*.pdf"):
        doc = fitz.open(file_path)
        text = "\n".join(page.get_text() for page in doc)
        doc_id = os.path.basename(file_path)
        
        collection.add(
            documents=[text],
            ids=[doc_id],
        )
    print("Documents uploaded successfully!")
    question = "Can I prepay my loan without penalty?"
    results = collection.query(query_texts=[question], n_results=5)
    documents = results.get("documents", [[]])[0]
    print("Retrieved docs:", documents)
    return True
create_vector_chromadb()