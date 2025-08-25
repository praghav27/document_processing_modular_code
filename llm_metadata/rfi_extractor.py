

# # import json
# # import re
# # from typing import Dict, List
# # from .prompts import DocumentMetadataPrompts
# # from processors.content_verbalizer import ContentVerbalizer
 
# # class RFIExtractor:
# #     """Extract RFI metadata (8 NEW fields) from documents using Azure OpenAI - No chunking for RFI"""
   
# #     def __init__(self):
# #         """Initialize RFI extractor with existing Azure OpenAI client"""
# #         self.verbalizer = ContentVerbalizer()  # Reuse existing client
# #         self.rfi_fields = [
# #             'project_name', 'client', 'region', 'industry', 
# #             'prepared_date', 'station_discipline', 'scope_of_work', 'required_activities'
# #         ]
       
# #         print("✅ RFI Extractor initialized with NEW fields - NO CHUNKING")
# #         print(f"   📊 Fields: {len(self.rfi_fields)} RFI metadata fields (no doc_id, using project_id)")
# #         print(f"   🚫 Chunking: DISABLED for RFI documents")
   
# #     async def extract_metadata_only(self, text_elements: List[Dict]) -> Dict:
# #         """
# #         Extract ONLY RFI metadata (9 new fields) from complete document text elements
# #         NO CHUNKING - Only metadata extraction for indexing
# #         """
# #         try:
# #             print("🔍 Extracting RFI metadata ONLY (No chunking for RFI)")
           
# #             # Convert text elements to complete document text
# #             complete_document_text = self._prepare_complete_document_text(text_elements)
           
# #             if not complete_document_text.strip():
# #                 print("⚠️ No text found in document, using RFI defaults")
# #                 return self._get_rfi_default_metadata()
           
# #             print(f"📊 Complete document text prepared:")
# #             print(f"   📄 Pages processed: {self._count_pages(text_elements)}")
# #             print(f"   📝 Text length: {len(complete_document_text)} characters")
# #             print(f"   🎯 Ready for metadata-only extraction (NO CHUNKING)")
           
# #             # Generate metadata using Azure OpenAI (reusing existing client)
# #             if self.verbalizer.client:
# #                 metadata = await self._extract_metadata_with_azure_openai(complete_document_text)
# #             else:
# #                 print("❌ Azure OpenAI client not available")
# #                 return self._get_rfi_default_metadata()
           
# #             # Validate and clean metadata for RFI (9 new fields)
# #             validated_metadata = self._validate_rfi_metadata(metadata)
           
# #             print("✅ RFI metadata-only extraction completed (NO CHUNKING)")
# #             return validated_metadata
           
# #         except Exception as e:
# #             print(f"❌ Error extracting RFI metadata: {e}")
# #             return self._get_rfi_default_metadata()
   
# #     def _prepare_complete_document_text(self, text_elements: List[Dict]) -> str:
# #         """Convert text elements to complete document text"""
# #         complete_text = ""
       
# #         # Process ALL text elements from the complete document
# #         for element in text_elements:
# #             content = element.get('content', '').strip()
# #             role = element.get('role', 'unknown')
           
# #             # Add role context for better understanding
# #             if content:
# #                 complete_text += f"[{role}] {content}\n\n"
       
# #         print(f"🔍 Processing {len(text_elements)} text elements from complete document...")
# #         return complete_text
   
# #     def _count_pages(self, text_elements: List[Dict]) -> str:
# #         """Count total pages in document"""
# #         pages = set()
# #         for element in text_elements:
# #             page_num = element.get('page_number', 1)
# #             pages.add(page_num)
       
# #         total_pages = max(pages) if pages else 1
# #         return f"{total_pages}/{total_pages}"
   
# #     async def _extract_metadata_with_azure_openai(self, complete_document_text: str) -> Dict:
# #         """Extract RFI metadata using Azure OpenAI API with NEW fields"""
# #         try:
# #             print(f"📄 Sending {len(complete_document_text)} characters to LLM for RFI analysis")
# #             print("🤖 Calling LLM for metadata-only extraction (NEW FIELDS)...")
           
# #             # Get the NEW RFI-specific prompt with new fields
# #             prompt = self._get_new_rfi_extraction_prompt(complete_document_text)
           
