#uvicorn retrivalPipeline:app --reload --port 8002
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage,SystemMessage
from langchain_groq import ChatGroq
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import requests        
import pymysql         
import urllib3 


load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],
    # allow_origins=["*"],
    allow_credentials=True,
    # allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

persist_directory= "db/chroma_db"
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

db = Chroma(
    persist_directory=persist_directory,
    embedding_function=embedding_model,
    collection_name="langchain",
    collection_metadata={"hnsw:space" : "cosine"}
)


mysql_db = pymysql.connect(
    host="localhost",
    user="root",
    password="mysql",
    database="legalAdviser_RAG"
)

def get_cursor():
    mysql_db.ping(reconnect=True)
    return mysql_db.cursor()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3        
    alpha: float = 0.75

def extract_case_type(context: str) -> str:
    case_types = [
        "murder", "bribery", "fraud", "assault", "robbery",
        "rape", "theft", "manslaughter", "kidnapping", "drug",
        "corruption", "contract", "negligence", "defamation",
        "homicide", "extortion", "embezzlement", "forgery"
    ]
    for keyword in case_types:
        if keyword in context.lower():
            print(f"Case type found: {keyword}")
            return keyword
    return ""


def fetch_client_details(query: str):
    try:
        words = [w for w in query.lower().replace("case", "").strip().split() if len(w) > 2]
        print(f"Search words: {words}")

        if not words:
            return None

        conditions = " OR ".join(["case_name LIKE %s" for _ in words])
        values = [f"%{w}%" for w in words]
        print(f"SQL values: {values}")

        cur = get_cursor()
        cur.execute(f"""
            SELECT case_name,  next_hearing_date, notes, fee_paid, case_status,  last_hearing_date
            FROM client_details
            WHERE {conditions}
        """, values)

        rows = cur.fetchall()
        print(f"Found rows: {len(rows)}")

        if not rows:
            return None

        return [
            {
                "case_name": r[0],
                "last_hearing_date": str(r[5]) if r[5] else "Not specified",
                "next_hearing_date": str(r[1]) if r[1] else "Not specified",
                "fee_paid": float(r[3]) if r[3] else 0.00,
                "case_status": r[4],
                "notes": r[2] or ""
            }
            for r in rows
        ]

    except Exception as e:
        print(f"MySQL fetch failed: {e}")
        return None

# ── Fetch related links from CourtListener ───────
def fetch_related_links(search_term: str):
    try:
        url = "https://www.courtlistener.com/api/rest/v4/search/"
        headers = {"Authorization": "Token 4571f32c57dbb3dc179613ea6d8b064c2baffb33"}
        params = {"q": search_term, "type": "o", "format": "json", "page": 1}

        response = requests.get(
            url,
            headers=headers,
            params=params,
            verify=False,
            timeout=15
        )

        print(f"CourtListener status: {response.status_code}")
        data = response.json()
        results = data.get("results", [])
        print(f"CourtListener results count: {len(results)}")

        links = []
        for case in results[:5]:
            case_name = case.get("caseName", "Unknown Case")
            absolute_url = case.get("absolute_url", "")
            court = case.get("court_id", "")
            date_filed = case.get("dateFiled", "")
            if absolute_url:
                links.append({
                    "name": case_name,
                    "url": f"https://www.courtlistener.com{absolute_url}",
                    "court": court,
                    "date": date_filed
                })

        print(f"Links found: {len(links)}")
        return links

    except Exception as e:
        print(f"CourtListener fetch failed: {e}")
        return []


# ── Add this endpoint to retrivalPipeline.py ────
@app.post("/reload")
def reload_db():
    global db
    try:
        db = Chroma(
            persist_directory=persist_directory,
            embedding_function=embedding_model,
            collection_name="langchain",
            collection_metadata={"hnsw:space": "cosine"}
        )
        count = db._collection.count()
        print(f"✅ ChromaDB reloaded — {count} chunks")
        return {"message": f"✅ Reloaded — {count} chunks indexed"}
    except Exception as e:
        return {"message": f"❌ Reload failed: {e}"}


