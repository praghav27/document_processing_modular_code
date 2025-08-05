from abc import ABC, abstractmethod
from typing import Dict, List
import json
import re

class BaseMetadataExtractor(ABC):
    """Abstract base class for document metadata extraction using LLM"""
    
    def __init__(self):
        """Initialize the base metadata extractor"""
        self.client = None
        self._initialize_llm_client()
    
    @abstractmethod
    def _initialize_llm_client(self):
        """Initialize the LLM client - implemented by subclasses"""
        pass
    
    @abstractmethod
    def get_domain_config(self) -> Dict:
        """Get domain and service configuration - implemented by subclasses"""
        pass
    
    @abstractmethod
    def get_extraction_prompt(self, document_text: str) -> str:
        """Get the extraction prompt - implemented by subclasses"""
        pass
    
    @abstractmethod
    def _get_default_metadata(self) -> Dict:
        """Get default metadata structure - implemented by subclasses"""
        pass
    
    def extract_metadata(self, text_elements: List[Dict]) -> Dict:
        """
        Main metadata extraction method - common workflow for all extractors
        
        Args:
            text_elements: List of ALL text elements from entire document
            
        Returns:
            Dict: Extracted metadata
        """
        try:
            total_pages = max([elem.get('page_number', 1) for elem in text_elements]) if text_elements else 0
            print(f"🔍 Extracting metadata from COMPLETE {total_pages}-page document using LLM")
            
            # Get complete document text without any filtering
            complete_document_text = self._get_complete_document_text(
                text_elements, 
                max_chars=25000
            )
            
            if not complete_document_text.strip():
                print("⚠️ No text found in document")
                return self._get_default_metadata()
            
            print(f"📄 Sending {len(complete_document_text)} characters to LLM for analysis")
            
            # Use LLM for metadata extraction
            if self.client:
                metadata = self._extract_metadata_with_llm(complete_document_text)
                
                # Validate and clean metadata
                validated_metadata = self._validate_metadata(metadata)
                
                print(f"✅ Metadata extraction completed from {total_pages}-page document")
                self._print_metadata_summary(validated_metadata)
                
                return validated_metadata
            else:
                print("❌ LLM client not available - cannot extract metadata")
                return self._get_default_metadata()
            
        except Exception as e:
            print(f"❌ Error extracting metadata from complete document: {e}")
            return self._get_default_metadata()
    
    def _get_complete_document_text(self, text_elements: List[Dict], max_chars: int = 25000) -> str:
        """
        Processes all pages from document extraction
        
        Args:
            text_elements: List of ALL text elements from entire document
            max_chars: Maximum characters to capture more content
            
        Returns:
            str: Complete document text for comprehensive metadata extraction
        """
        print(f"🔍 Processing {len(text_elements)} text elements from complete document...")
        
        # Group all content by page for systematic processing
        pages_content = {}
        
        for element in text_elements:
            content = element.get('content', '').strip()
            role = element.get('role', 'unknown')
            page_number = element.get('page_number', 1)
            
            if not content:
                continue
                
            if page_number not in pages_content:
                pages_content[page_number] = []
                
            pages_content[page_number].append({
                'content': content,
                'role': role,
                'page': page_number
            })
        
        # Build complete document text systematically
        complete_text = ""
        total_pages = len(pages_content) if pages_content else 0
        
        # Add document header with processing info
        complete_text += f"=== COMPLETE DOCUMENT FOR METADATA EXTRACTION ===\n"
        complete_text += f"Document pages: {total_pages} (Document Intelligence Standard Tier)\n"
        complete_text += f"Text elements: {len(text_elements)}\n"
        complete_text += f"Processing: ALL content without filtering\n\n"
        
        # Process ALL pages systematically
        pages_processed = 0
        for page_num in sorted(pages_content.keys()):
            page_elements = pages_content[page_num]
            
            # Add clear page separation
            page_content = f"\n{'='*50} PAGE {page_num} {'='*50}\n"
            
            # Add all content from this page without filtering
            for element in page_elements:
                element_text = f"[{element['role']}] {element['content']}\n\n"
                
                # Check if we're approaching character limit
                if len(complete_text + page_content + element_text) > max_chars:
                    # For early pages (1-15), try to include more content
                    if page_num <= 15:
                        remaining_chars = max_chars - len(complete_text + page_content)
                        if remaining_chars > 200:  # Minimum meaningful content size
                            truncated_content = element['content'][:remaining_chars-100]
                            page_content += f"[{element['role']}] {truncated_content}... [TRUNCATED]\n\n"
                            complete_text += page_content
                            complete_text += f"\n[DOCUMENT TRUNCATED AT PAGE {page_num} DUE TO CHARACTER LIMIT]\n"
                            pages_processed = page_num
                            break
                    else:
                        # For later pages, stop processing
                        complete_text += f"\n[PROCESSING STOPPED AT PAGE {page_num} - CHARACTER LIMIT REACHED]\n"
                        pages_processed = page_num - 1
                        break
                else:
                    page_content += element_text
            
            # If we hit the limit, break out of page loop
            if len(complete_text + page_content) > max_chars:
                break
                
            complete_text += page_content
            pages_processed = page_num
        
        # Add processing summary
        final_length = len(complete_text)
        complete_text += f"\n{'='*50} PROCESSING SUMMARY {'='*50}\n"
        complete_text += f"Pages included: {pages_processed}/{total_pages}\n"
        complete_text += f"Text length: {final_length}/{max_chars} characters\n"
        complete_text += f"Coverage: {(pages_processed/total_pages)*100:.1f}% of document\n"
        
        print(f"📊 Complete document text prepared:")
        print(f"   📄 Pages processed: {pages_processed}/{total_pages}")
        print(f"   📝 Text length: {final_length} characters") 
        print(f"   🎯 Ready for comprehensive metadata extraction")
        
        return complete_text
    
    def _extract_metadata_with_llm(self, complete_document_text: str) -> Dict:
        """Extract metadata using LLM - uses the llm_client"""
        from .llm_client import LLMClient
        
        try:
            print("🤖 Calling LLM for comprehensive metadata extraction...")
            
            # Get the extraction prompt
            prompt = self.get_extraction_prompt(complete_document_text)
            
            # Use LLM client for extraction
            llm_client = LLMClient(client=self.client)
            response_text = llm_client.extract_metadata(prompt)
            
            print(f"📝 LLM response: {len(response_text)} characters")
            
            # Parse the JSON response
            metadata = llm_client.parse_json_response(response_text)
            print("✅ Successfully parsed metadata from LLM")
            return metadata
                
        except Exception as e:
            print(f"❌ LLM API error: {e}")
            print("❌ No fallback available - returning defaults")
            return self._get_default_metadata()
    
    def _validate_metadata(self, metadata: Dict) -> Dict:
        """
        Validate and clean metadata - common validation logic
        Subclasses can override for specific validation rules
        """
        from .text_utils import validate_and_clean_field, validate_against_domain_list
        
        # Get domain configuration
        domain_config = self.get_domain_config()
        required_fields = [
            'project_title', 'client_name', 'vendor_name', 
            'submission_date', 'domain_category', 'service_category',
            'revenue_range', 'region', 'project_value',
            'compliance_standard', 'equipments_used'
        ]
        
        validated = {}
        
        for field in required_fields:
            value = metadata.get(field, 'Not Specified')
            validated[field] = validate_and_clean_field(field, value)
        
        # Validate domain against configuration
        if validated['domain_category'] not in domain_config.get('domains', []):
            if validated['domain_category'] not in ['Not Specified', 'Not mentioned in RFP']:
                print(f"⚠️ Domain '{validated['domain_category']}' not in domain list")
            validated['domain_category'] = 'Not mentioned in RFP'
        
        # Validate service against configuration
        all_services = []
        for domain_services in domain_config.get('services', {}).values():
            all_services.extend(domain_services)
        
        if validated['service_category'] not in all_services:
            if validated['service_category'] not in ['Not Specified', 'Not mentioned in RFP']:
                print(f"⚠️ Service '{validated['service_category']}' not in service list")
            validated['service_category'] = 'Not mentioned in RFP'
        
        # Set default vendor if not found
        if validated['vendor_name'] == 'Not Specified':
            validated['vendor_name'] = 'tetratech'
        
        return validated
    
    def _print_metadata_summary(self, metadata: Dict):
        """Print extracted metadata summary"""
        print(f"\n🤖 LLM-EXTRACTED DOCUMENT METADATA")
        print(f"{'='*80}")
        print(f"📝 Project Title: {metadata.get('project_title', 'N/A')}")
        print(f"🏢 Client Name: {metadata.get('client_name', 'N/A')}")
        print(f"🏭 Vendor Name: {metadata.get('vendor_name', 'N/A')}")
        print(f"📅 Submission Date: {metadata.get('submission_date', 'N/A')}")
        print(f"🏷️ Domain Category: {metadata.get('domain_category', 'N/A')}")
        print(f"⚙️ Service Category: {metadata.get('service_category', 'N/A')}")
        print(f"💰 Revenue Range: {metadata.get('revenue_range', 'N/A')}")
        print(f"🌍 Region: {metadata.get('region', 'N/A')}")
        print(f"💵 Project Value: {metadata.get('project_value', 'N/A')}")
        print(f"📜 Compliance Standard: {metadata.get('compliance_standard', 'N/A')}")
        print(f"🔧 Equipments Used: {metadata.get('equipments_used', 'N/A')}")
        
        # Validation feedback
        domain_config = self.get_domain_config()
        domain = metadata.get('domain_category', '')
        service = metadata.get('service_category', '')
        
        if domain in domain_config.get('domains', []):
            print(f"   ✅ Domain matches domain list")
        elif domain == 'Not mentioned in RFP':
            print(f"   ⚠️ Domain not identified in document")
        else:
            print(f"   ❌ Domain not in domain list")
        
        all_services = []
        for domain_services in domain_config.get('services', {}).values():
            all_services.extend(domain_services)
        
        if service in all_services:
            print(f"   ✅ Service matches service list")
        elif service == 'Not mentioned in RFP':
            print(f"   ⚠️ Service not identified in document")
        else:
            print(f"   ❌ Service not in service list")
    
    def get_status_info(self) -> Dict:
        """Get status information about the metadata extractor"""
        domain_config = self.get_domain_config()
        return {
            "client_initialized": self.client is not None,
            "status": "ready" if self.client else "not_available",
            "domains_configured": len(domain_config.get('domains', [])),
            "services_configured": sum(len(services) for services in domain_config.get('services', {}).values()),
            "total_fields": 11,
            "fallback_available": False
        }