from chromadb import HttpClient
from chromadb.utils import embedding_functions
import glob, fitz, os

# -----------------------------
# 1️⃣ Connect to remote Chroma server
# -----------------------------
chroma_host = os.getenv("CHROMA_URL")  # Cloud Run URL
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
    client.create_collection(name=collection_name)
except Exception:
    pass  # collection already exists

# -----------------------------
# 4️⃣ Upload PDFs
# -----------------------------
for file_path in glob.glob("data/policy_docs/*.pdf"):
    doc = fitz.open(file_path)
    text = "\n".join(page.get_text() for page in doc)

    payload = {
        "documents": [text],
        "ids": [os.path.basename(file_path)],
        "metadatas": [{"source": os.path.basename(file_path)}]
    }

    client.add(collection_name, **payload)
    print(f"Uploaded: {file_path}")
