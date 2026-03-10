#uvicorn retrivalPipeline:app --reload

from fastapi import FastAPI
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage,SystemMessage
from langchain_groq import ChatGroq
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

persist_directory= "db/chroma_db"
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

db = Chroma(
    persist_directory=persist_directory,
    embedding_function=embedding_model,
    collection_metadata={"hnsw:space" : "cosine"}
)

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3        
    alpha: float = 0.75
   
    

@app.post("/ask")
def ask_question(data: QueryRequest):

    query = data.query
    k = data.top_k

    retrival = db.as_retriever(search_kwargs={'k':k})
    retrieval_docs = retrival.invoke(query)

    insert_theInput = f"""based on the following document , please aunswer this question : {query}

Documents : {chr(10).join(f"-{doc.page_content}" for doc in retrieval_docs)}

Please provide a clear, helpful answer using only the information from these documents. If you can't find the answer in the documents, say "I don't have enough information to answer that question based on the provided documents."
"""
    model = ChatGroq(model="llama-3.1-8b-instant")

    message = [
        SystemMessage(content="you are a helpful assistent."),
        HumanMessage(content=insert_theInput)
    ]
    result = model.invoke(message)

    context_docs = [doc.page_content for doc in retrieval_docs]

    return {
        "query": query,
        "answer": result.content,
        "context": [{
                "id": i + 1,
                "content": doc.page_content,
                "source": doc.metadata.get("source", "Unknown"),
                "page": doc.metadata.get("page", "N/A"),
            }
            for i, doc in enumerate(retrieval_docs)
        ],
        "top_k": k,
        "alpha": data.alpha,
    }

  