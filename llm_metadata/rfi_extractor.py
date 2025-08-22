

import json
import re
from typing import Dict, List
from .prompts import DocumentMetadataPrompts
from processors.content_verbalizer import ContentVerbalizer
 
class RFIExtractor:
    """Extract RFI metadata (8 NEW fields) from documents using Azure OpenAI - No chunking for RFI"""
   
    def __init__(self):
        """Initialize RFI extractor with existing Azure OpenAI client"""
        self.verbalizer = ContentVerbalizer()  # Reuse existing client
        self.rfi_fields = [
            'project_name', 'client', 'region', 'industry', 
            'prepared_date', 'station_discipline', 'scope_of_work', 'required_activities'
        ]
       
        print("✅ RFI Extractor initialized with NEW fields - NO CHUNKING")
        print(f"   📊 Fields: {len(self.rfi_fields)} RFI metadata fields (no doc_id, using project_id)")
        print(f"   🚫 Chunking: DISABLED for RFI documents")
   
    async def extract_metadata_only(self, text_elements: List[Dict]) -> Dict:
        """
        Extract ONLY RFI metadata (9 new fields) from complete document text elements
        NO CHUNKING - Only metadata extraction for indexing
        """
        try:
            print("🔍 Extracting RFI metadata ONLY (No chunking for RFI)")
           
            # Convert text elements to complete document text
            complete_document_text = self._prepare_complete_document_text(text_elements)
           
            if not complete_document_text.strip():
                print("⚠️ No text found in document, using RFI defaults")
                return self._get_rfi_default_metadata()
           
            print(f"📊 Complete document text prepared:")
            print(f"   📄 Pages processed: {self._count_pages(text_elements)}")
            print(f"   📝 Text length: {len(complete_document_text)} characters")
            print(f"   🎯 Ready for metadata-only extraction (NO CHUNKING)")
           
            # Generate metadata using Azure OpenAI (reusing existing client)
            if self.verbalizer.client:
                metadata = await self._extract_metadata_with_azure_openai(complete_document_text)
            else:
                print("❌ Azure OpenAI client not available")
                return self._get_rfi_default_metadata()
           
            # Validate and clean metadata for RFI (9 new fields)
            validated_metadata = self._validate_rfi_metadata(metadata)
           
            print("✅ RFI metadata-only extraction completed (NO CHUNKING)")
            return validated_metadata
           
        except Exception as e:
            print(f"❌ Error extracting RFI metadata: {e}")
            return self._get_rfi_default_metadata()
   
    def _prepare_complete_document_text(self, text_elements: List[Dict]) -> str:
        """Convert text elements to complete document text"""
        complete_text = ""
       
        # Process ALL text elements from the complete document
        for element in text_elements:
            content = element.get('content', '').strip()
            role = element.get('role', 'unknown')
           
            # Add role context for better understanding
            if content:
                complete_text += f"[{role}] {content}\n\n"
       
        print(f"🔍 Processing {len(text_elements)} text elements from complete document...")
        return complete_text
   
    def _count_pages(self, text_elements: List[Dict]) -> str:
        """Count total pages in document"""
        pages = set()
        for element in text_elements:
            page_num = element.get('page_number', 1)
            pages.add(page_num)
       
        total_pages = max(pages) if pages else 1
        return f"{total_pages}/{total_pages}"
   
    async def _extract_metadata_with_azure_openai(self, complete_document_text: str) -> Dict:
        """Extract RFI metadata using Azure OpenAI API with NEW fields"""
        try:
            print(f"📄 Sending {len(complete_document_text)} characters to LLM for RFI analysis")
            print("🤖 Calling LLM for metadata-only extraction (NEW FIELDS)...")
           
            # Get the NEW RFI-specific prompt with new fields
            prompt = self._get_new_rfi_extraction_prompt(complete_document_text)
           
            response = await self.verbalizer.client.chat.completions.create(
                model="gpt-4o",  # Use same model as ContentVerbalizer
                messages=[
                    {"role": "system", "content": "You are an expert RFI analyst. Extract the 9 new metadata fields for RFI documents. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,  # Sufficient for new fields
                temperature=0.1  # Low temperature for consistent extraction
            )
           
            response_text = response.choices[0].message.content.strip()
            print(f"📝 LLM response: {len(response_text)} characters")
           
            # Clean and parse JSON response
            metadata = self._parse_json_response(response_text)
           
            print("✅ Successfully parsed NEW metadata from LLM")
            return metadata
               
        except Exception as e:
            print(f"❌ Azure OpenAI API error: {e}")
            return self._get_rfi_default_metadata()
   
    def _get_new_rfi_extraction_prompt(self, document_text: str) -> str:
        """Get the NEW RFI metadata extraction prompt for 9 fields"""
        return f"""
You are an expert RFI (Request for Information) analyzer. Extract EXACTLY 9 metadata fields from the document. Return ONLY a valid JSON object.

**DOCUMENT TEXT:**
{document_text}

**EXTRACTION REQUIREMENTS:**

1. **project_name**: Find the main project name, RFI title, or project identifier. Look for project titles, names, or main subject headings.

2. **client**: Identify the organization or client requesting the information. Look for "Client:", "Owner:", issuing organization names, or companies requesting the RFI.

3. **region**: Extract geographical location information. Look for:
   - Countries, provinces/states, cities
   - Project locations, service areas
   - Regional identifiers, geographical references

4. **industry**: Determine the industry sector this RFI relates to. Common industries include:
   - "Power & Energy", "Water & Wastewater", "Transportation", "Oil & Gas", "Mining", 
   - "Environmental", "Infrastructure", "Telecommunications", "Manufacturing", "Healthcare"

5. **prepared_date**: Extract document creation date, preparation date, or issue date. Look for "Date:", "Issued:", "Prepared:", etc. Use YYYY-MM-DD format.

6. **station_discipline**: Identify the engineering discipline or technical area. Look for:
   - "Civil", "Electrical", "Mechanical", "Structural", "Environmental", "Process", 
   - "Instrumentation", "Control Systems", "HVAC", "Piping", "Architectural"

7. **scope_of_work**: Create a SHORT summary (max 200 words) of the work scope for vector/keyword search. Include main activities, deliverables, and objectives.

8. **required_activities**: Create a SHORT summary (max 200 words) of required activities for vector/keyword search. Include tasks, responsibilities, and actions needed.

**RESPONSE FORMAT - ONLY JSON:**
{{
    "project_name": "extracted project name or 'Not Specified'",
    "client": "extracted client name or 'Not Specified'",
    "region": "extracted region/location or 'Not Specified'",
    "industry": "extracted industry sector or 'Not Specified'",
    "prepared_date": "date in YYYY-MM-DD or 'Not Specified'",
    "station_discipline": "extracted discipline or 'Not Specified'",
    "scope_of_work": "short summary of work scope or 'Not Specified'",
    "required_activities": "short summary of required activities or 'Not Specified'"
}}

**CRITICAL**: Return ONLY the JSON object. No explanation, no markdown, no extra text.
        """
   
    def _parse_json_response(self, response_text: str) -> Dict:
        """Parse JSON response from Azure OpenAI"""
        try:
            # Remove any markdown formatting if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = re.sub(r'```[^`]*```', '', response_text).strip()
           
            # Clean up any remaining formatting
            response_text = response_text.strip()
            if response_text.startswith('json'):
                response_text = response_text[4:].strip()
           
            # Parse JSON
            metadata = json.loads(response_text)
            return metadata
           
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"Raw response: {response_text[:200]}...")
            return self._get_rfi_default_metadata()
   
    def _validate_rfi_metadata(self, metadata: Dict) -> Dict:
        """Validate and clean RFI metadata (9 new fields)"""
        validated = {}
       
        for field in self.rfi_fields:
            value = metadata.get(field, 'Not Specified')
           
            # Clean and validate the value
            if isinstance(value, str):
                value = value.strip()
                value = re.sub(r'^["\']+|["\']+$', '', value)  # Remove quotes
                if not value or value.lower() in ['none', 'null', 'undefined', '', 'n/a']:
                    value = 'Not Specified'
                elif len(value) > 500:  # Limit field length
                    value = value[:500] + '...'
            else:
                value = 'Not Specified'
           
            validated[field] = value
       
        return validated
   
    def _get_rfi_default_metadata(self) -> Dict:
        """Get default RFI metadata structure (8 fields, no doc_id)"""
        return {
            'project_name': 'Not Specified',
            'client': 'Not Specified',
            'region': 'Not Specified',
            'industry': 'Not Specified',
            'prepared_date': 'Not Specified',
            'station_discipline': 'Not Specified',
            'scope_of_work': 'Not Specified',
            'required_activities': 'Not Specified'
        }
   
    def get_status_info(self) -> Dict:
        """Get status information about the RFI metadata extractor"""
        return {
            "extractor_type": "RFI_METADATA_ONLY",
            "fields_count": len(self.rfi_fields),
            "fields": self.rfi_fields,
            "chunking_enabled": False,
            "client_initialized": self.verbalizer.client is not None,
            "status": "ready" if self.verbalizer.client else "client_unavailable",
            "reuses_existing_client": True
        }