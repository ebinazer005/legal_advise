#uvicorn retrivalPipeline:app --reload --port 8002

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
    allow_credentials=False,
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

    insert_theInput = f"""You are a Legal Advice Assistant.
    Based on the following legal documents and case law, answer the user's legal question.
    User Question: {query}

Legal Documents : {chr(10).join(f"-{doc.page_content}" for doc in retrieval_docs)}

Instructions:
1. Provide legal guidance based ONLY on the provided documents.
2. If relevant, reference previous legal cases or rulings mentioned in the documents.
3. Explain the legal reasoning clearly and professionally.
4. Do NOT invent legal facts or cases.
5. If the documents do not contain enough information, respond with:
"I don't have enough information from the provided legal documents to answer that question."

Provide the response in a clear legal explanation format.

"""
    model = ChatGroq(model="llama-3.1-8b-instant")

    message = [
        SystemMessage(content="""You are an experienced Legal Adviser AI specializing in legal research and case analysis.

Your role is to analyze legal documents, previous case rulings, and statutes to provide clear legal explanations.

Always:
- Base your answer strictly on the provided documents.
- Reference relevant cases when possible.
- Provide structured legal reasoning.
- Avoid speculation or assumptions.
"""),
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

  