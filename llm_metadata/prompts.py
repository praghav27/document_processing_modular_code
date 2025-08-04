

# """
# Prompts for Power Business Unit RFP document metadata extraction using LLM
# Contains ONLY the prompts used for extracting document-level metadata from first 2 pages
# Specialized for Power Business Unit domains and services
# Enhanced with region, compliance standard, and equipment extraction capabilities
# """

# class DocumentMetadataPrompts:
#     """Document metadata extraction prompt templates for Power Business Unit RFPs"""
    
#     @staticmethod
#     def get_document_metadata_extraction_prompt(first_two_pages_text: str):
#         """
#         Get the document metadata extraction prompt for Power Business Unit RFP analysis
#         Enhanced to extract region, compliance standards, and equipment information from RFP documents
        
#         Args:
#             first_two_pages_text: Text content from first 2 pages of document
            
#         Returns:
#             str: Complete metadata extraction prompt for Power Business Unit including all 11 fields
#         """
#         return f"""
# You are an expert Power Business Unit RFP analyzer. Extract EXACTLY 11 metadata fields from the document. Return ONLY a valid JSON object.

# **DOCUMENT TEXT:**
# {first_two_pages_text}

# **EXTRACTION REQUIREMENTS:**

# 1. **project_title**: Find the main project name, RFP title, or proposal subject. Look for document titles, project codes, or proposal names in headers or main content.

# 2. **client_name**: Identify the organization requesting the services. Look for "To:", "Client:", recipient names, or organizations issuing the RFP.

# 3. **vendor_name**: Find the service provider or responding organization. Look for "From:", company names submitting the proposal, or service provider information.

# 4. **submission_date**: Extract document dates. Look for submission dates, proposal dates, or document creation dates. Use YYYY-MM-DD format.

# 5. **domain_category**: MUST select from these Power Business Unit domains ONLY:
#    - "Renewable Energy"
#    - "Energy Infrastructure & Grid Modernization"  
#    - "Conventional Power Systems"
#    - "Resource Sector Electrification & Integration"
#    - "Environmental & Regulatory Services"
#    - "International & Remote Community Energy Projects"
   
#    If no clear domain is found, use "Not mentioned in RFP"

# 6. **service_category**: MUST select from these Power Business Unit services ONLY:

#    **For Renewable Energy:**
#    - "Site selection and feasibility studies"
#    - "Resource assessment (wind speed, solar irradiation, hydrology)"
#    - "Environmental permitting and approvals"
#    - "Detailed electrical and civil engineering design"
#    - "Grid interconnection and impact studies"
#    - "Independent Engineer (IE) and Owner's Engineer (OE) services"
#    - "Procurement and construction oversight"
#    - "SCADA and control systems integration"

#    **For Energy Infrastructure & Grid Modernization:**
#    - "Power system planning (load flow, short-circuit, contingency analysis)"
#    - "Substation layout and protection design"
#    - "Smart meter and grid automation consulting"
#    - "Renewable integration into existing grids"
#    - "Distributed energy system modeling and control"
#    - "Grid modernization roadmap development"
#    - "SCADA and communication systems design"
#    - "Arc flash and grounding studies"

#    **For Conventional Power Systems:**
#    - "Retrofit design and emissions reduction planning"
#    - "Regulatory compliance and license support"
#    - "Equipment and system upgrade engineering"
#    - "Decommissioning and remediation planning"
#    - "Safety analysis and QA/QC inspections"
#    - "Performance optimization and life extension analysis"

#    **For Resource Sector Electrification & Integration:**
#    - "Power supply studies for remote operations"
#    - "Diesel replacement with renewables or hybrid systems"
#    - "Transmission line routing and permitting"
#    - "On-site energy storage and backup systems"
#    - "Load forecasting and reliability assessments"
#    - "Grid connection strategy and economic analysis"

