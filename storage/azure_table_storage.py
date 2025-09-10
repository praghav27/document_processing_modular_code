# import os
# import json
# import uuid
# from datetime import datetime
# from typing import Dict, Any, List, Union, Optional, Set
# from azure.data.tables import TableServiceClient, TableEntity
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# class AzureTableMetadataHandler:
#     """Enhanced handler for Azure Table Storage with metadata management for RFP/RFI documents and component data"""
    
#     def __init__(self):
#         """Initialize the Azure Table Storage handler"""
#         self.connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
#         if not self.connection_string:
#             raise ValueError("AZURE_STORAGE_CONNECTION_STRING environment variable not found")
        
#         self.table_service_client = TableServiceClient.from_connection_string(self.connection_string)
        
#         # Cache for RFP GUIDs to associate RFIs
#         self._rfp_guid_cache = {}
    
#     def _create_table_if_not_exists(self, table_name: str):
#         """Create table if it doesn't exist"""
#         table_client = self.table_service_client.get_table_client(table_name=table_name)
#         try:
#             table_client.create_table()  # Will succeed if table doesn't exist
#             print(f"✅ Created new table: {table_name}")
#         except Exception as e:
#             if "TableAlreadyExists" in str(e):
#                 pass  # Ignore - table is already there
#             else:
#                 print(f"❌ Failed to create table {table_name}: {e}")
#                 raise
#         return table_client

    
#     def _generate_rfp_guid(self, project_id: str) -> str:
#         """Generate or retrieve consistent GUID for RFP project"""
#         if project_id in self._rfp_guid_cache:
#             return self._rfp_guid_cache[project_id]
        
#         # Generate new GUID and cache it
#         rfp_guid = str(uuid.uuid4())
#         self._rfp_guid_cache[project_id] = rfp_guid
#         return rfp_guid
    
#     def _get_rfp_guid_for_rfi(self, project_id: str, table_name: str) -> Optional[str]:
#         """Get the RFP GUID for associating an RFI document"""
#         # First check cache
#         if project_id in self._rfp_guid_cache:
#             return self._rfp_guid_cache[project_id]
        
#         # Query the table for existing RFP with same project_id
#         try:
#             table_client = self.table_service_client.get_table_client(table_name=table_name)
#             filter_query = f"ProjectId eq '{project_id}' and DocumentType eq 'RFP'"
#             entities = list(table_client.query_entities(filter_query))
            
#             if entities:
#                 rfp_guid = entities[0].get('RFP_GUID')
#                 if rfp_guid:
#                     self._rfp_guid_cache[project_id] = rfp_guid
#                     return rfp_guid
#         except Exception as e:
#             print(f"Error querying for RFP GUID: {e}")
        
#         # If no RFP found, create a new GUID (this RFI might come before its RFP)
#         return self._generate_rfp_guid(project_id)
    
#     def _sanitize_for_azure(self, value: Any) -> Any:
#         """Sanitize individual values for Azure Table Storage"""
#         if value is None:
#             return ""
#         elif isinstance(value, str):
#             # Azure Table Storage has 64KB limit per property
#             return value[:32000] if len(value) > 32000 else value
#         elif isinstance(value, (list, dict)):
#             return json.dumps(value, default=str)
#         else:
#             return str(value)
    
#     def store_file_metadata(self, metadata: Dict[str, Any], table_name: str = "FileMetadata") -> Optional[str]:
#         """
#         Store file metadata with 6 key columns and rest as JSON metadata
        
#         Args:
#             metadata: Dictionary containing file metadata
#             table_name: Name of the Azure table (default: "FileMetadata")
            
#         Returns:
#             Optional[str]: Entity key if successful, None if failed
#         """
#         try:
#             # Create table client
#             table_client = self._create_table_if_not_exists(table_name)
            
#             # Define the 6 important columns to extract
#             key_columns = {
#                 'project_name': metadata.get('project_name', ''),
#                 'client': metadata.get('client', ''),
#                 'region': metadata.get('region', ''),
#                 'industry': metadata.get('industry', ''),
#                 'document_type': metadata.get('document_type', ''),
#                 'project_id': metadata.get('project_id', '')
#             }
            
#             # Extract remaining fields for metadata JSON
#             remaining_fields = {k: v for k, v in metadata.items() if k not in key_columns.keys()}
            
#             # Create entity
#             entity = TableEntity()
            
#             # Set partition and row keys
#             entity['PartitionKey'] = str(key_columns['project_id']) if key_columns['project_id'] else f"unknown_{datetime.utcnow().strftime('%Y%m%d')}"
#             entity['RowKey'] = f"{str(uuid.uuid4())[:8]}_{datetime.utcnow().isoformat().replace(':', '_').replace('-', '_')}"
            
#             # Add the 6 key columns
#             entity['ProjectName'] = self._sanitize_for_azure(key_columns['project_name'])
#             entity['Client'] = self._sanitize_for_azure(key_columns['client'])
#             entity['Region'] = self._sanitize_for_azure(key_columns['region'])
#             entity['Industry'] = self._sanitize_for_azure(key_columns['industry'])
#             entity['DocumentType'] = self._sanitize_for_azure(key_columns['document_type'])
#             entity['ProjectId'] = self._sanitize_for_azure(key_columns['project_id'])
            
#             # Handle GUID assignment based on document type
#             if key_columns['document_type'].upper() == 'RFP':
#                 # For RFP, generate new GUID
#                 rfp_guid = self._generate_rfp_guid(key_columns['project_id'])
#                 entity['RFP_GUID'] = rfp_guid
#             elif key_columns['document_type'].upper() == 'RFI':
#                 # For RFI, associate with existing RFP or create new GUID
#                 rfp_guid = self._get_rfp_guid_for_rfi(key_columns['project_id'], table_name)
#                 entity['RFP_GUID'] = rfp_guid
#             else:
#                 # For other document types, create unique GUID
#                 entity['RFP_GUID'] = str(uuid.uuid4())
            
#             # Add metadata as JSON string
#             entity['Metadata'] = json.dumps(remaining_fields, default=str, ensure_ascii=False)
            
#             # Add system fields
#             entity['CreatedAt'] = datetime.utcnow().isoformat()
#             entity['UpdatedAt'] = datetime.utcnow().isoformat()
            
#             # Store to Azure
#             table_client.create_entity(entity=entity)
#             entity_key = f"{entity['PartitionKey']}_{entity['RowKey']}"
            
#             print(f"✅ Successfully stored metadata for {key_columns['document_type']} - {key_columns['project_name']}")
#             print(f"   Entity Key: {entity_key}")
#             print(f"   RFP GUID: {entity['RFP_GUID']}")
            
#             return entity_key
            
#         except Exception as e:
#             print(f"❌ Error storing metadata: {str(e)}")
#             return None
    
#     def store_component_data(self, data: Dict[str, Any], table_name: str = "ComponentData") -> List[str]:
#         """
#         Store component data by creating separate records for each component
        
#         Args:
#             data: Dictionary containing component data with structure shown in example
#             table_name: Name of the Azure table (default: "ComponentData")
            
