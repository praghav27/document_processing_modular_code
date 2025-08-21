import json
import re
from typing import Dict, List
from .tip_prompts import TIPPrompts
from processors.content_verbalizer import ContentVerbalizer

class TIPMetadataExtractor:
    """Extract TIP metadata (6 fields) from documents using Azure OpenAI"""
   
    def __init__(self):
        """Initialize TIP extractor with existing Azure OpenAI client"""
        self.verbalizer = ContentVerbalizer()  # Reuse existing client
        self.tip_fields = [
            'doc_id', 'project_name', 'prepared_by', 'stations_tip',
            'scope_of_work', 'qa_qc_info'
        ]
       
        print("✅ TIP Metadata Extractor initialized - reusing existing Azure OpenAI client")
        print(f"   📊 Fields: {len(self.tip_fields)} TIP metadata fields")
        print(f"   🔄 Client reuse: ✅ No duplicate initialization")
   
    async def extract_metadata(self, text_elements: List[Dict], doc_id_from_filename: str = None) -> Dict:
        """
        Extract TIP metadata (6 fields) from complete document text elements
       
        Args:
            text_elements: List of text elements from document
            doc_id_from_filename: Document ID extracted from filename (fallback)
           
        Returns:
            Dict: Extracted metadata with 6 required fields for TIP
        """
        try:
            print("🔍 Extracting TIP metadata from COMPLETE document using LLM")
           
            # Convert text elements to complete document text
            complete_document_text = self._prepare_complete_document_text(text_elements)
           
            if not complete_document_text.strip():
                print("⚠️ No text found in document, using TIP defaults")
                return self._get_tip_default_metadata(doc_id_from_filename)
           
            print(f"📊 Complete document text prepared:")
            print(f"   📄 Pages processed: {self._count_pages(text_elements)}")
            print(f"   📝 Text length: {len(complete_document_text)} characters")
            print(f"   🎯 Ready for TIP metadata extraction")
           
            # Generate metadata using Azure OpenAI
            if self.verbalizer.client:
                metadata = await self._extract_metadata_with_azure_openai(complete_document_text)
                
                # Use filename doc_id as fallback if not found in document
                if metadata.get('doc_id') == 'Not Found' and doc_id_from_filename:
                    metadata['doc_id'] = doc_id_from_filename
                    print(f"🔄 Using filename doc_id as fallback: {doc_id_from_filename}")
            else:
                print("❌ Azure OpenAI client not available")
                return self._get_tip_default_metadata(doc_id_from_filename)
           
            # Validate and clean metadata for TIP (6 fields)
            validated_metadata = self._validate_tip_metadata(metadata)
           
            print("✅ TIP metadata extraction completed from complete document")
            return validated_metadata
           
        except Exception as e:
            print(f"❌ Error extracting TIP metadata: {e}")
            return self._get_tip_default_metadata(doc_id_from_filename)
   
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
        """Extract TIP metadata using Azure OpenAI API"""
        try:
            print(f"📄 Sending {len(complete_document_text)} characters to LLM for TIP analysis")
            print("🤖 Calling LLM for TIP metadata extraction...")
           
            # Get the TIP-specific prompt
            prompt = TIPPrompts.get_tip_metadata_extraction_prompt(complete_document_text)
           
            response = await self.verbalizer.client.chat.completions.create(
                model="gpt-4o",  # Use same model as ContentVerbalizer
                messages=[
                    {"role": "system", "content": "You are an expert TIP document analyst. Extract metadata fields accurately. Return only valid JSON with the 6 required fields for TIP documents."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,  # Sufficient for TIP metadata fields including 300-word scope
                temperature=0.1  # Low temperature for consistent extraction
            )
           
            response_text = response.choices[0].message.content.strip()
            print(f"📝 LLM response: {len(response_text)} characters")
           
            # Clean and parse JSON response
            metadata = self._parse_json_response(response_text)
            print("✅ Successfully parsed TIP metadata from LLM")
            return metadata
               
        except Exception as e:
            print(f"❌ Azure OpenAI API error: {e}")
            return self._get_tip_default_metadata()
   
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
            return self._get_tip_default_metadata()
   
    def _validate_tip_metadata(self, metadata: Dict) -> Dict:
        """Validate and clean TIP metadata (6 fields)"""
        validated = {}
       
        for field in self.tip_fields:
            value = metadata.get(field, 'Not Specified')
           
            # Clean and validate the value
            if isinstance(value, str):
                value = value.strip()
                value = re.sub(r'^["\']+|["\']+$', '', value)  # Remove quotes
                if not value or value.lower() in ['none', 'null', 'undefined', '', 'n/a']:
                    value = 'Not Specified'
                elif field == 'scope_of_work' and len(value) > 1000:  # Cap scope at reasonable length
                    value = value[:1000] + '...'
                elif field != 'scope_of_work' and len(value) > 500:  # Other fields capped
                    value = value[:500] + '...'
            else:
                value = 'Not Specified'
           
            validated[field] = value
       
        return validated
   
    def _get_tip_default_metadata(self, doc_id_from_filename: str = None) -> Dict:
        """Get default TIP metadata structure (6 fields)"""
        return {
            'doc_id': doc_id_from_filename if doc_id_from_filename else 'Not Found',
            'project_name': 'Not Specified',
            'prepared_by': 'Not Specified',
            'stations_tip': 'Not Specified',
            'scope_of_work': 'Not Specified',
            'qa_qc_info': 'Not Specified'
        }
   
    def get_status_info(self) -> Dict:
        """Get status information about the TIP metadata extractor"""
        return {
            "extractor_type": "TIP",
            "fields_count": len(self.tip_fields),
            "fields": self.tip_fields,
            "client_initialized": self.verbalizer.client is not None,
            "status": "ready" if self.verbalizer.client else "client_unavailable",
            "reuses_existing_client": True
        }