# #             response = await self.verbalizer.client.chat.completions.create(
# #                 model="gpt-4o",  # Use same model as ContentVerbalizer
# #                 messages=[
# #                     {"role": "system", "content": "You are an expert RFI analyst. Extract the 9 new metadata fields for RFI documents. Return only valid JSON."},
# #                     {"role": "user", "content": prompt}
# #                 ],
# #                 max_tokens=800,  # Sufficient for new fields
# #                 temperature=0.1  # Low temperature for consistent extraction
# #             )
           
# #             response_text = response.choices[0].message.content.strip()
# #             print(f"📝 LLM response: {len(response_text)} characters")
           
# #             # Clean and parse JSON response
# #             metadata = self._parse_json_response(response_text)
           
# #             print("✅ Successfully parsed NEW metadata from LLM")
# #             return metadata
               
# #         except Exception as e:
# #             print(f"❌ Azure OpenAI API error: {e}")
# #             return self._get_rfi_default_metadata()
   
# #     def _get_new_rfi_extraction_prompt(self, document_text: str) -> str:
# #         """Get the NEW RFI metadata extraction prompt for 9 fields"""
# #         return f"""
# # You are an expert RFI (Request for Information) analyzer. Extract EXACTLY 9 metadata fields from the document. Return ONLY a valid JSON object.

# # **DOCUMENT TEXT:**
# # {document_text}

# # **EXTRACTION REQUIREMENTS:**

# # 1. **project_name**: Find the main project name, RFI title, or project identifier. Look for project titles, names, or main subject headings.

# # 2. **client**: Identify the organization or client requesting the information. Look for "Client:", "Owner:", issuing organization names, or companies requesting the RFI.

# # 3. **region**: Extract geographical location information. Look for:
# #    - Countries, provinces/states, cities
# #    - Project locations, service areas
# #    - Regional identifiers, geographical references

# # 4. **industry**: Determine the industry sector this RFI relates to. Common industries include:
# #    - "Power & Energy", "Water & Wastewater", "Transportation", "Oil & Gas", "Mining", 
# #    - "Environmental", "Infrastructure", "Telecommunications", "Manufacturing", "Healthcare"

# # 5. **prepared_date**: Extract document creation date, preparation date, or issue date. Look for "Date:", "Issued:", "Prepared:", etc. Use YYYY-MM-DD format.

# # 6. **station_discipline**: Identify the engineering discipline or technical area. Look for:
# #    - "Civil", "Electrical", "Mechanical", "Structural", "Environmental", "Process", 
# #    - "Instrumentation", "Control Systems", "HVAC", "Piping", "Architectural"

# # 7. **scope_of_work**: Create a SHORT summary (max 200 words) of the work scope for vector/keyword search. Include main activities, deliverables, and objectives.

# # 8. **required_activities**: Create a SHORT summary (max 200 words) of required activities for vector/keyword search. Include tasks, responsibilities, and actions needed.

# # **RESPONSE FORMAT - ONLY JSON:**
# # {{
# #     "project_name": "extracted project name or 'Not Specified'",
# #     "client": "extracted client name or 'Not Specified'",
# #     "region": "extracted region/location or 'Not Specified'",
# #     "industry": "extracted industry sector or 'Not Specified'",
# #     "prepared_date": "date in YYYY-MM-DD or 'Not Specified'",
# #     "station_discipline": "extracted discipline or 'Not Specified'",
# #     "scope_of_work": "short summary of work scope or 'Not Specified'",
# #     "required_activities": "short summary of required activities or 'Not Specified'"
# # }}

# # **CRITICAL**: Return ONLY the JSON object. No explanation, no markdown, no extra text.
# #         """
   
# #     def _parse_json_response(self, response_text: str) -> Dict:
# #         """Parse JSON response from Azure OpenAI"""
# #         try:
# #             # Remove any markdown formatting if present
# #             if "```json" in response_text:
# #                 response_text = response_text.split("```json")[1].split("```")[0].strip()
# #             elif "```" in response_text:
# #                 response_text = re.sub(r'```[^`]*```', '', response_text).strip()
           
# #             # Clean up any remaining formatting
# #             response_text = response_text.strip()
# #             if response_text.startswith('json'):
# #                 response_text = response_text[4:].strip()
           
# #             # Parse JSON
# #             metadata = json.loads(response_text)
# #             return metadata
           
# #         except json.JSONDecodeError as e:
# #             print(f"❌ JSON parsing failed: {e}")
# #             print(f"Raw response: {response_text[:200]}...")
# #             return self._get_rfi_default_metadata()
   
