"""
Utility functions for metadata extraction - Updated for RFI support
Text processing, validation, and extraction helpers
"""

import re
from typing import Dict, List, Any

def validate_and_clean_field(field_name: str, value: Any, max_length: int = 200) -> str:
    """
    Validate and clean a metadata field value - Updated for RFI fields
    
    Args:
        field_name: Name of the field being validated
        value: Raw field value
        max_length: Maximum allowed length
        
    Returns:
        str: Cleaned and validated field value
    """
    # Convert to string and clean
    if isinstance(value, str):
        value = value.strip()
        # Remove quotes
        value = re.sub(r'^["\']+|["\']+$', '', value)
        
        # Check for empty or invalid values
        if not value or value.lower() in ['none', 'null', 'undefined', '', 'n/a']:
            return get_default_value_for_field(field_name)
        
        # Special handling for RFI description - don't truncate
        if field_name == 'rfi_description':
            return value  # Keep full description
        
        # Truncate if too long
        if len(value) > max_length:
            value = value[:max_length] + '...'
    else:
        return get_default_value_for_field(field_name)
    
    return value

def get_default_value_for_field(field_name: str) -> str:
    """Get default value for a specific field - Updated for RFI fields"""
    # RFI-specific fields
    if field_name in ['rfi_description', 'duration', 'document_id']:
        return 'Not mentioned in RFI'
    # RFP-specific fields
    elif field_name in ['revenue_range', 'region', 'project_value', 'compliance_standard', 'equipments_used']:
        return 'Not mentioned in RFP'
    # Common fields that use different defaults based on document type
    elif field_name in ['domain_category', 'service_category']:
        return 'Not mentioned in document'  # Generic default
    elif field_name == 'vendor_name':
        return 'tetratech'
    else:
        return 'Not Specified'

def validate_against_domain_list(value: str, valid_domains: List[str], document_type: str = 'RFP') -> str:
    """
    Validate a value against a list of valid domains - Updated for document type
    
    Args:
        value: Value to validate
        valid_domains: List of valid domain values
        document_type: Type of document (RFP or RFI)
        
    Returns:
        str: Validated value or default
    """
    if value in valid_domains:
        return value
    elif value in ['Not Specified', 'Not mentioned in RFP', 'Not mentioned in RFI', 'Not mentioned in document']:
        return value
    else:
        if document_type == 'RFI':
            return 'Not mentioned in RFI'
        else:
            return 'Not mentioned in RFP'

def extract_dates(text: str) -> List[str]:
    """
    Extract dates from text using various patterns
    
    Args:
        text: Input text
        
    Returns:
        List[str]: List of found dates
    """
    date_patterns = [
        r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4})'
    ]
    
    dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dates.extend(matches)
    
    return dates

def extract_financial_info(text: str) -> List[str]:
    """
    Extract financial information from text
    
    Args:
        text: Input text
        
    Returns:
        List[str]: List of found financial information
    """
    financial_patterns = [
        r'\$([0-9,]+(?:\.[0-9]{1,2})?)\s*(?:million|m|k|thousand|billion|b)\b',
        r'(?:budget|contract value|estimated cost|project cost|value)[\s:]*\$([0-9,]+(?:\.[0-9]{1,2})?)',
        r'\$([0-9,]+(?:\.[0-9]{1,2})?)\s*(?:-|to)\s*\$([0-9,]+(?:\.[0-9]{1,2})?)',
        r'(?:under|below|less than)\s*\$([0-9,]+(?:\.[0-9]{1,2})?)',
        r'(?:over|above|more than)\s*\$([0-9,]+(?:\.[0-9]{1,2})?)'
    ]
    
    financial_info = []
    for pattern in financial_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        financial_info.extend([match if isinstance(match, str) else match[0] for match in matches])
    
    return financial_info

