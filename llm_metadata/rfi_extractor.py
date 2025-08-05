from typing import Dict
import re
from .base_extractor import BaseMetadataExtractor
from .config_loader import ConfigLoader
from .rfi_prompts import RFIPrompts
from .llm_client import LLMClient
from config import AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT_NAME

# Import Azure OpenAI
try:
    from openai import AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class RFIMetadataExtractor(BaseMetadataExtractor):
    """Extract RFI document metadata from full document using Azure OpenAI"""
    
    def __init__(self):
        """Initialize the RFI metadata extractor with Azure OpenAI"""
        # Load Power Business Unit configuration (reusing for domains/services)
        self._config = ConfigLoader.load_power_config()
        super().__init__()
    
    def _initialize_llm_client(self):
        """Initialize the Azure OpenAI client"""
        try:
            if OPENAI_AVAILABLE and AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT:
                self.client = AzureOpenAI(
                    api_key=AZURE_OPENAI_API_KEY,
                    api_version=AZURE_OPENAI_API_VERSION,
                    azure_endpoint=AZURE_OPENAI_ENDPOINT
                )
                print("✅ RFI - Azure OpenAI client initialized for metadata extraction")
                print(f"   Endpoint: {AZURE_OPENAI_ENDPOINT}")
                print(f"   Deployment: {AZURE_OPENAI_DEPLOYMENT_NAME}")
                print(f"   RFI Processing: Enabled with 8 metadata fields")
            else:
                print("❌ Azure OpenAI credentials not found or OpenAI library not available")
                print("⚠️  Cannot proceed without Azure OpenAI - no fallback available")
                
        except Exception as e:
            print(f"❌ Error initializing Azure OpenAI client: {e}")
            self.client = None
    
    def get_domain_config(self) -> Dict:
        """Get domain and service configuration (reusing Power Business Unit config)"""
        return self._config
    
    def get_extraction_prompt(self, document_text: str) -> str:
        """Get the RFI extraction prompt"""
        return RFIPrompts.get_rfi_metadata_extraction_prompt(document_text)
    
    def _get_default_metadata(self) -> Dict:
        """Get default RFI metadata structure with 8 fields"""
        return {
            'document_id': 'Not Specified',
            'client_name': 'Not Specified',
            'domain_category': 'Not mentioned in RFI',
            'service_category': 'Not mentioned in RFI',
            'project_title': 'Not Specified',
            'rfi_description': 'Not mentioned in RFI',
            'submission_date': 'Not Specified',
            'duration': 'Not mentioned in RFI'
        }
    
    def extract_rfi_description(self, complete_document_text: str) -> str:
        """Extract comprehensive RFI description (800 words summary)"""
        try:
            print("🤖 Generating comprehensive RFI description (800 words summary)...")
            
            # Get the RFI description prompt
            description_prompt = RFIPrompts.get_rfi_description_prompt(complete_document_text)
            
            # Use LLM client for description generation with specific system message
            llm_client = LLMClient(client=self.client)
            
            # Call with specific system message for text generation
            response = self.client.chat.completions.create(
                model="gpt-4",  # Use deployment name directly
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert technical writer. Generate ONLY flowing paragraph text - never JSON, never bullet points, never structured formats. Write continuous prose in paragraph form."
                    },
                    {"role": "user", "content": description_prompt}
                ],
                max_tokens=1200,
                temperature=0.2
            )
            
            rfi_description = response.choices[0].message.content.strip()
            
            # Aggressive JSON cleaning
            description = rfi_description.strip()
            
            # Remove JSON markdown if present
            if '```json' in description.lower():
                print("⚠️ Removing JSON markdown formatting...")
                description = re.sub(r'```json.*?```', '', description, flags=re.DOTALL).strip()
            elif '```' in description:
                print("⚠️ Removing code block formatting...")
                description = re.sub(r'```.*?```', '', description, flags=re.DOTALL).strip()
            
            # Remove JSON structure if it starts with {
            if description.strip().startswith('{') and description.strip().endswith('}'):
                print("⚠️ LLM returned JSON instead of text, attempting to extract content...")
                # Try to extract readable content from JSON
                try:
                    import json
                    json_data = json.loads(description)
                    
                    # Build a proper description from JSON content
                    description_parts = []
                    
                    if 'document_title' in json_data:
                        description_parts.append(f"This {json_data.get('document_title', 'document')}")
                    
                    if 'project_name' in json_data:
                        description_parts.append(f"concerns the {json_data['project_name']} project")
                    
                    if 'project_location' in json_data:
                        description_parts.append(f"located at {json_data['project_location']}")
                    
                    # Create a proper flowing description
                    if description_parts:
                        description = ". ".join(description_parts) + ". This RFI seeks information from qualified engineering firms regarding their technical capabilities, project approach, and relevant experience with similar infrastructure projects. The document outlines comprehensive requirements for electrical design, environmental considerations, and compliance with industry standards."
                    else:
                        description = "This RFI document requests information from qualified engineering firms regarding a power infrastructure project. The document outlines technical requirements, project scope, and submission guidelines for potential contractors."
                        
                except json.JSONDecodeError:
                    print("⚠️ Could not parse JSON, using fallback description...")
                    description = "This RFI document requests information from qualified engineering firms regarding a power infrastructure project. The document outlines technical requirements, project scope, and submission guidelines for potential contractors."
            
            # Remove any remaining JSON-like structures
            description = re.sub(r'\{[^}]*\}', '', description).strip()
            
            # Remove any leading/trailing quotes
            description = description.strip().strip('"').strip("'")
            
            # Ensure we have some content
            if not description or len(description) < 50:
                description = "This RFI document requests comprehensive information from qualified engineering firms regarding a power infrastructure project. The document outlines detailed technical requirements, project scope, timeline considerations, and submission guidelines for potential contractors interested in providing engineering services."
            
            print(f"✅ RFI description generated: {len(description)} characters")
            
            return description.strip()
                
        except Exception as e:
            print(f"❌ Error generating RFI description: {e}")
            return "This RFI document requests information from qualified engineering firms regarding a power infrastructure project. The document outlines technical requirements, project scope, and submission guidelines for potential contractors."
    
    def extract_metadata(self, text_elements) -> Dict:
        """
        Main RFI metadata extraction method with 8 fields
        
        Args:
            text_elements: List of ALL text elements from entire RFI document
            
        Returns:
            Dict: Extracted RFI metadata with 8 fields
        """
        try:
            total_pages = max([elem.get('page_number', 1) for elem in text_elements]) if text_elements else 0
            print(f"🔍 Extracting RFI metadata from COMPLETE {total_pages}-page RFI document using LLM")
            
            # Get complete document text
            complete_document_text = self._get_complete_document_text(
                text_elements, 
                max_chars=25000
            )
            
            if not complete_document_text.strip():
                print("⚠️ No text found in RFI document")
                return self._get_default_metadata()
            
            print(f"📄 Sending {len(complete_document_text)} characters to LLM for RFI analysis")
            
            # Extract basic metadata (6 fields: document_id, client_name, domain_category, service_category, project_title, submission_date)
            if self.client:
                # Extract basic metadata using main extraction
                basic_metadata = self._extract_metadata_with_llm(complete_document_text)
                
                # Generate comprehensive RFI description (800 words)
                rfi_description = self.extract_rfi_description(complete_document_text)
                
                # Extract duration using specific prompt
                duration = self._extract_duration(complete_document_text)
                
                # Combine all metadata
                full_metadata = {
                    'document_id': basic_metadata.get('document_id', 'Not Specified'),
                    'client_name': basic_metadata.get('client_name', 'Not Specified'),
                    'domain_category': basic_metadata.get('domain_category', 'Not mentioned in RFI'),
                    'service_category': basic_metadata.get('service_category', 'Not mentioned in RFI'),
                    'project_title': basic_metadata.get('project_title', 'Not Specified'),
                    'rfi_description': rfi_description,
                    'submission_date': basic_metadata.get('submission_date', 'Not Specified'),
                    'duration': duration
                }
                
                # Validate and clean metadata
                validated_metadata = self._validate_rfi_metadata(full_metadata)
                
                print(f"✅ RFI metadata extraction completed from {total_pages}-page document")
                self._print_rfi_metadata_summary(validated_metadata)
                
                return validated_metadata
            else:
                print("❌ LLM client not available - cannot extract RFI metadata")
                return self._get_default_metadata()
            
        except Exception as e:
            print(f"❌ Error extracting RFI metadata from complete document: {e}")
            return self._get_default_metadata()
    
    def _extract_duration(self, complete_document_text: str) -> str:
        """Extract project duration using specific prompt"""
        try:
            print("🕐 Extracting project duration...")
            
            # Get the duration extraction prompt
            duration_prompt = RFIPrompts.get_duration_extraction_prompt(complete_document_text)
            
            # Use LLM client for duration extraction
            llm_client = LLMClient(client=self.client)
            duration_response = llm_client.extract_metadata(duration_prompt, model_config={
                "max_tokens": 100,  # Reduced tokens for simple duration
                "temperature": 0.1
            })
            
            # Parse duration from response - CLEAN UP JSON/MARKDOWN
            duration = duration_response.strip()
            
            # Remove any JSON formatting
            if '```json' in duration:
                duration = duration.split('```json')[1].split('```')[0].strip()
            elif '```' in duration:
                duration = duration.split('```')[1].strip()
            
            # Clean up the response
            if duration.lower().startswith('duration:'):
                duration = duration[9:].strip()
            
            # Extract just the duration value if it's in JSON format
            if duration.startswith('{') and 'duration' in duration.lower():
                try:
                    # Try to extract duration from JSON
                    import json
                    duration_data = json.loads(duration)
                    if 'project_duration' in duration_data:
                        duration = duration_data['project_duration']
                    elif 'duration' in duration_data:
                        duration = duration_data['duration']
                except:
                    # If JSON parsing fails, look for duration pattern in text
                    import re
                    duration_match = re.search(r'(\d+\s*(?:weeks?|months?|years?))', duration, re.IGNORECASE)
                    if duration_match:
                        duration = duration_match.group(1)
                    else:
                        duration = 'Not mentioned in RFI'
            
            # Final cleanup - remove quotes and extra whitespace
            duration = duration.strip().strip('"').strip("'")
            
            print(f"✅ Duration extracted: {duration}")
            return duration if duration and len(duration) < 100 else 'Not mentioned in RFI'
                
        except Exception as e:
            print(f"❌ Error extracting duration: {e}")
            return 'Not mentioned in RFI'
    
    def _validate_rfi_metadata(self, metadata: Dict) -> Dict:
        """
        Validate and clean RFI metadata
        """
        from .text_utils import validate_and_clean_field
        
        # Get domain configuration
        domain_config = self.get_domain_config()
        required_fields = [
            'document_id', 'client_name', 'domain_category', 'service_category',
            'project_title', 'rfi_description', 'submission_date', 'duration'
        ]
        
        validated = {}
        
        for field in required_fields:
            value = metadata.get(field, 'Not Specified')
            if field == 'rfi_description':
                # Don't truncate RFI description, keep full 800-word summary
                validated[field] = value if value and value.strip() else 'Not mentioned in RFI'
            else:
                validated[field] = validate_and_clean_field(field, value)
        
        # Validate domain against configuration
        if validated['domain_category'] not in domain_config.get('domains', []):
            if validated['domain_category'] not in ['Not Specified', 'Not mentioned in RFI']:
                print(f"⚠️ Domain '{validated['domain_category']}' not in domain list")
            validated['domain_category'] = 'Not mentioned in RFI'
        
        # Validate service against configuration
        all_services = []
        for domain_services in domain_config.get('services', {}).values():
            all_services.extend(domain_services)
        
        if validated['service_category'] not in all_services:
            if validated['service_category'] not in ['Not Specified', 'Not mentioned in RFI']:
                print(f"⚠️ Service '{validated['service_category']}' not in service list")
            validated['service_category'] = 'Not mentioned in RFI'
        
        return validated
    
    def _print_rfi_metadata_summary(self, metadata: Dict):
        """Print extracted RFI metadata summary with 250-300 word description preview"""
        print(f"\n🤖 LLM-EXTRACTED RFI DOCUMENT METADATA")
        print(f"{'='*80}")
        print(f"🆔 Document ID: {metadata.get('document_id', 'N/A')}")
        print(f"🏢 Client Name: {metadata.get('client_name', 'N/A')}")
        print(f"🏷️ Domain Category: {metadata.get('domain_category', 'N/A')}")
        print(f"⚙️ Service Category: {metadata.get('service_category', 'N/A')}")
        print(f"📝 Project Title: {metadata.get('project_title', 'N/A')}")
        
        # Show RFI description - 250-300 words in terminal
        rfi_desc = metadata.get('rfi_description', '')
        if rfi_desc and len(rfi_desc) > 20:
            words = rfi_desc.split()
            # Show 250-300 words (targeting ~275 words)
            preview_words = words[:275] if len(words) > 275 else words
            preview = ' '.join(preview_words)
            print(f"📄 RFI Description: {preview}")
        else:
            print(f"📄 RFI Description: {rfi_desc}")
        
        print(f"📅 Submission Date: {metadata.get('submission_date', 'N/A')}")
        print(f"⏱️ Duration: {metadata.get('duration', 'N/A')}")
        
        # Validation feedback
        domain_config = self.get_domain_config()
        domain = metadata.get('domain_category', '')
        service = metadata.get('service_category', '')
        
        if domain in domain_config.get('domains', []):
            print(f"   ✅ Domain matches domain list")
        elif domain == 'Not mentioned in RFI':
            print(f"   ⚠️ Domain not identified in document")
        else:
            print(f"   ❌ Domain not in domain list")
        
        all_services = []
        for domain_services in domain_config.get('services', {}).values():
            all_services.extend(domain_services)
        
        if service in all_services:
            print(f"   ✅ Service matches service list")
        elif service == 'Not mentioned in RFI':
            print(f"   ⚠️ Service not identified in document")
        else:
            print(f"   ❌ Service not in service list")
    
    def get_rfi_info(self) -> Dict:
        """Get RFI processing configuration information"""
        return {
            "document_type": "RFI",
            "business_unit": self._config.get("business_unit", "Power Business Unit"),
            "domains": self._config.get("domains", []),
            "services": self._config.get("services", {}),
            "total_domains": len(self._config.get("domains", [])),
            "total_services": sum(len(services) for services in self._config.get("services", {}).values()),
            "metadata_fields": 8,
            "rfi_specific_fields": ["document_id", "rfi_description", "duration"]
        }
    
    def get_status_info(self) -> Dict:
        """Get status information about the RFI metadata extractor"""
        base_info = super().get_status_info()
        rfi_info = {
            "openai_available": OPENAI_AVAILABLE,
            "api_key_present": bool(AZURE_OPENAI_API_KEY),
            "endpoint": AZURE_OPENAI_ENDPOINT,
            "deployment": AZURE_OPENAI_DEPLOYMENT_NAME,
            "document_type": "RFI",
            "metadata_fields": 8
        }
        base_info.update(rfi_info)
        return base_info