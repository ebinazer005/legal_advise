#uvicorn fileUploadinDB:app --reload
import os
import shutil
import pymysql
from fastapi import FastAPI, UploadFile, File
from typing import List
from fastapi.middleware.cors import CORSMiddleware

import threading
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv


import threading

app = FastAPI()

#enable cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "docs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

#dbConnection
db = pymysql.connect(
    host="localhost",
    user="root",
    password="mysql",
    database="legalAdviser_RAG"
)

cursor = db.cursor()


#ingastion
persist_directory = "db/chroma_db"
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def load_document(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        return TextLoader(file_path, encoding="utf-8").load()
    elif ext == ".pdf":
        return PyPDFLoader(file_path).load()
    elif ext == ".docx":
        return Docx2txtLoader(file_path).load()
    return []

def run_ingestion():
    print("🔄 Running ingestion pipeline...")
    all_docs = []

    for file_name in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        if os.path.isdir(file_path):
            continue
        docs = load_document(file_path)
        if docs:
            all_docs.extend(docs)
            print(f"Loaded: {file_name}")

    if not all_docs:
        print("No documents found")
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(all_docs)

    #clear old + re-index
    Chroma(
        persist_directory=persist_directory,
        embedding_function=embedding_model
    ).delete_collection()

    Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=persist_directory,
        collection_metadata={"hnsw:space": "cosine"}
    )

    print(f"Ingestion done — {len(chunks)} chunks indexed")

# File watcher
class DocsWatcher(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print(f"📄 New file detected: {event.src_path}")
            threading.Timer(1.5, run_ingestion).start()  

    def on_deleted(self, event):
        if not event.is_directory:
            print(f"🗑️ File deleted: {event.src_path}")
            threading.Timer(1.5, run_ingestion).start()

# Start watcher on server start ────────────────
observer = Observer()
observer.schedule(DocsWatcher(), path=UPLOAD_FOLDER, recursive=False)
observer.start()
print("👀 Watching docs folder for changes...")

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):

    uploaded_files = []

    for file in files:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # store metadata in SQL
        query = "INSERT INTO documents (file_name, file_path) VALUES (%s,%s)"
        cursor.execute(query, (file.filename, file_path))
        db.commit()

        uploaded_files.append(file.filename)

    return {"message": "Files uploaded successfully", "files": uploaded_files}

#for retrive the file
@app.get("/files")
def get_files():

    cursor.execute("SELECT file_name, file_path, upload_time FROM documents")

    rows = cursor.fetchall()

    files = []

    for r in rows:
        files.append({
            "name": r[0],
            "path": r[1],
            "uploaded_at": str(r[2])
        })

    return {"files": files}