import os
import requests
import logging
from app.models.document_models import DocumentExtractionOutput
from app.agents.document_agent import extract_document_data
from logging.handlers import RotatingFileHandler

if not os.path.exists("logs"):
    os.makedirs("logs")

# Configure a clean separate logger interface for Agent 2
doc_logger = logging.getLogger("document_agent_logger")
if not doc_logger.handlers:
    file_handler = RotatingFileHandler(
        "logs/document_processing.log", 
        maxBytes=5 * 1024 * 1024, 
        backupCount=3,
        encoding="utf-8"
    )
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(formatter)
    doc_logger.addHandler(file_handler)
    doc_logger.setLevel(logging.WARNING)

def process_and_stage_document(raw_text_content: str) -> dict:
    """
    Independent wrapper service that orchestrates raw document text extraction,
    runs semantic model auditing, and manages local staging repository updates.
    """
    doc_logger.info("Initializing Agent 2 Document Extraction Sequence.")
    
    if not raw_text_content.strip():
        doc_logger.warning("Empty text payload passed to document parser.")
        return {"status": "error", "message": "Input document text content cannot be blank."}
        
    try:
        # Execute extraction agent workflow
        extracted_payload: DocumentExtractionOutput = extract_document_data(raw_text_content)
        
        doc_logger.info(
            f"Successfully executed Agent 2 extraction. Type: {extracted_payload.documentType} | "
            f"Confidence: {extracted_payload.confidence}%"
        )
        
        return {
            "status": "success",
            "data": extracted_payload.dict()
        }
        
    except Exception as service_err:
        doc_logger.error(f"Critical execution error in Document Extraction Service: {str(service_err)}")
        return {
            "status": "error",
            "message": f"Document execution subsystem error: {str(service_err)}"
        }