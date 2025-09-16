# import re
# import uuid
# from datetime import datetime
# from typing import List, Dict


# class SimpleChunkerRFI:
#     """Advanced text chunker with better section detection and debugging for enhanced component format with specific fields"""
    
#     def __init__(self):
#         self.section_patterns = {
#             'section_heading': r'\[ParagraphRole\.SECTION_HEADING\]',
#             'numbered_section': r'^\s*(\d+\.\d+)\s+([A-Z\s]+)',
#             'cleanup_tags': r'\[None\]\s*|\[ParagraphRole\.[^\]]+\]',
#             'page_footer': r'\[ParagraphRole\.PAGE_FOOTER\]\s*([^\[]+)'
#         }
    
#     def chunk_text_for_RFI(self, text: str, document_metadata: Dict = None, project_id: str = None) -> List[Dict]:
#         """Create chunks from text with enhanced section detection and document metadata integration - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS"""
#         print(f"DEBUG: Input text length: {len(text)}")
#         print(f"DEBUG: First 200 chars: {repr(text[:200])}")
        
#         chunks = []
#         chunk = self._create_chunk_for_RFI(document_metadata, project_id)
#         # Add deliverables_list, location, state, country to chunk if present in metadata
#         if document_metadata:
#             chunk["deliverables_list"] = document_metadata.get("deliverables_list", "not mentioned in the document")
#             chunk["location"] = document_metadata.get("location", "Not mentioned in document")
#             chunk["state"] = document_metadata.get("state", "Not mentioned in document")
#             chunk["country"] = document_metadata.get("country", "Not mentioned in document")
#         chunks.append(chunk)
#         print(f"DEBUG: Total chunks created: {len(chunks)}")
#         return chunks
    

#     def _create_chunk_for_RFI(self, document_metadata: Dict = None, project_id: str = None) -> Dict:
#         """Create chunk with comprehensive metadata including LLM-extracted document metadata - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS"""
        
#         # Use LLM-extracted metadata if available, otherwise use defaults
#         if document_metadata:
#             # Extract key fields from LLM metadata - ENHANCED FORMAT
#             project_name = document_metadata.get('project_name', '')
                
#             client = document_metadata.get('client', '')
#             if not client:
#                 client = 'hydro_one'  # Default fallback
                
#             region = document_metadata.get('region', '')
#             if not region:
#                 region = 'canada'  # Default fallback
                
#             industry = document_metadata.get('industry', '')
#             if not industry:
#                 industry = 'power_energy'  # Default fallback
                
#             prepared_date = document_metadata.get('prepared_date', '')
#             if not prepared_date:
#                 prepared_date = datetime.now().strftime('%Y-%m-%d')  # Current date as fallback

#             field_type = document_metadata.get('field_type', '')
#             if not field_type:
#                 field_type = 'Brown Field'  # Default fallback

#             voltage_class = document_metadata.get('voltage_class', '')
#             if not voltage_class:
#                 voltage_class = 'Distribution (120 V - 34.5 kV)'  # Default fallback

#             contract_types = document_metadata.get('contract_types', '')
#             if not contract_types:
#                 contract_types = 'Fixed Price'  # Default fallback

#             pricing = document_metadata.get('pricing', '')
#             if not pricing:
#                 pricing = "null"  # Default fallback
            
#             # Components - ENHANCED: Extract all components with specific fields from metadata
#             components = document_metadata.get('components', {})

#             deliverables_list = document_metadata.get('deliverables_list', 'not mentioned in the document')
#             location = document_metadata.get('location', 'Not mentioned in document')
#             state = document_metadata.get('state', 'Not mentioned in document')
#             country = document_metadata.get('country', 'Not mentioned in document')
#         else:
#             # Default values when no metadata is available
#             project_name = ''
#             client = 'hydro_one'
#             region = 'canada'
#             industry = 'power_energy'
#             prepared_date = datetime.now().strftime('%Y-%m-%d')
#             field_type = 'Brown Field'
#             voltage_class = 'Distribution (120 V - 34.5 kV)'
#             contract_types = 'Fixed Price' 
#             pricing = '3.5M USD' 
#             components = {}
#             deliverables_list = 'not mentioned in the document'
#             location = 'Not mentioned in document'
#             state = 'Not mentioned in document'
#             country = 'Not mentioned in document'

        
#         # Create chunk structure with enhanced component format (now includes component-specific fields)
#         chunk = {
#             # 'chunk_id': str(uuid.uuid4())[:8],
#             'chunk_id': str(uuid.uuid4()),
#             'project_id': project_id,
#             "project_name": project_name,
#             'content_type': 'text',
#             "client": client,
#             "region": region,
#             "location": location,
#             "state": state,
#             "country": country,
#             "prepared_date": prepared_date,
#             "field_type" : field_type,
#             "voltage_class":voltage_class,
#             "contract_types":contract_types,
#             "pricing":pricing,
#             "deliverables_list": deliverables_list,
#             "components": components # ENHANCED: Store entire components structure with specific fields
#         }
#         return chunk