#         Returns:
#             List[str]: List of entity keys if successful, empty list if failed
#         """
#         try:
#             # Create table client
#             table_client = self._create_table_if_not_exists(table_name)
            
#             # Extract common fields - Updated to match new JSON structure
#             common_fields = {
#                 'chunk_id': data.get('chunk_id', ''),
#                 'project_id': data.get('project_id', ''),
#                 'project_name': data.get('project_name', ''),
#                 'content_type': data.get('content_type', ''),
#                 'client': data.get('client', ''),
#                 'region': data.get('region', ''),
#                 'industry': data.get('industry', ''),
#                 'prepared_date': data.get('prepared_date', ''),
#                 'field_type': data.get('field_type', ''),
#                 'voltage_class': data.get('voltage_class', ''),
#                 'contract_types': data.get('contract_types', ''),
#                 'pricing': data.get('pricing', '')
#             }
            
#             # Get components data
#             components = data.get('components', {})
            
#             entity_keys = []
            
#             # Process each component
#             for component_name, component_data in components.items():
#                 # Create entity for this component
#                 entity = TableEntity()
                
#                 # Set partition and row keys
#                 entity['PartitionKey'] = str(common_fields['project_id']) if common_fields['project_id'] else f"unknown_{datetime.utcnow().strftime('%Y%m%d')}"
                
#                 # Create component-specific chunk_id and row key
#                 component_chunk_id = f"{common_fields['chunk_id']}_{component_name}"
#                 entity['RowKey'] = f"comp_{component_chunk_id}_{datetime.utcnow().isoformat().replace(':', '_').replace('-', '_')}"
                
#                 # Add component key columns - Updated fields
#                 entity['ChunkId'] = self._sanitize_for_azure(component_chunk_id)
#                 entity['ProjectId'] = self._sanitize_for_azure(common_fields['project_id'])
#                 entity['ProjectName'] = self._sanitize_for_azure(common_fields['project_name'])
#                 entity['ContentType'] = self._sanitize_for_azure(common_fields['content_type'])
#                 entity['Client'] = self._sanitize_for_azure(common_fields['client'])
#                 entity['Region'] = self._sanitize_for_azure(common_fields['region'])
#                 entity['Industry'] = self._sanitize_for_azure(common_fields['industry'])
#                 entity['PreparedDate'] = self._sanitize_for_azure(common_fields['prepared_date'])
#                 entity['FieldType'] = self._sanitize_for_azure(common_fields['field_type'])
#                 entity['VoltageClass'] = self._sanitize_for_azure(common_fields['voltage_class'])
#                 entity['ContractTypes'] = self._sanitize_for_azure(common_fields['contract_types'])
#                 entity['Pricing'] = self._sanitize_for_azure(common_fields['pricing'])
                
#                 # Add component-specific fields
#                 entity['ComponentName'] = self._sanitize_for_azure(component_name)
#                 entity['ScopeOfWork'] = self._sanitize_for_azure(component_data.get('scope_of_work', ''))
#                 entity['RequiredActivities'] = self._sanitize_for_azure(component_data.get('required_activities', ''))
                
#                 # Handle component-specific fields based on component type
#                 if component_name == 'ELE':
#                     entity['DisconnectSwitches'] = self._sanitize_for_azure(component_data.get('disconnect_switches', ''))
#                     entity['Transformer'] = self._sanitize_for_azure(component_data.get('transformer', ''))
#                 elif component_name == 'AUX':
#                     entity['HVACAndFAS'] = self._sanitize_for_azure(component_data.get('HVAC_and_FAS', ''))
#                     entity['HADsArrangements'] = self._sanitize_for_azure(component_data.get('HADs_arrangements', ''))
#                 elif component_name == 'CNT':
#                     entity['ControlDesignPackages'] = self._sanitize_for_azure(component_data.get('control_design_packages', ''))
#                     entity['SCADAInfrastructure'] = self._sanitize_for_azure(component_data.get('SCADA_infrastructure', ''))
#                 elif component_name == 'TEL':
#                     entity['StationLANNetworks'] = self._sanitize_for_azure(component_data.get('station_lan_networks', ''))
#                     entity['SCADAAndTransportInfrastructure'] = self._sanitize_for_azure(component_data.get('scada_and_transport_infrastructure', ''))
#                 elif component_name == 'MET':
#                     entity['NewMeteringInstallations'] = self._sanitize_for_azure(component_data.get('new_metering_installations', ''))
#                     entity['ExistingMeteringRetainOrUpdate'] = self._sanitize_for_azure(component_data.get('existing_metering_retain_or_update', ''))
#                 elif component_name == 'STE':  # New component type - Site Preparation
#                     entity['GradingAndRoads'] = self._sanitize_for_azure(component_data.get('grading_and_roads', ''))
#                     entity['DrainageAndWaterManagement'] = self._sanitize_for_azure(component_data.get('drainage_and_water_management', ''))
                
#                 # Store additional component data as JSON if any other fields exist
#                 other_fields = {k: v for k, v in component_data.items() if k not in [
#                     'scope_of_work', 'required_activities', 'disconnect_switches', 'transformer',
#                     'HVAC_and_FAS', 'HADs_arrangements', 'control_design_packages', 'SCADA_infrastructure',
#                     'station_lan_networks', 'scada_and_transport_infrastructure', 'new_metering_installations',
#                     'existing_metering_retain_or_update', 'grading_and_roads', 'drainage_and_water_management'
#                 ]}
                
#                 if other_fields:
#                     entity['AdditionalData'] = json.dumps(other_fields, default=str, ensure_ascii=False)
                
#                 # Generate unique GUID for this component record
#                 entity['RecordGUID'] = str(uuid.uuid4())
                
#                 # Add system timestamp
#                 entity['SystemCreatedAt'] = datetime.utcnow().isoformat()
#                 entity['SystemUpdatedAt'] = datetime.utcnow().isoformat()
                
#                 # Store to Azure
#                 table_client.create_entity(entity=entity)
#                 entity_key = f"{entity['PartitionKey']}_{entity['RowKey']}"
#                 entity_keys.append(entity_key)
                
#                 print(f"✅ Successfully stored component {component_name} for project {common_fields['project_name']}")
#                 print(f"   Entity Key: {entity_key}")
#                 print(f"   Component Chunk ID: {component_chunk_id}")
#                 print(f"   Record GUID: {entity['RecordGUID']}")
            
#             return entity_keys
            
#         except Exception as e:
#             print(f"❌ Error storing component data: {str(e)}")
#             return []
    
#     def get_components_by_project(self, project_id: str, table_name: str = "ComponentData") -> Dict[str, Any]:
#         """
#         Get all components for a specific project
        
#         Args:
#             project_id: Project ID to search for
#             table_name: Table name to query
            
#         Returns:
#             Dictionary with project info and components
#         """
#         try:
#             table_client = self.table_service_client.get_table_client(table_name=table_name)
            
#             # Query for all components with this project_id
#             filter_query = f"ProjectId eq '{project_id}'"
#             entities = list(table_client.query_entities(filter_query))
            
#             result = {
#                 'project_id': project_id,
#                 'project_info': None,
#                 'components': {}
#             }
            
