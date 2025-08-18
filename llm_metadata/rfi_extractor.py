

# import json
# import re
# from typing import Dict, List
# from .prompts import DocumentMetadataPrompts
# from processors.content_verbalizer import ContentVerbalizer

# class RFIExtractor:
#     """Extract RFI metadata (8 fields) from documents using Azure OpenAI - Reuses existing client"""
    
#     def __init__(self):
#         """Initialize RFI extractor with existing Azure OpenAI client"""
#         self.verbalizer = ContentVerbalizer()  # Reuse existing client - no duplicate initialization
#         self.rfi_fields = [
#             'document_id', 'client_name', 'domain_category', 'service_category',
#             'project_title', 'rfi_description', 'submission_date', 'duration'
#         ]
        
#         # Print initialization info without duplicate client setup
#         print("✅ RFI Extractor initialized - reusing existing Azure OpenAI client")
#         print(f"   📊 Fields: {len(self.rfi_fields)} RFI metadata fields")
#         print(f"   🔄 Client reuse: ✅ No duplicate initialization")
    
#     def extract_metadata(self, text_elements: List[Dict]) -> Dict:
#         """
#         Extract RFI metadata (8 fields) from complete document text elements
        
#         Args:
#             text_elements: List of text elements from document (complete document, not just first 2 pages)
            
#         Returns:
#             Dict: Extracted metadata with 8 required fields for RFI
#         """
#         try:
#             print("🔍 Extracting RFI metadata from COMPLETE document using LLM")
            
#             # Convert text elements to complete document text
#             complete_document_text = self._prepare_complete_document_text(text_elements)
            
#             if not complete_document_text.strip():
#                 print("⚠️ No text found in document, using RFI defaults")
#                 return self._get_rfi_default_metadata()
            
#             print(f"📊 Complete document text prepared:")
#             print(f"   📄 Pages processed: {self._count_pages(text_elements)}")
#             print(f"   📝 Text length: {len(complete_document_text)} characters")
#             print(f"   🎯 Ready for comprehensive metadata extraction")
            
#             # Generate metadata using Azure OpenAI (reusing existing client)
#             if self.verbalizer.client:
#                 metadata = self._extract_metadata_with_azure_openai(complete_document_text)
#             else:
#                 print("❌ Azure OpenAI client not available")
#                 return self._get_rfi_default_metadata()
            
#             # Validate and clean metadata for RFI (8 fields)
#             validated_metadata = self._validate_rfi_metadata(metadata)
            
#             print("✅ RFI metadata extraction completed from complete document")
#             return validated_metadata
            
#         except Exception as e:
#             print(f"❌ Error extracting RFI metadata: {e}")
#             return self._get_rfi_default_metadata()
    
#     def _prepare_complete_document_text(self, text_elements: List[Dict]) -> str:
#         """Convert text elements to complete document text (not just first 2 pages)"""
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
    
#     def _extract_metadata_with_azure_openai(self, complete_document_text: str) -> Dict:
#         """Extract RFI metadata using Azure OpenAI API (reusing existing client)"""
#         try:
#             print(f"📄 Sending {len(complete_document_text)} characters to LLM for RFI analysis")
#             print("🤖 Calling LLM for comprehensive metadata extraction...")
            
#             # Get the RFI-specific prompt (6 basic fields first)
#             prompt = DocumentMetadataPrompts.get_rfi_extraction_prompt(complete_document_text)
            
#             response = self.verbalizer.client.chat.completions.create(
#                 model="gpt-4",  # Use same model as ContentVerbalizer
#                 messages=[
#                     {"role": "system", "content": "You are an expert RFI analyst. Extract metadata and match domains/services to the exact lists provided. Return only valid JSON with the 8 required fields for RFI documents."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 max_tokens=1000,  # Sufficient for RFI basic fields
#                 temperature=0.1  # Low temperature for consistent extraction
#             )
            
#             response_text = response.choices[0].message.content.strip()
#             print(f"📝 LLM response: {len(response_text)} characters")
            
#             # Clean and parse JSON response
#             metadata = self._parse_json_response(response_text)
            
#             # Generate comprehensive RFI description using separate prompt
#             print("🤖 Generating comprehensive RFI description (800 words summary)...")
#             rfi_description = self._generate_rfi_description(complete_document_text)
#             if rfi_description:
#                 metadata['rfi_description'] = rfi_description
#                 print(f"✅ RFI description generated: {len(rfi_description)} characters")
            
