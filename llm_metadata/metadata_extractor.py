# import json
# import re
# from typing import Dict, List
# from .prompts import DocumentMetadataPrompts
# from config import AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT_NAME

# # Import Azure OpenAI
# try:
#     from openai import AzureOpenAI
#     OPENAI_AVAILABLE = True
# except ImportError:
#     OPENAI_AVAILABLE = False

# class DocumentMetadataExtractor:
#     """Extract Power Business Unit RFP metadata from first 2 pages using Azure OpenAI"""
    
#     def __init__(self):
#         """Initialize the Power Business Unit metadata extractor with Azure OpenAI"""
#         self.client = None
#         self.power_domains = [
#             "Renewable Energy",
#             "Energy Infrastructure & Grid Modernization",
#             "Conventional Power Systems", 
#             "Resource Sector Electrification & Integration",
#             "Environmental & Regulatory Services",
#             "International & Remote Community Energy Projects"
#         ]
        
#         self.power_services = {
#             "Renewable Energy": [
#                 "Site selection and feasibility studies",
#                 "Resource assessment (wind speed, solar irradiation, hydrology)",
#                 "Environmental permitting and approvals",
#                 "Detailed electrical and civil engineering design",
#                 "Grid interconnection and impact studies",
#                 "Independent Engineer (IE) and Owner's Engineer (OE) services",
#                 "Procurement and construction oversight",
#                 "SCADA and control systems integration"
#             ],
#             "Energy Infrastructure & Grid Modernization": [
#                 "Power system planning (load flow, short-circuit, contingency analysis)",
#                 "Substation layout and protection design",
#                 "Smart meter and grid automation consulting",
#                 "Renewable integration into existing grids",
#                 "Distributed energy system modeling and control",
#                 "Grid modernization roadmap development",
#                 "SCADA and communication systems design",
#                 "Arc flash and grounding studies"
#             ],
#             "Conventional Power Systems": [
#                 "Retrofit design and emissions reduction planning",
#                 "Regulatory compliance and license support",
#                 "Equipment and system upgrade engineering",
#                 "Decommissioning and remediation planning",
#                 "Safety analysis and QA/QC inspections",
#                 "Performance optimization and life extension analysis"
#             ],
#             "Resource Sector Electrification & Integration": [
#                 "Power supply studies for remote operations",
#                 "Diesel replacement with renewables or hybrid systems",
#                 "Transmission line routing and permitting",
#                 "On-site energy storage and backup systems",
#                 "Load forecasting and reliability assessments",
#                 "Grid connection strategy and economic analysis"
#             ],
#             "Environmental & Regulatory Services": [
#                 "Environmental impact assessments (EIA)",
#                 "Public and Indigenous consultation support",
#                 "Permitting (federal, provincial, municipal)",
#                 "Climate risk and adaptation planning",
#                 "Biodiversity, habitat, and wildlife impact studies",
#                 "GHG emissions and carbon accounting",
#                 "Sustainability/ESG reporting and disclosures"
#             ],
#             "International & Remote Community Energy Projects": [
#                 "Off-grid and hybrid system design",
#                 "Stakeholder and community engagement",
#                 "Socioeconomic impact assessments",
#                 "Electrification master planning",
#                 "Capacity building and training",
#                 "Procurement and construction monitoring"
#             ]
#         }
        
#         self._initialize_azure_openai_client()
    
#     def _initialize_azure_openai_client(self):
#         """Initialize the Azure OpenAI client"""
#         try:
#             if OPENAI_AVAILABLE and AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT:
#                 self.client = AzureOpenAI(
#                     api_key=AZURE_OPENAI_API_KEY,
#                     api_version=AZURE_OPENAI_API_VERSION,
#                     azure_endpoint=AZURE_OPENAI_ENDPOINT
#                 )
#                 print("✅ Power Business Unit - Azure OpenAI client initialized for metadata extraction")
#                 print(f"   Endpoint: {AZURE_OPENAI_ENDPOINT}")
#                 print(f"   Deployment: {AZURE_OPENAI_DEPLOYMENT_NAME}")
#                 print(f"   Power Domains: {len(self.power_domains)} configured")
#             else:
#                 print("❌ Azure OpenAI credentials not found or OpenAI library not available")
#                 print("⚠️  Using Power Business Unit fallback metadata extraction")
                
#         except Exception as e:
#             print(f"❌ Error initializing Azure OpenAI client: {e}")
#             self.client = None
    
#     def extract_document_metadata(self, text_elements: List[Dict]) -> Dict:
#         """
#         Extract Power Business Unit RFP metadata from first 2 pages using Azure OpenAI
        
#         Args:
#             text_elements: List of text elements from document
            
#         Returns:
#             Dict: Extracted metadata with 9 required fields for Power Business Unit (including project_value)
#         """
#         try:
#             print("🔍 Extracting Power Business Unit RFP metadata from first 2 pages...")
            
#             # Extract text from first 2 pages
#             first_two_pages_text = self._get_first_two_pages_text(text_elements)
            
#             if not first_two_pages_text.strip():
#                 print("⚠️ No text found in first 2 pages, using Power Business Unit defaults")
#                 return self._get_power_default_metadata()
            
#             print(f"📄 Analyzing {len(first_two_pages_text)} characters for Power Business Unit domains")
            
#             # Generate metadata using Azure OpenAI
#             if self.client:
#                 metadata = self._extract_metadata_with_azure_openai(first_two_pages_text)
#             else:
#                 # Fallback extraction for Power Business Unit
#                 metadata = self._extract_power_metadata_fallback(first_two_pages_text)
            
#             # Validate and clean metadata with Power Business Unit constraints
#             validated_metadata = self._validate_power_metadata(metadata)
            
#             print(f"✅ Power Business Unit metadata extracted successfully")
#             self._print_power_metadata_summary(validated_metadata)
            
#             return validated_metadata
            
#         except Exception as e:
#             print(f"❌ Error extracting Power Business Unit metadata: {e}")
#             return self._get_power_default_metadata()
    
#     def _get_first_two_pages_text(self, text_elements: List[Dict]) -> str:
#         """Extract text content from first 2 pages only"""
#         first_two_pages_text = ""
        