# #     def _validate_rfi_metadata(self, metadata: Dict) -> Dict:
# #         """Validate and clean RFI metadata (9 new fields)"""
# #         validated = {}
       
# #         for field in self.rfi_fields:
# #             value = metadata.get(field, 'Not Specified')
           
# #             # Clean and validate the value
# #             if isinstance(value, str):
# #                 value = value.strip()
# #                 value = re.sub(r'^["\']+|["\']+$', '', value)  # Remove quotes
# #                 if not value or value.lower() in ['none', 'null', 'undefined', '', 'n/a']:
# #                     value = 'Not Specified'
# #                 elif len(value) > 500:  # Limit field length
# #                     value = value[:500] + '...'
# #             else:
# #                 value = 'Not Specified'
           
# #             validated[field] = value
       
# #         return validated
   
# #     def _get_rfi_default_metadata(self) -> Dict:
# #         """Get default RFI metadata structure (8 fields, no doc_id)"""
# #         return {
# #             'project_name': 'Not Specified',
# #             'client': 'Not Specified',
# #             'region': 'Not Specified',
# #             'industry': 'Not Specified',
# #             'prepared_date': 'Not Specified',
# #             'station_discipline': 'Not Specified',
# #             'scope_of_work': 'Not Specified',
# #             'required_activities': 'Not Specified'
# #         }
   
# #     def get_status_info(self) -> Dict:
# #         """Get status information about the RFI metadata extractor"""
# #         return {
# #             "extractor_type": "RFI_METADATA_ONLY",
# #             "fields_count": len(self.rfi_fields),
# #             "fields": self.rfi_fields,
# #             "chunking_enabled": False,
# #             "client_initialized": self.verbalizer.client is not None,
# #             "status": "ready" if self.verbalizer.client else "client_unavailable",
# #             "reuses_existing_client": True
# #         }


# import json
# import re
# from typing import Dict, List
# from .prompts import DocumentMetadataPrompts
# from processors.content_verbalizer import ContentVerbalizer
 
# class RFIExtractor:
#     """Extract RFI metadata (8 fields) from documents using Azure OpenAI - No chunking for RFI"""
   
#     def __init__(self):
#         """Initialize RFI extractor with existing Azure OpenAI client"""
#         self.verbalizer = ContentVerbalizer()  # Reuse existing client
#         self.rfi_fields = [
#             'project_name', 'client', 'region', 'industry', 
#             'prepared_date', 'station_discipline', 'scope_of_work', 'required_activities'
#         ]
       
#         print("✅ RFI Extractor initialized - NO CHUNKING MODE")
#         print(f"   📊 Fields: {len(self.rfi_fields)} RFI metadata fields")
#         print(f"   🚫 Chunking: DISABLED for RFI documents")
#         print(f"   🚫 Verbalization: DISABLED for RFI tables/images")
   
#     async def extract_metadata_only(self, text_elements: List[Dict]) -> Dict:
#         """
#         Extract ONLY RFI metadata (8 fields) from complete document text elements
#         NO CHUNKING - Only metadata extraction for indexing
#         """
#         try:
#             print("🔍 Extracting RFI metadata ONLY (No chunking, no verbalization)")
           
#             # Convert text elements to complete document text
#             complete_document_text = self._prepare_complete_document_text(text_elements)
           
#             if not complete_document_text.strip():
#                 print("⚠️ No text found in document, using RFI defaults")
#                 return self._get_rfi_default_metadata()
           
#             print(f"📊 Complete document text prepared:")
#             print(f"   📄 Pages processed: {self._count_pages(text_elements)}")
#             print(f"   📝 Text length: {len(complete_document_text)} characters")
#             print(f"   🎯 Ready for metadata-only extraction (NO CHUNKING, NO VERBALIZATION)")
           
#             # Generate metadata using Azure OpenAI (reusing existing client)
#             if self.verbalizer.client:
#                 metadata = await self._extract_metadata_with_azure_openai(complete_document_text)
#             else:
#                 print("❌ Azure OpenAI client not available")
#                 return self._get_rfi_default_metadata()
           
#             # Validate and clean metadata for RFI (8 fields)
#             validated_metadata = self._validate_rfi_metadata(metadata)
           
#             print("✅ RFI metadata-only extraction completed (NO CHUNKING, NO VERBALIZATION)")
#             return validated_metadata
           
