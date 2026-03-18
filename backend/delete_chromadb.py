from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

persist_directory = "db/chroma_db"
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

db = Chroma(
    persist_directory=persist_directory,
    embedding_function=embedding_model,
    collection_name="langchain"
)

db.delete_collection()
print("ChromaDB cleared")