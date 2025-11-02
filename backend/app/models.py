import uuid
from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# --- Helper Classes ---

class ContractStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Signatory(BaseModel):
    name: Optional[str] = Field(default=None, description="Full name of the signatory")
    role: Optional[str] = Field(default=None, description="Title or role of the signatory (e.g., 'VP of Sales')")

class PartyDetails(BaseModel):
    legal_name: Optional[str] = Field(default=None, description="The full legal name of the company or entity")
    role: Optional[str] = Field(default=None, description="The role of this party in the contract (e.g., customer, vendor)")
    registration_details: Optional[str] = Field(default=None, description="Registration info, e.g., 'Federal Tax ID: 12-3456789'")
    address: Optional[str] = Field(default=None, description="Full mailing or legal address")
    signatories: Optional[List[Signatory]] = Field(default_factory=list, description="Authorized signatories for this party")

class AccountInfo(BaseModel):
    account_number: Optional[str] = Field(default=None, description="Customer account number or reference ID")
    billing_contact_name: Optional[str] = Field(default=None)
    billing_contact_email: Optional[str] = Field(default=None)
    billing_contact_phone: Optional[str] = Field(default=None)
    technical_contact_name: Optional[str] = Field(default=None)
    technical_contact_email: Optional[str] = Field(default=None)
    technical_contact_phone: Optional[str] = Field(default=None)

class LineItem(BaseModel):
    description: Optional[str] = Field(default=None)
    quantity: Optional[float] = Field(default=None)
    unit_price: Optional[float] = Field(default=None)
    total: Optional[float] = Field(default=None, description="Total for this line item (quantity * unit_price)")
    item_type: Optional[Literal["recurring", "one-time"]] = Field(default=None, description="Type of charge")

class FinancialDetails(BaseModel):
    total_contract_value: Optional[float] = Field(default=None, description="The total value of the contract over its full term")
    monthly_recurring_revenue: Optional[float] = Field(default=None, description="MRR")
    total_one_time_fees: Optional[float] = Field(default=None, description="All setup, implementation, or one-time charges")
    currency: Optional[str] = Field(default="USD", description="Currency (e.g., 'USD', 'EUR')")
    tax_information: Optional[str] = Field(default=None, description="Details on tax liabilities or rates")
    line_items: Optional[List[LineItem]] = Field(default_factory=list)

class BankingDetails(BaseModel):
    bank_name: Optional[str] = Field(default=None)
    account_number: Optional[str] = Field(default=None)
    routing_number: Optional[str] = Field(default=None)

class PaymentStructure(BaseModel):
    payment_terms: Optional[str] = Field(default=None, description="e.g., 'Net 30', 'Net 60'")
    payment_schedule: Optional[str] = Field(default=None, description="e.g., 'Monthly recurring billing', 'On completion'")
    due_dates: Optional[str] = Field(default=None, description="e.g., '30th of each month'")
    payment_method: Optional[str] = Field(default=None, description="e.g., 'ACH transfer', 'Wire transfer', 'Check'")
    late_payment_clause: Optional[str] = Field(default=None, description="Penalties for late payments, e.g., '1.5% monthly interest'")
    banking_details: Optional[BankingDetails] = Field(default=None)

class RevenueClassification(BaseModel):
    contract_type: Optional[Literal["recurring", "one-time", "both"]] = Field(default=None, description="Primary type of revenue")
    billing_cycle: Optional[str] = Field(default=None, description="e.g., 'Monthly', 'Annually', 'Quarterly'")
    renewal_terms: Optional[str] = Field(default=None, description="Full text of the renewal clause")
    auto_renewal: Optional[bool] = Field(default=None, description="Does the contract auto-renew?")

class SLADetail(BaseModel):
    metric: Optional[str] = Field(default=None, description="The metric being measured, e.g., 'Uptime', 'Response Time'")
    commitment: Optional[str] = Field(default=None, description="The specific commitment, e.g., '99.9%', '1 hour response'")

class SLA(BaseModel):
    sla_details: Optional[List[SLADetail]] = Field(default_factory=list)
    penalty_clauses: Optional[str] = Field(default=None, description="Text describing penalties for SLA misses")
    remedies: Optional[str] = Field(default=None, description="Other remedies or service credits")
    support_terms: Optional[str] = Field(default=None, description="e.g., '8x5 business hours', '24/7 support'")

class ExtractedContractData(BaseModel):
    parties: Optional[List[PartyDetails]] = Field(default_factory=list)
    account_info: Optional[AccountInfo] = Field(default=None)
    financial_details: Optional[FinancialDetails] = Field(default=None)
    payment_structure: Optional[PaymentStructure] = Field(default=None)
    revenue_classification: Optional[RevenueClassification] = Field(default=None)
    service_level_agreements: Optional[SLA] = Field(default=None)
    
    effective_date: Optional[str] = Field(default=None, description="The date the contract becomes effective")
    term_length: Optional[str] = Field(default=None, description="The duration of the contract, e.g., '24 months'")
    governing_law: Optional[str] = Field(default=None, description="The jurisdiction for the contract, e.g., 'State of California'")

# --- 2. Database Schema ---

class ContractDB(BaseModel):
    contract_id: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True)
    filename: str
    storage_path: str = Field(description="Internal path where the original PDF is stored")
    
    status: str = Field(default=ContractStatus.PENDING, index=True)
    progress_percentage: int = Field(default=0)
    
    extracted_data: Optional[ExtractedContractData] = Field(default=None)
    
    confidence_score: Optional[float] = Field(default=None, index=True)
    gap_analysis: Optional[List[str]] = Field(default_factory=list, description="List of missing critical fields")
    
    error_message: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# --- 3. API Schemas ---

class UploadResponse(BaseModel):
    contract_id: str
    filename: str
    status: str

class StatusResponse(BaseModel):
    contract_id: str
    status: str
    progress_percentage: int
    error_message: Optional[str] = None

class ContractListResponse(BaseModel):
    contract_id: str
    filename: str
    status: str
    confidence_score: Optional[float] = None
    created_at: datetime

class PaginatedContractList(BaseModel):
    total_count: int
    page: int
    page_size: int
    items: List[ContractListResponse]