@app.post("/ask")
def ask_question(data: QueryRequest):
    query = data.query
    k = data.top_k

    retriever = db.as_retriever(search_kwargs={'k': k})
    retrieval_docs = retriever.invoke(query)

    client_context = ""
    reference_context = ""

    for doc in retrieval_docs:
        source = doc.metadata.get("source", "Unknown")
        doc_type = doc.metadata.get("doc_type", "reference")
        file_name = os.path.basename(source)

        if doc_type == "client":
            client_context += f"\n📄 {file_name}\n  - {doc.page_content}\n"
        else:
            reference_context += f"\n📄 {file_name}\n  - {doc.page_content}\n"

    # ── Detect case search ───────────────────────
    case_keywords = ["case", "client", "defendant", "accused", "matter", "vs", "v.", "surash", "murder", "bribe"]
    is_case_search = any(word in query.lower() for word in case_keywords)

    # ── Fetch from MySQL & CourtListener ─────────
    client_details = fetch_client_details(query) if is_case_search else None
    related_links = []
    if is_case_search:
        case_type = extract_case_type(client_context + reference_context)
        if not case_type:
            case_type = query  # fallback
        print(f"CourtListener search term: {case_type}")
        related_links = fetch_related_links(case_type)

    if is_case_search:

        if client_details:
            db_info = ""
            for c in client_details:
                db_info += f"""
- Case Name: {c['case_name']}
- Last Hearing: {c['last_hearing_date']}
- Next Hearing: {c['next_hearing_date']}
- Fee Paid: RM {c['fee_paid']}
- Case Status: {c['case_status']}
- Notes: {c['notes']}
"""
        else:
            db_info = "No records found in database"

    
        links_context = ""
        for link in related_links:
            links_context += f"- {link['name']} | Court: {link['court']} | Date: {link['date']} | URL: {link['url']}\n"

        insert_theInput = f"""You are a Legal Case Management Assistant for Ebinazer Selvaraj Consultancy.

User Query: {query}

DATABASE RECORDS (use ONLY for Section 1):
{db_info}

CLIENT DOCUMENTS (use ONLY for Section 2):
{client_context if client_context else "No client documents"}

COURTLISTENER ONLINE CASES (use ONLY for Section 3):
{links_context if links_context else "No online cases found"}

REFERENCE DOCUMENTS (use ONLY for Section 4):
{reference_context if reference_context else "No reference documents"}

Please respond in EXACTLY this format:


-------------    SECTION 1 — CLIENT DETAILS  --------------

👤 Case Name: 

📅 Last Hearing Date: 

⏭️ Next Hearing Date: 

💰 Fee Paid: RM 

📋 Case Status: 

📝 Notes:


-------------    SECTION 2 — EVIDENCE ANALYSIS  --------------

⚖️ EVIDENCE AGAINST CLIENT:
- (list each point)

✅ EVIDENCE IN FAVOUR OF CLIENT:
- (list each point)


-------------    SECTION 3 — RELATED ONLINE CASES  --------------

(List each case from COURTLISTENER with name, court, date and full URL)


-------------    SECTION 4 — REFERENCE  ARGUMENTS   --------------

⚖️ Likely Verdict:
🗣️ Strong Defence Arguments:
🗣️ Prosecution Likely Arguments:

Instructions:
- Section 1: ONLY from DATABASE RECORDS
- Section 2: ONLY from CLIENT DOCUMENTS
- Section 3: ONLY from COURTLISTENER ONLINE CASES — include full URLs
- Section 4: Based on REFERENCE DOCUMENTS
- If field not found write "Not specified"
"""

    else:
        insert_theInput = f"""You are a Legal Advice Assistant for Ebinazer Selvaraj Consultancy.

Question: {query}

Available Documents:
{client_context}
{reference_context}

Answer clearly and concisely. Reference documents if relevant.
"""

    model = ChatGroq(model="llama-3.1-8b-instant")
    messages = [
        SystemMessage(content="You are an experienced Legal Adviser AI for Ebinazer Selvaraj Consultancy. Be professional, precise and always follow the exact format requested."),
        HumanMessage(content=insert_theInput)
    ]

    result = model.invoke(messages)

    return {
        "query": query,
        "answer": result.content,
        "context": [
            {
                "id": i + 1,
                "content": doc.page_content,
                "source": doc.metadata.get("source", "Unknown"),
                "doc_type": doc.metadata.get("doc_type", "reference"),
                "page": doc.metadata.get("page", "N/A"),
            }
            for i, doc in enumerate(retrieval_docs)
        ],
        "related_links": related_links,
        "top_k": k,
        "alpha": data.alpha,
    }