#         # Filter elements from pages 1 and 2
#         for element in text_elements:
#             page_number = element.get('page_number', 1)
#             if page_number <= 2:
#                 content = element.get('content', '').strip()
#                 role = element.get('role', 'unknown')
                
#                 # Add role context for better understanding
#                 if content:
#                     first_two_pages_text += f"[{role}] {content}\n\n"
        
#         # Limit text length to avoid token limits (keep first 6000 characters for safety)
#         if len(first_two_pages_text) > 6000:
#             first_two_pages_text = first_two_pages_text[:6000] + "... [truncated for token limit]"
        
#         return first_two_pages_text
    
#     def _extract_metadata_with_azure_openai(self, first_two_pages_text: str) -> Dict:
#         """Extract Power Business Unit metadata using Azure OpenAI API"""
#         try:
#             print("🤖 Calling Azure OpenAI for Power Business Unit metadata extraction...")
            
#             # Get the Power Business Unit specific prompt
#             prompt = DocumentMetadataPrompts.get_document_metadata_extraction_prompt(first_two_pages_text)
            
#             response = self.client.chat.completions.create(
#                 model=AZURE_OPENAI_DEPLOYMENT_NAME,
#                 messages=[
#                     {"role": "system", "content": "You are a Power Business Unit RFP expert. Extract metadata and match domains/services to the exact Power Business Unit lists provided. Return only valid JSON with the 9 required fields including region, revenue_range, and project_value."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 max_tokens=900,  # Increased for 9 fields
#                 temperature=0.1  # Low temperature for consistent extraction
#             )
            
#             response_text = response.choices[0].message.content.strip()
#             print(f"📝 Azure OpenAI response length: {len(response_text)} characters")
            
#             # Clean and parse JSON response
#             metadata = self._parse_json_response(response_text)
#             print("✅ Successfully parsed Power Business Unit metadata from Azure OpenAI")
#             return metadata
                
#         except Exception as e:
#             print(f"❌ Azure OpenAI API error: {e}")
#             print("🔄 Falling back to Power Business Unit text-based extraction...")
#             return self._extract_power_metadata_fallback(first_two_pages_text)
    
#     def _parse_json_response(self, response_text: str) -> Dict:
#         """Parse JSON response from Azure OpenAI"""
#         try:
#             # Remove any markdown formatting if present
#             if "```json" in response_text:
#                 response_text = response_text.split("```json")[1].split("```")[0].strip()
#             elif "```" in response_text:
#                 # Remove any code block markers
#                 response_text = re.sub(r'```[^`]*```', '', response_text).strip()
#                 # If that didn't work, try extracting content between first ``` pair
#                 if "```" in response_text:
#                     parts = response_text.split("```")
#                     if len(parts) >= 3:
#                         response_text = parts[1].strip()
            
#             # Clean up any remaining formatting
#             response_text = response_text.strip()
#             if response_text.startswith('json'):
#                 response_text = response_text[4:].strip()
            
#             # Parse JSON
#             metadata = json.loads(response_text)
#             return metadata
            
#         except json.JSONDecodeError as e:
#             print(f"❌ JSON parsing failed: {e}")
#             print(f"Raw response: {response_text}")
#             # Try regex fallback
#             return self._extract_with_regex_fallback(response_text)
    
#     def _extract_with_regex_fallback(self, response_text: str) -> Dict:
#         """Extract Power Business Unit metadata using regex when JSON parsing fails"""
#         print("🔧 Using regex fallback for Power Business Unit metadata extraction...")
        
#         metadata = self._get_power_default_metadata()
        
#         # Regex patterns to extract individual fields (now includes revenue_range and region)
#         patterns = {
#             'project_title': r'"project_title":\s*"([^"]*)"',
#             'client_name': r'"client_name":\s*"([^"]*)"',
#             'vendor_name': r'"vendor_name":\s*"([^"]*)"',
#             'submission_date': r'"submission_date":\s*"([^"]*)"',
#             'domain_category': r'"domain_category":\s*"([^"]*)"',
#             'service_category': r'"service_category":\s*"([^"]*)"',
#             'revenue_range': r'"revenue_range":\s*"([^"]*)"',
#             'region': r'"region":\s*"([^"]*)"'
#         }
        
#         for field, pattern in patterns.items():
#             match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
#             if match and match.group(1).strip():
#                 value = match.group(1).strip()
#                 if value and value.lower() not in ['not specified', 'unknown', 'null', 'none']:
#                     metadata[field] = value
        
#         return metadata
    
#     def _extract_power_metadata_fallback(self, text_content: str) -> Dict:
#         """Fallback Power Business Unit metadata extraction using text analysis"""
#         print("🔄 Using Power Business Unit text-based metadata extraction...")
        
#         metadata = self._get_power_default_metadata()
#         lines = text_content.split('\n')
#         text_lower = text_content.lower()
        
#         # Extract project title (look for power/energy related titles)
#         for line in lines[:15]:
#             line = line.strip()
#             cleaned_line = re.sub(r'^\[.*?\]\s*', '', line).strip()
#             if (cleaned_line and 
#                 len(cleaned_line) > 10 and 
#                 len(cleaned_line) < 150 and
#                 not re.match(r'^(page|confidential|statement|date)', cleaned_line.lower())):
#                 # Prioritize lines with power/energy keywords
#                 if any(keyword in cleaned_line.lower() for keyword in 
#                       ['power', 'energy', 'renewable', 'grid', 'solar', 'wind', 'electrical', 'substation']):
#                     metadata['project_title'] = cleaned_line
#                     break
#                 elif not metadata['project_title'] or metadata['project_title'] == 'Not Specified':
#                     metadata['project_title'] = cleaned_line
        
#         # Look for vendor/company names
#         vendor_patterns = [
#             r'from[:\s]+([^\n]+)',
#             r'prepared by[:\s]+([^\n]+)',
#             r'submitted by[:\s]+([^\n]+)',
#             r'tetratech',
#             r'company[:\s]+([^\n]+)'
#         ]
        
#         for pattern in vendor_patterns:
#             match = re.search(pattern, text_lower)
#             if match:
#                 if pattern == r'tetratech':
#                     metadata['vendor_name'] = 'Tetratech'
#                 else:
#                     vendor = match.group(1).strip()
#                     if vendor and len(vendor) < 100:
#                         metadata['vendor_name'] = vendor.title()
#                 break
        