#             for entity in entities:
#                 component_name = entity.get('ComponentName', '')
                
#                 if not result['project_info']:
#                     result['project_info'] = {
#                         'project_name': entity.get('ProjectName', ''),
#                         'client': entity.get('Client', ''),
#                         'industry': entity.get('Industry', ''),
#                         'region': entity.get('Region', ''),
#                         'prepared_date': entity.get('PreparedDate', ''),
#                         'content_type': entity.get('ContentType', ''),
#                         'field_type': entity.get('FieldType', ''),
#                         'voltage_class': entity.get('VoltageClass', ''),
#                         'contract_types': entity.get('ContractTypes', ''),
#                         'pricing': entity.get('Pricing', '')
#                     }
                
#                 component_info = {
#                     'chunk_id': entity.get('ChunkId', ''),
#                     'component_name': component_name,
#                     'scope_of_work': entity.get('ScopeOfWork', ''),
#                     'required_activities': entity.get('RequiredActivities', ''),
#                     'record_guid': entity.get('RecordGUID', ''),
#                     'created_at': entity.get('SystemCreatedAt', '')
#                 }
                
#                 # Add component-specific fields
#                 if component_name == 'ELE':
#                     component_info.update({
#                         'disconnect_switches': entity.get('DisconnectSwitches', ''),
#                         'transformer': entity.get('Transformer', '')
#                     })
#                 elif component_name == 'AUX':
#                     component_info.update({
#                         'hvac_and_fas': entity.get('HVACAndFAS', ''),
#                         'hads_arrangements': entity.get('HADsArrangements', '')
#                     })
#                 elif component_name == 'CNT':
#                     component_info.update({
#                         'control_design_packages': entity.get('ControlDesignPackages', ''),
#                         'scada_infrastructure': entity.get('SCADAInfrastructure', '')
#                     })
#                 elif component_name == 'TEL':
#                     component_info.update({
#                         'station_lan_networks': entity.get('StationLANNetworks', ''),
#                         'scada_and_transport_infrastructure': entity.get('SCADAAndTransportInfrastructure', '')
#                     })
#                 elif component_name == 'MET':
#                     component_info.update({
#                         'new_metering_installations': entity.get('NewMeteringInstallations', ''),
#                         'existing_metering_retain_or_update': entity.get('ExistingMeteringRetainOrUpdate', '')
#                     })
#                 elif component_name == 'STE':  # New component type
#                     component_info.update({
#                         'grading_and_roads': entity.get('GradingAndRoads', ''),
#                         'drainage_and_water_management': entity.get('DrainageAndWaterManagement', '')
#                     })
                
#                 # Add additional data if exists
#                 if entity.get('AdditionalData'):
#                     try:
#                         additional_data = json.loads(entity['AdditionalData'])
#                         component_info['additional_data'] = additional_data
#                     except:
#                         pass
                
#                 result['components'][component_name] = component_info
            
#             return result
            
#         except Exception as e:
#             print(f"❌ Error querying component data: {str(e)}")
#             return {}
    
#     def get_rfp_with_associated_rfis(self, project_id: str, table_name: str = "FileMetadata") -> Dict[str, Any]:
#         """
#         Get RFP and all associated RFIs for a project
        
#         Args:
#             project_id: Project ID to search for
#             table_name: Table name to query
            
#         Returns:
#             Dictionary with RFP and associated RFIs
#         """
#         try:
#             table_client = self.table_service_client.get_table_client(table_name=table_name)
            
#             # Query for all documents with this project_id
#             filter_query = f"ProjectId eq '{project_id}'"
#             entities = list(table_client.query_entities(filter_query))
            
#             result = {
#                 'project_id': project_id,
#                 'rfp': None,
#                 'rfis': [],
#                 'other_documents': []
#             }
            
#             for entity in entities:
#                 doc_type = entity.get('DocumentType', '').upper()
                
#                 # Parse metadata back to dict
#                 metadata = {}
#                 if entity.get('Metadata'):
#                     try:
#                         metadata = json.loads(entity['Metadata'])
#                     except:
#                         pass
                
#                 doc_info = {
#                     'document_type': entity.get('DocumentType', ''),
#                     'project_name': entity.get('ProjectName', ''),
#                     'client': entity.get('Client', ''),
#                     'region': entity.get('Region', ''),
#                     'industry': entity.get('Industry', ''),
#                     'rfp_guid': entity.get('RFP_GUID', ''),
#                     'created_at': entity.get('CreatedAt', ''),
#                     'metadata': metadata,
#                     'entity_key': f"{entity['PartitionKey']}_{entity['RowKey']}"
#                 }
                
#                 if doc_type == 'RFP':
#                     result['rfp'] = doc_info
#                 elif doc_type == 'RFI':
#                     result['rfis'].append(doc_info)
#                 else:
#                     result['other_documents'].append(doc_info)
            
#             return result
            
#         except Exception as e:
#             print(f"❌ Error querying project data: {str(e)}")
#             return {}
    
#     def get_all_rfps_with_rfi_counts(self, table_name: str = "FileMetadata") -> List[Dict[str, Any]]:
#         """
#         Get all RFPs with count of associated RFIs
        
#         Args:
#             table_name: Table name to query
            
#         Returns:
#             List of RFP information with RFI counts
#         """
#         try:
#             table_client = self.table_service_client.get_table_client(table_name=table_name)
            
#             # Get all entities
#             entities = list(table_client.list_entities())
            
#             # Group by RFP_GUID
#             rfp_groups = {}
            
#             for entity in entities:
#                 rfp_guid = entity.get('RFP_GUID', '')
#                 doc_type = entity.get('DocumentType', '').upper()
                
#                 if rfp_guid not in rfp_groups:
#                     rfp_groups[rfp_guid] = {
#                         'rfp_guid': rfp_guid,
#                         'rfp_info': None,
#                         'rfi_count': 0,
#                         'total_documents': 0
#                     }
                
#                 rfp_groups[rfp_guid]['total_documents'] += 1
                
#                 if doc_type == 'RFP':
#                     rfp_groups[rfp_guid]['rfp_info'] = {
#                         'project_id': entity.get('ProjectId', ''),
#                         'project_name': entity.get('ProjectName', ''),
#                         'client': entity.get('Client', ''),
#                         'region': entity.get('Region', ''),
#                         'industry': entity.get('Industry', ''),
#                         'created_at': entity.get('CreatedAt', '')
#                     }
#                 elif doc_type == 'RFI':
#                     rfp_groups[rfp_guid]['rfi_count'] += 1
            
#             # Convert to list and filter out groups without RFP info
#             result = []
#             for group in rfp_groups.values():
#                 if group['rfp_info']:
#                     result.append({
#                         'rfp_guid': group['rfp_guid'],
#                         'project_id': group['rfp_info']['project_id'],
#                         'project_name': group['rfp_info']['project_name'],
#                         'client': group['rfp_info']['client'],
#                         'region': group['rfp_info']['region'],
#                         'industry': group['rfp_info']['industry'],
#                         'created_at': group['rfp_info']['created_at'],
#                         'rfi_count': group['rfi_count'],
#                         'total_documents': group['total_documents']
#                     })
            
