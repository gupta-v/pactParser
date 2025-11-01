from datetime import datetime, timezone
from app.celery_app import celery_app
from app.database import get_db_sync
from app.models import ContractStatus

from app.llm_parser import read_pdf_text, parse_contract_text
from app.scoring import calculate_score_and_gaps


@celery_app.task(bind=True, max_retries=3)
def process_contract(self, contract_id: str, file_path: str):
    """
    The main background task for processing a single contract.
    """
    db = get_db_sync()
    
    def update_progress(percentage: int, status: str = ContractStatus.PROCESSING):
        """Helper to update MongoDB progress."""
        db.contracts.update_one(
            {"contract_id": contract_id},
            {"$set": {"progress_percentage": percentage, "status": status}}
        )

    try:
        # --- Step 1: Set status to 'processing' ---
        print(f"Starting processing for {contract_id}")
        update_progress(10)
        
        # --- Step 2: Read PDF to Text (REAL) ---
        print(f"Reading PDF: {file_path}")
        update_progress(30)
        extracted_text = read_pdf_text(file_path)
        
        # --- Step 3: LLM Extraction (REAL) ---
        print(f"Parsing text for {contract_id}")
        update_progress(70)
        extracted_data_json = parse_contract_text(extracted_text)
        
        # --- Step 4: Scoring & Gap Analysis (REAL) ---
        print(f"Scoring data for {contract_id}")
        update_progress(90)
        score, gaps = calculate_score_and_gaps(extracted_data_json)

        # --- Step 5: SUCCESS: Update DB with final data ---
        db.contracts.update_one(
            {"contract_id": contract_id},
            {"$set": {
                "status": ContractStatus.COMPLETED,
                "progress_percentage": 100,
                "extracted_data": extracted_data_json,
                "confidence_score": score,
                "gap_analysis": gaps,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        print(f"✅ Successfully processed contract {contract_id}")

    except Exception as e:
        # --- Step 6: FAILURE: Catch-all error handler ---
        print(f"❌ Failed to process {contract_id}: {e}")
        
        db.contracts.update_one(
            {"contract_id": contract_id},
            {"$set": {
                "status": ContractStatus.FAILED,
                "progress_percentage": 0,
                "error_message": str(e),
                "updated_at": datetime.now(timezone.utc)
            }}
        )