#         # Look for client names
#         client_patterns = [
#             r'to[:\s]+([^\n]+)',
#             r'client[:\s]+([^\n]+)',
#             r'customer[:\s]+([^\n]+)'
#         ]
        
#         for pattern in client_patterns:
#             match = re.search(pattern, text_lower)
#             if match:
#                 client = match.group(1).strip()
#                 if client and len(client) < 100:
#                     metadata['client_name'] = client.title()
#                 break
        
#         # Look for dates
#         date_patterns = [
#             r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
#             r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
#             r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4})'
#         ]
        
#         for pattern in date_patterns:
#             match = re.search(pattern, text_content, re.IGNORECASE)
#             if match:
#                 metadata['submission_date'] = match.group(1)
#                 break
        
#         # Determine Power Business Unit domain based on keywords
#         domain_keywords = {
#             "Renewable Energy": ["renewable", "solar", "wind", "hydro", "photovoltaic", "pv", "turbine", "clean energy"],
#             "Energy Infrastructure & Grid Modernization": ["grid", "substation", "transmission", "distribution", "smart grid", "power system", "electrical infrastructure"],
#             "Conventional Power Systems": ["power plant", "thermal", "coal", "gas", "nuclear", "generator", "boiler", "turbine"],
#             "Resource Sector Electrification & Integration": ["mining", "oil", "gas", "remote", "diesel", "electrification", "resource sector"],
#             "Environmental & Regulatory Services": ["environmental", "assessment", "permitting", "consultation", "compliance", "regulatory", "eia"],
#             "International & Remote Community Energy Projects": ["community", "off-grid", "remote", "international", "indigenous", "rural electrification"]
#         }
        
#         for domain, keywords in domain_keywords.items():
#             if any(keyword in text_lower for keyword in keywords):
#                 metadata['domain_category'] = domain
#                 break
        
#         # Determine service category based on identified domain and content
#         if metadata['domain_category'] != "Not mentioned in RFP":
#             domain_services = self.power_services.get(metadata['domain_category'], [])
#             for service in domain_services:
#                 service_keywords = service.lower().split()[:3]  # Use first 3 words as keywords
#                 if any(keyword in text_lower for keyword in service_keywords):
#                     metadata['service_category'] = service
#                     break
        
#         # NEW: revenue_range, region, and project_value remain as "Not mentioned in RFP" in fallback
#         metadata['revenue_range'] = 'Not mentioned in RFP'
#         metadata['region'] = 'Not mentioned in RFP'
#         metadata['project_value'] = 'Not mentioned in RFP'
        
#         # Enhanced region extraction for fallback
#         region_patterns = [
#             # Canadian provinces
#             r'\b(ontario|alberta|british columbia|bc|quebec|manitoba|saskatchewan|nova scotia|ns|new brunswick|nb|newfoundland|pei|prince edward island|northwest territories|nwt|nunavut|yukon)\b',
#             # Major Canadian cities
#             r'\b(toronto|calgary|vancouver|montreal|ottawa|edmonton|winnipeg|halifax|quebec city|victoria|saskatoon|regina|hamilton|london|kitchener|waterloo)\b',
#             # US states and cities (common in Canadian RFPs)
#             r'\b(california|texas|new york|florida|washington|oregon|seattle|portland|san francisco|los angeles|chicago|boston|denver)\b',
#             # Regional descriptors
#             r'\b(atlantic canada|western canada|central canada|eastern canada|northern ontario|southern alberta|coastal bc|pacific northwest|east coast|west coast)\b',
#             # Generic location patterns
#             r'(?:located in|project site in|service area|location:|site:)\s*([^\n,]+)',
#             r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2,3})\b',  # City, Province format
#         ]
        
#         for pattern in region_patterns:
#             match = re.search(pattern, text_lower, re.IGNORECASE)
#             if match:
#                 region = match.group(1).strip() if len(match.groups()) >= 1 else match.group(0).strip()
#                 if region and len(region) < 100:
#                     metadata['region'] = region.title()
#                     break
        
#         # Enhanced revenue extraction for fallback
#         revenue_patterns = [
#             r'\$([0-9,]+(?:\.[0-9]{1,2})?)\s*(?:million|m|k|thousand|billion|b)\b',
#             r'(?:budget|contract value|estimated cost|project cost|value)[\s:]*\$([0-9,]+(?:\.[0-9]{1,2})?)',
#             r'\$([0-9,]+(?:\.[0-9]{1,2})?)\s*(?:-|to)\s*\$([0-9,]+(?:\.[0-9]{1,2})?)',
#             r'(?:under|below|less than)\s*\$([0-9,]+(?:\.[0-9]{1,2})?)',
#             r'(?:over|above|more than)\s*\$([0-9,]+(?:\.[0-9]{1,2})?)',
#         ]
        
#         for pattern in revenue_patterns:
#             match = re.search(pattern, text_content, re.IGNORECASE)
#             if match:
#                 revenue = match.group(0).strip()
#                 if revenue and len(revenue) < 100:
#                     metadata['revenue_range'] = revenue
#                     break
        
#         # Enhanced project value extraction for fallback (specific amounts)
#         project_value_patterns = [
#             r'(?:contract value|project value|total cost|award amount|professional fees)[\s:]*(\$[0-9,]+(?:\.[0-9]{1,2})?(?:\s*(?:million|M|thousand|K|CAD|USD))?)\b',
#             r'(?:project budget|allocated budget|service value|development cost)[\s:]*(\$[0-9,]+(?:\.[0-9]{1,2})?(?:\s*(?:million|M|thousand|K|CAD|USD))?)\b',
#             r'(?:contract amount|award value|total project cost)[\s:]*(\$[0-9,]+(?:\.[0-9]{1,2})?(?:\s*(?:million|M|thousand|K|CAD|USD))?)\b',
#             r'(?:capital investment|project investment)[\s:]*(\$[0-9,]+(?:\.[0-9]{1,2})?(?:\s*(?:million|M|thousand|K|CAD|USD))?)\b',
#         ]
        
#         for pattern in project_value_patterns:
#             match = re.search(pattern, text_content, re.IGNORECASE)
#             if match:
#                 project_value = match.group(1).strip()
#                 if project_value and len(project_value) < 50:
#                     metadata['project_value'] = project_value
#                     break
        