#             return sorted(result, key=lambda x: x['created_at'], reverse=True)
            
#         except Exception as e:
#             print(f"❌ Error getting RFP summary: {str(e)}")
#             return []
    
#     def query_by_criteria(self, table_name: str, **criteria) -> List[TableEntity]:
#         """
#         Query entities by various criteria
        
#         Args:
#             table_name: Table name to query
#             **criteria: Query criteria (client, industry, document_type, etc.)
            
#         Returns:
#             List of matching entities
#         """
#         try:
#             table_client = self.table_service_client.get_table_client(table_name=table_name)
            
#             # Build filter query
#             filters = []
#             for key, value in criteria.items():
#                 if key.lower() == 'client':
#                     filters.append(f"Client eq '{value}'")
#                 elif key.lower() == 'industry':
#                     filters.append(f"Industry eq '{value}'")
#                 elif key.lower() == 'document_type':
#                     filters.append(f"DocumentType eq '{value}'")
#                 elif key.lower() == 'project_id':
#                     filters.append(f"ProjectId eq '{value}'")
#                 elif key.lower() == 'region':
#                     filters.append(f"Region eq '{value}'")
#                 elif key.lower() == 'component_name':
#                     filters.append(f"ComponentName eq '{value}'")
#                 elif key.lower() == 'field_type':
#                     filters.append(f"FieldType eq '{value}'")
#                 elif key.lower() == 'voltage_class':
#                     filters.append(f"VoltageClass eq '{value}'")
#                 elif key.lower() == 'contract_types':
#                     filters.append(f"ContractTypes eq '{value}'")
            
#             if filters:
#                 filter_query = " and ".join(filters)
#                 entities = list(table_client.query_entities(filter_query))
#             else:
#                 entities = list(table_client.list_entities())
            
#             return entities
            
#         except Exception as e:
#             print(f"❌ Error querying by criteria: {str(e)}")
#             return []


# # # Example usage
# # if __name__ == "__main__":
# #     # Initialize handler
# #     handler = AzureTableMetadataHandler()
    
# #     """
# #     **********************************************************************************************************
# #     Example: Storing and retrieving RFP and RFI metadata Which is File Metadata
# #     **********************************************************************************************************    
# #     """
    
# #     # # Sample metadata
# #     # sample_metadata = {
# #     #     'project_name': 'Merivale TS- Component Replacement',
# #     #     'client': 'Hydro One Networks Inc.',
# #     #     'region': 'Ottawa, Ontario, Canada',
# #     #     'industry': 'Power & Energy',
# #     #     'prepared_date': '2021-11-15',
# #     #     'station_discipline': 'AUX',
# #     #     'scope_of_work': 'The project involves replacing aging assets at Merivale TS, including 230kV GIS breakers, 230/115kV autotransformers, and 115kV oil circuit breakers, along with upgrades to disconnect switches, instrument transformers, strain insulators, protection, control, telecom facilities, and AC station service supply to meet Hydro One standards.',
# #     #     'required_activities': 'Design, supply, install, and commission HVAC and Fire Alarm Systems, including heat detection and emergency ventilation, integrate with existing systems, review and approve contractor packages, prepare technical specifications, provide field support, issue as-built drawings, and oversee installation of overhead gantry and monorail cranes for new buildings.',
# #     #     'project_id': '705-22318727.00',
# #     #     'document_type': 'RFP',
# #     #     'filename': '705-22318727.00-RFP-Merivale TS Sust&Dev-EN-ST-AUX-TIP.pdf'
# #     # }
    
# #     # # Store the RFP metadata
# #     # print("🔄 Storing RFP metadata...")
# #     # rfp_key = handler.store_file_metadata(sample_metadata, "FileMetadata")
    
# #     # # Create a sample RFI for the same project
# #     # rfi_metadata = sample_metadata.copy()
# #     # rfi_metadata.update({
# #     #     'document_type': 'RFI',
# #     #     'filename': '705-22318727.00-RFI-001-Clarification.pdf',
# #     #     'rfi_number': 'RFI-001',
# #     #     'rfi_subject': 'Clarification on HVAC specifications'
# #     # })
    
# #     # print("\n🔄 Storing RFI metadata...")
# #     # rfi_key = handler.store_file_metadata(rfi_metadata, "FileMetadata")
    
# #     # # Get RFP with associated RFIs
# #     # print("\n🔍 Retrieving RFP with associated RFIs...")
# #     # project_data = handler.get_rfp_with_associated_rfis('705-22318727.00', "FileMetadata")
    
# #     # print(f"\n📊 Project: {project_data.get('project_id')}")
# #     # if project_data.get('rfp'):
# #     #     print(f"   RFP: {project_data['rfp']['project_name']}")
# #     #     print(f"   RFP GUID: {project_data['rfp']['rfp_guid']}")
# #     # print(f"   RFIs: {len(project_data.get('rfis', []))}")
    
# #     # # Get summary of all RFPs
# #     # print("\n📈 Getting RFP summary...")
# #     # rfp_summary = handler.get_all_rfps_with_rfi_counts("FileMetadata")
    
# #     # for rfp in rfp_summary:
# #     #     print(f"   Project: {rfp['project_name']} | RFIs: {rfp['rfi_count']} | Total Docs: {rfp['total_documents']}")
        
    
# #     """
# #     **********************************************************************************************************
# #     Example: Storing and retrieving Component Data with new structure
# #     **********************************************************************************************************
# #     """
# #     # Sample component data with new JSON structure
# #     sample_component_data = {
# #         "chunk_id": "f7993bb2-32f3-412a-a8f1-f59280379ba7",
# #         "project_id": "705-22318727.00",
# #         "project_name": "",
# #         "content_type": "text",
# #         "client": "Hydro One",
# #         "region": "Merivale, Ontario",
# #         "industry": "Power & Energy",
# #         "prepared_date": "2021-11-01",
# #         "field_type": "Brown Field",
# #         "voltage_class": "Transmission (115–230 kV)",
# #         "contract_types": "Not mentioned in the document",
# #         "pricing": "Not mentioned in RFP",
# #         "components": {
# #             "ELE": {
# #                 "scope_of_work": "The electrical scope involves the replacement of one transformer and installation of a new transformer at Merivale TS. It includes designing and installing transformer spill containment systems, oil-water separators, and associated piping, ensuring compliance with Hydro One standards.",
# #                 "required_activities": "The electrical activities include collecting design data, preparing design drawings and reports, supporting permit applications, overseeing construction, participating in commissioning, and preparing as-built documentation. The installation of spill containment pits and oil-water separators is also required.",
# #                 "disconnect_switches": "not mentioned in document",
# #                 "transformer": "230/115kV transformers"
# #             },
# #             "STE": {
# #                 "scope_of_work": "The site preparation scope includes grading and drainage modifications for the Merivale TS yard, installation of new roads, fences, and spill containment pits, and ensuring compliance with Hydro One standards for drainage and erosion control.",
# #                 "required_activities": "Site preparation activities involve grading the station yard, modifying existing drainage systems, installing new roads and fences, and preparing engineering drawings for regulatory approvals. The work also includes ensuring erosion and sediment control during construction.",
# #                 "grading_and_roads": "Grading for new and existing station yards, installation of new roads, and modification of existing roads to facilitate work from other disciplines.",
# #                 "drainage_and_water_management": "Design and modification of station yard drainage systems, including spill containment pits and oil-water separators, ensuring compliance with Hydro One standards."
# #             }
# #         }
# #     }
    