def extract_geographical_refs(text: str) -> List[str]:
    """
    Extract geographical references from text
    
    Args:
        text: Input text
        
    Returns:
        List[str]: List of found geographical references
    """
    geo_patterns = [
        # Canadian provinces
        r'\b(ontario|alberta|british columbia|bc|quebec|manitoba|saskatchewan|nova scotia|ns|new brunswick|nb|newfoundland|pei|prince edward island|northwest territories|nwt|nunavut|yukon)\b',
        # Major Canadian cities
        r'\b(toronto|calgary|vancouver|montreal|ottawa|edmonton|winnipeg|halifax|quebec city|victoria|saskatoon|regina|hamilton|london|kitchener|waterloo)\b',
        # US states and cities
        r'\b(california|texas|new york|florida|washington|oregon|seattle|portland|san francisco|los angeles|chicago|boston|denver)\b',
        # Regional descriptors
        r'\b(atlantic canada|western canada|central canada|eastern canada|northern ontario|southern alberta|coastal bc|pacific northwest|east coast|west coast)\b',
        # Generic location patterns
        r'(?:located in|project site in|service area|location:|site:)\s*([^\n,]+)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2,3})\b'
    ]
    
    geo_refs = []
    for pattern in geo_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        geo_refs.extend([match if isinstance(match, str) else match[0] for match in matches])
    
    return geo_refs

def extract_equipment_mentions(text: str) -> List[str]:
    """
    Extract equipment mentions from text
    
    Args:
        text: Input text
        
    Returns:
        List[str]: List of found equipment
    """
    equipment_patterns = [
        r'(?:equipment|machinery|tools|instruments|devices)[\s:]*([^\n]+)',
        r'(?:using|utilizing|employing)[\s:]*([^\n,]+(?:equipment|machinery|tools|instruments|devices)[^\n,]*)',
        r'\b(transformer|generator|turbine|motor|pump|compressor|valve|sensor|meter|controller|switch|relay|cable|conductor|insulator|breaker|fuse|capacitor|reactor|inverter|converter)\b[^\n,]*',
        r'(?:installed|deployed|operated|maintained)[\s:]*([^\n,]+(?:equipment|system|unit)[^\n,]*)',
        r'(?:technical specifications|specs)[\s:]*([^\n]+)'
    ]
    
    equipment_found = []
    for pattern in equipment_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]  # Take first group if tuple
            equipment = match.strip()
            if equipment and len(equipment) < 100 and equipment not in equipment_found:
                equipment_found.append(equipment)
    
    return equipment_found[:3]  # Limit to first 3 equipment items

def extract_compliance_standards(text: str) -> List[str]:
    """
    Extract compliance standards from text
    
    Args:
        text: Input text
        
    Returns:
        List[str]: List of found compliance standards
    """
    compliance_patterns = [
        r'(?:compliance|standard|code|regulation|certification)[\s:]*([^\n,]+(?:iso|ieee|nema|csa|ul|astm|api|asme|ansi|iec|din|bs|en|ce|fcc|rohs)[^\n,]*)',
        r'\b(iso[\s-]?\d+(?::\d+)?|ieee[\s-]?\d+|nema[\s-]?\w+|csa[\s-]?\w+|ul[\s-]?\d+|astm[\s-]?\w+|api[\s-]?\d+|asme[\s-]?\w+|ansi[\s-]?\w+|iec[\s-]?\d+)\b',
        r'(?:meets|complies with|according to|per|follows)[\s:]*([^\n,]+(?:standard|code|regulation|requirement)[^\n,]*)',
        r'(?:quality assurance|qa|qc|quality control)[\s:]*([^\n,]+)',
        r'(?:certified|accredited)[\s:]*([^\n,]+)'
    ]
    
    compliance_found = []
    for pattern in compliance_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]  # Take first group if tuple
            compliance = match.strip()
            if compliance and len(compliance) < 200 and compliance not in compliance_found:
                compliance_found.append(compliance)
    
    return compliance_found[:3]  # Limit to first 3 compliance items

