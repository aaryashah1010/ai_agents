from pydantic import BaseModel, Field
from typing import List, Optional

class VoiceInputPayload(BaseModel):
    """
    Validates incoming voice transcriptions sent from the frontend dashboard.
    """
    transcript: str = Field(
        ..., 
        description="The raw text transcription decoded from the user's verbal instruction."
    )


class VoiceItemRow(BaseModel):
    """
    Represents an item row extracted dynamically from conversational speech.
    """
    itemName: str = Field(..., description="The name or description of the product or asset.")
    quantity: float = Field(..., description="The numeric quantity requested.")
    unit: Optional[str] = Field(None, description="The packaging unit like Box, Pcs, Kg, Liters.")

class DiscountDetail(BaseModel):
    """
    Captures financial deductions explicitly mentioned in the voice stream.
    """
    type: Optional[str] = Field(None, description="The type of deduction, e.g., Percentage or Flat.")
    value: Optional[float] = Field(None, description="The numeric value of the applied discount.")


class VoiceActionOutput(BaseModel):
    """
    The rigid target schema structure that Gemini must fill out deterministically.
    """
    intent: str = Field(..., description="The mapped core intention matching your supported action list.")
    confidence: int = Field(..., description="Model certainty metric score ranking from 0 to 100.")
    partyType: Optional[str] = Field(None, description="Classification of the external entity: Customer, Vendor, or null.")
    customerName: Optional[str] = Field(None, description="The identified name of the customer party, or null.")
    vendorName: Optional[str] = Field(None, description="The identified name of the vendor party, or null.")
    
    # Nested item matrix list row structure
    items: List[VoiceItemRow] = Field(default_factory=list, description="A structured list array of extracted item line profiles.")
    
    discount: Optional[DiscountDetail] = Field(None, description="Extracted pricing reduction breakdowns.")
    deliveryDateText: Optional[str] = Field(None, description="Preserved literal text representation of relative time metrics.")
    paymentTerms: Optional[str] = Field(None, description="Literal payment instructions or null.")
    suggestedERPAction: str = Field(..., description="The UI navigation routing command string recommended for the ERP form.")
    
    # Quality Assurance, Exception handling and Human-In-the-Loop properties
    missingFields: List[str] = Field(default_factory=list, description="Lists mandatory transaction parameters missing from user speech.")
    warnings: List[str] = Field(default_factory=list, description="Captures semantic discrepancies or analytical observations.")
    confirmationRequired: bool = Field(True, description="Safety flag to hold transaction execution until manual approval takes place.")