import os
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

def load_documents(folder_path):
    all_documents = []

    if not os.path.exists(folder_path):
        print(f"Folder does not exist: {folder_path}")
        return []

    files = os.listdir(folder_path)
    print(f"Found {len(files)} files in '{folder_path}'")

    for file_name in files:
        file_path = os.path.join(folder_path, file_name)

        if os.path.isdir(file_path):
            continue

        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == ".txt":
            loader = TextLoader(file_path, encoding='utf-8')
        elif file_extension == ".pdf":
            loader = PyPDFLoader(file_path)
        elif file_extension == ".docx":
            loader = Docx2txtLoader(file_path)
        else:
            print(f"Unsupported file: {file_name}")
            continue

        documents = loader.load()
        all_documents.extend(documents)
        print(f"Loaded {file_name} — {len(documents)} pages")
        for i, doc in enumerate(documents):
           print(f"document : {i+1}")
           print(f"metadata : {doc.metadata['source']}")
           print(f"content length : {len(doc.page_content)} characters")
           print(f"content preview : {doc.page_content[:100]}")
           print(f"metadata : {doc.metadata}")

    
        
    return all_documents

def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True
    )

    chunks = text_splitter.split_documents(documents)


    return chunks


def create_vector_store(chunks,persist_directory = "db/chroma_db"):

    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2") 
    vectorstores = Chroma.from_documents(
        documents = chunks,
        embedding = embedding_model,
        persist_directory = persist_directory,
        collection_metadata={"hnsw:space" : "cosine"}  # this is alogrithem
    
    )
    return vectorstores

def main():
    documents = load_documents(folder_path="docs")

    chunks = split_documents(documents)

    vectorStore = create_vector_store(chunks)
    
if __name__ == "__main__":
    main()



