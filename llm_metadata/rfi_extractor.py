

import json
import re
from typing import Dict, List
from .prompts import DocumentMetadataPrompts
from processors.content_verbalizer import ContentVerbalizer

class RFIExtractor:
    """Extract RFI metadata (enhanced component-based format with component-specific fields) from documents using Azure OpenAI"""
   
    def __init__(self):
        """Initialize RFI extractor with existing Azure OpenAI client"""
        self.verbalizer = ContentVerbalizer()  # Reuse existing client
        self.new_rfi_fields = [
            'project_name', 'client', 'industry', 'region', 'prepared_date', 'components'
        ]
        
        # Component mapping with specific fields
        self.valid_components = {
            'ELE': {
                'name': 'Electrical',
                'specific_fields': ['voltage_class', 'transformer']
            },
            'FND': {
                'name': 'Foundations', 
                'specific_fields': ['transformer_foundations', 'equipment_support_foundations']
            },
            'AUX': {
                'name': 'Auxiliary',
                'specific_fields': ['HVAC_and_FAS', 'HADs_arrangements']
            },
            'CNT': {
                'name': 'Control',
                'specific_fields': ['control_design_packages', 'SCADA_infrastructure']
            },
            'EQP': {
                'name': 'Equipment',
                'specific_fields': ['bus_systems', 'circuit_breakers_and_disconnects']
            },
            'TEL': {
                'name': 'Telecom',
                'specific_fields': ['station_lan_networks', 'scada_and_transport_infrastructure']
            },
            'PRT': {
                'name': 'Protection',
                'specific_fields': ['transformer_protection', 'breaker_protection']
            },
            'STE': {
                'name': 'Site Preparation',
                'specific_fields': ['grading_and_roads', 'drainage_and_water_management']
            },
            'STR': {
                'name': 'Structures',
                'specific_fields': ['steel_and_station_structures', 'transformer_and_equipment_structures']
            },
            'MET': {
                'name': 'Metering',
                'specific_fields': ['new_metering_installations', 'existing_metering_retain_or_update']
            },
            'LN': {
                'name': 'Lines (Transmission Lines)',
                'specific_fields': ['line_relocations_and_bypasses', 'line_rerouting_and_extensions']
            }
        }
      
        print("✅ Enhanced RFI Extractor initialized - ENHANCED COMPONENT FORMAT WITH SPECIFIC FIELDS")
        print(f"   📊 Components: {len(self.valid_components)} component types")
        print(f"   🚫 Chunking: DISABLED for RFI documents")
        print(f"   📄 First 10 Pages: ENABLED - extracts all content from pages 1-10")
        print(f"   ⚡ Component Fields: Each component has 2 specific fields + scope_of_work + required_activities")
   
    async def extract_metadata_only(self, text_elements: List[Dict], azure_di_result=None) -> Dict:
        """
        Extract ONLY RFI metadata (enhanced component format with specific fields) from complete document text elements + first 10 pages content
        NO CHUNKING - Only metadata extraction for indexing
        """
        try:
            print("🔍 Enhanced RFI metadata extraction (DI text + First 10 pages content) - ENHANCED COMPONENT FORMAT")
           
            # Step 1: Convert text elements to complete document text (existing)
            complete_document_text = self._prepare_complete_document_text(text_elements)
            print(f"📄 Document Intelligence extracted text: {len(complete_document_text)} characters")
           
            # Step 2: NEW - Extract first 10 pages comprehensive content
            first_10_pages_content = ""
            if azure_di_result:
                first_10_pages_content = self._extract_first_10_pages_comprehensive_content(azure_di_result)
                print(f"📄 First 10 pages comprehensive content: {len(first_10_pages_content)} characters")
            else:
                print("⚠️ No Azure DI result provided - skipping first 10 pages extraction")
           
            # Step 3: Combine both contents
            if first_10_pages_content:
                combined_content = f"""=== DOCUMENT INTELLIGENCE EXTRACTED TEXT ===
{complete_document_text}

=== FIRST 10 PAGES COMPREHENSIVE CONTENT ===
{first_10_pages_content}"""
                print(f"🔗 Combined content: {len(combined_content)} characters")
            else:
                combined_content = complete_document_text
                print(f"📝 Using DI text only: {len(combined_content)} characters")
           
            if not combined_content.strip():
                print("⚠️ No text found in document, using RFI defaults")
                return self._get_rfi_default_metadata()
           
            print(f"📊 Content prepared for LLM analysis:")
            print(f"   📄 Pages processed: {self._count_pages(text_elements)}")
            print(f"   📝 Total content length: {len(combined_content)} characters")
            print(f"   🎯 Ready for enhanced metadata extraction with specific component fields")
           
            # Step 4: Generate metadata using Azure OpenAI with combined content
            if self.verbalizer.client:
                metadata = await self._extract_metadata_with_azure_openai(combined_content)
            else:
                print("❌ Azure OpenAI client not available")
                return self._get_rfi_default_metadata()
           
            # Step 5: Validate and clean metadata for RFI (enhanced format)
            validated_metadata = self._validate_rfi_metadata(metadata)
           
            print("✅ Enhanced RFI metadata extraction completed (DI + First 10 Pages) - ENHANCED COMPONENT FORMAT")
            return validated_metadata
           
        except Exception as e:
            print(f"❌ Error extracting enhanced RFI metadata: {e}")
            return self._get_rfi_default_metadata()

    def _extract_first_10_pages_comprehensive_content(self, azure_di_result) -> str:
        """
        Extract ALL content from the first 10 pages of the document (or all pages if document has fewer than 10 pages)
        Includes: text paragraphs, tables, and figures from pages 1-10
        """
        try:
            first_10_pages_content = []
            
            print("🔍 Extracting comprehensive first 10 pages content...")
            
            # Step 1: Determine the maximum page number in the document
            max_page_number = self._get_document_max_page_number(azure_di_result)
            pages_to_extract = min(10, max_page_number)
            
            print(f"📄 Document has {max_page_number} pages, extracting content from pages 1-{pages_to_extract}")
            
            # Step 2: Extract text from pages 1-10 (or fewer if document is smaller)
            if hasattr(azure_di_result, 'paragraphs') and azure_di_result.paragraphs:
                pages_paragraphs = []
                for paragraph in azure_di_result.paragraphs:
                    try:
                        # Get page number safely
                        page_num = 1
                        if hasattr(paragraph, 'bounding_regions') and paragraph.bounding_regions:
                            page_num = getattr(paragraph.bounding_regions[0], 'page_number', 1)
                        
                        if 1 <= page_num <= pages_to_extract:  # Extract from pages 1 to pages_to_extract
                            content = getattr(paragraph, 'content', '')
                            role = getattr(paragraph, 'role', 'paragraph')
                            if content and content.strip():
                                pages_paragraphs.append(f"[Page {page_num}][{role}] {content.strip()}")
                    except Exception as e:
                        continue
                
                if pages_paragraphs:
                    first_10_pages_content.append(f"=== PAGES 1-{pages_to_extract} TEXT CONTENT ===")
                    first_10_pages_content.extend(pages_paragraphs)
                    print(f"📝 Extracted {len(pages_paragraphs)} paragraphs from pages 1-{pages_to_extract}")
            
            # Step 3: Extract tables from pages 1-10 (or fewer)
            if hasattr(azure_di_result, 'tables') and azure_di_result.tables:
                pages_tables = []
                for idx, table in enumerate(azure_di_result.tables):
                    try:
                        # Get page number from table
                        table_page = 1
                        if hasattr(table, 'bounding_regions') and table.bounding_regions:
                            table_page = getattr(table.bounding_regions[0], 'page_number', 1)
                        
                        if 1 <= table_page <= pages_to_extract:  # Extract from pages 1 to pages_to_extract
                            # Convert table to text representation
                            table_text = self._convert_table_to_text(table)
                            if table_text:
                                pages_tables.append(f"[Page {table_page}][TABLE_{idx+1}] {table_text}")
                    except Exception as e:
                        continue
                
                if pages_tables:
                    first_10_pages_content.append(f"\n=== PAGES 1-{pages_to_extract} TABLES ===")
                    first_10_pages_content.extend(pages_tables)
                    print(f"📊 Extracted {len(pages_tables)} tables from pages 1-{pages_to_extract}")
            
            # Step 4: Extract figures/images from pages 1-10 (or fewer)
            if hasattr(azure_di_result, 'figures') and azure_di_result.figures:
                pages_figures = []
                for idx, figure in enumerate(azure_di_result.figures):
                    try:
                        # Get page number from figure
                        figure_page = 1
                        if hasattr(figure, 'bounding_regions') and figure.bounding_regions:
                            figure_page = getattr(figure.bounding_regions[0], 'page_number', 1)
                        
                        if 1 <= figure_page <= pages_to_extract:  # Extract from pages 1 to pages_to_extract
                            # Extract figure text content
                            figure_text = self._extract_figure_content(figure, azure_di_result)
                            if figure_text:
                                pages_figures.append(f"[Page {figure_page}][FIGURE_{idx+1}] {figure_text}")
                            else:
                                pages_figures.append(f"[Page {figure_page}][FIGURE_{idx+1}] Visual content from page {figure_page}")
                    except Exception as e:
                        continue
                
                if pages_figures:
                    first_10_pages_content.append(f"\n=== PAGES 1-{pages_to_extract} FIGURES ===")
                    first_10_pages_content.extend(pages_figures)
                    print(f"🖼️ Extracted {len(pages_figures)} figures from pages 1-{pages_to_extract}")
            
            # Combine all first 10 pages content
            combined_first_10_pages = "\n\n".join(first_10_pages_content)
            
            print(f"✅ First 10 pages comprehensive extraction complete:")
            print(f"   📄 Pages extracted: 1-{pages_to_extract} (out of {max_page_number} total)")
            print(f"   📄 Total first 10 pages content: {len(combined_first_10_pages)} characters")
            
            return combined_first_10_pages
            
        except Exception as e:
            print(f"❌ Error extracting first 10 pages content: {e}")
            return ""

    def _get_document_max_page_number(self, azure_di_result) -> int:
        """Get the maximum page number in the document"""
        max_page = 1
        try:
            # Check paragraphs for page numbers
            if hasattr(azure_di_result, 'paragraphs') and azure_di_result.paragraphs:
                for paragraph in azure_di_result.paragraphs:
                    if hasattr(paragraph, 'bounding_regions') and paragraph.bounding_regions:
                        page_num = getattr(paragraph.bounding_regions[0], 'page_number', 1)
                        max_page = max(max_page, page_num)
            
            # Check tables for page numbers
            if hasattr(azure_di_result, 'tables') and azure_di_result.tables:
                for table in azure_di_result.tables:
                    if hasattr(table, 'bounding_regions') and table.bounding_regions:
                        page_num = getattr(table.bounding_regions[0], 'page_number', 1)
                        max_page = max(max_page, page_num)
            
            # Check figures for page numbers
            if hasattr(azure_di_result, 'figures') and azure_di_result.figures:
                for figure in azure_di_result.figures:
                    if hasattr(figure, 'bounding_regions') and figure.bounding_regions:
                        page_num = getattr(figure.bounding_regions[0], 'page_number', 1)
                        max_page = max(max_page, page_num)
            
            print(f"📄 Document maximum page number detected: {max_page}")
            return max_page
            
        except Exception as e:
            print(f"⚠️ Error detecting max page number: {e}, defaulting to 1")
            return 1

    def _convert_table_to_text(self, table) -> str:
        """Convert Azure DI table to text representation"""
        try:
            if not hasattr(table, 'cells') or not table.cells:
                return ""
            
            # Create a grid structure
            max_row = max(cell.row_index for cell in table.cells) + 1
            max_col = max(cell.column_index for cell in table.cells) + 1
            
            # Initialize grid
            grid = [["" for _ in range(max_col)] for _ in range(max_row)]
            
            # Fill grid with cell content
            for cell in table.cells:
                content = getattr(cell, 'content', '').strip()
                if content:
                    grid[cell.row_index][cell.column_index] = content
            
            # Convert grid to text
            table_lines = []
            for row in grid:
                if any(cell.strip() for cell in row):  # Skip empty rows
                    row_text = " | ".join(cell.strip() for cell in row)
                    table_lines.append(row_text)
            
            return "\n".join(table_lines)
            
        except Exception as e:
            print(f"⚠️ Error converting table to text: {e}")
            return ""

    def _extract_figure_content(self, figure, result) -> str:
        """Extract text content from figure using spans"""
        try:
            if hasattr(figure, 'spans') and figure.spans and hasattr(result, 'content'):
                content_parts = []
                for span in figure.spans:
                    try:
                        span_content = result.content[span.offset:span.offset + span.length]
                        if span_content.strip():
                            content_parts.append(span_content.strip())
                    except:
                        continue
                return " ".join(content_parts)
            return ""
        except Exception as e:
            return ""
   
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
      
        print(f"📝 Processing {len(text_elements)} text elements from complete document...")
        return complete_text
  
    def _count_pages(self, text_elements: List[Dict]) -> str:
        """Count total pages in document"""
        pages = set()
        for element in text_elements:
            page_num = element.get('page_number', 1)
            pages.add(page_num)
      
        total_pages = max(pages) if pages else 1
        return f"{total_pages}/{total_pages}"
  
    async def _extract_metadata_with_azure_openai(self, combined_content: str) -> Dict:
        """Extract RFI metadata using Azure OpenAI API with combined content"""
        try:
            print(f"📄 Sending {len(combined_content)} characters to LLM for enhanced RFI analysis")
            print("🤖 Calling LLM for metadata extraction (DI + First 10 Pages) - ENHANCED COMPONENT FORMAT...")
          
            # Get the RFI-specific prompt with enhanced format
            prompt = self._get_enhanced_rfi_extraction_prompt(combined_content)
          
            response = await self.verbalizer.client.chat.completions.create(
                model="gpt-4o",  # Use same model as ContentVerbalizer
                messages=[
                    {"role": "system", "content": "You are an expert RFI analyst. Extract the metadata fields for RFI documents from the comprehensive content provided. Return only valid JSON in the enhanced component-based format with component-specific fields."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,  # Increased for enhanced component structure
                temperature=0.1  # Low temperature for consistent extraction
            )
          
            response_text = response.choices[0].message.content.strip()
            print(f"📝 LLM response: {len(response_text)} characters")
          
            # Clean and parse JSON response
            metadata = self._parse_json_response(response_text)
          
            print("✅ Successfully parsed enhanced metadata from LLM - ENHANCED COMPONENT FORMAT")
            return metadata
              
        except Exception as e:
            print(f"❌ Azure OpenAI API error: {e}")
            return self._get_rfi_default_metadata()

    def _get_enhanced_rfi_extraction_prompt(self, combined_content: str) -> str:
        """Get the enhanced RFI metadata extraction prompt for enhanced component format with specific fields"""
        return f"""
You are an expert RFI (Request for Information) analyzer. Extract metadata fields from the comprehensive document content provided below. Return ONLY a valid JSON object in the ENHANCED COMPONENT-BASED FORMAT with component-specific fields.

**IMPORTANT**: The content below includes:
1. Document Intelligence extracted text (structured text elements)
2. First 10 pages comprehensive content (all text, tables, and figures from pages 1-10)

Use ALL this information to extract the most accurate metadata.

**COMBINED DOCUMENT CONTENT:**
{combined_content}

**EXTRACTION REQUIREMENTS:**

1. **project_name**: Extract ONLY the explicit Project Name from the document content.

SEARCH LOCATIONS (ONLY these specific fields):
1. Look for "Project Name:" label followed by the actual project name
2. Look for explicit project name fields in document metadata tables
3. Look for clearly labeled project identification sections
4. Check the first 10 pages comprehensive content for project titles

STRICT RULES:
- ONLY extract text that appears after explicit labels like "Project Name:", "Project:", or "Project Title:"
- DO NOT extract document titles, headers, or section headings
- DO NOT extract AR numbers, document types, or TIP titles
- DO NOT extract station names unless they explicitly appear after "Project Name:" label
- DO NOT infer or assume project names from document content
- The project name must be explicitly stated and labeled as such
- If no explicit "Project Name:" field exists, return exactly: ""

2. **client**: Identify the organization or client requesting the information. Look in both the Document Intelligence text and first 10 pages content for "Client:", "Owner:", issuing organization names, or companies requesting the RFI.

3. **industry**: Determine the industry sector this RFI relates to. Common industries include:
  - "Power & Energy", "Water & Wastewater", 
  - "Environmental", "Infrastructure"
  - Check first 10 pages content and tables for industry indicators
  - If not found, return exactly: ""

4. **region**: Extract geographical location information from all content. Look for:
  - Countries, provinces/states, cities
  - Project locations, service areas
  - Regional identifiers, geographical references
  - Check both structured text and first 10 pages tables/figures for location info
  - If not found, return exactly: ""

5. **prepared_date**: Extract the document preparation date from ALL provided content.

SEARCH LOCATIONS (in order of priority):
1. Look for "Date:" field in document headers or metadata tables (including first 10 pages tables)
2. Look for "Prepared By:" sections followed by dates
3. Look for "Issue Date:", "Created:", or "Revision Date:" in all content
4. Look for dates in document footers or headers
5. Look for dates in format MM/DD/YYYY, DD/MM/YYYY, or YYYY-MM-DD in first 10 pages content

DATE FORMAT RULES:
- ALWAYS convert to YYYY-MM-DD format (standardized ISO format)
- Examples: "11/15/2021" becomes "2021-11-15", "March 2023" becomes "2023-03-01", "2022-05-10" stays "2022-05-10"
- If only partial date available, use first day of month/year (e.g., "November 2021" becomes "2021-11-01")
- Ignore revision dates unless no preparation date exists
- If not found, return exactly: ""

6. **components**: You are an expert document analyzer specializing in Technical Information Packages (TIP) and engineering documents.

Your task is to identify the engineering components and extract ALL required fields for each component found.

VALID COMPONENTS (use ONLY these codes):
- "ELE" → Electrical (fields: voltage_class, transformer)
- "FND" → Foundations (fields: transformer_foundations, equipment_support_foundations)
- "AUX" → Auxiliary (fields: HVAC_and_FAS, HADs_arrangements)
- "CNT" → Control (fields: control_design_packages, SCADA_infrastructure)
- "EQP" → Equipment (fields: bus_systems, circuit_breakers_and_disconnects)
- "TEL" → Telecom (fields: station_lan_networks, scada_and_transport_infrastructure)
- "PRT" → Protection (fields: transformer_protection, breaker_protection)
- "STE" → Site Preparation (fields: grading_and_roads, drainage_and_water_management)
- "STR" → Structures (fields: steel_and_station_structures, transformer_and_equipment_structures)
- "MET" → Metering (fields: new_metering_installations, existing_metering_retain_or_update)
- "LN" → Lines (fields: line_relocations_and_bypasses, line_rerouting_and_extensions)

COMPONENT IDENTIFICATION RULES:
1. Look for explicit mentions of these component codes in document titles, section headers, or content
2. Look for component descriptions that match the full names (e.g., "Electrical" maps to "ELE")
3. Analyze scope of work and required activities to determine which components they relate to
4. DO NOT assume or infer components - only use components that are explicitly mentioned or clearly described
5. Each component must have ALL 4 fields: scope_of_work, required_activities, and 2 component-specific fields

For each identified component, extract ALL 4 fields:

**SCOPE_OF_WORK for each component**: You are an expert business and technical writer. 
Your task is to summarize the 'Scope of Work' related to this SPECIFIC COMPONENT from ALL the provided content into a concise paragraph, 
retaining all critical information and technical details for this component only.

When analyzing the document, note that the 'scope of work' section may appear under different but similar headings
example : ['scope and deliverables', 'Project Description', 'Purpose','General', 'Introduction', 'Scope of Services', 'Work', 'Invitation',etc]
Regardless of the variation in naming, identify and extract these sections consistently and treat them as part of 'scope of work' for this component.

The summary will be vectorized in Azure AI Search for vector search and retrieval purposes.  

RULES:
- The summary must contain only important information related to this specific component and must be concise
- Minimize the use of stop words and filler words
- Use information from both Document Intelligence text and first 10 pages comprehensive content
- Look for scope sections in tables and figures from first 10 pages that relate to this component
- Only include content that is relevant to this specific component (ELE, FND, AUX, etc.)
- If not found, return: "not mentioned in document"

**REQUIRED_ACTIVITIES for each component**: You are an expert summarizer for the section *Required Activities* for this SPECIFIC COMPONENT. 
The summarized content can contain up to 7 lines of 50 words for this section related to this component only.

When analyzing the document, note that the 'required activities' section may appear under different but similar headings
example : ['Performance of the Work', 'Work Activities', 'Site Preparation Activities', 'Installation Activities', 'Key Activities', 'Work Tasks', 'Activities', 'Work to be performed', 'Work Requirements', 'Services Required','Construction Requirements']
Regardless of the variation in naming, identify and extract these sections consistently and treat them as part of 'required_activities' for this component.

Instructions: 
- **Do not miss any keywords** - Important keywords include installation of equipment related to this component
- **Make sure all the points are covered and summarized** that relate to this specific component
- **Include all the contents from each subheading of the section** that are relevant to this component
- **Do not provide the result in bullet points/numbers** 
- **Use information from both Document Intelligence text AND first 10 pages content**
- **Check first 10 pages tables and figures for activity information** related to this component
- **Only include activities that are relevant to this specific component (ELE, FND, AUX, etc.)**
- **If no clear information is found for this component, return: "not mentioned in document"**

**COMPONENT-SPECIFIC FIELDS** (extract these based on the component type):

**FOR ELE (Electrical) Component:**
- **voltage_class**: Extract voltage levels mentioned (e.g., "115kV", "230kV", "44kV"). Look for voltage specifications in electrical equipment descriptions. Example: "115kV" or "230kV". If not found: "not mentioned in document"
- **transformer**: Extract transformer specifications (e.g., "230/115kV autotransformers (150/200/250MVA)"). Look for transformer ratings, types, and capacities. Example: "230/115kV autotransformers (150/200/250MVA)". If not found: "not mentioned in document"

**FOR FND (Foundations) Component:**
- **transformer_foundations**: Extract information about transformer foundation work (e.g., "230kV transformer foundations with spill containment"). Look for foundation specifications for transformers. If not found: "not mentioned in document"
- **equipment_support_foundations**: Extract information about equipment support foundations (e.g., "breaker foundations for 115kV/230kV SF6 breakers"). Look for foundation work for electrical equipment. If not found: "not mentioned in document"

**FOR AUX (Auxiliary) Component:**
- **HVAC_and_FAS**: Extract HVAC and Fire Alarm System information (e.g., "Review and upgrade HVAC and Fire Alarm System in existing buildings"). Look for HVAC, ventilation, and fire safety systems. If not found: "not mentioned in document"
- **HADs_arrangements**: Extract HADs (Hazardous Area Detection) arrangements (e.g., "Provide arrangement layout of HADs for new T24 transformer"). Look for hazard detection or arrangement layouts. If not found: "not mentioned in document"

**FOR CNT (Control) Component:**
- **control_design_packages**: Extract control design package information (e.g., "Provide complete control design package as per latest BES standard"). Look for control system design work. If not found: "not mentioned in document"
- **SCADA_infrastructure**: Extract SCADA infrastructure information (e.g., "Install new SCADA infrastructure at control buildings"). Look for SCADA system installations or upgrades. If not found: "not mentioned in document"

**FOR EQP (Equipment) Component:**
- **bus_systems**: Extract bus system information (e.g., "Install new 2x2303kcmil ASC drops from high-level bus to breaker disconnect switch"). Look for bus installation or modification work. If not found: "not mentioned in document"
- **circuit_breakers_and_disconnects**: Extract circuit breaker and disconnect information (e.g., "Install one new 3000A SF6 circuit breaker"). Look for breaker and disconnect switch installations. If not found: "not mentioned in document"

**FOR TEL (Telecom) Component:**
- **station_lan_networks**: Extract station LAN network information (e.g., "Design and install new BES station LAN for 230kV and 115kV systems"). Look for network infrastructure work. If not found: "not mentioned in document"
- **scada_and_transport_infrastructure**: Extract SCADA transport infrastructure (e.g., "Configure local and remote routers to provide direct SCADA connectivity"). Look for communication transport systems. If not found: "not mentioned in document"

**FOR PRT (Protection) Component:**
- **transformer_protection**: Extract transformer protection information (e.g., "Design and install protections for new 230/28kV transformers 3T1 and 3T2"). Look for transformer protection schemes. If not found: "not mentioned in document"
- **breaker_protection**: Extract breaker protection information (e.g., "230kV Circuit Switcher 3DS-MTU for outage staging"). Look for circuit breaker protection systems. If not found: "not mentioned in document"

**FOR STE (Site Preparation) Component:**
- **grading_and_roads**: Extract grading and road information (e.g., "Provide grading for 72,030 sq m new station yard including asphalt road"). Look for site grading and road construction work. If not found: "not mentioned in document"
- **drainage_and_water_management**: Extract drainage system information (e.g., "Provide one drainage system with 653m main drain, 5404m underdrain"). Look for drainage and water management systems. If not found: "not mentioned in document"

**FOR STR (Structures) Component:**
- **steel_and_station_structures**: Extract steel and station structure information (e.g., "Provide structural steel design for PowerCo TS station structures"). Look for structural steel design work. If not found: "not mentioned in document"
- **transformer_and_equipment_structures**: Extract transformer and equipment structure information (e.g., "Design structures for two 230kV transformers with spill containment area"). Look for equipment support structures. If not found: "not mentioned in document"

**FOR MET (Metering) Component:**
- **new_metering_installations**: Extract new metering installation information (e.g., "Design twelve new IESO Market Rules compliant 3EL metering installations"). Look for new meter installations. If not found: "not mentioned in document"
- **existing_metering_retain_or_update**: Extract existing metering information (e.g., "Retain existing LV metering as per Appendix E"). Look for existing meter modifications. If not found: "not mentioned in document"

**FOR LN (Lines) Component:**
- **line_relocations_and_bypasses**: Extract line relocation and bypass information (e.g., "Relocation of 115kV and 230kV lines for new West 115kV yard"). Look for transmission line relocation work. If not found: "not mentioned in document"
- **line_rerouting_and_extensions**: Extract line rerouting and extension information (e.g., "Reroute M5G to new east yard bay"). Look for line rerouting and extension projects. If not found: "not mentioned in document"

If no components can be clearly identified, return empty components object: (empty object)

**RESPONSE FORMAT - ONLY JSON:**
{{
   "project_name": "extracted project name or empty string",
   "client": "extracted client name or empty string",
   "industry": "extracted industry sector or empty string", 
   "region": "extracted region/location or empty string",
   "prepared_date": "date in YYYY-MM-DD format or empty string",
   "components": {{
     "ELE": {{
       "scope_of_work": "electrical scope content or not mentioned in document",
       "required_activities": "electrical activities content or not mentioned in document",
       "voltage_class": "voltage level or not mentioned in document",
       "transformer": "transformer specifications or not mentioned in document"
     }},
     "AUX": {{
       "scope_of_work": "auxiliary scope content or not mentioned in document", 
       "required_activities": "auxiliary activities content or not mentioned in document",
       "HVAC_and_FAS": "HVAC and FAS information or not mentioned in document",
       "HADs_arrangements": "HADs arrangement information or not mentioned in document"
     }}
   }}
}}

**CRITICAL**: 
- Return ONLY the JSON object. No explanation, no markdown, no extra text.
- Use empty strings ("") for basic fields where no information is found
- Use "not mentioned in document" for component-specific fields where no information is found
- Only include components in the components object that are actually identified in the document
- Please Do not Perform Mathematical Calculations or interpretations for any component's fields
- Date must be in YYYY-MM-DD format only
- Components must use the exact codes from the valid list above
- Each included component MUST have all 4 fields: scope_of_work, required_activities, and 2 component-specific fields

Extract the metadata now:
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
        """Validate and clean RFI metadata (enhanced format with component-specific fields)"""
        validated = {
            "project_name": "",
            "client": "",
            "industry": "", 
            "region": "",
            "prepared_date": "",
            "components": {}
        }
        
        # Validate basic fields
        for field in ['project_name', 'client', 'industry', 'region', 'prepared_date']:
            value = metadata.get(field, '')
            if isinstance(value, str):
                value = value.strip()
                # Clean up common placeholder values
                if value.lower() in ['none', 'null', 'undefined', 'n/a', 'not specified', 'not mentioned in document']:
                    value = ''
                elif len(value) > 200:  # Limit field length
                    value = value[:200] + '...'
            validated[field] = value if isinstance(value, str) else ''
        
        # Validate components with enhanced structure
        components = metadata.get('components', {})
        if isinstance(components, dict):
            for comp_code, comp_data in components.items():
                # Only allow valid component codes
                if comp_code in self.valid_components and isinstance(comp_data, dict):
                    validated_comp = {}
                    
                    # Validate common fields
                    for common_field in ['scope_of_work', 'required_activities']:
                        sub_value = comp_data.get(common_field, '')
                        if isinstance(sub_value, str):
                            sub_value = sub_value.strip()
                            if sub_value.lower() in ['none', 'null', 'undefined', 'n/a', 'not specified']:
                                sub_value = 'not mentioned in document'
                        validated_comp[common_field] = sub_value if isinstance(sub_value, str) else 'not mentioned in document'
                    
                    # Validate component-specific fields
                    specific_fields = self.valid_components[comp_code]['specific_fields']
                    for specific_field in specific_fields:
                        sub_value = comp_data.get(specific_field, '')
                        if isinstance(sub_value, str):
                            sub_value = sub_value.strip()
                            if sub_value.lower() in ['none', 'null', 'undefined', 'n/a', 'not specified']:
                                sub_value = 'not mentioned in document'
                        validated_comp[specific_field] = sub_value if isinstance(sub_value, str) else 'not mentioned in document'
                    
                    # Only add component if it has some meaningful content (not all "not mentioned in document")
                    has_content = any(
                        value and value != 'not mentioned in document' 
                        for value in validated_comp.values()
                    )
                    
                    if has_content:
                        validated['components'][comp_code] = validated_comp
        
        return validated
  
    def _get_rfi_default_metadata(self) -> Dict:
        """Get default RFI metadata structure (enhanced format)"""
        return {
            "project_name": "",
            "client": "",
            "industry": "",
            "region": "",
            "prepared_date": "",
            "components": {}
        }
  
    def get_status_info(self) -> Dict:
        """Get status information about the enhanced RFI metadata extractor"""
        return {
            "extractor_type": "RFI_METADATA_ENHANCED_COMPONENT_FORMAT_WITH_SPECIFIC_FIELDS",
            "fields_count": len(self.new_rfi_fields),
            "fields": self.new_rfi_fields,
            "components": {comp_code: comp_info for comp_code, comp_info in self.valid_components.items()},
            "total_components": len(self.valid_components),
            "chunking_enabled": False,
            "verbalization_enabled": False,
            "first_10_pages_extraction": True,
            "component_specific_fields": True,
            "fields_per_component": 4,  # scope_of_work + required_activities + 2 specific fields
            "client_initialized": self.verbalizer.client is not None,
            "status": "ready" if self.verbalizer.client else "client_unavailable",
            "reuses_existing_client": True,
            "enhancement": "DI_text + first_10_pages_comprehensive_content + enhanced_component_format_with_specific_fields"
        }