#     def print_chunks(self, chunks: List[Dict]):
#         """Print chunks with detailed formatting including LLM-extracted metadata - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS"""
#         print(f"\n{'='*80}")
#         print(f"TEXT CHUNKING RESULTS WITH LLM METADATA - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS - Total chunks: {len(chunks)}")
#         print(f"{'='*80}")
        
#         if not chunks:
#             print("WARNING: NO CHUNKS WERE CREATED!")
#             print("This might indicate issues with:")
#             print("- Section splitting regex patterns")
#             print("- Text cleaning removing too much content")
#             print("- Input text format not matching expected patterns")
#             return
        
#         # Print LLM metadata summary first - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS
#         if chunks and len(chunks) > 0:
#             chunk = chunks[0]
#             print(f"\nLLM-EXTRACTED DOCUMENT METADATA (ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS):")
#             print(f"   Project Name: {chunk.get('project_name', 'N/A')}")
#             print(f"   Client: {chunk.get('client', 'N/A')}")
#             print(f"   Industry: {chunk.get('industry', 'N/A')}")
#             print(f"   Region: {chunk.get('region', 'N/A')}")
#             print(f"   Prepared Date: {chunk.get('prepared_date', 'N/A')}")
#             print(f"   Field Type: {chunk.get('field_type', 'N/A')}")
#             print(f"   Voltage Class: {chunk.get('voltage_class', 'N/A')}")
#             print(f"   Contract Types: {chunk.get('contract_types', 'N/A')}")
#             print(f"   Pricing: {chunk.get('pricing', 'N/A')}")
#             # print(f"   Components: {chunk.get('components', 'N/A')}")
           

#             # ENHANCED: Display components structure with specific fields
#             components = chunk.get('components', {})
#             if components:
#                 print(f"   Components Found: {len(components)} component(s)")
#                 for comp_code, comp_data in components.items():
#                     print(f"      • {comp_code} Component:")
                    
#                     # Show common fields
#                     scope_len = len(comp_data.get('scope_of_work', ''))
#                     activities_len = len(comp_data.get('required_activities', ''))
#                     print(f"        - Scope of Work: {scope_len} chars")
#                     print(f"        - Required Activities: {activities_len} chars")
                    
#                     # Show component-specific fields
#                     for field_name, field_value in comp_data.items():
#                         if field_name not in ['scope_of_work', 'required_activities']:
#                             field_preview = field_value[:50] + "..." if len(field_value) > 50 else field_value
#                             print(f"        - {field_name}: {field_preview}")
#             else:
#                 print(f"   Components: No components identified")

#             # print(f"   Field Type : {chunk.get('field_type', 'N/A')}")
#             # print(f"   Voltage Class: {chunk.get('voltage_class', 'N/A')}")
            
#             print(f"{'='*80}")
    
#     def debug_text_analysis(self, text: str):
#         """Debug method to analyze the input text"""
#         print(f"\n{'='*60}")
#         print("TEXT ANALYSIS DEBUG - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS")
#         print(f"{'='*60}")
#         print(f"Total text length: {len(text)} characters")
#         print(f"Total lines: {len(text.split(chr(10)))}")
        
#         # Check for section headings
#         section_headings = re.findall(self.section_patterns['section_heading'], text)
#         print(f"Section headings found: {len(section_headings)}")
        
#         # Check for numbered sections
#         numbered_sections = re.findall(self.section_patterns['numbered_section'], text, re.MULTILINE)
#         print(f"Numbered sections found: {len(numbered_sections)}")
        
#         # Show some examples
#         print("\nFirst 500 characters:")
#         print(repr(text[:500]))
        
#         print("\nLast 500 characters:")
#         print(repr(text[-500:]))
        
#         if section_headings:
#             print(f"\nSection heading examples: {section_headings[:3]}")
        
#         if numbered_sections:
#             print(f"\nNumbered section examples: {numbered_sections[:3]}")


