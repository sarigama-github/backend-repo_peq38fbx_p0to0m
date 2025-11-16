import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Company, Module

app = FastAPI(title="Global Management Mini-ERP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Global Management Mini-ERP Backend Running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# -------- Mini-ERP endpoints --------

class CompanyCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    country: Optional[str] = None
    modules: Optional[List[str]] = []

@app.post("/api/companies")
def create_company(payload: CompanyCreate):
    company = Company(**payload.model_dump())
    company_id = create_document("company", company)
    return {"id": company_id, "message": "Company created"}

@app.get("/api/companies")
def list_companies():
    docs = get_documents("company", limit=50)
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return docs

class ModuleToggle(BaseModel):
    company_id: str
    name: str
    enabled: bool

@app.post("/api/modules/toggle")
def toggle_module(payload: ModuleToggle):
    # naive insert to record module toggles; in real app we'd update existing
    mod = Module(company_id=payload.company_id, name=payload.name, enabled=payload.enabled)
    module_id = create_document("module", mod)
    return {"id": module_id, "message": "Module updated"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