#             # Extract project duration using separate prompt  
#             print("🕐 Extracting project duration...")
#             duration = self._extract_project_duration(complete_document_text)
#             if duration:
#                 metadata['duration'] = duration
#                 print(f"✅ Duration extracted: {duration}")
            
#             print("✅ Successfully parsed metadata from LLM")
#             return metadata
                
#         except Exception as e:
#             print(f"❌ Azure OpenAI API error: {e}")
#             return self._get_rfi_default_metadata()
    
#     def _generate_rfi_description(self, complete_document_text: str) -> str:
#         """Generate comprehensive 800-word RFI description using separate prompt"""
#         try:
#             description_prompt = DocumentMetadataPrompts.get_rfi_description_prompt(complete_document_text)
            
#             response = self.verbalizer.client.chat.completions.create(
#                 model="gpt-4",
#                 messages=[
#                     {"role": "system", "content": "You are an expert technical writer specializing in power infrastructure projects. Write flowing paragraph summaries only."},
#                     {"role": "user", "content": description_prompt}
#                 ],
#                 max_tokens=1200,  # Sufficient for 800-word description
#                 temperature=0.3  # Slightly higher for creative writing
#             )
            
#             return response.choices[0].message.content.strip()
            
#         except Exception as e:
#             print(f"❌ Error generating RFI description: {e}")
#             return "Not mentioned in RFI"
    
#     def _extract_project_duration(self, complete_document_text: str) -> str:
#         """Extract project duration using separate prompt"""
#         try:
#             duration_prompt = DocumentMetadataPrompts.get_duration_extraction_prompt(complete_document_text)
            
#             response = self.verbalizer.client.chat.completions.create(
#                 model="gpt-4",
#                 messages=[
#                     {"role": "system", "content": "You are an expert at extracting project duration from documents. Return only the duration text."},
#                     {"role": "user", "content": duration_prompt}
#                 ],
#                 max_tokens=100,  # Short response for duration only
#                 temperature=0.1  # Low temperature for precise extraction
#             )
            
#             duration = response.choices[0].message.content.strip()
#             # Clean any extra formatting
#             duration = duration.replace('"', '').replace("'", '').strip()
            
#             return duration
            
#         except Exception as e:
#             print(f"❌ Error extracting duration: {e}")
#             return "Not Specified"
    
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
#                     if field in ['domain_category', 'service_category', 'rfi_description']:
#                         value = 'Not mentioned in RFI'
#                     else:
#                         value = 'Not Specified'
#                 elif len(value) > 500 and field != 'rfi_description':  # rfi_description can be longer
#                     value = value[:500] + '...'
#             else:
#                 if field in ['domain_category', 'service_category', 'rfi_description']:
#                     value = 'Not mentioned in RFI'
#                 else:
#                     value = 'Not Specified'
            
#             validated[field] = value
        
#         return validated
    
#     def _get_rfi_default_metadata(self) -> Dict:
#         """Get default RFI metadata structure (8 fields)"""
#         return {
#             'document_id': 'Not Specified',
#             'client_name': 'Not Specified',
#             'domain_category': 'Not mentioned in RFI',
#             'service_category': 'Not mentioned in RFI',
#             'project_title': 'Not Specified',
#             'rfi_description': 'Not mentioned in RFI',
#             'submission_date': 'Not Specified',
#             'duration': 'Not Specified'
#         }
    
