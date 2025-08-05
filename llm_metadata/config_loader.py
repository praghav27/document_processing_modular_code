"""
Configuration loader for metadata extraction
Contains domain-specific configurations and field schemas
"""

from typing import Dict, List

class ConfigLoader:
    """Load and manage business unit configurations"""
    
    @staticmethod
    def load_power_config() -> Dict:
        """Load Power Business Unit configuration"""
        return {
            "business_unit": "Power Business Unit",
            "domains": [
                "Renewable Energy",
                "Energy Infrastructure & Grid Modernization",
                "Conventional Power Systems", 
                "Resource Sector Electrification & Integration",
                "Environmental & Regulatory Services",
                "International & Remote Community Energy Projects"
            ],
            "services": {
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
        }
    
    @staticmethod
    def load_custom_config(config_path: str) -> Dict:
        """Load custom configuration from file (for future extensibility)"""
        import json
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading config from {config_path}: {e}")
            return ConfigLoader.get_default_config()
    
    @staticmethod
    def get_field_schemas() -> Dict:
        """Get field schemas and validation rules"""
        return {
            # RFP Fields (11 fields)
            'project_title': {
                'required': True,
                'max_length': 200,
                'default': 'Not Specified'
            },
            'client_name': {
                'required': True,
                'max_length': 200,
                'default': 'Not Specified'
            },
            'vendor_name': {
                'required': True,
                'max_length': 200,
                'default': 'tetratech'
            },
            'submission_date': {
                'required': True,
                'max_length': 50,
                'default': 'Not Specified',
                'format': 'YYYY-MM-DD'
            },
            'domain_category': {
                'required': True,
                'max_length': 200,
                'default': 'Not mentioned in RFP',
                'validate_against_list': True
            },
            'service_category': {
                'required': True,
                'max_length': 200,
                'default': 'Not mentioned in RFP',
                'validate_against_list': True
            },
            'revenue_range': {
                'required': True,
                'max_length': 200,
                'default': 'Not mentioned in RFP'
            },
            'region': {
                'required': True,
                'max_length': 200,
                'default': 'Not mentioned in RFP'
            },
            'project_value': {
                'required': True,
                'max_length': 200,
                'default': 'Not mentioned in RFP'
            },
            'compliance_standard': {
                'required': True,
                'max_length': 200,
                'default': 'Not mentioned in RFP'
            },
            'equipments_used': {
                'required': True,
                'max_length': 500,
                'default': 'Not mentioned in RFP'
            },
            # RFI Fields (8 fields)
            'document_id': {
                'required': True,
                'max_length': 100,
                'default': 'Not Specified'
            },
            'rfi_description': {
                'required': True,
                'max_length': 5000,  # Allow longer for 800-word description
                'default': 'Not mentioned in RFI'
            },
            'duration': {
                'required': True,
                'max_length': 100,
                'default': 'Not mentioned in RFI'
            }
        }
    
    @staticmethod
    def get_rfi_field_schemas() -> Dict:
        """Get RFI-specific field schemas"""
        base_schemas = ConfigLoader.get_field_schemas()
        rfi_fields = [
            'document_id', 'client_name', 'domain_category', 'service_category',
            'project_title', 'rfi_description', 'submission_date', 'duration'
        ]
        return {field: base_schemas[field] for field in rfi_fields if field in base_schemas}
    
    @staticmethod
    def get_rfp_field_schemas() -> Dict:
        """Get RFP-specific field schemas"""
        base_schemas = ConfigLoader.get_field_schemas()
        rfp_fields = [
            'project_title', 'client_name', 'vendor_name', 'submission_date',
            'domain_category', 'service_category', 'revenue_range', 'region',
            'project_value', 'compliance_standard', 'equipments_used'
        ]
        return {field: base_schemas[field] for field in rfp_fields if field in base_schemas}
    
    @staticmethod
    def validate_config(config: Dict) -> bool:
        """Validate configuration structure"""
        required_keys = ['business_unit', 'domains', 'services']
        
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing required config key: {key}")
                return False
        
        if not isinstance(config['domains'], list):
            print("❌ 'domains' must be a list")
            return False
        
        if not isinstance(config['services'], dict):
            print("❌ 'services' must be a dictionary")
            return False
        
        return True
    
    @staticmethod
    def get_default_config() -> Dict:
        """Get minimal default configuration"""
        return {
            "business_unit": "Default",
            "domains": ["Not mentioned in document"],
            "services": {"Default": ["Not mentioned in document"]}
        }