#    **For Environmental & Regulatory Services:**
#    - "Environmental impact assessments (EIA)"
#    - "Public and Indigenous consultation support"
#    - "Permitting (federal, provincial, municipal)"
#    - "Climate risk and adaptation planning"
#    - "Biodiversity, habitat, and wildlife impact studies"
#    - "GHG emissions and carbon accounting"
#    - "Sustainability/ESG reporting and disclosures"

#    **For International & Remote Community Energy Projects:**
#    - "Off-grid and hybrid system design"
#    - "Stakeholder and community engagement"
#    - "Socioeconomic impact assessments"
#    - "Electrification master planning"
#    - "Capacity building and training"
#    - "Procurement and construction monitoring"

#    If no matching service is found, use "Not mentioned in RFP"

# 7. **revenue_range**: Extract any revenue, budget, contract value, or financial information mentioned in the RFP. Look for:
#    - Project budget ranges (e.g., "$1M-$5M", "Under $10M", "Between $500K-$2M")
#    - Contract values or estimated costs
#    - Financial scope indicators
#    - Budget categories or spending ranges
   
#    If no financial information is found, use "Not mentioned in RFP"

# 8. **region**: Extract geographical location information from the RFP. Look for:
#    - **Countries**: Canada, USA, Mexico, UK, Australia, etc.
#    - **Provinces/States**: Ontario, Alberta, British Columbia, California, Texas, etc.
#    - **Cities**: Toronto, Calgary, Vancouver, Montreal, Ottawa, etc.
#    - **Regions**: Atlantic Canada, Western Canada, Pacific Northwest, Northeast USA, etc.
#    - **Project locations**: "Located in...", "Project site in...", "Service area..."
#    - **Address information**: Street addresses, postal codes, regional identifiers
#    - **Geographical references**: Northern Ontario, Southern Alberta, Coastal BC, etc.
#    - **Administrative regions**: Federal districts, municipal areas, jurisdictions

#    **Regional Extraction Examples:**
#    - "Chester Technology Park, Nova Scotia" → "Nova Scotia, Canada"
#    - "Project located in Calgary, Alberta" → "Alberta, Canada"
#    - "Site: Toronto, ON" → "Ontario, Canada"
#    - "Service area: Pacific Northwest" → "Pacific Northwest"
#    - "Location: 123 Main St, Vancouver, BC V6B 1A1" → "British Columbia, Canada"
#    - "Northern Alberta operations" → "Alberta, Canada"
#    - "East Coast facility" → "East Coast"

#    If no geographical location is found, use "Not mentioned in RFP"

# 9. **project_value**: Extract specific project value, contract amount, or total project cost mentioned in the RFP. Look for:
#    - **Exact Contract Values**: "$2.5 million", "$500,000", "$1.2M contract"
#    - **Total Project Cost**: "Project value: $3M", "Total cost: $1.5 million"
#    - **Contract Amounts**: "Contract amount: $750K", "Award value: $2M"
#    - **Project Budget**: "Project budget: $4.2M", "Allocated budget: $1.8M"
#    - **Financial Scope**: "Value of services: $900K", "Professional fees: $450K"
#    - **Specific Dollar Amounts**: Look for exact monetary values with currency symbols
#    - **Project Investment**: "Capital investment: $5M", "Development cost: $3.2M"

#    **Project Value Extraction Examples:**
#    - "Contract value: $2.5 million" → "$2.5 million"
#    - "Total project cost estimated at $1.2M" → "$1.2M"
#    - "Professional services budget: $750,000" → "$750,000"
#    - "Award amount: $3.2 million CAD" → "$3.2 million CAD"
#    - "Project investment of $5M over 2 years" → "$5M"
#    - "Service value: $850K" → "$850K"

#    **Different from revenue_range**: This should be a SPECIFIC dollar amount mentioned for THIS project, not a general range.

#    If no specific project value is found, use "Not mentioned in RFP"

