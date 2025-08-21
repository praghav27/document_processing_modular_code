"""
TIP Document Metadata Extraction Prompts
Custom prompts for extracting specific metadata from TIP documents
"""

class TIPPrompts:
    """Prompts for TIP document metadata extraction"""
    
    @staticmethod
    def get_tip_metadata_extraction_prompt(document_text: str) -> str:
        """
        Get the TIP metadata extraction prompt for 6 specific fields
        
        Args:
            document_text: Complete text content from TIP document
            
        Returns:
            str: Complete metadata extraction prompt for TIP documents
        """
        return f"""
You are an expert TIP (Technical Information Package) document analyzer. Extract EXACTLY 6 metadata fields from the document. Return ONLY a valid JSON object.

**DOCUMENT TEXT:**
{document_text}

**EXTRACTION REQUIREMENTS:**

1. **doc_id**: Find the document ID or reference number. Look for patterns like "705-25318708.00", "705-25318710.00", or similar numeric patterns with dashes and decimals. This is usually in headers, footers, or document titles.

2. **project_name**: Identify the main project name or title. Look for project titles, station names, facility names, or main project identifiers in headers, titles, or project description sections.

3. **prepared_by**: Find who prepared or authored the document. Look for "Prepared by:", "Author:", "Engineer:", "Consultant:", company names, or individual names responsible for document preparation.

4. **stations_tip**: Extract station information, equipment types, and technical infrastructure. Look for:
   - Station names, numbers, or identifiers
   - Equipment types: auxiliary (aux), electrical (ele), equipment (eqp), transformers, substations
   - Technical infrastructure: transmission lines, distribution systems, power equipment
   - Facility codes, equipment designations, or technical abbreviations
   - Any station-related technical specifications or equipment lists

5. **scope_of_work**: Create a comprehensive 300-word technical summary of the project scope. Include:
   - Technical objectives and project goals
   - Engineering work to be performed
   - Equipment installation, modification, or maintenance activities
   - Technical specifications and requirements
   - Construction, installation, or implementation phases
   - Testing, commissioning, or operational procedures
   - Compliance requirements and technical standards
   - Project deliverables and technical outcomes
   Focus on technical details and engineering aspects, not general project management.

6. **qa_qc_info**: Extract quality assurance and quality control information. Look for:
   - QA/QC procedures, checklists, or requirements
   - Quality control checkpoints or review processes
   - PIDP (Project Implementation and Development Plan) checklist information
   - Pre-RFC (Request for Change) checklist status
   - Completion status of quality processes (Yes/No, Completed/Pending)
   - Quality standards, inspection requirements, or approval processes
   - Any checkbox items, completion status, or quality verification steps

**RESPONSE FORMAT - ONLY JSON:**
{{
    "doc_id": "extracted document ID or 'Not Found'",
    "project_name": "extracted project name or 'Not Specified'",
    "prepared_by": "extracted author/preparer or 'Not Specified'",
    "stations_tip": "extracted station/equipment info or 'Not Specified'",
    "scope_of_work": "comprehensive 300-word technical scope summary",
    "qa_qc_info": "extracted QA/QC information or 'Not Specified'"
}}

**CRITICAL**: Return ONLY the JSON object. No explanation, no markdown, no extra text.
        """