from chromadb import Client
from chromadb.utils import embedding_functions
import os, glob, fitz

ef = embedding_functions.SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
client = Client()

collection = client.create_collection("policy_docs", embedding_function=ef)

for file in glob.glob("Resources/BL4A_policy_docs/*.pdf"):
    doc = fitz.open(file)
    text = "\n".join(page.get_text() for page in doc)
    collection.add(documents=[text], ids=[os.path.basename(file)])