# 10. **compliance_standard**: Extract compliance standards, regulations, codes, or certifications mentioned in the RFP. Look for:
#     - **ISO Standards**: "ISO 9001", "ISO 14001", "ISO 45001", "ISO 27001", etc.
#     - **IEEE Standards**: "IEEE 802.11", "IEEE 1547", "IEEE C57", etc.
#     - **Industry Standards**: "NEMA", "CSA", "UL", "ASTM", "API", "ASME", "ANSI", "IEC", etc.
#     - **Regulatory Compliance**: "OSHA compliance", "EPA regulations", "CEC standards", etc.
#     - **Quality Standards**: "Quality assurance program", "QA/QC procedures", "Six Sigma", etc.
#     - **Safety Standards**: "Safety analysis", "Arc flash studies", "NFPA 70E", etc.
#     - **Environmental Standards**: "Environmental compliance", "LEED certification", etc.
#     - **Certification Requirements**: "Professional Engineer certification", "Certified technician", etc.

#     **Compliance Standard Extraction Examples:**
#     - "ISO9001:2015 certified quality program" → "ISO9001:2015 certified quality program"
#     - "NEMA standards compliance" → "NEMA standards compliance"
#     - "IEEE C57.12.00 transformer standards" → "IEEE C57.12.00 transformer standards"
#     - "OSHA safety requirements" → "OSHA safety requirements"
#     - "CSA approval required" → "CSA approval required"
#     - "Quality assurance per ISO 9001" → "Quality assurance per ISO 9001"

#     If no compliance standards are found, use "Not mentioned in RFP"

# 11. **equipments_used**: Extract equipment, machinery, tools, or technical systems mentioned in the RFP. Look for:
#     - **Electrical Equipment**: "Transformers", "Generators", "Motors", "Switchgear", "Breakers", etc.
#     - **Power Generation**: "Turbines", "Solar panels", "Wind turbines", "Inverters", "Converters", etc.
#     - **Measurement Devices**: "Meters", "Sensors", "Controllers", "Monitoring systems", etc.
#     - **Construction Equipment**: "Cranes", "Excavators", "Trucks", "Testing equipment", etc.
#     - **IT/Communication**: "SCADA systems", "Communication equipment", "Software platforms", etc.
#     - **Safety Equipment**: "Protection systems", "Safety devices", "Personal protective equipment", etc.
#     - **Specialized Tools**: "Diagnostic equipment", "Calibration tools", "Installation tools", etc.

#     **Equipment Extraction Examples:**
#     - "230kV transformers and switchgear" → "230kV transformers and switchgear"
#     - "SCADA monitoring systems" → "SCADA monitoring systems"
#     - "Arc flash analysis software" → "Arc flash analysis software"
#     - "Power quality meters and sensors" → "Power quality meters and sensors"
#     - "Mobile testing equipment" → "Mobile testing equipment"
#     - "Protective relay systems" → "Protective relay systems"

#     **Note**: Combine related equipment into logical groups, separate multiple items with commas.

#     If no equipment is mentioned, use "Not mentioned in RFP"

# **ANALYSIS FOCUS:**
# - Scan document headers, titles, and main content for power/energy keywords
# - Look for project descriptions mentioning renewable energy, grid systems, power infrastructure
# - Identify service requests like feasibility studies, engineering design, environmental assessments
# - Match document content to the specific Power Business Unit domains and services listed above
# - For recipient/client information, check headers and "To:" sections
# - For vendor/respondent information, check "From:" sections and company letterheads
# - Extract the most relevant date found in the document
# - **REGION FOCUS**: Carefully scan for ANY geographical references including project locations, service areas, addresses, city/province/country mentions
# - **PROJECT VALUE FOCUS**: Look for specific contract amounts, project costs, or exact dollar values mentioned for this particular project
# - **COMPLIANCE FOCUS**: Look for any mention of standards, codes, regulations, certifications, or compliance requirements
# - **EQUIPMENT FOCUS**: Identify specific equipment, tools, systems, or technology mentioned in the project scope
# - **REVENUE vs PROJECT VALUE**: revenue_range = general budget ranges, project_value = specific dollar amount for this project

