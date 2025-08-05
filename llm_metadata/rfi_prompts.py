"""
RFI-specific prompt templates for metadata extraction
Contains prompts for RFI document analysis with 8 metadata fields
"""

class RFIPrompts:
    """RFI-specific prompt templates"""
    
    @staticmethod
    def get_rfi_metadata_extraction_prompt(full_document_text: str) -> str:
        """
        Get the RFI metadata extraction prompt for basic fields
        
        Args:
            full_document_text: Complete text content from RFI document
            
        Returns:
            str: Complete metadata extraction prompt for RFI with 6 basic fields
        """
        return f"""
You are an expert RFI (Request for Information) document analyst. Extract EXACTLY 6 basic metadata fields from the RFI document. Return ONLY a valid JSON object.

**FULL RFI DOCUMENT TEXT:**
{full_document_text}

**EXTRACTION REQUIREMENTS:**

1. **document_id**: Find the RFI document ID, reference number, or document identifier. Look for:
   - "RFI ID:", "Document ID:", "Reference Number:", "RFI No.:", "RFI Ref:"
   - "Document Reference:", "RFI Number:", "Identifier:", "Doc ID:"
   - Any alphanumeric identifier that uniquely identifies this RFI
   - Header information, document titles, or reference sections
   
   If no specific document ID is found, use "Not Specified"

2. **client_name**: Identify the organization requesting the information. Look for:
   - "To:", "Client:", "From:", recipient names
   - Organizations issuing the RFI
   - Company names, government departments, or agencies
   - Header information showing the requesting organization
   
   If no clear client is found, use "Not Specified"

3. **project_title**: Find the main project name, RFI title, or subject. Look for:
   - Document titles, project names, or RFI subjects
   - "Subject:", "Project:", "Re:", "Title:"
   - Main heading or purpose of the RFI
   - Project codes or identifiers
   
   If no clear project title is found, use "Not Specified"

4. **submission_date**: Extract document dates. Look for:
   - Submission dates, RFI dates, or document creation dates
   - "Date:", "Submitted on:", "RFI Date:", "Document Date:"
   - Any relevant date mentioned in the RFI
   - Use YYYY-MM-DD format
   
   If no date is found, use "Not Specified"

5. **domain_category**: MUST select from these Power Business Unit domains ONLY:
   - "Renewable Energy"
   - "Energy Infrastructure & Grid Modernization"  
   - "Conventional Power Systems"
   - "Resource Sector Electrification & Integration"
   - "Environmental & Regulatory Services"
   - "International & Remote Community Energy Projects"
   
   Analyze the RFI content to determine which domain it belongs to based on:
   - Technical requirements mentioned
   - Services being requested
   - Project scope and objectives
   - Industry context and applications
   
   If no clear domain is found, use "Not mentioned in RFI"

6. **service_category**: MUST select from these Power Business Unit services ONLY:

   **For Renewable Energy:**
   - "Site selection and feasibility studies"
   - "Resource assessment (wind speed, solar irradiation, hydrology)"
   - "Environmental permitting and approvals"
   - "Detailed electrical and civil engineering design"
   - "Grid interconnection and impact studies"
   - "Independent Engineer (IE) and Owner's Engineer (OE) services"
   - "Procurement and construction oversight"
   - "SCADA and control systems integration"

   **For Energy Infrastructure & Grid Modernization:**
   - "Power system planning (load flow, short-circuit, contingency analysis)"
   - "Substation layout and protection design"
   - "Smart meter and grid automation consulting"
   - "Renewable integration into existing grids"
   - "Distributed energy system modeling and control"
   - "Grid modernization roadmap development"
   - "SCADA and communication systems design"
   - "Arc flash and grounding studies"

   **For Conventional Power Systems:**
   - "Retrofit design and emissions reduction planning"
   - "Regulatory compliance and license support"
   - "Equipment and system upgrade engineering"
   - "Decommissioning and remediation planning"
   - "Safety analysis and QA/QC inspections"
   - "Performance optimization and life extension analysis"

   **For Resource Sector Electrification & Integration:**
   - "Power supply studies for remote operations"
   - "Diesel replacement with renewables or hybrid systems"
   - "Transmission line routing and permitting"
   - "On-site energy storage and backup systems"
   - "Load forecasting and reliability assessments"
   - "Grid connection strategy and economic analysis"

   **For Environmental & Regulatory Services:**
   - "Environmental impact assessments (EIA)"
   - "Public and Indigenous consultation support"
   - "Permitting (federal, provincial, municipal)"
   - "Climate risk and adaptation planning"
   - "Biodiversity, habitat, and wildlife impact studies"
   - "GHG emissions and carbon accounting"
   - "Sustainability/ESG reporting and disclosures"

   **For International & Remote Community Energy Projects:**
   - "Off-grid and hybrid system design"
   - "Stakeholder and community engagement"
   - "Socioeconomic impact assessments"
   - "Electrification master planning"
   - "Capacity building and training"
   - "Procurement and construction monitoring"

   If no matching service is found, use "Not mentioned in RFI"

**ANALYSIS FOCUS:**
- Scan ALL pages of the RFI document for identifying information
- Look for document headers, titles, and reference sections
- Identify the requesting organization and project context
- Match RFI content to Power Business Unit domains and services
- Extract dates from any part of the document
- Focus on the main purpose and scope of the RFI

**RESPONSE FORMAT - ONLY JSON:**
{{
    "document_id": "extracted document ID or 'Not Specified'",
    "client_name": "extracted client name or 'Not Specified'", 
    "project_title": "extracted project title or 'Not Specified'",
    "submission_date": "date in YYYY-MM-DD or 'Not Specified'",
    "domain_category": "exact domain from Power Business Unit list or 'Not mentioned in RFI'",
    "service_category": "exact service from Power Business Unit list or 'Not mentioned in RFI'"
}}

**CRITICAL**: Return ONLY the JSON object with these 6 fields. No explanation, no markdown, no extra text. Do NOT include rfi_description or duration fields in this response.
        """
    
    @staticmethod
    def get_rfi_description_prompt(full_document_text: str) -> str:
        """
        Get the RFI description generation prompt (800 words comprehensive summary)
        
        Args:
            full_document_text: Complete text content from RFI document
            
        Returns:
            str: Prompt for generating comprehensive RFI description
        """
        return f"""
You are an expert technical writer specializing in power infrastructure projects. Write a comprehensive 800-word summary of this RFI document in flowing paragraph format.

**CRITICAL: Write ONLY in paragraph format - NO JSON, NO bullet points, NO structured data.**

**RFI DOCUMENT CONTENT:**
{full_document_text}

**WRITING INSTRUCTIONS:**
Write exactly 800 words of flowing prose that covers:

- Document purpose and requesting organization
- Project scope, location, and technical requirements  
- Equipment specifications and infrastructure details
- Engineering standards and compliance requirements
- Information being requested from contractors
- Submission requirements and timeline
- Technical expertise and experience requirements
- All content from tables, images, and structured data

**WRITING STYLE:**
- Use natural paragraph transitions
- Write in third person professional tone
- Include specific technical details, numbers, and dates
- Maintain flow between topics
- Focus on power/energy infrastructure context

**SAMPLE OPENING:**
"This Request for Information document issued by [Organization] seeks comprehensive information from qualified engineering firms regarding the [Project Name] project. The initiative involves [technical scope] at [location] and encompasses [key requirements]..."

Write your 800-word summary now (paragraph format only):
        """
    
    @staticmethod
    def get_duration_extraction_prompt(full_document_text: str) -> str:
        """
        Get the duration extraction prompt for RFI documents
        
        Args:
            full_document_text: Complete text content from RFI document
            
        Returns:
            str: Prompt for extracting project duration
        """
        return f"""
You are an expert at extracting project duration information from RFI documents.

**CRITICAL INSTRUCTION: Return ONLY the duration text - NO JSON, NO additional formatting.**

**FULL RFI DOCUMENT TEXT:**
{full_document_text}

**DURATION EXTRACTION REQUIREMENTS:**

Look for project duration information in these formats:

1. **Direct Duration Statements**: "Project duration: X months/years", "Timeline: X months", "Duration: X years"
2. **Timeline Ranges**: "Start date to end date", "From [date] to [date]"
3. **Phase-based Duration**: Multiple phases with individual durations
4. **Milestone-based Timeline**: "Implementation over X months", "Delivery within X months/years"
5. **Tables and Schedules**: Project schedules, timeline charts, milestone tables
6. **Response Timeline**: "Information needed for X-year project", "Long-term project spanning X years"

**EXTRACTION GUIDELINES:**
- Look across ALL pages and sections for timeline information
- Check tables and structured content for timeline information
- If multiple durations mentioned, prioritize the overall project duration
- Include units (months, years, weeks)
- If only start/end dates given, calculate the duration
- Consider both development and implementation phases

**RESPONSE FORMAT:**
Return ONLY the duration in simple text format:
- "24 months" or "3 years" or "18-24 months"
- If no duration found: "Not mentioned in RFI"
- If unclear: "Duration not clearly specified"

**EXAMPLES OF GOOD RESPONSES:**
- "24 months"
- "3 years"
- "18-24 months"
- "109 weeks"
- "Not mentioned in RFI"

Extract the duration now (return ONLY the duration text):
        """