# class TextExtractorRFI:
#     """Handle text extraction and chunking logic - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS"""
    
#     def __init__(self):
#         pass
    
    
#     def extract_rfp_id_from_text(self, text: str) -> str:
#         """
#         Extract RFP ID from page footer using regex.
#         Returns the first matching footer content, or 'unknown_rfp' if not found.
#         """
#         # Use the same pattern as in SimpleChunker
#         page_footer_pattern = r'\[ParagraphRole\.PAGE_FOOTER\]\s*([^\[]+)'
#         matches = re.findall(page_footer_pattern, text)
#         if matches:
#             rfp_id = matches[0].strip()
#             print(f"Found RFP ID in footer using regex: '{rfp_id}'")
#             return rfp_id
#         print(f"No RFP ID found in footer using regex - using default RFP ID")
#         return 'unknown_rfp'
        
#     def create_text_chunks_with_simple_chunker_for_RFI(self, text_elements: List[Dict], document_metadata: Dict, project_id: str = None) -> List[Dict]:
#         """Create text chunks using the sophisticated SimpleChunker with LLM metadata - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS"""
#         # Create all text content with role tags (like previous code)
#         all_text = "\n\n".join([f"[{elem.get('role', 'unknown')}] {elem['content']}" for elem in text_elements])
        
#         # Print original processed sections (like previous code)
#         print("\n" + "="*60)
#         print("ORIGINAL PROCESSED SECTIONS - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS")
#         print("="*60)
#         section_text = all_text.split("[ParagraphRole.SECTION_HEADING]")
#         processed_sections = []
#         for section in section_text:
#             section = section.replace("[None] ", "")
#             section = section.replace("\n\n", "")
#             processed_sections.append(section.strip())
        
#         print("Printing processed sections:\n")
#         for i, section in enumerate(processed_sections, 1):
#             if section.strip():
#                 print(f"Section {i}: {section[:200]}...")
#                 print("-" * 40)
        
#         # Advanced chunking with debugging and LLM metadata - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS
#         chunker = SimpleChunkerRFI()
#         chunks = chunker.chunk_text_for_RFI(all_text, document_metadata, project_id=project_id)
#         chunker.debug_text_analysis(all_text)
#         chunker.print_chunks(chunks)
#         print("\nENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS CHUNKS:")
#         print(chunks)
#         return chunks





import re
import uuid
from datetime import datetime
from typing import List, Dict