# **RESPONSE FORMAT - ONLY JSON:**
# {{
#     "project_title": "extracted title or 'Not Specified'",
#     "client_name": "extracted client name or 'Not Specified'", 
#     "vendor_name": "extracted vendor name or 'Not Specified'",
#     "submission_date": "date in YYYY-MM-DD or 'Not Specified'",
#     "domain_category": "exact domain from Power Business Unit list or 'Not mentioned in RFP'",
#     "service_category": "exact service from Power Business Unit list or 'Not mentioned in RFP'",
#     "revenue_range": "extracted budget/revenue range or 'Not mentioned in RFP'",
#     "region": "extracted geographical location or 'Not mentioned in RFP'",
#     "project_value": "extracted specific project value/contract amount or 'Not mentioned in RFP'",
#     "compliance_standard": "extracted compliance standards/regulations or 'Not mentioned in RFP'",
#     "equipments_used": "extracted equipment/tools/systems or 'Not mentioned in RFP'"
# }}

# **CRITICAL**: Return ONLY the JSON object. No explanation, no markdown, no extra text.
#         """



"""
Prompts for Power Business Unit RFP document metadata extraction using LLM
Contains ONLY the prompts used for extracting document-level metadata from first 2 pages
Specialized for Power Business Unit domains and services
Enhanced with region, compliance standard, and equipment extraction capabilities
"""

