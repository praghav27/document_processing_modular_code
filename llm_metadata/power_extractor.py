from typing import Dict
from .base_extractor import BaseMetadataExtractor
from .config_loader import ConfigLoader
from .prompts import PowerPrompts
from .llm_client import LLMClient
from config import AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT_NAME

# Import Azure OpenAI
try:
    from openai import AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class PowerMetadataExtractor(BaseMetadataExtractor):
    """Extract Power Business Unit RFP metadata from full document using Azure OpenAI"""
    
    def __init__(self):
        """Initialize the Power Business Unit metadata extractor with Azure OpenAI"""
        # Load Power Business Unit configuration
        self._power_config = ConfigLoader.load_power_config()
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
                print("✅ Power Business Unit - Azure OpenAI client initialized for metadata extraction")
                print(f"   Endpoint: {AZURE_OPENAI_ENDPOINT}")
                print(f"   Deployment: {AZURE_OPENAI_DEPLOYMENT_NAME}")
                print(f"   Power Domains: {len(self._power_config['domains'])} configured")
            else:
                print("❌ Azure OpenAI credentials not found or OpenAI library not available")
                print("⚠️  Cannot proceed without Azure OpenAI - no fallback available")
                
        except Exception as e:
            print(f"❌ Error initializing Azure OpenAI client: {e}")
            self.client = None
    
    def get_domain_config(self) -> Dict:
        """Get Power Business Unit domain and service configuration"""
        return self._power_config
    
    def get_extraction_prompt(self, document_text: str) -> str:
        """Get the Power Business Unit extraction prompt"""
        return PowerPrompts.get_document_metadata_extraction_prompt(document_text)
    
    def _get_default_metadata(self) -> Dict:
        """Get default Power Business Unit metadata structure"""
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
    
    def get_power_business_info(self) -> Dict:
        """Get Power Business Unit configuration information"""
        return {
            "business_unit": self._power_config.get("business_unit", "Power Business Unit"),
            "domains": self._power_config.get("domains", []),
            "services": self._power_config.get("services", {}),
            "total_domains": len(self._power_config.get("domains", [])),
            "total_services": sum(len(services) for services in self._power_config.get("services", {}).values()),
            "metadata_fields": 11
        }
    
    def get_status_info(self) -> Dict:
        """Get status information about the Power Business Unit metadata extractor"""
        base_info = super().get_status_info()
        power_info = {
            "openai_available": OPENAI_AVAILABLE,
            "api_key_present": bool(AZURE_OPENAI_API_KEY),
            "endpoint": AZURE_OPENAI_ENDPOINT,
            "deployment": AZURE_OPENAI_DEPLOYMENT_NAME,
            "business_unit": "Power Business Unit"
        }
        base_info.update(power_info)
        return base_info

# Backwards compatibility alias
class DocumentMetadataExtractor(PowerMetadataExtractor):
    """Backwards compatibility alias for existing code"""
    
    def extract_document_metadata(self, text_elements):
        """Backwards compatibility method name"""
        return self.extract_metadata(text_elements)