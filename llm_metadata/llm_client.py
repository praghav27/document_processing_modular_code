import json
import re
from typing import Dict, Optional
from config import AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT_NAME

# Import Azure OpenAI
try:
    from openai import AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class LLMClient:
    """Abstract LLM client for metadata extraction"""
    
    def __init__(self, provider="azure_openai", client=None, **config):
        """
        Initialize LLM client
        
        Args:
            provider: LLM provider type
            client: Pre-initialized client (for backwards compatibility)
            **config: Additional configuration
        """
        self.provider = provider
        self.client = client
        self.config = config
        
        if not self.client:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client based on provider"""
        if self.provider == "azure_openai":
            self._initialize_azure_openai()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def _initialize_azure_openai(self):
        """Initialize Azure OpenAI client"""
        try:
            if OPENAI_AVAILABLE and AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT:
                self.client = AzureOpenAI(
                    api_key=AZURE_OPENAI_API_KEY,
                    api_version=AZURE_OPENAI_API_VERSION,
                    azure_endpoint=AZURE_OPENAI_ENDPOINT
                )
                print("✅ Azure OpenAI client initialized for metadata extraction")
                print(f"   Endpoint: {AZURE_OPENAI_ENDPOINT}")
                print(f"   Deployment: {AZURE_OPENAI_DEPLOYMENT_NAME}")
            else:
                print("❌ Azure OpenAI credentials not found or OpenAI library not available")
                print("⚠️  Cannot proceed without Azure OpenAI - no fallback available")
                
        except Exception as e:
            print(f"❌ Error initializing Azure OpenAI client: {e}")
            self.client = None
    
    def extract_metadata(self, prompt: str, model_config: Optional[Dict] = None) -> str:
        """
        Extract metadata using LLM
        
        Args:
            prompt: Extraction prompt
            model_config: Optional model configuration
            
        Returns:
            str: Raw LLM response
        """
        if not self.client:
            raise Exception("LLM client not initialized")
        
        if self.provider == "azure_openai":
            return self._extract_with_azure_openai(prompt, model_config)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _extract_with_azure_openai(self, prompt: str, model_config: Optional[Dict] = None) -> str:
        """Extract metadata using Azure OpenAI"""
        default_config = {
            "max_tokens": 1500,
            "temperature": 0.1
        }
        
        if model_config:
            default_config.update(model_config)
        
        response = self.client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert RFP analyzer. Extract all 11 metadata fields from the complete document. Focus especially on finding financial data (project_value), pricing tables, and commercial information. Return only valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            **default_config
        )
        
        return response.choices[0].message.content.strip()
    
    def parse_json_response(self, response_text: str) -> Dict:
        """Parse JSON response from LLM with enhanced error handling"""
        try:
            # Clean up any markdown formatting
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = re.sub(r'```[^`]*```', '', response_text).strip()
                if "```" in response_text:
                    parts = response_text.split("```")
                    if len(parts) >= 3:
                        response_text = parts[1].strip()
            
            # Remove any leading/trailing text
            response_text = response_text.strip()
            if response_text.startswith('json'):
                response_text = response_text[4:].strip()
            
            # Find JSON object boundaries
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx+1]
                metadata = json.loads(json_text)
                return metadata
            else:
                # Try parsing the entire response
                metadata = json.loads(response_text)
                return metadata
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"❌ Raw response: {response_text[:500]}...")
            return self._get_default_metadata()
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
            return self._get_default_metadata()
    
    def _get_default_metadata(self) -> Dict:
        """Get default metadata structure when parsing fails"""
        return {
            'project_title': 'Not Specified',
            'client_name': 'Not Specified',
            'vendor_name': 'tetratech',
            'submission_date': 'Not Specified',
            'domain_category': 'Not mentioned in RFP',
            'service_category': 'Not mentioned in RFP',
            'revenue_range': 'Not mentioned in RFP',
            'region': 'Not mentioned in RFP',
            'project_value': 'Not mentioned in RFP',
            'compliance_standard': 'Not mentioned in RFP',
            'equipments_used': 'Not mentioned in RFP'
        }
    
    def is_available(self) -> bool:
        """Check if LLM client is available and ready"""
        return self.client is not None
    
    def get_provider_info(self) -> Dict:
        """Get information about the LLM provider"""
        if self.provider == "azure_openai":
            return {
                "provider": "Azure OpenAI",
                "available": OPENAI_AVAILABLE,
                "endpoint": AZURE_OPENAI_ENDPOINT,
                "deployment": AZURE_OPENAI_DEPLOYMENT_NAME,
                "api_version": AZURE_OPENAI_API_VERSION,
                "client_ready": self.client is not None
            }
        else:
            return {
                "provider": self.provider,
                "available": False,
                "client_ready": False
            }

class AzureOpenAIClient(LLMClient):
    """Specialized Azure OpenAI client"""
    
    def __init__(self, **config):
        super().__init__(provider="azure_openai", **config)