#         except Exception as e:
#             print(f"❌ Error extracting RFI metadata: {e}")
#             return self._get_rfi_default_metadata()
   
#     def _prepare_complete_document_text(self, text_elements: List[Dict]) -> str:
#         """Convert text elements to complete document text"""
#         complete_text = ""
       
#         # Process ALL text elements from the complete document
#         for element in text_elements:
#             content = element.get('content', '').strip()
#             role = element.get('role', 'unknown')
           
#             # Add role context for better understanding
#             if content:
#                 complete_text += f"[{role}] {content}\n\n"
       
#         print(f"🔍 Processing {len(text_elements)} text elements from complete document...")
#         return complete_text
   
#     def _count_pages(self, text_elements: List[Dict]) -> str:
#         """Count total pages in document"""
#         pages = set()
#         for element in text_elements:
#             page_num = element.get('page_number', 1)
#             pages.add(page_num)
       
#         total_pages = max(pages) if pages else 1
#         return f"{total_pages}/{total_pages}"
   
#     async def _extract_metadata_with_azure_openai(self, complete_document_text: str) -> Dict:
#         """Extract RFI metadata using Azure OpenAI API with 8 fields"""
#         try:
#             print(f"📄 Sending {len(complete_document_text)} characters to LLM for RFI analysis")
#             print("🤖 Calling LLM for metadata-only extraction (8 FIELDS)...")
           
#             # Get the RFI-specific prompt with 8 fields
#             prompt = self._get_rfi_extraction_prompt(complete_document_text)
           
#             response = await self.verbalizer.client.chat.completions.create(
#                 model="gpt-4o",  # Use same model as ContentVerbalizer
#                 messages=[
#                     {"role": "system", "content": "You are an expert RFI analyst. Extract the 8 metadata fields for RFI documents. Return only valid JSON."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 max_tokens=800,  # Sufficient for 8 fields
#                 temperature=0.1  # Low temperature for consistent extraction
#             )
           
#             response_text = response.choices[0].message.content.strip()
#             print(f"📝 LLM response: {len(response_text)} characters")
           
#             # Clean and parse JSON response
#             metadata = self._parse_json_response(response_text)
           
#             print("✅ Successfully parsed metadata from LLM")
#             return metadata
               
#         except Exception as e:
#             print(f"❌ Azure OpenAI API error: {e}")
#             return self._get_rfi_default_metadata()
   
#     def _get_rfi_extraction_prompt(self, document_text: str) -> str:
#         """Get the RFI metadata extraction prompt for 8 fields"""
#         return f"""
# You are an expert RFI (Request for Information) analyzer. Extract EXACTLY 8 metadata fields from the document. Return ONLY a valid JSON object.

# **DOCUMENT TEXT:**
# {document_text}

# **EXTRACTION REQUIREMENTS:**

# 1. **project_name**:You are an expert document analyzer.
# Your task is to extract only the Project Name from the given text.
# RULES:
# Do not take any heading, section title, or metadata.
# Only extract the project name if it is explicitly mentioned in the text body.
# If the project name is not present, return exactly: "Not mentioned in document".
# Extract the project name from the document.

# 2. **client**: Identify the organization or client requesting the information. Look for "Client:", "Owner:", issuing organization names, or companies requesting the RFI."

# 3. **region**: Extract geographical location information. Look for:
#    - Countries, provinces/states, cities
#    - Project locations, service areas
#    - Regional identifiers, geographical references
   

# 4. **industry**: Determine the industry sector this RFI relates to. Common industries include:
#    - "Power & Energy", "Water & Wastewater", 
#    - "Environmental", "Infrastructure"
#    - If not found, return exactly: "Not mentioned in document"

# 5. **prepared_date**: Extract document creation date, preparation date, or issue date. Look for "Date:", "Issued:", "Prepared:", etc. Use YYYY-MM-DD format.If not found, return exactly: "Not mentioned in document"

# 6. **station_discipline**: Identify the engineering discipline or technical area. Look for:
#    - "Civil", "Electrical", "Mechanical", "Structural", "Environmental", "Process", 
#    - "Instrumentation", "Control Systems", "HVAC", "Piping", "Architectural"
#    - If not found, return exactly: "Not mentioned in document"

# 7. **scope_of_work**: You are an expert business and technical writer. 
#    Your task is to summarize the given 'Scope of Work' text into a concise paragraph, 
#    retaining all critical information and technical details. 
#    The summary will be vectorized in Azure AI Search for vector search and retrieval purposes.  
#    RULES:
#    - The summary must contain only important information and must be concise.
#    - Minimize the use of stop words and filler words.
   
   
#    Extract and summarize the scope of work content from the document.

