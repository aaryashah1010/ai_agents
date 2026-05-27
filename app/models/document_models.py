from pydantic import BaseModel, Field
from typing import List, Optional

# --- SUB-MODELS FOR INDIVIDUAL DATA SECTIONS ---

class PartyDetails(BaseModel):
    name: Optional[str] = Field(None, description="Legal trading name of the company party")
    gstin: Optional[str] = Field(None, description="15-character Goods and Services Tax Identification Number")

class FinancialSummary(BaseModel):
    documentNo: Optional[str] = Field(None, description="Invoice, PO, or Quotation reference serial number")
    documentDate: Optional[str] = Field(None, description="Date of document issuance (YYYY-MM-DD format)")
    dueDate: Optional[str] = Field(None, description="Payment maturity deadline date")
    paymentTerms: Optional[str] = Field(None, description="Net payment condition terms (e.g., Net 30, COD)")
    totalAmount: Optional[float] = Field(None, description="Final gross total value including taxes and adjustments")
    taxAmount: Optional[float] = Field(None, description="Total aggregated tax component value")
    subtotal: Optional[float] = Field(None, description="Net taxable amount before taxes and discounts")
    discount: Optional[float] = Field(None, description="Total absolute deduction value applied")
    roundOff: Optional[float] = Field(None, description="Mathematical round-off fractional adjustments")

class LineItem(BaseModel):
    itemName: str = Field(..., description="The descriptive text name of the product or service")
    itemCode: Optional[str] = Field(None, description="SKU, manufacturing ID, or serial tracking index code")
    description: Optional[str] = Field(None, description="Extended line narrative summary text details")
    hsnSac: Optional[str] = Field(None, description="Harmonized System Nomenclature or Service Accounting Code")
    quantity: Optional[float] = Field(None, description="Total volume or count unit multiplier")
    unit: Optional[str] = Field(None, description="Physical unit of measurement (e.g., Kg, Pcs, Boxes)")
    rate: Optional[float] = Field(None, description="Individual unit base financial value price")
    discount: Optional[float] = Field(None, description="Line-specific structural value reductions applied")
    taxPercent: Optional[float] = Field(None, description="Applicable individual tax rate metric percentage code")
    taxAmount: Optional[float] = Field(None, description="Calculated fractional financial tax applied to this line row")
    lineTotal: Optional[float] = Field(None, description="Final gross row total calculation: (quantity * rate) +/- tax/discount")

# --- CORE DOCUMENT EXTRACTION PAYLOAD AGENT CONTAINER ---

class DocumentExtractionOutput(BaseModel):
    documentType: str = Field(..., description="The verified operational layout context tier (e.g., Purchase Invoice, Quotation, Unknown)")
    confidence: int = Field(..., description="Model confidence tracking score evaluated from 0 to 100")
    vendor: PartyDetails = Field(default_factory=PartyDetails)
    customer: PartyDetails = Field(default_factory=PartyDetails)
    document: FinancialSummary = Field(default_factory=FinancialSummary)
    lineItems: List[LineItem] = Field(default_factory=list, description="Array collection list of parsed line items rows")
    missingFields: List[str] = Field(default_factory=list, description="List names of standard criteria parameters missing from raw payload inputs")
    warnings: List[str] = Field(default_factory=list, description="Operational anomalies or validation warnings found during execution processing")
    requiresHumanReview: bool = Field(True, description="Human-in-the-loop review safeguard switch. Per guidelines, always defaults to True")