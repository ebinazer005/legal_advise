# uvicorn getExternalApis:app --reload --port 8001

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, os, re, time

app = FastAPI()  

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str

@app.post("/ingest")
def ingest_cases(data: SearchRequest):
    url = "https://www.courtlistener.com/api/rest/v4/search/"
    headers = {"Authorization": "Token 4571f32c57dbb3dc179613ea6d8b064c2baffb33"}
    os.makedirs("docs", exist_ok=True)

    downloaded_files = []
    processing_log = []
    page = 1    
    max_pages = 3

    while page <= max_pages and len(downloaded_files) < 5:
        params = {"q": data.query, "type": "o", "format": "json", "page": page}
        response = requests.get(url, headers=headers, params=params)
        result = response.json()

        if "results" not in result:
            break

        for case in result["results"]:
            if len(downloaded_files) >= 5:
                break

            case_name = case.get("caseName", "unknown_case")
            original_name = case_name 
            case_name = re.sub(r'[^a-zA-Z0-9_]', '_', case_name)
            opinion_url = case.get("absolute_url")
            if not opinion_url:
                processing_log.append({"case": original_name, "status": "⚠️ No URL"})
                continue

            opinion_id = opinion_url.split("/")[2]

            try:
                opinion_api = f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/"
                opinion_data = requests.get(opinion_api, headers=headers, timeout=10 , verify=False).json()
                text = (
                    opinion_data.get("plain_text") or
                    opinion_data.get("html_with_citations") or
                    opinion_data.get("html") or ""
                )
                file_name = f"{case_name}_{opinion_id}"

                if text and len(text) > 200:
                    with open(f"docs/{file_name}.txt", "w", encoding="utf-8") as f:
                        f.write(text)
                    downloaded_files.append({"name": f"{file_name}.txt", "type": "TXT"})
                    processing_log.append({"case": case_name, "status": "✅ Saved"}) 

                else:
                    pdf_url = opinion_data.get("download_url")
                    if pdf_url:
                        try: 
                            pdf = requests.get(pdf_url, timeout=10).content
                            with open(f"docs/{file_name}.pdf", "wb") as f:
                                f.write(pdf)
                            downloaded_files.append({"name": f"{file_name}.pdf", "type": "PDF"})
                            processing_log.append({"case": case_name, "status": "✅ Saved PDF"})
                        except Exception:
                            processing_log.append({"case": case_name, "status": "❌ PDF failed"})
                    else:
                        processing_log.append({"case": case_name, "status": "⚠️ No document"})

            except Exception as e:
                processing_log.append({"case": original_name, "status": f"❌ Error"})

            time.sleep(0.5)

        page += 1
    print("Log:", processing_log)    
    print("Files:", downloaded_files)

    return {
        "files": downloaded_files,
        "log": processing_log
            }


@app.delete("/ingest/clear")
def clear_docs():
    folder = "docs"
    if not os.path.exists(folder):
        return {"message": "No files to delete"}
    files = os.listdir(folder)
    for f in files:
        os.remove(os.path.join(folder, f))
    return {"message": f"Deleted {len(files)} files successfully"}