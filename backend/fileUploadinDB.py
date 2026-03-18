# uvicorn fileUploadinDB:app --reload
import os
import shutil
import pymysql
from fastapi import FastAPI, UploadFile, File
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests as http_requests 
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "docs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── DB ───────────────────────────────────────────
db = pymysql.connect(
    host="localhost",
    user="root",
    password="mysql",
    database="legalAdviser_RAG"
)

def get_cursor():
    db.ping(reconnect=True)
    return db.cursor()

# ── Embeddings ───────────────────────────────────
persist_directory = "db/chroma_db"
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# ── Document loader ──────────────────────────────
def load_document(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        return TextLoader(file_path, encoding="utf-8").load()
    elif ext == ".pdf":
        return PyPDFLoader(file_path).load()
    elif ext == ".docx":
        return Docx2txtLoader(file_path).load()
    return []

# ── Ingestion ────────────────────────────────────
ingestion_lock = threading.Lock()

# def run_ingestion():
#     if not ingestion_lock.acquire(blocking=False):
#         print("Ingestion already running, skipping...")
#         return
#     try:
#         print("Running ingestion pipeline...")
#         all_docs = []

#         cur = get_cursor()
#         cur.execute("SELECT file_name FROM documents")
#         manual_files = {row[0] for row in cur.fetchall()}

#         for file_name in os.listdir(UPLOAD_FOLDER):
#             file_path = os.path.join(UPLOAD_FOLDER, file_name)
#             if os.path.isdir(file_path):
#                 continue
#             docs = load_document(file_path)
#             if docs:
#                 for doc in docs:
#                     doc.metadata["doc_type"] = "client" if file_name in manual_files else "reference"
#                 all_docs.extend(docs)
#                 print(f"Loaded: {file_name}")

#         if not all_docs:
#             print("No documents found")
#             return

#         splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
#         chunks = splitter.split_documents(all_docs)

#         Chroma.from_documents(
#             documents=chunks,
#             embedding=embedding_model,
#             persist_directory=persist_directory,
#             collection_metadata={"hnsw:space": "cosine"},
#             collection_name="langchain"
#         )
#         print(f"Ingestion done — {len(chunks)} chunks indexed")

#     except Exception as e:
#         print(f"Ingestion error: {e}")
#     finally:
#         ingestion_lock.release()


def run_ingestion():
    if not ingestion_lock.acquire(blocking=False):
        print("Ingestion already running, skipping...")
        return
    try:
        print("Running ingestion pipeline...")
        all_docs = []

        cur = get_cursor()
        cur.execute("SELECT file_name FROM documents")
        manual_files = {row[0] for row in cur.fetchall()}

        for file_name in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, file_name)
            if os.path.isdir(file_path):
                continue
            docs = load_document(file_path)
            if docs:
                for doc in docs:
                    doc.metadata["doc_type"] = "client" if file_name in manual_files else "reference"
                all_docs.extend(docs)
                print(f"Loaded: {file_name}")

        if not all_docs:
            print("No documents found")
            return

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(all_docs)

        Chroma.from_documents(
            documents=chunks,
            embedding=embedding_model,
            persist_directory=persist_directory,
            collection_metadata={"hnsw:space": "cosine"},
            collection_name="langchain"
        )
        print(f"Ingestion done — {len(chunks)} chunks indexed")

        # ✅ notify retrivalPipeline to reload ChromaDB
        try:
            http_requests.post("http://localhost:8002/reload", timeout=5)
            print("✅ retrivalPipeline reloaded")
        except Exception as e:
            print(f"⚠️ Could not reload retrivalPipeline: {e}")

    except Exception as e:
        print(f"Ingestion error: {e}")
    finally:
        ingestion_lock.release()
# ── File watcher ─────────────────────────────────
class DocsWatcher(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print(f"New file: {event.src_path}")
            threading.Timer(1.5, run_ingestion).start()

    def on_deleted(self, event):
        if not event.is_directory:
            print(f"File deleted: {event.src_path}")
            threading.Timer(1.5, run_ingestion).start()

observer = Observer()
observer.schedule(DocsWatcher(), path=UPLOAD_FOLDER, recursive=False)
observer.start()
print("Watching docs folder for changes...")

# ── Models ───────────────────────────────────────
class DeleteRequest(BaseModel):
    file_names: List[str]

class HearingRequest(BaseModel):
    case_name: str
    next_hearing_date: str
    last_hearing_date: str = ""
    notes: str = ""
    fee_paid: float = 0.00
    case_status: str = "Current"

# ── File endpoints ───────────────────────────────
@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    uploaded_files = []
    for file in files:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        cur = get_cursor()
        cur.execute("INSERT INTO documents (file_name, file_path) VALUES (%s,%s)", (file.filename, file_path))
        db.commit()
        uploaded_files.append(file.filename)
    return {"message": "Files uploaded successfully", "files": uploaded_files}

@app.get("/files")
def get_files():
    cur = get_cursor()
    cur.execute("SELECT file_name, file_path, upload_time FROM documents")
    rows = cur.fetchall()
    return {"files": [{"name": r[0], "path": r[1], "uploaded_at": str(r[2])} for r in rows]}

@app.delete("/files/delete")
def delete_files(data: DeleteRequest):
    deleted = []
    not_found = []
    for file_name in data.file_names:
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            deleted.append(file_name)
        else:
            not_found.append(file_name)
        cur = get_cursor()
        cur.execute("DELETE FROM documents WHERE file_name = %s", (file_name,))
        db.commit()
    return {"message": f"Deleted {len(deleted)} files", "deleted": deleted}

# ── Hearing endpoints ────────────────────────────
@app.post("/hearings")
def add_hearing(data: HearingRequest):
    cur = get_cursor()
    cur.execute(
        "INSERT INTO client_details (case_name, next_hearing_date, last_hearing_date, notes, fee_paid, case_status) VALUES (%s, %s, %s, %s, %s, %s)",
        (data.case_name, data.next_hearing_date, data.last_hearing_date or None, data.notes, data.fee_paid, data.case_status)
    )
    db.commit()
    return {"message": "✅ Client details added"}

@app.get("/hearings")
def get_all_hearings():
    cur = get_cursor()
    cur.execute("""
        SELECT id, case_name, next_hearing_date, last_hearing_date, notes, fee_paid, case_status
        FROM client_details
        ORDER BY next_hearing_date ASC
    """)
    rows = cur.fetchall()
    return {
        "all_hearings": [
            {
                "id": r[0],
                "case_name": r[1],
                "next_hearing_date": str(r[2]) if r[2] else "Not specified",
                "last_hearing_date": str(r[3]) if r[3] else "Not specified",
                "notes": r[4],
                "fee_paid": float(r[5]),
                "case_status": r[6]
            }
            for r in rows
        ]
    }

@app.delete("/hearings/{hearing_id}")
def delete_hearing(hearing_id: int):
    cur = get_cursor()
    cur.execute("DELETE FROM client_details WHERE id = %s", (hearing_id,))
    db.commit()
    return {"message": "✅ Deleted"}