def extract_document_ids(text: str) -> List[str]:
    """
    Extract document IDs from RFI text - NEW function for RFI support
    
    Args:
        text: Input text
        
    Returns:
        List[str]: List of found document IDs
    """
    document_id_patterns = [
        r'(?:rfi\s+(?:id|no|number|ref|reference))[\s:]*([^\n,]+)',
        r'(?:document\s+(?:id|no|number|ref|reference))[\s:]*([^\n,]+)',
        r'(?:reference\s+(?:no|number))[\s:]*([^\n,]+)',
        r'(?:doc\s+(?:id|no|number))[\s:]*([^\n,]+)',
        r'(?:identifier)[\s:]*([^\n,]+)',
        r'\b(rfi[-_]?\d+(?:[-_]\d+)*)\b',
        r'\b(doc[-_]?\d+(?:[-_]\d+)*)\b',
        r'\b([a-z]{2,4}[-_]?\d{4}[-_]?\d{3})\b'
    ]
    
    document_ids = []
    for pattern in document_id_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            doc_id = match.strip()
            if doc_id and len(doc_id) < 50 and doc_id not in document_ids:
                document_ids.append(doc_id)
    
    return document_ids[:3]  # Limit to first 3 document IDs

def extract_project_duration(text: str) -> List[str]:
    """
    Extract project duration from text - NEW function for RFI support
    
    Args:
        text: Input text
        
    Returns:
        List[str]: List of found project durations
    """
    duration_patterns = [
        r'(?:project\s+duration|duration|timeline|project\s+period|contract\s+period)[\s:]*([^\n,]+(?:months?|years?|weeks?))',
        r'(?:anticipated|expected|estimated)\s+(?:duration|timeline)[\s:]*([^\n,]+(?:months?|years?|weeks?))',
        r'(?:over|within|spanning)\s+(\d+\s*(?:months?|years?|weeks?))',
        r'(\d+)[\s-]*(?:to|-)[\s-]*(\d+)\s*(months?|years?|weeks?)',
        r'(?:implementation|development|project)\s+(?:over|within|spanning)\s+([^\n,]+(?:months?|years?|weeks?))',
        r'(?:start|begin|commence).+?(?:to|until|through).+?(\d+\s*(?:months?|years?|weeks?))',
        r'(?:multi[- ]year|long[- ]term)\s+(?:project|initiative)(?:\s+spanning)?[\s:]*([^\n,]+(?:years?))'
    ]
    
    durations = []
    for pattern in duration_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                # Handle multi-group matches like "2 to 3 years"
                if len(match) == 3:  # (start, end, unit)
                    duration = f"{match[0]} to {match[1]} {match[2]}"
                else:
                    duration = match[0]  # Take first group
            else:
                duration = match
            
            duration = duration.strip()
            if duration and len(duration) < 50 and duration not in durations:
                durations.append(duration)
    
    return durations[:3]  # Limit to first 3 durations

def clean_json_response(response_text: str) -> str:
    """
    Clean JSON response text by removing markdown formatting
    
    Args:
        response_text: Raw response text
        
    Returns:
        str: Cleaned response text
    """
    # Remove markdown formatting
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
    
    return response_text

def set_default_if_empty(value: str, default: str = "Not Specified") -> str:
    """
    Set default value if the input is empty or invalid
    
    Args:
        value: Input value
        default: Default value to use
        
    Returns:
        str: Value or default
    """
    if not value or value.strip() == "" or value.lower() in ['none', 'null', 'undefined', 'n/a']:
        return default
    return value.strip()