# #     # Store component data
# #     print("🔄 Storing component data with new structure...")
# #     component_keys = handler.store_component_data(sample_component_data, "RPIRequestDataV4")
    
# #     print(f"\n✅ Stored {len(component_keys)} component records")
# #     for key in component_keys:
# #         print(f"   - {key}")





import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Union, Optional, Set
from azure.data.tables import TableServiceClient, TableEntity
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AzureTableMetadataHandler:
    """Enhanced handler for Azure Table Storage with metadata management for RFP/RFI documents and component data"""
    
    def __init__(self):
        """Initialize the Azure Table Storage handler"""
        self.connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if not self.connection_string:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING environment variable not found")
        
        self.table_service_client = TableServiceClient.from_connection_string(self.connection_string)
        
        # Cache for RFP GUIDs to associate RFIs
        self._rfp_guid_cache = {}
        print("✅ Azure Table Storage Handler initialized")
    
    def _create_table_if_not_exists(self, table_name: str):
        """Create table if it doesn't exist"""
        table_client = self.table_service_client.get_table_client(table_name=table_name)
        try:
            table_client.create_table()  # Will succeed if table doesn't exist
            print(f"✅ Created new table: {table_name}")
        except Exception as e:
            if "TableAlreadyExists" in str(e):
                pass  # Ignore - table is already there
            else:
                print(f"❌ Failed to create table {table_name}: {e}")
                raise
        return table_client

    def _generate_rfp_guid(self, project_id: str) -> str:
        """Generate or retrieve consistent GUID for RFP project"""
        if project_id in self._rfp_guid_cache:
            return self._rfp_guid_cache[project_id]
        
        # Generate new GUID and cache it
        rfp_guid = str(uuid.uuid4())
        self._rfp_guid_cache[project_id] = rfp_guid
        return rfp_guid
    
    def _get_rfp_guid_for_rfi(self, project_id: str, table_name: str) -> Optional[str]:
        """Get the RFP GUID for associating an RFI document"""
        # First check cache
        if project_id in self._rfp_guid_cache:
            return self._rfp_guid_cache[project_id]
        
        # Query the table for existing RFP with same project_id
        try:
            table_client = self.table_service_client.get_table_client(table_name=table_name)
            filter_query = f"ProjectId eq '{project_id}' and DocumentType eq 'RFP'"
            entities = list(table_client.query_entities(filter_query))
            
            if entities:
                rfp_guid = entities[0].get('RFP_GUID')
                if rfp_guid:
                    self._rfp_guid_cache[project_id] = rfp_guid
                    return rfp_guid
        except Exception as e:
            print(f"⚠️ Error querying for RFP GUID: {e}")
        
        # If no RFP found, create a new GUID (this RFI might come before its RFP)
        return self._generate_rfp_guid(project_id)
    
    def _sanitize_for_azure(self, value: Any) -> Any:
        """Sanitize individual values for Azure Table Storage"""
        if value is None:
            return ""
        elif isinstance(value, str):
            # Azure Table Storage has 64KB limit per property
            return value[:32000] if len(value) > 32000 else value
        elif isinstance(value, (list, dict)):
            return json.dumps(value, default=str)[:32000]  # Ensure JSON doesn't exceed limit
        else:
            return str(value)[:32000]  # Ensure string conversion doesn't exceed limit
    
    def store_file_metadata(self, metadata: Dict[str, Any], table_name: str = "FileMetadataV2") -> Optional[str]:
        """
        Store file metadata with enhanced RFI support
        
        Args:
            metadata: Dictionary containing file metadata (includes RFI enhanced fields)
            table_name: Name of the Azure table (default: "FileMetadataV2")
            
        Returns:
            Optional[str]: Entity key if successful, None if failed
        """
        try:
            # Create table client
            table_client = self._create_table_if_not_exists(table_name)
            
            # Extract key columns based on document type
            document_type = metadata.get('document_type', 'RFP')
            project_id = metadata.get('project_id', '')
            
            if document_type == 'RFI':
                # RFI specific columns
                key_columns = {
                    'project_name': metadata.get('project_name', ''),
                    'client': metadata.get('client', ''),
                    'region': metadata.get('region', ''),
                    'industry': metadata.get('industry', ''),
                    'document_type': document_type,
                    'project_id': project_id,
                    'prepared_date': metadata.get('prepared_date', ''),
                    'field_type': metadata.get('field_type', ''),
                    'voltage_class': metadata.get('voltage_class', ''),
                    'contract_types': metadata.get('contract_types', ''),
                    'pricing': metadata.get('pricing', '')
                }
            else:
                # RFP specific columns (existing logic)
                key_columns = {
                    'project_title': metadata.get('project_title', ''),
                    'client_name': metadata.get('client_name', ''),
                    'region': metadata.get('region', ''),
                    'industry': metadata.get('industry', ''),
                    'document_type': document_type,
                    'project_id': project_id
                }
            
            # Extract remaining fields for metadata JSON
            remaining_fields = {k: v for k, v in metadata.items() if k not in key_columns.keys()}
            
            # Create entity
            entity = TableEntity()
            
            # Set partition and row keys
            entity['PartitionKey'] = str(project_id) if project_id else f"unknown_{datetime.utcnow().strftime('%Y%m%d')}"
            entity['RowKey'] = f"{str(uuid.uuid4())[:8]}_{datetime.utcnow().isoformat().replace(':', '_').replace('-', '_')}"
            
            # Add common fields
            entity['DocumentType'] = self._sanitize_for_azure(document_type)
            entity['ProjectId'] = self._sanitize_for_azure(project_id)
            entity['Region'] = self._sanitize_for_azure(key_columns['region'])
            entity['Industry'] = self._sanitize_for_azure(key_columns.get('industry', ''))
            
            # Add document-type specific fields
            if document_type == 'RFI':
                entity['ProjectName'] = self._sanitize_for_azure(key_columns['project_name'])
                entity['Client'] = self._sanitize_for_azure(key_columns['client'])
                entity['PreparedDate'] = self._sanitize_for_azure(key_columns['prepared_date'])
                entity['FieldType'] = self._sanitize_for_azure(key_columns['field_type'])
                entity['VoltageClass'] = self._sanitize_for_azure(key_columns['voltage_class'])
                entity['ContractTypes'] = self._sanitize_for_azure(key_columns['contract_types'])
                entity['Pricing'] = self._sanitize_for_azure(key_columns['pricing'])
                
                # Store components count for RFI
                components = metadata.get('components', {})
                entity['ComponentsCount'] = len(components) if isinstance(components, dict) else 0
                entity['ComponentTypes'] = self._sanitize_for_azure(','.join(components.keys()) if isinstance(components, dict) else '')
            else:
                entity['ProjectTitle'] = self._sanitize_for_azure(key_columns['project_title'])
                entity['ClientName'] = self._sanitize_for_azure(key_columns['client_name'])
                # Add other RFP specific fields
                entity['VendorName'] = self._sanitize_for_azure(metadata.get('vendor_name', ''))
                entity['DomainCategory'] = self._sanitize_for_azure(metadata.get('domain_category', ''))
                entity['ServiceCategory'] = self._sanitize_for_azure(metadata.get('service_category', ''))
                entity['RevenueRange'] = self._sanitize_for_azure(metadata.get('revenue_range', ''))
                entity['ProjectValue'] = self._sanitize_for_azure(metadata.get('project_value', ''))
                entity['EquipmentsUsed'] = self._sanitize_for_azure(metadata.get('equipments_used', ''))
                entity['ComplianceStandard'] = self._sanitize_for_azure(metadata.get('compliance_standard', ''))

            # Handle GUID assignment based on document type
            if document_type.upper() == 'RFP':
                # For RFP, generate new GUID
                rfp_guid = self._generate_rfp_guid(project_id)
                entity['RFP_GUID'] = rfp_guid
            elif document_type.upper() == 'RFI':
                # For RFI, associate with existing RFP or create new GUID
                rfp_guid = self._get_rfp_guid_for_rfi(project_id, table_name)
                entity['RFP_GUID'] = rfp_guid
            else:
                # For other document types, create unique GUID
                entity['RFP_GUID'] = str(uuid.uuid4())
            
            # Add processing metadata
            entity['DetectionConfidence'] = float(metadata.get('detection_confidence', 0))
            entity['DetectionReasoning'] = self._sanitize_for_azure(metadata.get('detection_reasoning', ''))
            entity['ExtractionMethod'] = self._sanitize_for_azure(metadata.get('extraction_method', ''))
            entity['Filename'] = self._sanitize_for_azure(metadata.get('filename', ''))
            
            # Add metadata as JSON string (remaining fields)
            if remaining_fields:
                entity['Metadata'] = self._sanitize_for_azure(json.dumps(remaining_fields, default=str, ensure_ascii=False))
            
            # Add system fields
            entity['CreatedAt'] = datetime.utcnow().isoformat()
            entity['UpdatedAt'] = datetime.utcnow().isoformat()
            
            # Store to Azure
            table_client.create_entity(entity=entity)
            entity_key = f"{entity['PartitionKey']}_{entity['RowKey']}"
            
            print(f"✅ Successfully stored {document_type} metadata")
            print(f"   📄 Document: {metadata.get('filename', 'N/A')}")
            print(f"   🔑 Entity Key: {entity_key}")
            print(f"   🆔 RFP GUID: {entity['RFP_GUID']}")
            if document_type == 'RFI':
                print(f"   🧩 Components: {entity['ComponentsCount']} ({entity['ComponentTypes']})")
            
            return entity_key
            
        except Exception as e:
            print(f"❌ Error storing file metadata: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def store_component_data(self, data: Dict[str, Any], table_name: str = "ComponentDataV2") -> List[str]:
        """
        Store component data by creating separate records for each component (Enhanced for RFI)
        
        Args:
            data: Dictionary containing component data with RFI structure
            table_name: Name of the Azure table (default: "ComponentDataV2")
            
        Returns:
            List[str]: List of entity keys if successful, empty list if failed
        """
        try:
            # Create table client
            table_client = self._create_table_if_not_exists(table_name)
            
            # Extract common fields - Updated to match RFI JSON structure
            common_fields = {
                'chunk_id': data.get('chunk_id', ''),
                'project_id': data.get('project_id', ''),
                'project_name': data.get('project_name', ''),
                'content_type': data.get('content_type', ''),
                'client': data.get('client', ''),
                'region': data.get('region', ''),
                'industry': data.get('industry', ''),
                'prepared_date': data.get('prepared_date', ''),
                'field_type': data.get('field_type', ''),
                'voltage_class': data.get('voltage_class', ''),
                'contract_types': data.get('contract_types', ''),
                'pricing': data.get('pricing', '')
            }
            
            # Get components data
            components = data.get('components', {})
            
            if not components:
                print(f"ℹ️ No components found in data to store")
                return []
            
            entity_keys = []
            
            # Process each component
            for component_name, component_data in components.items():
                # Create entity for this component
                entity = TableEntity()
                
                # Set partition and row keys
                entity['PartitionKey'] = str(common_fields['project_id']) if common_fields['project_id'] else f"unknown_{datetime.utcnow().strftime('%Y%m%d')}"
                
                # Create component-specific chunk_id and row key
                component_chunk_id = f"{common_fields['chunk_id']}_{component_name}"
                entity['RowKey'] = f"comp_{component_chunk_id}_{datetime.utcnow().isoformat().replace(':', '_').replace('-', '_')}"
                
                # Add component key columns - Updated fields for RFI
                entity['ChunkId'] = self._sanitize_for_azure(component_chunk_id)
                entity['ProjectId'] = self._sanitize_for_azure(common_fields['project_id'])
                entity['ProjectName'] = self._sanitize_for_azure(common_fields['project_name'])
                entity['ContentType'] = self._sanitize_for_azure(common_fields['content_type'])
                entity['Client'] = self._sanitize_for_azure(common_fields['client'])
                entity['Region'] = self._sanitize_for_azure(common_fields['region'])
                entity['Industry'] = self._sanitize_for_azure(common_fields['industry'])
                entity['PreparedDate'] = self._sanitize_for_azure(common_fields['prepared_date'])
                entity['FieldType'] = self._sanitize_for_azure(common_fields['field_type'])
                entity['VoltageClass'] = self._sanitize_for_azure(common_fields['voltage_class'])
                entity['ContractTypes'] = self._sanitize_for_azure(common_fields['contract_types'])
                entity['Pricing'] = self._sanitize_for_azure(common_fields['pricing'])
                
                # Add component-specific fields
                entity['ComponentName'] = self._sanitize_for_azure(component_name)
                entity['ScopeOfWork'] = self._sanitize_for_azure(component_data.get('scope_of_work', ''))
                entity['RequiredActivities'] = self._sanitize_for_azure(component_data.get('required_activities', ''))
                
                # Handle component-specific fields based on component type
                component_specific_fields = {}
                
                if component_name == 'ELE':
                    component_specific_fields = {
                        'DisconnectSwitches': component_data.get('disconnect_switches', ''),
                        'Transformer': component_data.get('transformer', '')
                    }
                elif component_name == 'FND':
                    component_specific_fields = {
                        'TransformerFoundations': component_data.get('transformer_foundations', ''),
                        'EquipmentSupportFoundations': component_data.get('equipment_support_foundations', '')
                    }
                elif component_name == 'AUX':
                    component_specific_fields = {
                        'HVACAndFAS': component_data.get('HVAC_and_FAS', ''),
                        'HADsArrangements': component_data.get('HADs_arrangements', '')
                    }
                elif component_name == 'CNT':
                    component_specific_fields = {
                        'ControlDesignPackages': component_data.get('control_design_packages', ''),
                        'SCADAInfrastructure': component_data.get('SCADA_infrastructure', '')
                    }
                elif component_name == 'EQP':
                    component_specific_fields = {
                        'BusSystems': component_data.get('bus_systems', ''),
                        'CircuitBreakersAndDisconnects': component_data.get('circuit_breakers_and_disconnects', '')
                    }
                elif component_name == 'TEL':
                    component_specific_fields = {
                        'StationLANNetworks': component_data.get('station_lan_networks', ''),
                        'SCADAAndTransportInfrastructure': component_data.get('scada_and_transport_infrastructure', '')
                    }
                elif component_name == 'PRT':
                    component_specific_fields = {
                        'TransformerProtection': component_data.get('transformer_protection', ''),
                        'BreakerProtection': component_data.get('breaker_protection', '')
                    }
                elif component_name == 'STE':
                    component_specific_fields = {
                        'GradingAndRoads': component_data.get('grading_and_roads', ''),
                        'DrainageAndWaterManagement': component_data.get('drainage_and_water_management', '')
                    }
                elif component_name == 'STR':
                    component_specific_fields = {
                        'SteelAndStationStructures': component_data.get('steel_and_station_structures', ''),
                        'TransformerAndEquipmentStructures': component_data.get('transformer_and_equipment_structures', '')
                    }
                elif component_name == 'MET':
                    component_specific_fields = {
                        'NewMeteringInstallations': component_data.get('new_metering_installations', ''),
                        'ExistingMeteringRetainOrUpdate': component_data.get('existing_metering_retain_or_update', '')
                    }
                elif component_name == 'LN':
                    component_specific_fields = {
                        'LineRelocationsAndBypasses': component_data.get('line_relocations_and_bypasses', ''),
                        'LineReroutingAndExtensions': component_data.get('line_rerouting_and_extensions', '')
                    }
                
                # Add component-specific fields to entity
                for field_name, field_value in component_specific_fields.items():
                    entity[field_name] = self._sanitize_for_azure(field_value)
                
                # Store additional component data as JSON if any other fields exist
                known_fields = {'scope_of_work', 'required_activities'} | set(component_specific_fields.keys())
                other_fields = {k: v for k, v in component_data.items() if k not in [field.lower().replace('_', '') for field in known_fields]}
                
                if other_fields:
                    entity['AdditionalData'] = self._sanitize_for_azure(json.dumps(other_fields, default=str, ensure_ascii=False))
                
                # Generate unique GUID for this component record
                entity['RecordGUID'] = str(uuid.uuid4())
                
                # Add system timestamp
                entity['SystemCreatedAt'] = datetime.utcnow().isoformat()
                entity['SystemUpdatedAt'] = datetime.utcnow().isoformat()
                
                # Store to Azure
                table_client.create_entity(entity=entity)
                entity_key = f"{entity['PartitionKey']}_{entity['RowKey']}"
                entity_keys.append(entity_key)
                
                print(f"✅ Successfully stored component {component_name}")
                print(f"   🔑 Entity Key: {entity_key}")
                print(f"   🆔 Record GUID: {entity['RecordGUID']}")
                print(f"   📝 Scope Length: {len(component_data.get('scope_of_work', ''))} chars")
                print(f"   ⚙️ Activities Length: {len(component_data.get('required_activities', ''))} chars")
            
            return entity_keys
            
        except Exception as e:
            print(f"❌ Error storing component data: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_components_by_project(self, project_id: str, table_name: str = "ComponentDataV2") -> Dict[str, Any]:
        """
        Get all components for a specific project
        
        Args:
            project_id: Project ID to search for
            table_name: Table name to query
            
        Returns:
            Dictionary with project info and components
        """
        try:
            table_client = self.table_service_client.get_table_client(table_name=table_name)
            
            # Query for all components with this project_id
            filter_query = f"ProjectId eq '{project_id}'"
            entities = list(table_client.query_entities(filter_query))
            
            result = {
                'project_id': project_id,
                'project_info': None,
                'components': {}
            }
            
            for entity in entities:
                component_name = entity.get('ComponentName', '')
                
                if not result['project_info']:
                    result['project_info'] = {
                        'project_name': entity.get('ProjectName', ''),
                        'client': entity.get('Client', ''),
                        'industry': entity.get('Industry', ''),
                        'region': entity.get('Region', ''),
                        'prepared_date': entity.get('PreparedDate', ''),
                        'content_type': entity.get('ContentType', ''),
                        'field_type': entity.get('FieldType', ''),
                        'voltage_class': entity.get('VoltageClass', ''),
                        'contract_types': entity.get('ContractTypes', ''),
                        'pricing': entity.get('Pricing', '')
                    }
                
                component_info = {
                    'chunk_id': entity.get('ChunkId', ''),
                    'component_name': component_name,
                    'scope_of_work': entity.get('ScopeOfWork', ''),
                    'required_activities': entity.get('RequiredActivities', ''),
                    'record_guid': entity.get('RecordGUID', ''),
                    'created_at': entity.get('SystemCreatedAt', '')
                }
                
                # Add component-specific fields based on component type
                if component_name == 'ELE':
                    component_info.update({
                        'disconnect_switches': entity.get('DisconnectSwitches', ''),
                        'transformer': entity.get('Transformer', '')
                    })
                elif component_name == 'FND':
                    component_info.update({
                        'transformer_foundations': entity.get('TransformerFoundations', ''),
                        'equipment_support_foundations': entity.get('EquipmentSupportFoundations', '')
                    })
                elif component_name == 'AUX':
                    component_info.update({
                        'hvac_and_fas': entity.get('HVACAndFAS', ''),
                        'hads_arrangements': entity.get('HADsArrangements', '')
                    })
                elif component_name == 'CNT':
                    component_info.update({
                        'control_design_packages': entity.get('ControlDesignPackages', ''),
                        'scada_infrastructure': entity.get('SCADAInfrastructure', '')
                    })
                elif component_name == 'EQP':
                    component_info.update({
                        'bus_systems': entity.get('BusSystems', ''),
                        'circuit_breakers_and_disconnects': entity.get('CircuitBreakersAndDisconnects', '')
                    })
                elif component_name == 'TEL':
                    component_info.update({
                        'station_lan_networks': entity.get('StationLANNetworks', ''),
                        'scada_and_transport_infrastructure': entity.get('SCADAAndTransportInfrastructure', '')
                    })
                elif component_name == 'PRT':
                    component_info.update({
                        'transformer_protection': entity.get('TransformerProtection', ''),
                        'breaker_protection': entity.get('BreakerProtection', '')
                    })
                elif component_name == 'STE':
                    component_info.update({
                        'grading_and_roads': entity.get('GradingAndRoads', ''),
                        'drainage_and_water_management': entity.get('DrainageAndWaterManagement', '')
                    })
                elif component_name == 'STR':
                    component_info.update({
                        'steel_and_station_structures': entity.get('SteelAndStationStructures', ''),
                        'transformer_and_equipment_structures': entity.get('TransformerAndEquipmentStructures', '')
                    })
                elif component_name == 'MET':
                    component_info.update({
                        'new_metering_installations': entity.get('NewMeteringInstallations', ''),
                        'existing_metering_retain_or_update': entity.get('ExistingMeteringRetainOrUpdate', '')
                    })
                elif component_name == 'LN':
                    component_info.update({
                        'line_relocations_and_bypasses': entity.get('LineRelocationsAndBypasses', ''),
                        'line_rerouting_and_extensions': entity.get('LineReroutingAndExtensions', '')
                    })
                
                # Add additional data if exists
                if entity.get('AdditionalData'):
                    try:
                        additional_data = json.loads(entity['AdditionalData'])
                        component_info['additional_data'] = additional_data
                    except:
                        pass
                
                result['components'][component_name] = component_info
            
            return result
            
        except Exception as e:
            print(f"❌ Error querying component data: {str(e)}")
            return {}
    
    def get_rfp_with_associated_rfis(self, project_id: str, table_name: str = "FileMetadataV2") -> Dict[str, Any]:
        """
        Get RFP and all associated RFIs for a project (Updated for enhanced metadata)
        
        Args:
            project_id: Project ID to search for
            table_name: Table name to query
            
        Returns:
            Dictionary with RFP and associated RFIs
        """
        try:
            table_client = self.table_service_client.get_table_client(table_name=table_name)
            
            # Query for all documents with this project_id
            filter_query = f"ProjectId eq '{project_id}'"
            entities = list(table_client.query_entities(filter_query))
            
            result = {
                'project_id': project_id,
                'rfp': None,
                'rfis': [],
                'other_documents': []
            }
            
            for entity in entities:
                doc_type = entity.get('DocumentType', '').upper()
                
                # Parse metadata back to dict
                metadata = {}
                if entity.get('Metadata'):
                    try:
                        metadata = json.loads(entity['Metadata'])
                    except:
                        pass
                
                # Create document info based on type
                if doc_type == 'RFI':
                    doc_info = {
                        'document_type': entity.get('DocumentType', ''),
                        'project_name': entity.get('ProjectName', ''),
                        'client': entity.get('Client', ''),
                        'region': entity.get('Region', ''),
                        'industry': entity.get('Industry', ''),
                        'prepared_date': entity.get('PreparedDate', ''),
                        'field_type': entity.get('FieldType', ''),
                        'voltage_class': entity.get('VoltageClass', ''),
                        'contract_types': entity.get('ContractTypes', ''),
                        'pricing': entity.get('Pricing', ''),
                        'components_count': entity.get('ComponentsCount', 0),
                        'component_types': entity.get('ComponentTypes', ''),
                        'rfp_guid': entity.get('RFP_GUID', ''),
                        'created_at': entity.get('CreatedAt', ''),
                        'metadata': metadata,
                        'entity_key': f"{entity['PartitionKey']}_{entity['RowKey']}"
                    }
                else:
                    doc_info = {
                        'document_type': entity.get('DocumentType', ''),
                        'project_title': entity.get('ProjectTitle', ''),
                        'client_name': entity.get('ClientName', ''),
                        'region': entity.get('Region', ''),
                        'industry': entity.get('Industry', ''),
                        'vendor_name': entity.get('VendorName', ''),
                        'domain_category': entity.get('DomainCategory', ''),
                        'rfp_guid': entity.get('RFP_GUID', ''),
                        'created_at': entity.get('CreatedAt', ''),
                        'metadata': metadata,
                        'entity_key': f"{entity['PartitionKey']}_{entity['RowKey']}"
                    }
                
                if doc_type == 'RFP':
                    result['rfp'] = doc_info
                elif doc_type == 'RFI':
                    result['rfis'].append(doc_info)
                else:
                    result['other_documents'].append(doc_info)
            
            return result
            
        except Exception as e:
            print(f"❌ Error querying project data: {str(e)}")
            return {}
    
    def query_by_criteria(self, table_name: str, **criteria) -> List[TableEntity]:
        """
        Query entities by various criteria (Enhanced for RFI fields)
        
        Args:
            table_name: Table name to query
            **criteria: Query criteria (client, industry, document_type, field_type, etc.)
            
        Returns:
            List of matching entities
        """
        try:
            table_client = self.table_service_client.get_table_client(table_name=table_name)
            
            # Build filter query
            filters = []
            for key, value in criteria.items():
                key_lower = key.lower()
                if key_lower == 'client':
                    filters.append(f"Client eq '{value}'")
                elif key_lower == 'client_name':
                    filters.append(f"ClientName eq '{value}'")
                elif key_lower == 'industry':
                    filters.append(f"Industry eq '{value}'")
                elif key_lower == 'document_type':
                    filters.append(f"DocumentType eq '{value}'")
                elif key_lower == 'project_id':
                    filters.append(f"ProjectId eq '{value}'")
                elif key_lower == 'region':
                    filters.append(f"Region eq '{value}'")
                elif key_lower == 'component_name':
                    filters.append(f"ComponentName eq '{value}'")
                elif key_lower == 'field_type':
                    filters.append(f"FieldType eq '{value}'")
                elif key_lower == 'voltage_class':
                    filters.append(f"VoltageClass eq '{value}'")
                elif key_lower == 'contract_types':
                    filters.append(f"ContractTypes eq '{value}'")
                elif key_lower == 'project_name':
                    filters.append(f"ProjectName eq '{value}'")
                elif key_lower == 'project_title':
                    filters.append(f"ProjectTitle eq '{value}'")
            
            if filters:
                filter_query = " and ".join(filters)
                entities = list(table_client.query_entities(filter_query))
            else:
                entities = list(table_client.list_entities())
            
            return entities
            
        except Exception as e:
            print(f"❌ Error querying by criteria: {str(e)}")
            return []

    def get_all_rfis_with_component_counts(self, table_name: str = "FileMetadataV2") -> List[Dict[str, Any]]:
        """
        Get all RFIs with count of associated components
        
        Args:
            table_name: Table name to query
            
        Returns:
            List of RFI information with component counts
        """
        try:
            table_client = self.table_service_client.get_table_client(table_name=table_name)
            
            # Get all RFI entities
            filter_query = "DocumentType eq 'RFI'"
            entities = list(table_client.query_entities(filter_query))
            
            result = []
            
            for entity in entities:
                rfi_info = {
                    'project_id': entity.get('ProjectId', ''),
                    'project_name': entity.get('ProjectName', ''),
                    'client': entity.get('Client', ''),
                    'region': entity.get('Region', ''),
                    'industry': entity.get('Industry', ''),
                    'prepared_date': entity.get('PreparedDate', ''),
                    'field_type': entity.get('FieldType', ''),
                    'voltage_class': entity.get('VoltageClass', ''),
                    'contract_types': entity.get('ContractTypes', ''),
                    'pricing': entity.get('Pricing', ''),
                    'components_count': entity.get('ComponentsCount', 0),
                    'component_types': entity.get('ComponentTypes', '').split(',') if entity.get('ComponentTypes') else [],
                    'rfp_guid': entity.get('RFP_GUID', ''),
                    'created_at': entity.get('CreatedAt', ''),
                    'entity_key': f"{entity['PartitionKey']}_{entity['RowKey']}"
                }
                result.append(rfi_info)
            
            return sorted(result, key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            print(f"❌ Error getting RFI summary: {str(e)}")
            return []