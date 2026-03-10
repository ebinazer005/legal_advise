#uvicorn fileUploadinDB:app --reload
import os
import shutil
import pymysql
from fastapi import FastAPI, UploadFile, File
from typing import List
from fastapi.middleware.cors import CORSMiddleware


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