from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class VoiceInputPayload(BaseModel):
    transcript: str = Field(
        ..., 
        description="The raw text transcription decoded from the user's verbal instruction."
    )


class VoiceItemRow(BaseModel):
    itemName: str = Field(..., description="The name or description of the product or asset.")
    quantity: Optional[float] = Field(None, gt=0, description="The numeric quantity requested.")
    unit: Optional[str] = Field(None, description="The packaging unit like Box, Pcs, Kg, Liters.")
    rate: Optional[float] = Field(None, description="The stated unit price or total item cost.")
        
    @field_validator('unit')
    @classmethod
    def standardize_units(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        mapping = {
            "pcs": "Pcs", "pieces": "Pcs", "piece": "Pcs",
            "box": "Box", "boxes": "Box",
            "kg": "Kg", "kilograms": "Kg",
            "units": "Unit", "unit": "Unit"
        }
        return mapping.get(v.lower(), v)

class DiscountDetail(BaseModel):
    type: Optional[str] = Field(None, description="The type of deduction, e.g., Percentage or Flat.")
    value: Optional[float] = Field(None, description="The numeric value of the applied discount.")


class VoiceActionOutput(BaseModel):
    intent: str = Field(..., description="The mapped core intention matching your supported action list.")
    confidence: int = Field(..., description="Model certainty metric score ranking from 0 to 100.")
    partyType: Optional[str] = Field(None, description="Classification of the external entity: Customer, Vendor, or null.")
    customerName: Optional[str] = Field(None, description="The identified name of the customer party, or null.")
    vendorName: Optional[str] = Field(None, description="The identified name of the vendor party, or null.")
    contactInfo: Optional[str] = Field(None, description="Extracted phone number, email address, or contact details.")
    
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