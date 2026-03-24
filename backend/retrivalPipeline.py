# #uvicorn retrivalPipeline:app --reload --port 8002
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import requests
import pymysql
import urllib3
import re

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

persist_directory = "db/chroma_db"
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

db = Chroma(
    persist_directory=persist_directory,
    embedding_function=embedding_model,
    collection_name="langchain",
    collection_metadata={"hnsw:space": "cosine"},
)

mysql_db = pymysql.connect(
    host="localhost",
    user="root",
    password="mysql",
    database="legalAdviser_RAG",
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
        "homicide", "extortion", "embezzlement", "forgery",
    ]
    for keyword in case_types:
        if keyword in context.lower():
            print(f"Case type found: {keyword}")
            return keyword
    return ""


def fetch_client_details(query: str):
    try:
        def extract_keywords(query: str):
            query = query.lower()
            noise_words = ["case", "id", "caseid", "case_id"]
            for word in noise_words:
                query = query.replace(word, "")
            words = re.findall(r"\b[a-z0-9]+\b", query)
            return [w for w in words if len(w) > 2]

        words = extract_keywords(query)
        print(f"Search words: {words}")

        if not words:
            return {
                "status": "error",
                "error": True,
                "message": "❌ Invalid query format. Please provide a case ID or case name."
            }

        # Separate case_id and name
        case_id = None
        name_words = []

        for w in words:
            if re.match(r"^[a-z]\d+$", w):  # matches s101, s102, n101 etc
                case_id = w
            else:
                name_words.append(w)

        print(f"Case ID: {case_id}, Name words: {name_words}")

        cur = get_cursor()
        rows = []
        found_by = None

        # 1. Search by case_id first
        if case_id:
            cur.execute(
                """
                SELECT case_id, case_name, next_hearing_date, notes, fee_paid, case_status, last_hearing_date
                FROM client_details
                WHERE LOWER(case_id) = %s
                """,
                (case_id,),
            )
            rows = cur.fetchall()
            if rows:
                found_by = "case_id"
                print("✅ Found by case_id")

        # 2. Fallback — search by name if case_id not found
        if not rows and name_words:
            conditions = " OR ".join(["LOWER(case_name) LIKE %s" for _ in name_words])
            values = [f"%{w}%" for w in name_words]
            cur.execute(
                f"""
                SELECT case_id, case_name, next_hearing_date, notes, fee_paid, case_status, last_hearing_date
                FROM client_details
                WHERE {conditions}
                """,
                values,
            )
            rows = cur.fetchall()
            if rows:
                found_by = "case_name"
                print("✅ Found by case_name")

        print(f"Found rows: {len(rows)}, found_by: {found_by}")

        # ❌ No result found at all
        if not rows:
            return {
                "status": "error",
                "error": True,
                "message": "❌ No record found for the given ID or name. Please check and try again."
            }

        # ⚠️ MISMATCH CHECK — case_id found but name doesn't match
        if found_by == "case_id" and name_words:
            db_case_name = rows[0][1].lower()
            name_matched = any(w in db_case_name for w in name_words)

            if not name_matched:
                print("⚠️ Name mismatch detected")
                return {
                    "status": "mismatch",
                    "error": False,
                    "warning": True,
                    "message": "⚠️ Case ID and client name mismatch. Please verify and try again.",
                    "case_id": rows[0][0],
                    "case_name": rows[0][1],
                }

        # ❌ Case exists but case_name is empty or invalid
        if (
            not str(rows[0][1]).strip()
            or str(rows[0][1]).strip().lower() == "not specified"
        ):
            return {
                "status": "error",
                "error": True,
                "message": "❌ Invalid Case ID or incomplete data. Please check your input."
            }

        # ✅ Normal match — return full details
        return {
            "status": "success",
            "error": False,
            "data": [
                {
                    "case_id": r[0],
                    "case_name": r[1],
                    "next_hearing_date": str(r[2]) if r[2] else "Not specified",
                    "notes": r[3] or "",
                    "fee_paid": float(r[4]) if r[4] else 0.00,
                    "case_status": r[5],
                    "last_hearing_date": str(r[6]) if r[6] else "Not specified",
                }
                for r in rows
            ]
        }

    except Exception as e:
        print(f"MySQL fetch failed: {e}")
        return {
            "status": "error",
            "error": True,
            "message": f"❌ Database error: {str(e)}"
        }