#         return metadata
    
#     def _validate_power_metadata(self, metadata: Dict) -> Dict:
#         """Validate and clean Power Business Unit metadata (now includes revenue_range and region)"""
#         required_fields = [
#             'project_title', 'client_name', 'vendor_name', 
#             'submission_date', 'domain_category', 'service_category',
#             'revenue_range', 'region', 'project_value'  # NEW: Added project_value as 9th field
#         ]
        
#         validated = {}
        
#         for field in required_fields:
#             value = metadata.get(field, 'Not Specified')
            
#             # Clean and validate the value
#             if isinstance(value, str):
#                 value = value.strip()
#                 value = re.sub(r'^["\']+|["\']+$', '', value)  # Remove quotes
#                 if not value or value.lower() in ['none', 'null', 'undefined', '', 'n/a']:
#                     # NEW: Set default values for new fields
#                     if field in ['revenue_range', 'region', 'project_value']:
#                         value = 'Not mentioned in RFP'
#                     else:
#                         value = 'Not Specified'
#                 elif len(value) > 200:
#                     value = value[:200] + '...'
#             else:
#                 # NEW: Set default values for new fields
#                 if field in ['revenue_range', 'region', 'project_value']:
#                     value = 'Not mentioned in RFP'
#                 else:
#                     value = 'Not Specified'
            
#             validated[field] = value
        
#         # Validate domain_category against Power Business Unit domains
#         if validated['domain_category'] not in self.power_domains:
#             if validated['domain_category'] != 'Not Specified':
#                 print(f"⚠️ Domain '{validated['domain_category']}' not in Power Business Unit list, setting to 'Not mentioned in RFP'")
#             validated['domain_category'] = 'Not mentioned in RFP'
        
#         # Validate service_category against Power Business Unit services
#         all_services = []
#         for domain_services in self.power_services.values():
#             all_services.extend(domain_services)
        
#         if validated['service_category'] not in all_services:
#             if validated['service_category'] != 'Not Specified':
#                 print(f"⚠️ Service '{validated['service_category']}' not in Power Business Unit list, setting to 'Not mentioned in RFP'")
#             validated['service_category'] = 'Not mentioned in RFP'
        
#         # Fallback vendor_name to tetratech if not found
#         if validated['vendor_name'] == 'Not Specified':
#             validated['vendor_name'] = 'tetratech'
        
#         # NEW: Ensure new fields always have values
#         if not validated.get('revenue_range') or validated['revenue_range'] == 'Not Specified':
#             validated['revenue_range'] = 'Not mentioned in RFP'
#         if not validated.get('region') or validated['region'] == 'Not Specified':
#             validated['region'] = 'Not mentioned in RFP'
#         if not validated.get('project_value') or validated['project_value'] == 'Not Specified':
#             validated['project_value'] = 'Not mentioned in RFP'
        
#         return validated
    
#     def _get_power_default_metadata(self) -> Dict:
#         """Get default Power Business Unit metadata structure (now includes revenue_range and region)"""
#         return {
#             'project_title': 'Not Specified',
#             'client_name': 'Not Specified',
#             'vendor_name': 'tetratech',
#             'submission_date': 'Not Specified',
#             'domain_category': 'Not mentioned in RFP',
#             'service_category': 'Not mentioned in RFP',
#             'revenue_range': 'Not mentioned in RFP',  # NEW: Default value for revenue range
#             'region': 'Not mentioned in RFP',          # NEW: Default value for region
#             'project_value': 'Not mentioned in RFP'    # NEW: Default value for project value
#         }
    
#     def _print_power_metadata_summary(self, metadata: Dict):
#         """Print Power Business Unit extracted metadata summary (now includes revenue_range and region)"""
#         print(f"📋 POWER BUSINESS UNIT METADATA SUMMARY:")
#         print(f"   📝 Project Title: {metadata.get('project_title', 'N/A')}")
#         print(f"   🏢 Client Name: {metadata.get('client_name', 'N/A')}")
#         print(f"   🏭 Vendor Name: {metadata.get('vendor_name', 'N/A')}")
#         print(f"   📅 Submission Date: {metadata.get('submission_date', 'N/A')}")
#         print(f"   ⚡ Domain Category: {metadata.get('domain_category', 'N/A')}")
#         print(f"   🔧 Service Category: {metadata.get('service_category', 'N/A')}")
#         print(f"   💰 Revenue Range: {metadata.get('revenue_range', 'N/A')}")      # NEW: Revenue Range display
#         print(f"   🌍 Region: {metadata.get('region', 'N/A')}")                    # NEW: Region display
#         print(f"   💵 Project Value: {metadata.get('project_value', 'N/A')}")      # NEW: Project Value display
        
#         # Validate against Power Business Unit lists
#         domain = metadata.get('domain_category', '')
#         service = metadata.get('service_category', '')
        
#         if domain in self.power_domains:
#             print(f"   ✅ Domain matches Power Business Unit list")
#         elif domain == 'Not mentioned in RFP':
#             print(f"   ⚠️ Domain not identified in RFP content")
#         else:
#             print(f"   ❌ Domain not in Power Business Unit list")
        
#         all_services = []
#         for domain_services in self.power_services.values():
#             all_services.extend(domain_services)
        
#         if service in all_services:
#             print(f"   ✅ Service matches Power Business Unit list")
#         elif service == 'Not mentioned in RFP':
#             print(f"   ⚠️ Service not identified in RFP content")
#         else:
#             print(f"   ❌ Service not in Power Business Unit list")
    
#     def get_status_info(self) -> Dict:
#         """Get status information about the Power Business Unit metadata extractor"""
#         return {
#             "client_initialized": self.client is not None,
#             "openai_available": OPENAI_AVAILABLE,
#             "api_key_present": bool(AZURE_OPENAI_API_KEY),
#             "endpoint": AZURE_OPENAI_ENDPOINT,
#             "deployment": AZURE_OPENAI_DEPLOYMENT_NAME,
#             "status": "ready" if self.client else "fallback_mode",
#             "business_unit": "Power Business Unit",
#             "domains_configured": len(self.power_domains),
#             "services_configured": sum(len(services) for services in self.power_services.values()),
#             "total_fields": 9  # NEW: Updated to reflect 9 fields
#         }
    
