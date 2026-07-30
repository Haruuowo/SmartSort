from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from smartsort import classifier, history

app = FastAPI(title="SmartSort API")

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SortRequest(BaseModel):
    folder_path: str
    dry_run: bool = True

@app.get("/api/files")
def list_files(folder_path: str):
    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail="Invalid directory path")
    
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    return {"files": files, "count": len(files)}

@app.post("/api/sort")
def sort_files(req: SortRequest):
    if not os.path.isdir(req.folder_path):
        raise HTTPException(status_code=400, detail="Invalid directory path")
        
    files_to_process = [f for f in os.listdir(req.folder_path) if os.path.isfile(os.path.join(req.folder_path, f))]
    
    results = []
    moved = 0
    duplicate = 0
    error = 0
    
    for item in files_to_process:
        item_path = os.path.join(req.folder_path, item)
        result = classifier.process_file(item_path, dry_run=req.dry_run)
        
        results.append({
            "filename": item,
            "status": result.get("status"),
            "destination": result.get("destination"),
            "reason": result.get("reason")
        })
        
        status = result.get("status")
        if status == "moved":
            moved += 1
        elif status == "duplicate":
            duplicate += 1
        else:
            error += 1
            
    return {
        "summary": {
            "moved": moved,
            "duplicate": duplicate,
            "error": error,
            "total": len(files_to_process)
        },
        "results": results
    }

@app.get("/api/history")
def get_history(limit: int = 50):
    try:
        records = history.get_history(limit)
        return {"history": records}
    except Exception as e:
        return {"error": str(e), "history": []}
