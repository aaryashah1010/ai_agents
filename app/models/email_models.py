from pydantic import BaseModel, Field
from typing import List, Optional


class EmailInput(BaseModel):
    id: Optional[int] = None  
    fromEmail: str
    fromName: str
    subject: str
    body: str
    attachmentNames: List[str]


class EmailClassificationOutput(BaseModel):
    id: int
    category: str
    confidence: int
    suggestedERPAction: str
    summary: str = Field(description="A strictly 1-sentence executive summary of the email text.")
    requiresHumanReview: bool   