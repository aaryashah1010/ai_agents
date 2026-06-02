import io
import logging
from pypdf import PdfReader

logger = logging.getLogger("app.log")

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Accepts raw binary bytes from a Gmail attachment, reads the PDF stream,
    and extracts all text contents into a single unified string array.
    """
    try:
        # Wrap the binary bytes in an in-memory file stream
        pdf_stream = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_stream)
        
        extracted_text = []
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                extracted_text.append(page_text)
                
        full_text = "\n".join(extracted_text).strip()
        
        if not full_text:
            logger.warning("PDF parsing completed but no text strings could be extracted.")
            return ""
            
        logger.info(f"Successfully extracted {len(full_text)} characters from email PDF attachment.")
        return full_text
        
    except Exception as pdf_err:
        logger.error(f"Failed to parse PDF binary attachment stream: {str(pdf_err)}")
        return ""