def fetch_related_links(search_term: str):
    try:
        url = "https://www.courtlistener.com/api/rest/v4/search/"
        headers = {"Authorization": "Token 4571f32c57dbb3dc179613ea6d8b064c2baffb33"}
        params = {"q": search_term, "type": "o", "format": "json", "page": 1}

        response = requests.get(url, headers=headers, params=params, verify=False, timeout=5)
        print(f"CourtListener status: {response.status_code}")
        data = response.json()
        results = data.get("results", [])
        print(f"CourtListener results count: {len(results)}")

        links = []
        for case in results[:5]:
            absolute_url = case.get("absolute_url", "")
            if absolute_url:
                links.append({
                    "name": case.get("caseName", "Unknown Case"),
                    "url": f"https://www.courtlistener.com{absolute_url}",
                    "court": case.get("court_id", ""),
                    "date": case.get("dateFiled", ""),
                })

        print(f"Links found: {len(links)}")
        return links

    except Exception as e:
        print(f"CourtListener fetch failed: {e}")
        return []


@app.post("/reload")
def reload_db():
    global db
    try:
        db = Chroma(
            persist_directory=persist_directory,
            embedding_function=embedding_model,
            collection_name="langchain",
            collection_metadata={"hnsw:space": "cosine"},
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

    case_keywords = [
    "case", "client", "defendant", "accused", "matter",
    "vs", "v.", "surash", "swathi", "murder", "bribe",
    ]
    
    is_case_search = any(word in query.lower() for word in case_keywords)

    


    # retriever = db.as_retriever(search_kwargs={"k": k})
    # retrieval_docs = retriever.invoke(query)

    retriever = db.as_retriever(search_kwargs={"k": k})

    search_query = query  # default

    # ✅ If case search, enrich query using DB result
    if is_case_search:
        client_details_response = fetch_client_details(query)

        if client_details_response and client_details_response.get("status") == "success":
            case_name = client_details_response["data"][0].get("case_name", "")
            case_id = client_details_response["data"][0].get("case_id", "")

            # 🔥 Enriched query (THIS IS THE FIX)
            search_query = f"{case_name} {case_id}"

    # 🔍 Use enriched query for retrieval
    retrieval_docs = retriever.invoke(search_query)

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

    case_keywords = [
        "case", "client", "defendant", "accused", "matter",
        "vs", "v.", "surash", "swathi", "murder", "bribe",
    ]
    is_case_search = any(word in query.lower() for word in case_keywords)

    # Fetch client details if case search
    client_details_response = fetch_client_details(query) if is_case_search else None

    # ❌ ERROR: Return immediately with error message (NO LLM CALL)
    if client_details_response and client_details_response.get("error"):
        return {
            "query": query,
            "answer": client_details_response["message"],
            "context": [],
            "related_links": [],
            "top_k": k,
            "alpha": data.alpha,
            "status": "error",
        }

    # ⚠️ WARNING: Return immediately with warning message (NO LLM CALL)
    if client_details_response and client_details_response.get("warning"):
        return {
            "query": query,
            "answer": client_details_response["message"],
            "case_id": client_details_response.get("case_id"),
            "case_name": client_details_response.get("case_name"),
            "context": [],
            "related_links": [],
            "top_k": k,
            "alpha": data.alpha,
            "status": "warning",
        }

    # Safe default — prevents NameError
    related_links = []

    # ── Fetch CourtListener links ──
    if is_case_search:
        case_type = extract_case_type(client_context + reference_context)

        if not case_type and client_details_response and not client_details_response.get("error"):
            case_name = client_details_response["data"][0].get("case_name", "").lower()
            if "murder" in case_name:
                case_type = "murder"
            elif "fraud" in case_name:
                case_type = "fraud"
            elif "bribery" in case_name:
                case_type = "bribery"
            else:
                case_type = case_name

        if not case_type:
            clean_words = re.findall(r"\b[a-zA-Z]+\b", query)
            case_type = " ".join(clean_words[:2])

        print(f"CourtListener search term: {case_type}")
        related_links = fetch_related_links(case_type)

    # ── Build db_info for prompt ──
    if client_details_response and client_details_response.get("status") == "success":
        db_info = ""
        for c in client_details_response["data"]:
            db_info += f"""
- Case ID: {c['case_id']}
- Case Name: {c['case_name']}
- Last Hearing: {c['last_hearing_date']}
- Next Hearing: {c['next_hearing_date']}
- Fee Paid: RM {c['fee_paid']}
- Case Status: {c['case_status']}
- Notes: {c['notes']}
"""
    else:
        db_info = "No records found in database"

    # ── Build prompt and call LLM ──
    if is_case_search:
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

🪪 Case ID:

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


-------------    SECTION 4 — REFERENCE ARGUMENTS  --------------

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
        HumanMessage(content=insert_theInput),
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
        "status": "success",
    }