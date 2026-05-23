from fastapi import APIRouter

from app.models.email_models import (
    EmailInput,
    EmailClassificationOutput,
)

from app.agents.email_agent import classify_email

router = APIRouter()


@router.post(
    "/classify-email",
    response_model=EmailClassificationOutput,
)

def classify(email: EmailInput):
    return classify_email(email)