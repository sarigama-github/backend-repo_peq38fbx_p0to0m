import os
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Company, Module, UserAccount

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

# -------- Simple API key auth (RBAC) --------

class AuthContext(BaseModel):
    user_id: str
    email: str
    role: str
    company_id: Optional[str] = None


def get_auth_context(x_api_key: Optional[str] = Header(default=None)) -> AuthContext:
    """
    Minimal API key auth using "useraccount" collection.
    - Clients send X-API-Key header.
    - We lookup a useraccount by api_key and return role + company context.
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    doc = db["useraccount"].find_one({"api_key": x_api_key}) if db else None
    if not doc:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return AuthContext(
        user_id=str(doc.get("_id")),
        email=doc.get("email"),
        role=doc.get("role", "viewer"),
        company_id=doc.get("company_id")
    )


def require_roles(*roles: str):
    def dependency(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if ctx.role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden: insufficient role")
        return ctx
    return dependency

# -------- Mini-ERP endpoints --------

class CompanyCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    country: Optional[str] = None
    modules: Optional[List[str]] = []

@app.post("/api/companies")
def create_company(payload: CompanyCreate, ctx: AuthContext = Depends(require_roles("admin"))):
    company = Company(**payload.model_dump())
    company_id = create_document("company", company)
    return {"id": company_id, "message": "Company created"}

@app.get("/api/companies")
def list_companies(ctx: AuthContext = Depends(require_roles("admin", "manager"))):
    docs = get_documents("company", limit=50)
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return docs

class ModuleToggle(BaseModel):
    company_id: str
    name: str
    enabled: bool

@app.post("/api/modules/toggle")
def toggle_module(payload: ModuleToggle, ctx: AuthContext = Depends(require_roles("admin", "manager"))):
    # naive insert to record module toggles; in real app we'd update existing
    mod = Module(company_id=payload.company_id, name=payload.name, enabled=payload.enabled)
    module_id = create_document("module", mod)
    return {"id": module_id, "message": "Module updated"}

# -------- User management for RBAC bootstrap --------

class UserCreate(BaseModel):
    name: str
    email: str
    role: str = "viewer"
    company_id: Optional[str] = None

class APIKeyIssue(BaseModel):
    email: str

@app.post("/api/users")
def create_user(payload: UserCreate, ctx: AuthContext = Depends(require_roles("admin"))):
    # In a real app, enforce unique email and hash secrets.
    api_key = os.urandom(16).hex()
    user = UserAccount(name=payload.name, email=payload.email, role=payload.role, company_id=payload.company_id, api_key=api_key)
    user_id = create_document("useraccount", user)
    return {"id": user_id, "api_key": api_key}

@app.post("/api/users/issue-key")
def issue_api_key(payload: APIKeyIssue, ctx: AuthContext = Depends(require_roles("admin"))):
    doc = db["useraccount"].find_one({"email": payload.email}) if db else None
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    new_key = os.urandom(16).hex()
    db["useraccount"].update_one({"_id": doc["_id"]}, {"$set": {"api_key": new_key}})
    return {"api_key": new_key}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
