from typing import Dict, Any
from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions
from fastapi import HTTPException
from config.settings import settings
from .storage_service import upload_to_gcs
import json

async def extract_text_from_pdf(file_content: bytes, deal_id: str) -> Dict[str, Any]:
    """
    Extract text from PDF using Document AI synchronous processing with imageless mode
    Fast: completes in 10-30 seconds for 16-30 page documents
    """
    try:
        # Upload to GCS (for reference/backup)
        gcs_path = f"deals/{deal_id}/pitch_deck.pdf"
        gcs_uri = upload_to_gcs(file_content, gcs_path)
        
        print(f"Starting Document AI processing for deal {deal_id} (imageless mode)...")
        
        # Initialize Document AI client
        opts = ClientOptions(
            api_endpoint=f"{settings.DOCUMENT_AI_LOCATION}-documentai.googleapis.com"
        )
        client = documentai.DocumentProcessorServiceClient(client_options=opts)
        
        # Configure the process request
        processor_name = f"projects/{settings.GCP_PROJECT_ID}/locations/{settings.DOCUMENT_AI_LOCATION}/processors/{settings.DOCUMENT_AI_PROCESSOR_ID}"
        
        # Create raw document
        raw_document = documentai.RawDocument(
            content=file_content,
            mime_type="application/pdf"
        )
        
        # Create request with imageless_mode enabled
        request = documentai.ProcessRequest(
            name=processor_name,
            raw_document=raw_document,
            skip_human_review=True,
            imageless_mode=True,  # ✅ Enables support for up to 30 pages
        )
        
        print(f"Sending synchronous request to Document AI with imageless_mode=True...")
        
        # Process document synchronously (returns in 10-30 seconds)
        result = client.process_document(request=request)
        document = result.document
        
        print(f"Document AI processing completed! Pages: {len(document.pages)}")
        
        # Extract text and structure
        extracted_data = {
            "text": document.text,
            "pages": len(document.pages),
            "entities": []
        }
        
        # Extract entities if available
        for entity in document.entities:
            extracted_data["entities"].append({
                "type": entity.type_,
                "mention_text": entity.mention_text,
                "confidence": entity.confidence
            })
        
        print(f"Extracted {len(extracted_data['entities'])} entities")
        
        return extracted_data
    
    except Exception as e:
        error_msg = str(e)
        print(f"Error in Document AI extraction: {error_msg}")
        
        # Check if it's a page limit error
        if "PAGE_LIMIT_EXCEEDED" in error_msg or "pages exceed the limit" in error_msg.lower():
            raise HTTPException(
                status_code=400, 
                detail="Document exceeds 30-page limit for fast processing. Please use a smaller document or contact support for batch processing."
            )
        
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {error_msg}")

async def extract_metadata_from_text(text: str) -> Dict[str, Any]:
    """Extract company name, founders, and sector from text using Gemini"""
    from google import genai
    from config.settings import settings
    
    try:
        # Use the same client as gemini_service
        client = genai.Client(
            vertexai=True,
            project=settings.GCP_PROJECT_ID,
            location=settings.GCP_LOCATION
        )
        
        prompt = f"""
        Extract the following information from this pitch deck text:
        1. Company name
        2. List of founder names
        3. Primary sector/industry
        
        Text:
        {text[:10000]}
        
        Return ONLY a JSON object with this structure:
        {{
            "company_name": "extracted name",
            "founder_names": ["founder1", "founder2"],
            "sector": "primary sector"
        }}
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        response_text = response.text.strip()
        
        if response_text.startswith("```json"):
            response_text = response_text[7:-3]
        elif response_text.startswith("```"):
            response_text = response_text[3:-3]
        
        metadata = json.loads(response_text)
        return metadata
    
    except Exception as e:
        print(f"Error extracting metadata: {str(e)}")
        return {
            "company_name": "Unknown",
            "founder_names": [],
            "sector": "Unknown"
        }