#     def get_status_info(self) -> Dict:
#         """Get status information about the RFI metadata extractor"""
#         return {
#             "extractor_type": "RFI",
#             "fields_count": len(self.rfi_fields),
#             "fields": self.rfi_fields,
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
    """Extract RFI metadata (8 fields) from documents using Azure OpenAI - Reuses existing client"""
   
    def __init__(self):
        """Initialize RFI extractor with existing Azure OpenAI client"""
        self.verbalizer = ContentVerbalizer()  # Reuse existing client - no duplicate initialization
        self.rfi_fields = [
            'document_id', 'client_name', 'domain_category', 'service_category',
            'project_title', 'rfi_description', 'submission_date', 'duration'
        ]
       
        # Print initialization info without duplicate client setup
        print("✅ RFI Extractor initialized - reusing existing Azure OpenAI client")
        print(f"   📊 Fields: {len(self.rfi_fields)} RFI metadata fields")
        print(f"   🔄 Client reuse: ✅ No duplicate initialization")
   
    # MODIFIED LINE 1: Changed from sync to async
    # OLD: def extract_metadata(self, text_elements: List[Dict]) -> Dict:
    # NEW: async def extract_metadata(self, text_elements: List[Dict]) -> Dict:
    async def extract_metadata(self, text_elements: List[Dict]) -> Dict:
        """
        Extract RFI metadata (8 fields) from complete document text elements
       
        Args:
            text_elements: List of text elements from document (complete document, not just first 2 pages)
           
        Returns:
            Dict: Extracted metadata with 8 required fields for RFI
        """
        try:
            print("🔍 Extracting RFI metadata from COMPLETE document using LLM")
           
            # Convert text elements to complete document text
            complete_document_text = self._prepare_complete_document_text(text_elements)
           
            if not complete_document_text.strip():
                print("⚠️ No text found in document, using RFI defaults")
                return self._get_rfi_default_metadata()
           
            print(f"📊 Complete document text prepared:")
            print(f"   📄 Pages processed: {self._count_pages(text_elements)}")
            print(f"   📝 Text length: {len(complete_document_text)} characters")
            print(f"   🎯 Ready for comprehensive metadata extraction")
           
            # Generate metadata using Azure OpenAI (reusing existing client)
            if self.verbalizer.client:
                # MODIFIED LINE 2: Added await for async call
                # OLD: metadata = self._extract_metadata_with_azure_openai(complete_document_text)
                # NEW: metadata = await self._extract_metadata_with_azure_openai(complete_document_text)
                metadata = await self._extract_metadata_with_azure_openai(complete_document_text)
            else:
                print("❌ Azure OpenAI client not available")
                return self._get_rfi_default_metadata()
           
            # Validate and clean metadata for RFI (8 fields)
            validated_metadata = self._validate_rfi_metadata(metadata)
           
            print("✅ RFI metadata extraction completed from complete document")
            return validated_metadata
           
        except Exception as e:
            print(f"❌ Error extracting RFI metadata: {e}")
            return self._get_rfi_default_metadata()
   
    def _prepare_complete_document_text(self, text_elements: List[Dict]) -> str:
        """Convert text elements to complete document text (not just first 2 pages)"""
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
   
    # MODIFIED LINE 3: Changed from sync to async
    # OLD: def _extract_metadata_with_azure_openai(self, complete_document_text: str) -> Dict:
    # NEW: async def _extract_metadata_with_azure_openai(self, complete_document_text: str) -> Dict:
    async def _extract_metadata_with_azure_openai(self, complete_document_text: str) -> Dict:
        """Extract RFI metadata using Azure OpenAI API (reusing existing client)"""
        try:
            print(f"📄 Sending {len(complete_document_text)} characters to LLM for RFI analysis")
            print("🤖 Calling LLM for comprehensive metadata extraction...")
           
            # Get the RFI-specific prompt (6 basic fields first)
            prompt = DocumentMetadataPrompts.get_rfi_extraction_prompt(complete_document_text)
           
            # MODIFIED LINE 4: Added await for async API call
            # OLD: response = self.verbalizer.client.chat.completions.create(
            # NEW: response = await self.verbalizer.client.chat.completions.create(
            response = await self.verbalizer.client.chat.completions.create(
                model="gpt-4o",  # Use same model as ContentVerbalizer
                messages=[
                    {"role": "system", "content": "You are an expert RFI analyst. Extract metadata and match domains/services to the exact lists provided. Return only valid JSON with the 8 required fields for RFI documents."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,  # Sufficient for RFI basic fields
                temperature=0.1  # Low temperature for consistent extraction
            )
           
            response_text = response.choices[0].message.content.strip()
            print(f"📝 LLM response: {len(response_text)} characters")
           
            # Clean and parse JSON response
            metadata = self._parse_json_response(response_text)
           
            # Generate comprehensive RFI description using separate prompt
            print("🤖 Generating comprehensive RFI description (800 words summary)...")
            # MODIFIED LINE 5: Added await for async call
            # OLD: rfi_description = self._generate_rfi_description(complete_document_text)
            # NEW: rfi_description = await self._generate_rfi_description(complete_document_text)
            rfi_description = await self._generate_rfi_description(complete_document_text)
            if rfi_description:
                metadata['rfi_description'] = rfi_description
                print(f"✅ RFI description generated: {len(rfi_description)} characters")
           
            # Extract project duration using separate prompt  
            print("🕐 Extracting project duration...")
            # MODIFIED LINE 6: Added await for async call
            # OLD: duration = self._extract_project_duration(complete_document_text)
            # NEW: duration = await self._extract_project_duration(complete_document_text)
            duration = await self._extract_project_duration(complete_document_text)
            if duration:
                metadata['duration'] = duration
                print(f"✅ Duration extracted: {duration}")
           
            print("✅ Successfully parsed metadata from LLM")
            return metadata
               
        except Exception as e:
            print(f"❌ Azure OpenAI API error: {e}")
            return self._get_rfi_default_metadata()
   
    # MODIFIED LINE 7: Changed from sync to async
    # OLD: def _generate_rfi_description(self, complete_document_text: str) -> str:
    # NEW: async def _generate_rfi_description(self, complete_document_text: str) -> str:
    async def _generate_rfi_description(self, complete_document_text: str) -> str:
        """Generate comprehensive 800-word RFI description using separate prompt"""
        try:
            description_prompt = DocumentMetadataPrompts.get_rfi_description_prompt(complete_document_text)
           
            # MODIFIED LINE 8: Added await for async API call
            # OLD: response = self.verbalizer.client.chat.completions.create(
            # NEW: response = await self.verbalizer.client.chat.completions.create(
            response = await self.verbalizer.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert technical writer specializing in power infrastructure projects. Write flowing paragraph summaries only."},
                    {"role": "user", "content": description_prompt}
                ],
                max_tokens=1200,  # Sufficient for 800-word description
                temperature=0.3  # Slightly higher for creative writing
            )
           
            return response.choices[0].message.content.strip()
           
        except Exception as e:
            print(f"❌ Error generating RFI description: {e}")
            return "Not mentioned in RFI"
   
    # MODIFIED LINE 9: Changed from sync to async
    # OLD: def _extract_project_duration(self, complete_document_text: str) -> str:
    # NEW: async def _extract_project_duration(self, complete_document_text: str) -> str:
    async def _extract_project_duration(self, complete_document_text: str) -> str:
        """Extract project duration using separate prompt"""
        try:
            duration_prompt = DocumentMetadataPrompts.get_duration_extraction_prompt(complete_document_text)
           
            # MODIFIED LINE 10: Added await for async API call
            # OLD: response = self.verbalizer.client.chat.completions.create(
            # NEW: response = await self.verbalizer.client.chat.completions.create(
            response = await self.verbalizer.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting project duration from documents. Return only the duration text."},
                    {"role": "user", "content": duration_prompt}
                ],
                max_tokens=100,  # Short response for duration only
                temperature=0.1  # Low temperature for precise extraction
            )
           
            duration = response.choices[0].message.content.strip()
            # Clean any extra formatting
            duration = duration.replace('"', '').replace("'", '').strip()
           
            return duration
           
        except Exception as e:
            print(f"❌ Error extracting duration: {e}")
            return "Not Specified"
   
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
                    if field in ['domain_category', 'service_category', 'rfi_description']:
                        value = 'Not mentioned in RFI'
                    else:
                        value = 'Not Specified'
                elif len(value) > 500 and field != 'rfi_description':  # rfi_description can be longer
                    value = value[:500] + '...'
            else:
                if field in ['domain_category', 'service_category', 'rfi_description']:
                    value = 'Not mentioned in RFI'
                else:
                    value = 'Not Specified'
           
            validated[field] = value
       
        return validated
   
    def _get_rfi_default_metadata(self) -> Dict:
        """Get default RFI metadata structure (8 fields)"""
        return {
            'document_id': 'Not Specified',
            'client_name': 'Not Specified',
            'domain_category': 'Not mentioned in RFI',
            'service_category': 'Not mentioned in RFI',
            'project_title': 'Not Specified',
            'rfi_description': 'Not mentioned in RFI',
            'submission_date': 'Not Specified',
            'duration': 'Not Specified'
        }
   
    def get_status_info(self) -> Dict:
        """Get status information about the RFI metadata extractor"""
        return {
            "extractor_type": "RFI",
            "fields_count": len(self.rfi_fields),
            "fields": self.rfi_fields,
            "client_initialized": self.verbalizer.client is not None,
            "status": "ready" if self.verbalizer.client else "client_unavailable",
            "reuses_existing_client": True
        }
 