# 8. **required_activities**: You are an expert summarizer for the section *Required Activities*. 
#    The summarized content can contain upto 7 lines of 50 words for this section.
   
#    Instructions: 
#    - **Do not miss any keywords** - Important key words include installation of equipments 
#    - **Make sure all the points are covered and summarized** 
#    - **Include all the contents from each subheadings of the section** 
#    - **Do not provide the result in bullet points/numbers** 
#    - **If no clear information is found, use "Not mentioned in RFI"** 
   
#    Extract and summarize the required activities from the document.

# **RESPONSE FORMAT - ONLY JSON:**
# {{
#     "project_name": "extracted project name or 'Not Specified'",
#     "client": "extracted client name or 'Not Specified'",
#     "region": "extracted region/location or 'Not Specified'",
#     "industry": "extracted industry sector or 'Not Specified'",
#     "prepared_date": "date in YYYY-MM-DD or 'Not Specified'",
#     "station_discipline": "extracted discipline or 'Not Specified'",
#     "scope_of_work": "short summary of work scope or 'Not Specified'",
#     "required_activities": "short summary of required activities or 'Not Specified'"
# }}

# **CRITICAL**: Return ONLY the JSON object. No explanation, no markdown, no extra text.
#         """
   
#     def _parse_json_response(self, response_text: str) -> Dict:
#         """Parse JSON response from Azure OpenAI"""
#         try:
#             # Remove any markdown formatting if present
#             if "```json" in response_text:
#                 response_text = response_text.split("```json")[1].split("```")[0].strip()
#             elif "```" in response_text:
#                 response_text = re.sub(r'```[^`]*```', '', response_text).strip()
           
#             # Clean up any remaining formatting
#             response_text = response_text.strip()
#             if response_text.startswith('json'):
#                 response_text = response_text[4:].strip()
           
#             # Parse JSON
#             metadata = json.loads(response_text)
#             return metadata
           
#         except json.JSONDecodeError as e:
#             print(f"❌ JSON parsing failed: {e}")
#             print(f"Raw response: {response_text[:200]}...")
#             return self._get_rfi_default_metadata()
   
#     def _validate_rfi_metadata(self, metadata: Dict) -> Dict:
#         """Validate and clean RFI metadata (8 fields)"""
#         validated = {}
       
#         for field in self.rfi_fields:
#             value = metadata.get(field, 'Not Specified')
           
#             # Clean and validate the value
#             if isinstance(value, str):
#                 value = value.strip()
#                 value = re.sub(r'^["\']+|["\']+$', '', value)  # Remove quotes
#                 if not value or value.lower() in ['none', 'null', 'undefined', '', 'n/a']:
#                     value = 'Not Specified'
#                 elif len(value) > 500:  # Limit field length
#                     value = value[:500] + '...'
#             else:
#                 value = 'Not Specified'
           
#             validated[field] = value
       
#         return validated
   
#     def _get_rfi_default_metadata(self) -> Dict:
#         """Get default RFI metadata structure (8 fields)"""
#         return {
#             'project_name': 'Not Specified',
#             'client': 'Not Specified',
#             'region': 'Not Specified',
#             'industry': 'Not Specified',
#             'prepared_date': 'Not Specified',
#             'station_discipline': 'Not Specified',
#             'scope_of_work': 'Not Specified',
#             'required_activities': 'Not Specified'
#         }
   
#     def get_status_info(self) -> Dict:
#         """Get status information about the RFI metadata extractor"""
#         return {
#             "extractor_type": "RFI_METADATA_ONLY",
#             "fields_count": len(self.rfi_fields),
#             "fields": self.rfi_fields,
#             "chunking_enabled": False,
#             "verbalization_enabled": False,
#             "client_initialized": self.verbalizer.client is not None,
#             "status": "ready" if self.verbalizer.client else "client_unavailable",
#             "reuses_existing_client": True
#         }

import json
import re
from typing import Dict, List
from .prompts import DocumentMetadataPrompts
from processors.content_verbalizer import ContentVerbalizer