class SimpleChunkerRFI:
    """Advanced text chunker with better section detection and debugging for enhanced component format with specific fields"""
    
    def __init__(self):
        self.section_patterns = {
            'section_heading': r'\[ParagraphRole\.SECTION_HEADING\]',
            'numbered_section': r'^\s*(\d+\.\d+)\s+([A-Z\s]+)',
            'cleanup_tags': r'\[None\]\s*|\[ParagraphRole\.[^\]]+\]',
            'page_footer': r'\[ParagraphRole\.PAGE_FOOTER\]\s*([^\[]+)'
        }
    
    def chunk_text_for_RFI(self, text: str, document_metadata: Dict = None, project_id: str = None) -> List[Dict]:
        """Create chunks from text with enhanced section detection and document metadata integration - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS"""
        print(f"DEBUG: Input text length: {len(text)}")
        print(f"DEBUG: First 200 chars: {repr(text[:200])}")
        
        chunks = []
        chunk = self._create_chunk_for_RFI(document_metadata, project_id)
        # Add deliverables_list, location, state, country to chunk if present in metadata
        if document_metadata:
            chunk["deliverables_list"] = document_metadata.get("deliverables_list", "not mentioned in the document")
            chunk["location"] = document_metadata.get("location", "Not mentioned in document")
            chunk["state"] = document_metadata.get("state", "Not mentioned in document")
            chunk["country"] = document_metadata.get("country", "Not mentioned in document")
        chunks.append(chunk)
        print(f"DEBUG: Total chunks created: {len(chunks)}")
        return chunks
    

    def _create_chunk_for_RFI(self, document_metadata: Dict = None, project_id: str = None) -> Dict:
        """Create chunk with comprehensive metadata including LLM-extracted document metadata - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS"""
        
        # Use LLM-extracted metadata if available, otherwise use defaults
        if document_metadata:
            # Extract key fields from LLM metadata - ENHANCED FORMAT
            project_name = document_metadata.get('project_name', '')
                
            client = document_metadata.get('client', '')
            if not client:
                client = 'hydro_one'  # Default fallback
                
            region = document_metadata.get('region', '')
            if not region:
                region = 'canada'  # Default fallback
                
            industry = document_metadata.get('industry', '')
            if not industry:
                industry = 'power_energy'  # Default fallback
                
            prepared_date = document_metadata.get('prepared_date', '')
            if not prepared_date:
                prepared_date = datetime.now().strftime('%Y-%m-%d')  # Current date as fallback

            field_type = document_metadata.get('field_type', '')
            if not field_type:
                field_type = 'Brown Field'  # Default fallback

            voltage_class = document_metadata.get('voltage_class', '')
            if not voltage_class:
                voltage_class = 'Distribution (120 V - 34.5 kV)'  # Default fallback

            contract_types = document_metadata.get('contract_types', '')
            if not contract_types:
                contract_types = 'Fixed Price'  # Default fallback

            pricing = document_metadata.get('pricing', '')
            if not pricing:
                pricing = "null"  # Default fallback
            
            # Components - ENHANCED: Extract all components with specific fields from metadata
            components = document_metadata.get('components', {})

            deliverables_list = document_metadata.get('deliverables_list', 'not mentioned in the document')
            location = document_metadata.get('location', 'Not mentioned in document')
            state = document_metadata.get('state', 'Not mentioned in document')
            country = document_metadata.get('country', 'Not mentioned in document')
        else:
            # Default values when no metadata is available
            project_name = ''
            client = 'hydro_one'
            region = 'canada'
            industry = 'power_energy'
            prepared_date = datetime.now().strftime('%Y-%m-%d')
            field_type = 'Brown Field'
            voltage_class = 'Distribution (120 V - 34.5 kV)'
            contract_types = 'Fixed Price' 
            pricing = '3.5M USD' 
            components = {}
            deliverables_list = 'not mentioned in the document'
            location = 'Not mentioned in document'
            state = 'Not mentioned in document'
            country = 'Not mentioned in document'

        
        # Create chunk structure with enhanced component format (now includes component-specific fields)
        chunk = {
            # 'chunk_id': str(uuid.uuid4())[:8],
            'chunk_id': str(uuid.uuid4()),
            'project_id': project_id,
            "project_name": project_name,
            'content_type': 'text',
            "client": client,
            "region": region,
            "location": location,
            "state": state,
            "country": country,
            "prepared_date": prepared_date,
            "field_type" : field_type,
            "voltage_class":voltage_class,
            "contract_types":contract_types,
            "pricing":pricing,
            "deliverables_list": deliverables_list,
            "components": components # ENHANCED: Store entire components structure with specific fields
        }
        return chunk

    def print_chunks(self, chunks: List[Dict]):
        """Print chunks with detailed formatting including LLM-extracted metadata - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS"""
        print(f"\n{'='*80}")
        print(f"TEXT CHUNKING RESULTS WITH LLM METADATA - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS - Total chunks: {len(chunks)}")
        print(f"{'='*80}")
        
        if not chunks:
            print("WARNING: NO CHUNKS WERE CREATED!")
            print("This might indicate issues with:")
            print("- Section splitting regex patterns")
            print("- Text cleaning removing too much content")
            print("- Input text format not matching expected patterns")
            return
        
        # Print LLM metadata summary first - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS
        if chunks and len(chunks) > 0:
            chunk = chunks[0]
            print(f"\nLLM-EXTRACTED DOCUMENT METADATA (ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS):")
            print(f"   Project Name: {chunk.get('project_name', 'N/A')}")
            print(f"   Client: {chunk.get('client', 'N/A')}")
            print(f"   Industry: {chunk.get('industry', 'N/A')}")
            print(f"   Region: {chunk.get('region', 'N/A')}")
            print(f"   Prepared Date: {chunk.get('prepared_date', 'N/A')}")
            print(f"   Field Type: {chunk.get('field_type', 'N/A')}")
            print(f"   Voltage Class: {chunk.get('voltage_class', 'N/A')}")
            print(f"   Contract Types: {chunk.get('contract_types', 'N/A')}")
            print(f"   Pricing: {chunk.get('pricing', 'N/A')}")
            # print(f"   Components: {chunk.get('components', 'N/A')}")
            print(f"   Location: {chunk.get('location', 'N/A')}")
            print(f"   State: {chunk.get('state', 'N/A')}")
            print(f"   Country: {chunk.get('country', 'N/A')}")
            deliverables = chunk.get('deliverables_list', '')
            deliverables_preview = ' '.join(deliverables.split()[:100])
            print(f"   Deliverables List (first 100 words): {deliverables_preview}")
           

            # ENHANCED: Display components structure with specific fields
            components = chunk.get('components', {})
            if components:
                print(f"   Components Found: {len(components)} component(s)")
                for comp_code, comp_data in components.items():
                    print(f"      • {comp_code} Component:")
                    
                    # Show common fields
                    scope_len = len(comp_data.get('scope_of_work', ''))
                    activities_len = len(comp_data.get('required_activities', ''))
                    print(f"        - Scope of Work: {scope_len} chars")
                    print(f"        - Required Activities: {activities_len} chars")
                    
                    # Show component-specific fields
                    for field_name, field_value in comp_data.items():
                        if field_name not in ['scope_of_work', 'required_activities']:
                            field_preview = field_value[:50] + "..." if len(field_value) > 50 else field_value
                            print(f"        - {field_name}: {field_preview}")
            else:
                print(f"   Components: No components identified")