def truncate_text(text: str, max_length: int = 200) -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Input text
        max_length: Maximum allowed length
        
    Returns:
        str: Truncated text
    """
    if len(text) > max_length:
        return text[:max_length] + '...'
    return text

def extract_project_values(text: str) -> List[str]:
    """
    Extract specific project values from text
    
    Args:
        text: Input text
        
    Returns:
        List[str]: List of found project values
    """
    project_value_patterns = [
        r'(?:contract value|project value|total cost|award amount|professional fees)[\s:]*(\$[0-9,]+(?:\.[0-9]{1,2})?(?:\s*(?:million|M|thousand|K|CAD|USD))?)\b',
        r'(?:project budget|allocated budget|service value|development cost)[\s:]*(\$[0-9,]+(?:\.[0-9]{1,2})?(?:\s*(?:million|M|thousand|K|CAD|USD))?)\b',
        r'(?:contract amount|award value|total project cost)[\s:]*(\$[0-9,]+(?:\.[0-9]{1,2})?(?:\s*(?:million|M|thousand|K|CAD|USD))?)\b',
        r'(?:capital investment|project investment)[\s:]*(\$[0-9,]+(?:\.[0-9]{1,2})?(?:\s*(?:million|M|thousand|K|CAD|USD))?)\b',
        r'TOTALS[\s:]*(\$[0-9,]+(?:\.[0-9]{1,2})?)',
        r'estimated at[\s:]*(\$[0-9,]+(?:\.[0-9]{1,2})?(?:\s*(?:\(USD\)|\(CAD\)|USD|CAD))?)'
    ]
    
    project_values = []
    for pattern in project_value_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        project_values.extend(matches)
    
    return project_values

def validate_rfi_metadata(metadata: Dict, domain_config: Dict) -> Dict:
    """
    Validate RFI-specific metadata fields - NEW function for RFI support
    
    Args:
        metadata: Raw metadata dictionary
        domain_config: Domain configuration
        
    Returns:
        Dict: Validated metadata
    """
    required_rfi_fields = [
        'document_id', 'client_name', 'domain_category', 'service_category',
        'project_title', 'rfi_description', 'submission_date', 'duration'
    ]
    
    validated = {}
    
    for field in required_rfi_fields:
        value = metadata.get(field, 'Not Specified')
        if field == 'rfi_description':
            # Don't truncate RFI description
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

def print_metadata_comparison(rfp_metadata: Dict, rfi_metadata: Dict):
    """
    Print comparison between RFP and RFI metadata fields - NEW utility function
    
    Args:
        rfp_metadata: RFP metadata dictionary
        rfi_metadata: RFI metadata dictionary
    """
    print(f"\n📊 METADATA FIELDS COMPARISON")
    print(f"{'='*60}")
    print(f"{'Field':<25} {'RFP':<20} {'RFI':<20}")
    print(f"{'-'*60}")
    
    # Common fields
    common_fields = ['client_name', 'domain_category', 'service_category', 'project_title', 'submission_date']
    
    for field in common_fields:
        rfp_val = rfp_metadata.get(field, 'N/A')[:15] + '...' if len(str(rfp_metadata.get(field, 'N/A'))) > 18 else str(rfp_metadata.get(field, 'N/A'))
        rfi_val = rfi_metadata.get(field, 'N/A')[:15] + '...' if len(str(rfi_metadata.get(field, 'N/A'))) > 18 else str(rfi_metadata.get(field, 'N/A'))
        print(f"{field:<25} {rfp_val:<20} {rfi_val:<20}")
    
    print(f"{'-'*60}")
    
    # RFP-specific fields
    rfp_specific = ['vendor_name', 'revenue_range', 'region', 'project_value', 'compliance_standard', 'equipments_used']
    print("RFP-SPECIFIC FIELDS:")
    for field in rfp_specific:
        val = str(rfp_metadata.get(field, 'N/A'))[:35] + '...' if len(str(rfp_metadata.get(field, 'N/A'))) > 38 else str(rfp_metadata.get(field, 'N/A'))
        print(f"  {field:<23} {val}")
    
    print(f"{'-'*60}")
    
    # RFI-specific fields
    rfi_specific = ['document_id', 'rfi_description', 'duration']
    print("RFI-SPECIFIC FIELDS:")
    for field in rfi_specific:
        val = str(rfi_metadata.get(field, 'N/A'))
        if field == 'rfi_description':
            val = f"{len(val)} characters" if val != 'N/A' else 'N/A'
        elif len(val) > 38:
            val = val[:35] + '...'
        print(f"  {field:<23} {val}")

def get_metadata_field_count(document_type: str) -> int:
    """
    Get the expected number of metadata fields for document type
    
    Args:
        document_type: Document type (RFP or RFI)
        
    Returns:
        int: Expected field count
    """
    if document_type.upper() == 'RFI':
        return 8  # RFI has 8 fields
    else:
        return 11  # RFP has 11 fields