class RFIExtractor:
   """Extract RFI metadata (8 fields) from documents using Azure OpenAI - No chunking for RFI"""
  
   def __init__(self):
       """Initialize RFI extractor with existing Azure OpenAI client"""
       self.verbalizer = ContentVerbalizer()  # Reuse existing client
       self.rfi_fields = [
           'project_name', 'client', 'region', 'industry', 
           'prepared_date', 'station_discipline', 'scope_of_work', 'required_activities'
       ]
      
       print("✅ RFI Extractor initialized - NO CHUNKING MODE")
       print(f"   📊 Fields: {len(self.rfi_fields)} RFI metadata fields")
       print(f"   🚫 Chunking: DISABLED for RFI documents")
       print(f"   🚫 Verbalization: DISABLED for RFI tables/images")
  
   async def extract_metadata_only(self, text_elements: List[Dict]) -> Dict:
       """
       Extract ONLY RFI metadata (8 fields) from complete document text elements
       NO CHUNKING - Only metadata extraction for indexing
       """
       try:
           print("🔍 Extracting RFI metadata ONLY (No chunking, no verbalization)")
          
           # Convert text elements to complete document text
           complete_document_text = self._prepare_complete_document_text(text_elements)
          
           if not complete_document_text.strip():
               print("⚠️ No text found in document, using RFI defaults")
               return self._get_rfi_default_metadata()
          
           print(f"📊 Complete document text prepared:")
           print(f"   📄 Pages processed: {self._count_pages(text_elements)}")
           print(f"   📝 Text length: {len(complete_document_text)} characters")
           print(f"   🎯 Ready for metadata-only extraction (NO CHUNKING, NO VERBALIZATION)")
          
           # Generate metadata using Azure OpenAI (reusing existing client)
           if self.verbalizer.client:
               metadata = await self._extract_metadata_with_azure_openai(complete_document_text)
           else:
               print("❌ Azure OpenAI client not available")
               return self._get_rfi_default_metadata()
          
           # Validate and clean metadata for RFI (8 fields)
           validated_metadata = self._validate_rfi_metadata(metadata)
          
           print("✅ RFI metadata-only extraction completed (NO CHUNKING, NO VERBALIZATION)")
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
       """Extract RFI metadata using Azure OpenAI API with 8 fields"""
       try:
           print(f"📄 Sending {len(complete_document_text)} characters to LLM for RFI analysis")
           print("🤖 Calling LLM for metadata-only extraction (8 FIELDS)...")
          
           # Get the RFI-specific prompt with 8 fields
           prompt = self._get_rfi_extraction_prompt(complete_document_text)
          
           response = await self.verbalizer.client.chat.completions.create(
               model="gpt-4o",  # Use same model as ContentVerbalizer
               messages=[
                   {"role": "system", "content": "You are an expert RFI analyst. Extract the 8 metadata fields for RFI documents. Return only valid JSON."},
                   {"role": "user", "content": prompt}
               ],
               max_tokens=800,  # Sufficient for 8 fields
               temperature=0.1  # Low temperature for consistent extraction
           )
          
           response_text = response.choices[0].message.content.strip()
           print(f"📝 LLM response: {len(response_text)} characters")
          
           # Clean and parse JSON response
           metadata = self._parse_json_response(response_text)
          
           print("✅ Successfully parsed metadata from LLM")
           return metadata
              
       except Exception as e:
           print(f"❌ Azure OpenAI API error: {e}")
           return self._get_rfi_default_metadata()
  
   def _get_rfi_extraction_prompt(self, document_text: str) -> str:
       """Get the RFI metadata extraction prompt for 8 fields"""
       return f"""
You are an expert RFI (Request for Information) analyzer. Extract EXACTLY 8 metadata fields from the document. Return ONLY a valid JSON object.

**DOCUMENT TEXT:**
{document_text}

**EXTRACTION REQUIREMENTS:**

1. **project_name**: You are an expert document analyzer specializing in Technical Information Packages (TIP) and engineering documents.

Your task is to extract ONLY the explicit Project Name from the document content.

SEARCH LOCATIONS (ONLY these specific fields):
1. Look for "Project Name:" label followed by the actual project name
2. Look for explicit project name fields in document metadata tables
3. Look for clearly labeled project identification sections

STRICT RULES:
- ONLY extract text that appears after explicit labels like "Project Name:", "Project:", or "Project Title:"
- DO NOT extract document titles, headers, or section headings
- DO NOT extract AR numbers, document types, or TIP titles
- DO NOT extract station names unless they explicitly appear after "Project Name:" label
- DO NOT infer or assume project names from document content
- The project name must be explicitly stated and labeled as such
- If no explicit "Project Name:" field exists, return exactly: "Not mentioned in document"

EXAMPLES of what NOT to extract:
- Document headers like "TECHNICAL INFORMATION PACKAGE"
- Section titles like "~ STATIONS – ENVIRONMENTAL ENV ~"
- AR numbers like "AR: 24127"
- General descriptions or scope statements

Extract the project name ONLY if explicitly labeled as "Project Name:" in the document.

2. **client**: Identify the organization or client requesting the information. Look for "Client:", "Owner:", issuing organization names, or companies requesting the RFI."

3. **region**: Extract geographical location information. Look for:
  - Countries, provinces/states, cities
  - Project locations, service areas
  - Regional identifiers, geographical references
  

4. **industry**: Determine the industry sector this RFI relates to. Common industries include:
  - "Power & Energy", "Water & Wastewater", 
  - "Environmental", "Infrastructure"
  - If not found, return exactly: "Not mentioned in document"

5. **prepared_date**: You are an expert document analyzer specializing in Technical Information Packages (TIP) and engineering documents.

Your task is to extract the document preparation date.

SEARCH LOCATIONS (in order of priority):
1. Look for "Date:" field in document headers or metadata tables
2. Look for "Prepared By:" sections followed by dates
3. Look for "Issue Date:", "Created:", or "Revision Date:"
4. Look for dates in document footers or headers
5. Look for dates in format MM/DD/YYYY, DD/MM/YYYY, or YYYY-MM-DD

RULES:
- Extract the most recent or primary date associated with document preparation
- Convert to YYYY-MM-DD format (e.g., 11/15/2021 becomes 2021-11-15)
- If only partial date available, use what's available (e.g., 2021-11 for November 2021)
- Ignore revision dates unless no preparation date exists
- If not found, return exactly: "Not mentioned in document"

Extract the preparation date from the document.

6. **station_discipline**: You are an expert document analyzer specializing in Technical Information Packages (TIP) and engineering documents.

Your task is to identify the engineering discipline and return ONLY the short keyword.

SEARCH LOCATIONS:
1. Document titles containing discipline codes (e.g., "~ LINES – ENVIRONMENTAL ENV ~")
2. Section headers with discipline abbreviations
3. TIP document type identifiers
4. Engineering discipline descriptions in scope of work

DISCIPLINE MAPPING (return only the short keyword):
- Environmental/Environmental Engineering → "ENV"
- Electrical/Hardware/Electrical Engineering → "ELE" 
- Mechanical/HVAC/Fire Systems → "MEC"
- Lines/Transmission Lines → "LN"
- Control/Control Systems → "CNT"
- Protection/Protective Systems → "PRT"
- Civil/Structural → "CIV"
- Auxiliary Systems → "AUX"
- Equipment → "EQP"

RULES:
- Return ONLY the 2-4 letter discipline code (e.g., "ENV", "ELE", "MEC")
- Look for discipline indicators in document structure and titles
- If multiple disciplines exist, return the primary/main one
- If not found or unclear, return exactly: "Not mentioned in document"

Identify the station discipline from the document.

7. **scope_of_work**: You are an expert business and technical writer. 
  Your task is to summarize the given 'Scope of Work' text into a concise paragraph, 
  retaining all critical information and technical details. 
  The summary will be vectorized in Azure AI Search for vector search and retrieval purposes.  
  RULES:
  - The summary must contain only important information and must be concise.
  - Minimize the use of stop words and filler words.
  
  
  Extract and summarize the scope of work content from the document.

8. **required_activities**: You are an expert summarizer for the section *Required Activities*. 
  The summarized content can contain upto 7 lines of 50 words for this section.
  
  Instructions: 
  - **Do not miss any keywords** - Important key words include installation of equipments 
  - **Make sure all the points are covered and summarized** 
  - **Include all the contents from each subheadings of the section** 
  - **Do not provide the result in bullet points/numbers** 
  - **If no clear information is found, use "Not mentioned in RFI"** 
  
  Extract and summarize the required activities from the document.

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
       """Validate and clean RFI metadata (8 fields)"""
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
       """Get default RFI metadata structure (8 fields)"""
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
           "verbalization_enabled": False,
           "client_initialized": self.verbalizer.client is not None,
           "status": "ready" if self.verbalizer.client else "client_unavailable",
           "reuses_existing_client": True
       }