#     def get_power_business_info(self) -> Dict:
#         """Get Power Business Unit configuration information"""
#         return {
#             "business_unit": "Power Business Unit",
#             "domains": self.power_domains,
#             "services": self.power_services,
#             "total_domains": len(self.power_domains),
#             "total_services": sum(len(services) for services in self.power_services.values()),
#             "metadata_fields": 9  # NEW: Updated to reflect 9 fields
#         }


import json
import re
from typing import Dict, List
from .prompts import DocumentMetadataPrompts
from config import AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT_NAME

# Import Azure OpenAI
try:
    from openai import AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class DocumentMetadataExtractor:
    """Extract Power Business Unit RFP metadata from first 2 pages using Azure OpenAI"""
    
    def __init__(self):
        """Initialize the Power Business Unit metadata extractor with Azure OpenAI"""
        self.client = None
        self.power_domains = [
            "Renewable Energy",
            "Energy Infrastructure & Grid Modernization",
            "Conventional Power Systems", 
            "Resource Sector Electrification & Integration",
            "Environmental & Regulatory Services",
            "International & Remote Community Energy Projects"
        ]
        
        self.power_services = {
            "Renewable Energy": [
                "Site selection and feasibility studies",
                "Resource assessment (wind speed, solar irradiation, hydrology)",
                "Environmental permitting and approvals",
                "Detailed electrical and civil engineering design",
                "Grid interconnection and impact studies",
                "Independent Engineer (IE) and Owner's Engineer (OE) services",
                "Procurement and construction oversight",
                "SCADA and control systems integration"
            ],
            "Energy Infrastructure & Grid Modernization": [
                "Power system planning (load flow, short-circuit, contingency analysis)",
                "Substation layout and protection design",
                "Smart meter and grid automation consulting",
                "Renewable integration into existing grids",
                "Distributed energy system modeling and control",
                "Grid modernization roadmap development",
                "SCADA and communication systems design",
                "Arc flash and grounding studies"
            ],
            "Conventional Power Systems": [
                "Retrofit design and emissions reduction planning",
                "Regulatory compliance and license support",
                "Equipment and system upgrade engineering",
                "Decommissioning and remediation planning",
                "Safety analysis and QA/QC inspections",
                "Performance optimization and life extension analysis"
            ],
            "Resource Sector Electrification & Integration": [
                "Power supply studies for remote operations",
                "Diesel replacement with renewables or hybrid systems",
                "Transmission line routing and permitting",
                "On-site energy storage and backup systems",
                "Load forecasting and reliability assessments",
                "Grid connection strategy and economic analysis"
            ],
            "Environmental & Regulatory Services": [
                "Environmental impact assessments (EIA)",
                "Public and Indigenous consultation support",
                "Permitting (federal, provincial, municipal)",
                "Climate risk and adaptation planning",
                "Biodiversity, habitat, and wildlife impact studies",
                "GHG emissions and carbon accounting",
                "Sustainability/ESG reporting and disclosures"
            ],
            "International & Remote Community Energy Projects": [
                "Off-grid and hybrid system design",
                "Stakeholder and community engagement",
                "Socioeconomic impact assessments",
                "Electrification master planning",
                "Capacity building and training",
                "Procurement and construction monitoring"
            ]
        }
        
        self._initialize_azure_openai_client()
    
    def _initialize_azure_openai_client(self):
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
                print(f"   Power Domains: {len(self.power_domains)} configured")
            else:
                print("❌ Azure OpenAI credentials not found or OpenAI library not available")
                print("⚠️  Using Power Business Unit fallback metadata extraction")
                
        except Exception as e:
            print(f"❌ Error initializing Azure OpenAI client: {e}")
            self.client = None
    
    def extract_document_metadata(self, text_elements: List[Dict]) -> Dict:
        """
        Extract Power Business Unit RFP metadata from first 2 pages using Azure OpenAI
        
        Args:
            text_elements: List of text elements from document
            
        Returns:
            Dict: Extracted metadata with 11 required fields for Power Business Unit (including compliance_standard and equipments_used)
        """
        try:
            print("🔍 Extracting Power Business Unit RFP metadata from first 2 pages...")
            
            # Extract text from first 2 pages
            first_two_pages_text = self._get_first_two_pages_text(text_elements)
            
            if not first_two_pages_text.strip():
                print("⚠️ No text found in first 2 pages, using Power Business Unit defaults")
                return self._get_power_default_metadata()
            
            print(f"📄 Analyzing {len(first_two_pages_text)} characters for Power Business Unit domains")
            
            # Generate metadata using Azure OpenAI
            if self.client:
                metadata = self._extract_metadata_with_azure_openai(first_two_pages_text)
            else:
                # Fallback extraction for Power Business Unit
                metadata = self._extract_power_metadata_fallback(first_two_pages_text)
            
            # Validate and clean metadata with Power Business Unit constraints
            validated_metadata = self._validate_power_metadata(metadata)
            
            print(f"✅ Power Business Unit metadata extracted successfully")
            self._print_power_metadata_summary(validated_metadata)
            
            return validated_metadata
            
        except Exception as e:
            print(f"❌ Error extracting Power Business Unit metadata: {e}")
            return self._get_power_default_metadata()
    
    def _get_first_two_pages_text(self, text_elements: List[Dict]) -> str:
        """Extract text content from first 2 pages only"""
        first_two_pages_text = ""
        
        # Filter elements from pages 1 and 2
        for element in text_elements:
            page_number = element.get('page_number', 1)
            if page_number <= 2:
                content = element.get('content', '').strip()
                role = element.get('role', 'unknown')
                
                # Add role context for better understanding
                if content:
                    first_two_pages_text += f"[{role}] {content}\n\n"
        
        # Limit text length to avoid token limits (keep first 6000 characters for safety)
        if len(first_two_pages_text) > 6000:
            first_two_pages_text = first_two_pages_text[:6000] + "... [truncated for token limit]"
        
        return first_two_pages_text
    
    def _extract_metadata_with_azure_openai(self, first_two_pages_text: str) -> Dict:
        """Extract Power Business Unit metadata using Azure OpenAI API"""
        try:
            print("🤖 Calling Azure OpenAI for Power Business Unit metadata extraction...")
            
            # Get the Power Business Unit specific prompt
            prompt = DocumentMetadataPrompts.get_document_metadata_extraction_prompt(first_two_pages_text)
            
            response = self.client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": "You are a Power Business Unit RFP expert. Extract metadata and match domains/services to the exact Power Business Unit lists provided. Return only valid JSON with the 11 required fields including region, revenue_range, project_value, compliance_standard, and equipments_used."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,  # Increased for 11 fields
                temperature=0.1  # Low temperature for consistent extraction
            )
            
            response_text = response.choices[0].message.content.strip()
            print(f"📝 Azure OpenAI response length: {len(response_text)} characters")
            
            # Clean and parse JSON response
            metadata = self._parse_json_response(response_text)
            print("✅ Successfully parsed Power Business Unit metadata from Azure OpenAI")
            return metadata
                
        except Exception as e:
            print(f"❌ Azure OpenAI API error: {e}")
            print("🔄 Falling back to Power Business Unit text-based extraction...")
            return self._extract_power_metadata_fallback(first_two_pages_text)
    
    def _parse_json_response(self, response_text: str) -> Dict:
        """Parse JSON response from Azure OpenAI"""
        try:
            # Remove any markdown formatting if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                # Remove any code block markers
                response_text = re.sub(r'```[^`]*```', '', response_text).strip()
                # If that didn't work, try extracting content between first ``` pair
                if "```" in response_text:
                    parts = response_text.split("```")
                    if len(parts) >= 3:
                        response_text = parts[1].strip()
            
            # Clean up any remaining formatting
            response_text = response_text.strip()
            if response_text.startswith('json'):
                response_text = response_text[4:].strip()
            
            # Parse JSON
            metadata = json.loads(response_text)
            return metadata
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"Raw response: {response_text}")
            # Try regex fallback
            return self._extract_with_regex_fallback(response_text)
    
    def _extract_with_regex_fallback(self, response_text: str) -> Dict:
        """Extract Power Business Unit metadata using regex when JSON parsing fails"""
        print("🔧 Using regex fallback for Power Business Unit metadata extraction...")
        
        metadata = self._get_power_default_metadata()
        
        # Regex patterns to extract individual fields (now includes all 11 fields)
        patterns = {
            'project_title': r'"project_title":\s*"([^"]*)"',
            'client_name': r'"client_name":\s*"([^"]*)"',
            'vendor_name': r'"vendor_name":\s*"([^"]*)"',
            'submission_date': r'"submission_date":\s*"([^"]*)"',
            'domain_category': r'"domain_category":\s*"([^"]*)"',
            'service_category': r'"service_category":\s*"([^"]*)"',
            'revenue_range': r'"revenue_range":\s*"([^"]*)"',
            'region': r'"region":\s*"([^"]*)"',
            'project_value': r'"project_value":\s*"([^"]*)"',
            'compliance_standard': r'"compliance_standard":\s*"([^"]*)"',  # NEW
            'equipments_used': r'"equipments_used":\s*"([^"]*)"'           # NEW
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
            if match and match.group(1).strip():
                value = match.group(1).strip()
                if value and value.lower() not in ['not specified', 'unknown', 'null', 'none']:
                    metadata[field] = value
        
        return metadata
    
    def _extract_power_metadata_fallback(self, text_content: str) -> Dict:
        """Fallback Power Business Unit metadata extraction using text analysis"""
        print("🔄 Using Power Business Unit text-based metadata extraction...")
        
        metadata = self._get_power_default_metadata()
        lines = text_content.split('\n')
        text_lower = text_content.lower()
        
        # Extract project title (look for power/energy related titles)
        for line in lines[:15]:
            line = line.strip()
            cleaned_line = re.sub(r'^\[.*?\]\s*', '', line).strip()
            if (cleaned_line and 
                len(cleaned_line) > 10 and 
                len(cleaned_line) < 150 and
                not re.match(r'^(page|confidential|statement|date)', cleaned_line.lower())):
                # Prioritize lines with power/energy keywords
                if any(keyword in cleaned_line.lower() for keyword in 
                      ['power', 'energy', 'renewable', 'grid', 'solar', 'wind', 'electrical', 'substation']):
                    metadata['project_title'] = cleaned_line
                    break
                elif not metadata['project_title'] or metadata['project_title'] == 'Not Specified':
                    metadata['project_title'] = cleaned_line
        
        # Look for vendor/company names
        vendor_patterns = [
            r'from[:\s]+([^\n]+)',
            r'prepared by[:\s]+([^\n]+)',
            r'submitted by[:\s]+([^\n]+)',
            r'tetratech',
            r'company[:\s]+([^\n]+)'
        ]
        
        for pattern in vendor_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if pattern == r'tetratech':
                    metadata['vendor_name'] = 'Tetratech'
                else:
                    vendor = match.group(1).strip()
                    if vendor and len(vendor) < 100:
                        metadata['vendor_name'] = vendor.title()
                break
        
        # Look for client names
        client_patterns = [
            r'to[:\s]+([^\n]+)',
            r'client[:\s]+([^\n]+)',
            r'customer[:\s]+([^\n]+)'
        ]
        
        for pattern in client_patterns:
            match = re.search(pattern, text_lower)
            if match:
                client = match.group(1).strip()
                if client and len(client) < 100:
                    metadata['client_name'] = client.title()
                break
        
        # Look for dates
        date_patterns = [
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                metadata['submission_date'] = match.group(1)
                break
        
        # Determine Power Business Unit domain based on keywords
        domain_keywords = {
            "Renewable Energy": ["renewable", "solar", "wind", "hydro", "photovoltaic", "pv", "turbine", "clean energy"],
            "Energy Infrastructure & Grid Modernization": ["grid", "substation", "transmission", "distribution", "smart grid", "power system", "electrical infrastructure"],
            "Conventional Power Systems": ["power plant", "thermal", "coal", "gas", "nuclear", "generator", "boiler", "turbine"],
            "Resource Sector Electrification & Integration": ["mining", "oil", "gas", "remote", "diesel", "electrification", "resource sector"],
            "Environmental & Regulatory Services": ["environmental", "assessment", "permitting", "consultation", "compliance", "regulatory", "eia"],
            "International & Remote Community Energy Projects": ["community", "off-grid", "remote", "international", "indigenous", "rural electrification"]
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                metadata['domain_category'] = domain
                break
        
        # Determine service category based on identified domain and content
        if metadata['domain_category'] != "Not mentioned in RFP":
            domain_services = self.power_services.get(metadata['domain_category'], [])
            for service in domain_services:
                service_keywords = service.lower().split()[:3]  # Use first 3 words as keywords
                if any(keyword in text_lower for keyword in service_keywords):
                    metadata['service_category'] = service
                    break
        
        # Set default values for new fields and existing fields
        metadata['revenue_range'] = 'Not mentioned in RFP'
        metadata['region'] = 'Not mentioned in RFP'
        metadata['project_value'] = 'Not mentioned in RFP'
        metadata['compliance_standard'] = 'Not mentioned in RFP'  # NEW
        metadata['equipments_used'] = 'Not mentioned in RFP'     # NEW
        
        # Enhanced region extraction for fallback
        region_patterns = [
            # Canadian provinces
            r'\b(ontario|alberta|british columbia|bc|quebec|manitoba|saskatchewan|nova scotia|ns|new brunswick|nb|newfoundland|pei|prince edward island|northwest territories|nwt|nunavut|yukon)\b',
            # Major Canadian cities
            r'\b(toronto|calgary|vancouver|montreal|ottawa|edmonton|winnipeg|halifax|quebec city|victoria|saskatoon|regina|hamilton|london|kitchener|waterloo)\b',
            # US states and cities (common in Canadian RFPs)
            r'\b(california|texas|new york|florida|washington|oregon|seattle|portland|san francisco|los angeles|chicago|boston|denver)\b',
            # Regional descriptors
            r'\b(atlantic canada|western canada|central canada|eastern canada|northern ontario|southern alberta|coastal bc|pacific northwest|east coast|west coast)\b',
            # Generic location patterns
            r'(?:located in|project site in|service area|location:|site:)\s*([^\n,]+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2,3})\b',  # City, Province format
        ]
        
        for pattern in region_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                region = match.group(1).strip() if len(match.groups()) >= 1 else match.group(0).strip()
                if region and len(region) < 100:
                    metadata['region'] = region.title()
                    break
        
        # Enhanced revenue extraction for fallback
        revenue_patterns = [
            r'\$([0-9,]+(?:\.[0-9]{1,2})?)\s*(?:million|m|k|thousand|billion|b)\b',
            r'(?:budget|contract value|estimated cost|project cost|value)[\s:]*\$([0-9,]+(?:\.[0-9]{1,2})?)',
            r'\$([0-9,]+(?:\.[0-9]{1,2})?)\s*(?:-|to)\s*\$([0-9,]+(?:\.[0-9]{1,2})?)',
            r'(?:under|below|less than)\s*\$([0-9,]+(?:\.[0-9]{1,2})?)',
            r'(?:over|above|more than)\s*\$([0-9,]+(?:\.[0-9]{1,2})?)',
        ]
        
        for pattern in revenue_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                revenue = match.group(0).strip()
                if revenue and len(revenue) < 100:
                    metadata['revenue_range'] = revenue
                    break
        
        # Enhanced project value extraction for fallback (specific amounts)
        project_value_patterns = [
            r'(?:contract value|project value|total cost|award amount|professional fees)[\s:]*(\$[0-9,]+(?:\.[0-9]{1,2})?(?:\s*(?:million|M|thousand|K|CAD|USD))?)\b',
            r'(?:project budget|allocated budget|service value|development cost)[\s:]*(\$[0-9,]+(?:\.[0-9]{1,2})?(?:\s*(?:million|M|thousand|K|CAD|USD))?)\b',
            r'(?:contract amount|award value|total project cost)[\s:]*(\$[0-9,]+(?:\.[0-9]{1,2})?(?:\s*(?:million|M|thousand|K|CAD|USD))?)\b',
            r'(?:capital investment|project investment)[\s:]*(\$[0-9,]+(?:\.[0-9]{1,2})?(?:\s*(?:million|M|thousand|K|CAD|USD))?)\b',
        ]
        
        for pattern in project_value_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                project_value = match.group(1).strip()
                if project_value and len(project_value) < 50:
                    metadata['project_value'] = project_value
                    break
        
        # NEW: Enhanced compliance standard extraction for fallback
        compliance_patterns = [
            r'(?:compliance|standard|code|regulation|certification)[\s:]*([^\n,]+(?:iso|ieee|nema|csa|ul|astm|api|asme|ansi|iec|din|bs|en|ce|fcc|rohs)[^\n,]*)',
            r'\b(iso[\s-]?\d+(?::\d+)?|ieee[\s-]?\d+|nema[\s-]?\w+|csa[\s-]?\w+|ul[\s-]?\d+|astm[\s-]?\w+|api[\s-]?\d+|asme[\s-]?\w+|ansi[\s-]?\w+|iec[\s-]?\d+)\b',
            r'(?:meets|complies with|according to|per|follows)[\s:]*([^\n,]+(?:standard|code|regulation|requirement)[^\n,]*)',
            r'(?:quality assurance|qa|qc|quality control)[\s:]*([^\n,]+)',
            r'(?:certified|accredited)[\s:]*([^\n,]+)',
        ]
        
        for pattern in compliance_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                compliance = match.group(1).strip()
                if compliance and len(compliance) < 200:
                    metadata['compliance_standard'] = compliance
                    break
        
        # NEW: Enhanced equipment extraction for fallback
        equipment_patterns = [
            r'(?:equipment|machinery|tools|instruments|devices)[\s:]*([^\n]+)',
            r'(?:using|utilizing|employing)[\s:]*([^\n,]+(?:equipment|machinery|tools|instruments|devices)[^\n,]*)',
            r'\b(transformer|generator|turbine|motor|pump|compressor|valve|sensor|meter|controller|switch|relay|cable|conductor|insulator|breaker|fuse|capacitor|reactor|inverter|converter)\b[^\n,]*',
            r'(?:installed|deployed|operated|maintained)[\s:]*([^\n,]+(?:equipment|system|unit)[^\n,]*)',
            r'(?:technical specifications|specs)[\s:]*([^\n]+)',
        ]
        
        equipment_found = []
        for pattern in equipment_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]  # Take first group if tuple
                equipment = match.strip()
                if equipment and len(equipment) < 100 and equipment not in equipment_found:
                    equipment_found.append(equipment)
        
        if equipment_found:
            metadata['equipments_used'] = ', '.join(equipment_found[:3])  # Limit to first 3 equipment items
        
        return metadata
    
    def _validate_power_metadata(self, metadata: Dict) -> Dict:
        """Validate and clean Power Business Unit metadata (now includes compliance_standard and equipments_used)"""
        required_fields = [
            'project_title', 'client_name', 'vendor_name', 
            'submission_date', 'domain_category', 'service_category',
            'revenue_range', 'region', 'project_value',
            'compliance_standard', 'equipments_used'  # NEW: Added as 10th and 11th fields
        ]
        
        validated = {}
        
        for field in required_fields:
            value = metadata.get(field, 'Not Specified')
            
            # Clean and validate the value
            if isinstance(value, str):
                value = value.strip()
                value = re.sub(r'^["\']+|["\']+$', '', value)  # Remove quotes
                if not value or value.lower() in ['none', 'null', 'undefined', '', 'n/a']:
                    # Set default values for new fields
                    if field in ['revenue_range', 'region', 'project_value', 'compliance_standard', 'equipments_used']:
                        value = 'Not mentioned in RFP'
                    else:
                        value = 'Not Specified'
                elif len(value) > 200:
                    value = value[:200] + '...'
            else:
                # Set default values for new fields
                if field in ['revenue_range', 'region', 'project_value', 'compliance_standard', 'equipments_used']:
                    value = 'Not mentioned in RFP'
                else:
                    value = 'Not Specified'
            
            validated[field] = value
        
        # Validate domain_category against Power Business Unit domains
        if validated['domain_category'] not in self.power_domains:
            if validated['domain_category'] != 'Not Specified':
                print(f"⚠️ Domain '{validated['domain_category']}' not in Power Business Unit list, setting to 'Not mentioned in RFP'")
            validated['domain_category'] = 'Not mentioned in RFP'
        
        # Validate service_category against Power Business Unit services
        all_services = []
        for domain_services in self.power_services.values():
            all_services.extend(domain_services)
        
        if validated['service_category'] not in all_services:
            if validated['service_category'] != 'Not Specified':
                print(f"⚠️ Service '{validated['service_category']}' not in Power Business Unit list, setting to 'Not mentioned in RFP'")
            validated['service_category'] = 'Not mentioned in RFP'
        
        # Fallback vendor_name to tetratech if not found
        if validated['vendor_name'] == 'Not Specified':
            validated['vendor_name'] = 'tetratech'
        
        # Ensure all new fields always have values
        for field in ['revenue_range', 'region', 'project_value', 'compliance_standard', 'equipments_used']:
            if not validated.get(field) or validated[field] == 'Not Specified':
                validated[field] = 'Not mentioned in RFP'
        
        return validated
    
    def _get_power_default_metadata(self) -> Dict:
        """Get default Power Business Unit metadata structure (now includes compliance_standard and equipments_used)"""
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
            'compliance_standard': 'Not mentioned in RFP',  # NEW: Default value for compliance standard
            'equipments_used': 'Not mentioned in RFP'       # NEW: Default value for equipments used
        }
    
    def _print_power_metadata_summary(self, metadata: Dict):
        """Print Power Business Unit extracted metadata summary (now includes compliance_standard and equipments_used)"""
        print(f"📋 POWER BUSINESS UNIT METADATA SUMMARY:")
        print(f"   📝 Project Title: {metadata.get('project_title', 'N/A')}")
        print(f"   🏢 Client Name: {metadata.get('client_name', 'N/A')}")
        print(f"   🏭 Vendor Name: {metadata.get('vendor_name', 'N/A')}")
        print(f"   📅 Submission Date: {metadata.get('submission_date', 'N/A')}")
        print(f"   ⚡ Domain Category: {metadata.get('domain_category', 'N/A')}")
        print(f"   🔧 Service Category: {metadata.get('service_category', 'N/A')}")
        print(f"   💰 Revenue Range: {metadata.get('revenue_range', 'N/A')}")
        print(f"   🌍 Region: {metadata.get('region', 'N/A')}")
        print(f"   💵 Project Value: {metadata.get('project_value', 'N/A')}")
        print(f"   📜 Compliance Standard: {metadata.get('compliance_standard', 'N/A')}")  # NEW: Compliance Standard display
        print(f"   ⚙️ Equipments Used: {metadata.get('equipments_used', 'N/A')}")           # NEW: Equipments Used display
        
        # Validate against Power Business Unit lists
        domain = metadata.get('domain_category', '')
        service = metadata.get('service_category', '')
        
        if domain in self.power_domains:
            print(f"   ✅ Domain matches Power Business Unit list")
        elif domain == 'Not mentioned in RFP':
            print(f"   ⚠️ Domain not identified in RFP content")
        else:
            print(f"   ❌ Domain not in Power Business Unit list")
        
        all_services = []
        for domain_services in self.power_services.values():
            all_services.extend(domain_services)
        
        if service in all_services:
            print(f"   ✅ Service matches Power Business Unit list")
        elif service == 'Not mentioned in RFP':
            print(f"   ⚠️ Service not identified in RFP content")
        else:
            print(f"   ❌ Service not in Power Business Unit list")
    
    def get_status_info(self) -> Dict:
        """Get status information about the Power Business Unit metadata extractor"""
        return {
            "client_initialized": self.client is not None,
            "openai_available": OPENAI_AVAILABLE,
            "api_key_present": bool(AZURE_OPENAI_API_KEY),
            "endpoint": AZURE_OPENAI_ENDPOINT,
            "deployment": AZURE_OPENAI_DEPLOYMENT_NAME,
            "status": "ready" if self.client else "fallback_mode",
            "business_unit": "Power Business Unit",
            "domains_configured": len(self.power_domains),
            "services_configured": sum(len(services) for services in self.power_services.values()),
            "total_fields": 11  # NEW: Updated to reflect 11 fields
        }
    
    def get_power_business_info(self) -> Dict:
        """Get Power Business Unit configuration information"""
        return {
            "business_unit": "Power Business Unit",
            "domains": self.power_domains,
            "services": self.power_services,
            "total_domains": len(self.power_domains),
            "total_services": sum(len(services) for services in self.power_services.values()),
            "metadata_fields": 11  # NEW: Updated to reflect 11 fields
        }