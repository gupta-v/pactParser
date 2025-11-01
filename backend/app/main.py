import os
import mimetypes
from fastapi import (
    FastAPI, 
    UploadFile, 
    HTTPException, 
    Depends,
    Query
)
from fastapi.responses import FileResponse
from pymongo.database import Database
from contextlib import asynccontextmanager

# --- ADD THIS IMPORT ---
from starlette.concurrency import run_in_threadpool

from app.database import get_db, create_indexes
from app.models import (
    ContractDB,
    UploadResponse,
    StatusResponse,
    ContractListResponse,
    PaginatedContractList,
    ContractStatus
)
from app.celery_app import celery_app

# --- Configuration ---
UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)


# --- App Lifespan (FIXED) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    """
    print("🚀 PactParser API is starting up...")
    # --- FIX: Added 'await' ---
    await create_indexes()
    yield
    print("👋 PactParser API is shutting down...")


# --- FastAPI App Initialization ---
app = FastAPI(
    title="PactParser API",
    description="API for asynchronous contract parsing and intelligence.",
    version="1.0.0",
    lifespan=lifespan
)


# --- API Endpoints (FIXED) ---

@app.post("/contracts/upload", response_model=UploadResponse)
async def upload_contract(
    file: UploadFile, 
    db: Database = Depends(get_db)
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Only PDFs are accepted."
        )

    new_contract = ContractDB(
        filename=file.filename,
        storage_path="" 
    )
    file_extension = ".pdf"
    storage_path = os.path.join(
        UPLOADS_DIR, f"{new_contract.contract_id}{file_extension}"
    )
    
    # --- FIX: Non-blocking file save ---
    try:
        file_content = await file.read()
        with open(storage_path, "wb") as buffer:
            await run_in_threadpool(buffer.write, file_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # --- FIX: Non-blocking database insert ---
    new_contract.storage_path = storage_path
    try:
        await run_in_threadpool(db.contracts.insert_one, new_contract.model_dump())
        print(f"✅ Successfully inserted {new_contract.contract_id} into DB.")
    except Exception as e:
        print(f"❌ DB Insert FAILED: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create contract entry in database: {e}")

    # 3. Dispatch the background task
    celery_app.send_task(
        "app.celery_worker.process_contract",
        args=[new_contract.contract_id, storage_path]
    )
    
    return UploadResponse(
        contract_id=new_contract.contract_id,
        filename=new_contract.filename,
        status=new_contract.status
    )

@app.get("/contracts", response_model=PaginatedContractList)
async def get_contract_list(
    status: str | None = Query(default=None),
    filename: str | None = Query(default=None), 
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Database = Depends(get_db)
):
    query = {}
    if status:
        query["status"] = status
    if filename:
        query["filename"] = {"$regex": filename, "$options": "i"}
        
    skip = (page - 1) * page_size
    
    # --- FIX: Non-blocking database calls ---
    total_count = await run_in_threadpool(db.contracts.count_documents, query)
    cursor = db.contracts.find(query).skip(skip).limit(page_size).sort("created_at", -1)
    items = [
        ContractListResponse(**doc) for doc in await run_in_threadpool(list, cursor)
    ]
    
    return PaginatedContractList(
        total_count=total_count,
        page=page,
        page_size=page_size,
        items=items
    )
    
@app.get("/contracts/{contract_id}", response_model=ContractDB)
async def get_contract_data(
    contract_id: str, 
    db: Database = Depends(get_db)
):
    # --- FIX: Non-blocking database call ---
    contract = await run_in_threadpool(db.contracts.find_one, {"contract_id": contract_id})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    if contract["status"] != ContractStatus.COMPLETED:
        raise HTTPException(
            status_code=400, 
            detail=f"Contract is still {contract['status']}. Data not available."
        )
    return contract

@app.get("/contracts/{contract_id}/status", response_model=StatusResponse)
async def get_processing_status(
    contract_id: str, 
    db: Database = Depends(get_db)
):
    # --- FIX: Non-blocking database call ---
    contract = await run_in_threadpool(db.contracts.find_one, {"contract_id": contract_id})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    return StatusResponse(
        contract_id=contract["contract_id"],
        status=contract["status"],
        progress_percentage=contract["progress_percentage"],
        error_message=contract["error_message"]
    )

@app.get("/contracts/{contract_id}/download")
async def download_contract_file(
    contract_id: str, 
    db: Database = Depends(get_db)
):
    # --- FIX: Non-blocking database call ---
    contract = await run_in_threadpool(db.contracts.find_one, {"contract_id": contract_id})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    file_path = contract["storage_path"]
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404, 
            detail="File not found on server."
        )

    media_type, _ = mimetypes.guess_type(file_path)
    if media_type is None:
        media_type = "application/octet-stream"

    return FileResponse(
        file_path,
        media_type=media_type,
        filename=contract["filename"]
    )