#             # print(f"   Field Type : {chunk.get('field_type', 'N/A')}")
#             # print(f"   Voltage Class: {chunk.get('voltage_class', 'N/A')}")
            
#             print(f"{'='*80}")
    
    def debug_text_analysis(self, text: str):
        """Debug method to analyze the input text"""
        print(f"\n{'='*60}")
        print("TEXT ANALYSIS DEBUG - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS")
        print(f"{'='*60}")
        print(f"Total text length: {len(text)} characters")
        print(f"Total lines: {len(text.split(chr(10)))}")
        
        # Check for section headings
        section_headings = re.findall(self.section_patterns['section_heading'], text)
        print(f"Section headings found: {len(section_headings)}")
        
        # Check for numbered sections
        numbered_sections = re.findall(self.section_patterns['numbered_section'], text, re.MULTILINE)
        print(f"Numbered sections found: {len(numbered_sections)}")
        
        # Show some examples
        print("\nFirst 500 characters:")
        print(repr(text[:500]))
        
        print("\nLast 500 characters:")
        print(repr(text[-500:]))
        
        if section_headings:
            print(f"\nSection heading examples: {section_headings[:3]}")
        
        if numbered_sections:
            print(f"\nNumbered section examples: {numbered_sections[:3]}")


class TextExtractorRFI:
    """Handle text extraction and chunking logic - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS"""
    
    def __init__(self):
        pass
    
    
    def extract_rfp_id_from_text(self, text: str) -> str:
        """
        Extract RFP ID from page footer using regex.
        Returns the first matching footer content, or 'unknown_rfp' if not found.
        """
        # Use the same pattern as in SimpleChunker
        page_footer_pattern = r'\[ParagraphRole\.PAGE_FOOTER\]\s*([^\[]+)'
        matches = re.findall(page_footer_pattern, text)
        if matches:
            rfp_id = matches[0].strip()
            print(f"Found RFP ID in footer using regex: '{rfp_id}'")
            return rfp_id
        print(f"No RFP ID found in footer using regex - using default RFP ID")
        return 'unknown_rfp'
        
    def create_text_chunks_with_simple_chunker_for_RFI(self, text_elements: List[Dict], document_metadata: Dict, project_id: str = None) -> List[Dict]:
        """Create text chunks using the sophisticated SimpleChunker with LLM metadata - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS"""
        # Create all text content with role tags (like previous code)
        all_text = "\n\n".join([f"[{elem.get('role', 'unknown')}] {elem['content']}" for elem in text_elements])
        
        # Print original processed sections (like previous code)
        print("\n" + "="*60)
        print("ORIGINAL PROCESSED SECTIONS - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS")
        print("="*60)
        section_text = all_text.split("[ParagraphRole.SECTION_HEADING]")
        processed_sections = []
        for section in section_text:
            section = section.replace("[None] ", "")
            section = section.replace("\n\n", "")
            processed_sections.append(section.strip())
        
        print("Printing processed sections:\n")
        for i, section in enumerate(processed_sections, 1):
            if section.strip():
                print(f"Section {i}: {section[:200]}...")
                print("-" * 40)
        
        # Advanced chunking with debugging and LLM metadata - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS
        chunker = SimpleChunkerRFI()
        chunks = chunker.chunk_text_for_RFI(all_text, document_metadata, project_id=project_id)
        chunker.debug_text_analysis(all_text)
        chunker.print_chunks(chunks)
        print("\nENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS CHUNKS:")
        print(chunks)
        return chunks