class DocumentMetadataPrompts:
    """Document metadata extraction prompt templates for Power Business Unit RFPs"""
    
    @staticmethod
    def get_document_metadata_extraction_prompt(first_two_pages_text: str):
        """
        Get the document metadata extraction prompt for Power Business Unit RFP analysis
        Enhanced to extract region, compliance standards, and equipment information from RFP documents
        
        Args:
            first_two_pages_text: Text content from first 2 pages of document
            
        Returns:
            str: Complete metadata extraction prompt for Power Business Unit including all 11 fields
        """
        return f"""
You are an expert Power Business Unit RFP analyzer. Extract EXACTLY 11 metadata fields from the document. Return ONLY a valid JSON object.

**DOCUMENT TEXT:**
{first_two_pages_text}

**EXTRACTION REQUIREMENTS:**

1. **project_title**: Find the main project name, RFP title, or proposal subject. Look for document titles, project codes, or proposal names in headers or main content.

2. **client_name**: Identify the organization requesting the services. Look for "To:", "Client:", recipient names, or organizations issuing the RFP.

3. **vendor_name**: Find the service provider or responding organization. Look for "From:", company names submitting the proposal, or service provider information.

4. **submission_date**: Extract document dates. Look for submission dates, proposal dates, or document creation dates. Use YYYY-MM-DD format.

5. **domain_category**: MUST select from these Power Business Unit domains ONLY:
   - "Renewable Energy"
   - "Energy Infrastructure & Grid Modernization"  
   - "Conventional Power Systems"
   - "Resource Sector Electrification & Integration"
   - "Environmental & Regulatory Services"
   - "International & Remote Community Energy Projects"
   
   If no clear domain is found, use "Not mentioned in RFP"

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

   If no matching service is found, use "Not mentioned in RFP"

7. **revenue_range**: Extract any revenue, budget, contract value, or financial information mentioned in the RFP. Look for:
   - Project budget ranges (e.g., "$1M-$5M", "Under $10M", "Between $500K-$2M")
   - Contract values or estimated costs
   - Financial scope indicators
   - Budget categories or spending ranges
   
   If no financial information is found, use "Not mentioned in RFP"

8. **region**: Extract geographical location information from the RFP. Look for:
   - **Countries**: Canada, USA, Mexico, UK, Australia, etc.
   - **Provinces/States**: Ontario, Alberta, British Columbia, California, Texas, etc.
   - **Cities**: Toronto, Calgary, Vancouver, Montreal, Ottawa, etc.
   - **Regions**: Atlantic Canada, Western Canada, Pacific Northwest, Northeast USA, etc.
   - **Project locations**: "Located in...", "Project site in...", "Service area..."
   - **Address information**: Street addresses, postal codes, regional identifiers
   - **Geographical references**: Northern Ontario, Southern Alberta, Coastal BC, etc.
   - **Administrative regions**: Federal districts, municipal areas, jurisdictions

   **Regional Extraction Examples:**
   - "Chester Technology Park, Nova Scotia" → "Nova Scotia, Canada"
   - "Project located in Calgary, Alberta" → "Alberta, Canada"
   - "Site: Toronto, ON" → "Ontario, Canada"
   - "Service area: Pacific Northwest" → "Pacific Northwest"
   - "Location: 123 Main St, Vancouver, BC V6B 1A1" → "British Columbia, Canada"
   - "Northern Alberta operations" → "Alberta, Canada"
   - "East Coast facility" → "East Coast"

   If no geographical location is found, use "Not mentioned in RFP"

9. **project_value**: Extract specific project value, contract amount, or total project cost mentioned in the RFP. Look for:
   - **Exact Contract Values**: "$2.5 million", "$500,000", "$1.2M contract"
   - **Total Project Cost**: "Project value: $3M", "Total cost: $1.5 million"
   - **Contract Amounts**: "Contract amount: $750K", "Award value: $2M"
   - **Project Budget**: "Project budget: $4.2M", "Allocated budget: $1.8M"
   - **Financial Scope**: "Value of services: $900K", "Professional fees: $450K"
   - **Specific Dollar Amounts**: Look for exact monetary values with currency symbols
   - **Project Investment**: "Capital investment: $5M", "Development cost: $3.2M"

   **Project Value Extraction Examples:**
   - "Contract value: $2.5 million" → "$2.5 million"
   - "Total project cost estimated at $1.2M" → "$1.2M"
   - "Professional services budget: $750,000" → "$750,000"
   - "Award amount: $3.2 million CAD" → "$3.2 million CAD"
   - "Project investment of $5M over 2 years" → "$5M"
   - "Service value: $850K" → "$850K"

   **Different from revenue_range**: This should be a SPECIFIC dollar amount mentioned for THIS project, not a general range.

   If no specific project value is found, use "Not mentioned in RFP"

10. **equipments_used**: Extract the list of equipments used for any power/energy renewable purposes mentioned in the RFP. Look for:
    - "equipment or hardware components"
    - "physical systems used in any power generation, transmission, distribution, or control domains"
    - "List all utility-scale components and grid-integrated systems mentioned"
    - "Identify the infrastructure components and control equipment discussed"
    - "The list of equipment can contain either a single item or multiple items"

    There are certain key equipments in Tech Power OU:
    **SCADA systems**: master stations, HMI, operator consoles
    **Programmable Logic Controllers (PLC)**: sensors, actuators
    **Remote Terminal Units (RTU)**: SEL-3530 RTAC, GE D20MX, SCADAPack 470, SCADAPack 474, ABB RTU560, Emerson ControlWave Micro, Siemens SICAM A8000, Motorola ACE1000, Motorola ACE3600, Sixnet VersaTRAK 
    **Communication infrastructure**: Ethernet/IP, Modbus, IEC 61850, DNP3, cellular systems, radio systems
    **HVAC systems**: heating, ventilation, air conditioning units—chillers, pumps, actuators, control sensors, DX systems, jet fans, ventilation units
    **Building Automation Systems (BAS)**: sensors, thermostats, DDC controllers, energy management control systems, integration with SCADA/BMS
    **Electrical & Instrumentation Hardware**: Transformers, switchgear, motor control centres (MCC), substation equipment, circuit breakers
    **Instrumentation and field devices**: current/voltage sensors, protective relays, arc‑flash mitigation devices, grounding systems, cable and load schedules 
    **Backup & Power Support**: UPS units, static transfer switches (STS), diesel generators, and emergency backup systems
    **Modern Energy & Grid Equipment**: Energy storage systems (battery energy storage), microgrid controllers, grid‑tie inverters, and generation and distribution lines

    **Equipments Used Examples:**
    "pv_arrays", "wind_turbines","hydro_turbines","transformers","switchgear",
    "control_panels","scada_systems","protection_relays","battery_energy_storage_systems",
    "inverters","capacitor_banks","transmission_lines","distribution_lines",
    "substation_equipment","reactive_power_compensators","load_tap_changers",
    "voltage_regulators","relay_panels","cable_trays","diesel_generators",
    "microgrid_controllers","grid_tie_inverters","circuit_breakers","control_buildings",
    "relay_settings_files","data_acquisition_units","solar_combiner_boxes",
    "underground_power_cables","overhead_conductors","metering_panels",
    "cooling_systems","fire_protection_systems","radiation_monitoring_devices",
    "nuclear","emergency_power_systems","grounding_electrodes","harmonic_filters",
    "reactors","synchronization_panels", "static transfer switches (STS)", "sensors", "thermostats", "DDC controllers", 
    "energy management control systems", "SCADA", "Control panels", "synchronization panels", "relay panels"

    If no specific equipment is found, use "Not mentioned in RFP"
    Make sure that there are no repetition in the final list.

11. **compliance_standard**: Extract the compliance standards mentioned in the RFPs. Look for:
    - regulatory requirements    
    - technical standards       
    - industry codes           
    - certification norms         
    - governing codes           
    - design compliance criteria  
    - engineering standards    
    - conformance specifications  
    - statutory guidelines    
    - mandated codes          
    - safety regulations          
    - utility compliance protocols

    **Compliance standards Examples:**
    "canadian_electrical_code", "cec", "ieee_standards", "csa_standards", "ul_certification",
    "iec_certification", "nerc_reliability_standards", "fips_140_encryption"

    If no compliance standards is found, use "Not mentioned in RFP"

**ANALYSIS FOCUS:**
- Scan document headers, titles, and main content for power/energy keywords
- Look for project descriptions mentioning renewable energy, grid systems, power infrastructure
- Identify service requests like feasibility studies, engineering design, environmental assessments
- Match document content to the specific Power Business Unit domains and services listed above
- For recipient/client information, check headers and "To:" sections
- For vendor/respondent information, check "From:" sections and company letterheads
- Extract the most relevant date found in the document
- **REGION FOCUS**: Carefully scan for ANY geographical references including project locations, service areas, addresses, city/province/country mentions
- **PROJECT VALUE FOCUS**: Look for specific contract amounts, project costs, or exact dollar values mentioned for this particular project
- **REVENUE vs PROJECT VALUE**: revenue_range = general budget ranges, project_value = specific dollar amount for this project
- **Equipments Used**: Make sure that there are no repetition in the final list.
- **Compliance standards**: Select the proper compliance standard from the RFP.

**RESPONSE FORMAT - ONLY JSON:**
{{
    "project_title": "extracted title or 'Not Specified'",
    "client_name": "extracted client name or 'Not Specified'", 
    "vendor_name": "extracted vendor name or 'Not Specified'",
    "submission_date": "date in YYYY-MM-DD or 'Not Specified'",
    "domain_category": "exact domain from Power Business Unit list or 'Not mentioned in RFP'",
    "service_category": "exact service from Power Business Unit list or 'Not mentioned in RFP'",
    "revenue_range": "extracted budget/revenue range or 'Not mentioned in RFP'",
    "region": "extracted geographical location or 'Not mentioned in RFP'",
    "project_value": "extracted specific project value/contract amount or 'Not mentioned in RFP'",
    "equipments_used": "extracted equipment/tools/systems or 'Not mentioned in RFP'",
    "compliance_standard": "extracted specific compliance standard or 'Not mentioned in RFP'"
}}

**CRITICAL**: Return ONLY the JSON object. No explanation, no markdown, no extra text.
        """