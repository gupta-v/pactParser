from app.models import ExtractedContractData

# --- Configuration ---
WEIGHTS = {
    "financial": 30,
    "party": 25,
    "payment": 20,
    "sla": 15,
    "contact": 10
}

def calculate_score_and_gaps(data: dict) -> (float, list):
    """
    Calculates a "completeness" score (0-100) and identifies
    data gaps based on the extracted contract data.
    
    This script is robust: it does NOT validate the content,
    only the *existence* of key fields.
    """
    
    score = 0.0
    gaps = []

    try:
        # 1. Pydantic validation: This is our first check.
        # If the LLM output is structurally invalid, this fails.
        parsed_data = ExtractedContractData(**data)
    except Exception as e:
        return 0.0, [f"Critical parse error: Invalid data structure from LLM. {e}"]

    # --- 1. Financial Completeness (30 points) ---
    # Check if the 'financial_details' object exists AND
    # if its key values are not None/empty.
    if parsed_data.financial_details:
        fin = parsed_data.financial_details
        if fin.total_contract_value or fin.monthly_recurring_revenue:
            score += WEIGHTS["financial"] * 0.5  # 15 pts
        else:
            gaps.append("Missing Total Contract Value or MRR.")
            
        if fin.line_items: # Checks if the list is not empty
            score += WEIGHTS["financial"] * 0.5  # 15 pts
        else:
            gaps.append("Missing detailed line items.")
    else:
        gaps.append("Missing all financial details.")

    # --- 2. Party Identification (25 points) ---
    # This is the robust fix. We no longer check the 'role' string.
    # We only check if at least two parties with 'legal_name's were found.
    if parsed_data.parties:
        # This list comprehension filters out any "blah blah" entries
        # that might have a null 'legal_name'.
        valid_parties = [p for p in parsed_data.parties if p.legal_name]
        
        if len(valid_parties) >= 2:
            score += WEIGHTS["party"] # 25 pts
        elif len(valid_parties) == 1:
            score += WEIGHTS["party"] * 0.5 # 12.5 pts
            gaps.append("Only one party was clearly identified with a legal name.")
        else:
            gaps.append("Failed to identify any parties with a legal name.")
    else:
        gaps.append("Failed to identify any contract parties.")

    # --- 3. Payment Terms Clarity (20 points) ---
    # Check if the 'payment_structure' object exists AND
    # if its key values are not None.
    if parsed_data.payment_structure:
        pay = parsed_data.payment_structure
        if pay.payment_terms: # e.g., "Net 30" (is not None)
            score += WEIGHTS["payment"] * 0.5 # 10 pts
        else:
            gaps.append("Missing payment terms (e.g., Net 30).")
            
        if pay.payment_schedule or pay.due_dates:
            score += WEIGHTS["payment"] * 0.5 # 10 pts
        else:
            gaps.append("Missing payment schedule or due dates.")
    else:
        gaps.append("Missing all payment structure details.")

    # --- 4. SLA Definition (15 points) ---
    # Check if 'sla_details' list is not empty OR 'penalty_clauses' is not None
    if parsed_data.service_level_agreements:
        sla = parsed_data.service_level_agreements
        if sla.sla_details or sla.penalty_clauses:
            score += WEIGHTS["sla"] # 15 pts
        else:
            gaps.append("SLA section found, but no specific metrics or penalties defined.")
    else:
        gaps.append("Missing Service Level Agreement (SLA) section.")

    # --- 5. Contact Information (10 points) ---
    # This will correctly fail your screenshot
    if parsed_data.account_info:
        acct = parsed_data.account_info
        if acct.billing_contact_name or acct.billing_contact_email:
            score += WEIGHTS["contact"] # 10 pts
        else:
            gaps.append("Missing billing contact details (name or email).")
    else:
        gaps.append("Missing all account and contact information.")

    return round(score, 2), gaps