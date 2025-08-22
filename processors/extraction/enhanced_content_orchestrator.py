
# import os
# from typing import Dict, List
# from storage.storage_factory import get_storage_instance
# from llm_metadata import RFIExtractor, RFPExtractor
# from llm_metadata.document_type_detector import DocumentTypeDetector
# from .text_extractor import TextExtractor
# from .table_extractor import TableExtractor
# from .image_extractor import ImageExtractor
# from .section_mapper import SectionMapper
# from data_indexing.data_to_rfp_indexer import AzureSearchRFPResponseUploader
# from data_indexing.data_to_rfi_indexer import AzureSearchRFPRequestUploader
# from config import (AZURE_AI_SEARCH_ENDPOINT, AZURE_AI_SEARCH_KEY, AZURE_AI_SEARCH_RFI_INDEX_NAME,
#     AZURE_AI_SEARCH_RFP_INDEX_NAME, ENABLE_DOCUMENT_TYPE_DETECTION, DEFAULT_DOCUMENT_TYPE)


# class ContentExtractor:
#     """Extract and process content with RFI NO-CHUNKING flow and RFP normal chunking flow"""
    
#     def __init__(self):
#         self.storage = get_storage_instance()
#         self.text_elements = []
#         self.text_chunks = []
#         self.document_metadata = {}
#         self.document_type = "RFP"  # Default document type
#         self.document_type_info = {}
        
#         # Initialize components
#         self.type_detector = DocumentTypeDetector()
#         self.data_indexing_RFP_request = AzureSearchRFPRequestUploader()
#         self.data_indexing_RFP_response = AzureSearchRFPResponseUploader()
#         self.text_extractor = TextExtractor()
#         self.table_extractor = TableExtractor()
#         self.image_extractor = ImageExtractor()
#         self.section_mapper = SectionMapper()

#     def _extract_project_id_from_filename(self, filename: str) -> str:
#         """Extract project ID (first 15 characters) from filename"""
#         if not filename:
#             return "unknown_project"
        
#         base_name = os.path.splitext(filename)[0]
#         project_id = base_name[:15] if len(base_name) >= 15 else base_name
#         print(f"🔑 Extracted Project ID: {project_id}")
#         return project_id
    
#     async def extract_all_content(self, result, filename: str, client=None, operation_id=None) -> Dict:
#         """Extract content with RFI NO-CHUNKING flow or RFP normal chunking flow"""
#         base_filename = os.path.splitext(filename)[0]
        
#         print(f"🔍 Extracting content from {filename}...")
#         print(f"📋 Debug: client={client is not None}, operation_id={operation_id}")
        
#         # Step 1: Extract text elements using Azure DI
#         print(f"📋 Step 1: Extracting text elements...")
#         self.text_elements = self.text_extractor.extract_text(result)
#         print(f"📋 Text elements extracted: {len(self.text_elements)}")

#         # Extract project ID from filename
#         project_id = self._extract_project_id_from_filename(filename)
        
#         # Step 2: Document type selection (Auto-detect or Hardcoded)
#         if ENABLE_DOCUMENT_TYPE_DETECTION:
#             print(f"📄 Step 1.2: Auto-detecting document type (RFI vs RFP)...")
#             self.document_type_info = self.type_detector.detect_document_type(self.text_elements)
#             self.document_type = self.document_type_info.get('document_type', 'RFP')
#             self.type_detector.print_detection_summary(self.document_type_info)
#         else:
#             self.document_type = DEFAULT_DOCUMENT_TYPE
#             print(f"🔒 HARDCODED: Using {self.document_type} extractor (detection disabled)")
#             self.document_type_info = {
#                 'document_type': self.document_type,
#                 'confidence': 1.0,
#                 'reasoning': 'Hardcoded configuration setting'
#             }
        
#         document_type_folder = "rfp_request" if self.document_type == "RFI" else "rfp_response"
#         self.storage.set_project_context(filename, document_type_folder)    

#         # Step 3: Extract tables and images (ALWAYS - both RFI and RFP)
#         print(f"📋 Step 3: Extracting tables with section association...")
#         tables = self.table_extractor.extract_tables(result, base_filename, self.section_mapper, self.storage)

#         print(f"📋 Step 4: Extracting figures with section association...")
#         figures = self.image_extractor.extract_figures(result, base_filename, client, operation_id, self.section_mapper, self.text_elements, self.storage)
        
#         # Step 4: Branch based on document type
#         if self.document_type == "RFI":
#             return await self._process_rfi_no_chunking(base_filename, filename, project_id, tables, figures)
#         else:
#             return await self._process_rfp_with_chunking(base_filename, filename, project_id, tables, figures)

#     async def _process_rfi_no_chunking(self, base_filename: str, filename: str, project_id: str, tables: List[Dict], figures: List[Dict]) -> Dict:
#         """Process RFI documents - NO CHUNKING, only metadata extraction and indexing"""
#         print(f"🚫 RFI PROCESSING: NO CHUNKING - Metadata extraction only")
        
#         # Step 1: Extract RFI metadata using NEW fields (NO chunking)
#         print(f"🤖 Step 1: Extracting RFI metadata using LLM (NEW FIELDS - NO CHUNKING)...")
#         rfi_extractor = RFIExtractor()
#         self.document_metadata = await rfi_extractor.extract_metadata_only(self.text_elements)
#         print(f"📋 RFI metadata extracted: {len(self.document_metadata)} NEW fields")
        
#         # Step 2: Create single metadata document for indexing (NO text chunks)
#         print(f"📤 Step 2: Creating single metadata document for RFI indexing...")
#         rfi_metadata_document = self._create_rfi_metadata_document(self.document_metadata, base_filename, project_id)
        
#         # Step 3: Index only the metadata document (NO chunks)
#         print(f"📤 Step 3: Indexing RFI metadata document (NO CHUNKS)...")
#         metadata_list = [rfi_metadata_document]  # Single document in list format
#         chunk_data_for_indexing = {
#             "filename": filename,
#             "total_chunks": 1,  # Only one metadata document
#             "processing_method": "rfi_metadata_only_no_chunking",
#             "chunks": metadata_list
#         }
        
#         # Upload to RFI index
#         try:
#             self.data_indexing_RFP_request.upload_chunks_from_dict(chunk_data_for_indexing)
#             print(f"✅ RFI metadata uploaded to Azure AI Search (NO CHUNKS)")
#         except Exception as e:
#             print(f"❌ Error uploading RFI metadata: {e}")
        
#         # Step 4: Save ONLY the single RFI metadata document locally (NO chunking files)
#         if rfi_metadata_document:
#             print(f"💾 Saving single RFI metadata document locally...")
#             single_document_list = [rfi_metadata_document]
#             chunk_data, json_path = self.storage.save_text_chunks(single_document_list, base_filename)
#             print(f"✅ Single RFI metadata document saved locally: {json_path}")
#         else:
#             print(f"⚠️ No RFI metadata document to save")
        
#         print(f"✅ RFI processing complete - NO CHUNKING!")
#         self._print_rfi_debug(all_text, tables, figures)
        
#         return {
#             "text": all_text,
#             "text_chunks": [],  # NO chunks for RFI
#             "tables": tables,
#             "images": figures,
#             "raw_text": all_text,
#             "document_metadata": self.document_metadata,
#             "document_type": self.document_type,
#             "document_type_info": self.document_type_info,
#             "project_id": project_id,
#             "rfi_processing_mode": "metadata_only_no_chunking",
#             "stats": {
#                 "text_count": 0,  # NO text chunks for RFI
#                 "table_count": len(tables),
#                 "image_count": len(figures),
#                 "total_chunks": 0,  # NO chunks for RFI
#                 "metadata_documents": 1  # Only metadata document
#             }
#         }

#     async def _process_rfp_with_chunking(self, base_filename: str, filename: str, project_id: str, tables: List[Dict], figures: List[Dict]) -> Dict:
#         """Process RFP documents - NORMAL CHUNKING flow (existing code)"""
#         print(f"✅ RFP PROCESSING: NORMAL CHUNKING - Full chunking flow")
        
#         # Extract RFP ID for chunks
#         all_text = "\n\n".join([f"[{elem.get('role', 'unknown')}] {elem['content']}" for elem in self.text_elements])
#         rfp_id = self.text_extractor.extract_rfp_id_from_text(all_text)
#         print(f"🔑 Extracted RFP ID for all chunks: {rfp_id}")
        
#         # Step 1: Extract RFP metadata using existing fields
#         print(f"🤖 Step 1: Extracting RFP metadata using LLM from complete document...")
#         rfp_extractor = RFPExtractor()
#         self.document_metadata = await rfp_extractor.extract_metadata(self.text_elements)
#         print(f"📋 RFP metadata extracted: {len(self.document_metadata)} fields")
                
#         # Step 2: Create text chunks with LLM metadata using SimpleChunker
#         print(f"📋 Step 2: Creating text chunks with LLM metadata using SimpleChunker...")
#         self.text_chunks = self.text_extractor.create_text_chunks_with_simple_chunker(
#             self.text_elements, 
#             self.document_metadata, 
#             project_id
#         )
#         print(f"📋 Text chunks created: {len(self.text_chunks)}")
        
#         # Step 3: Create table and image chunks with verbalization
#         print(f"🤖 Creating table chunks with verbalization, section mapping, and LLM metadata...")
#         table_chunks = await self.table_extractor.create_table_chunks(
#             tables, 
#             base_filename, 
#             self.document_metadata, 
#             self.section_mapper, 
#             self.text_elements, 
#             rfp_id=rfp_id, 
#             project_id=project_id
#         )

#         print(f"🤖 Creating image chunks with verbalization, section mapping, and LLM metadata...")
#         image_chunks = await self.image_extractor.create_image_chunks(
#             figures, 
#             base_filename, 
#             self.document_metadata, 
#             self.section_mapper, 
#             self.text_elements, 
#             rfp_id=rfp_id, 
#             project_id=project_id
#         )

#         # Step 4: Combine all chunks and save
#         all_chunks = self.text_chunks + table_chunks + image_chunks
        
#         if all_chunks:
#             print(f"📋 Saving enhanced text chunks to local storage...")
#             chunk_data, json_path = self.storage.save_text_chunks(all_chunks, base_filename)
            
#             if chunk_data:
#                 self.data_indexing_RFP_response.upload_chunks_from_dict(chunk_data)
#                 print(f"✅ RFP chunks uploaded to Azure AI Search")

#         # Save text content to local storage
#         if all_text.strip():
#             self.storage.save_raw_text(all_text, base_filename)
        
#         print(f"✅ RFP processing complete with full chunking!")
#         self._print_rfp_debug(all_text, self.text_chunks, tables, figures, table_chunks, image_chunks)
        
#         return {
#             "text": all_text,
#             "text_chunks": all_chunks,
#             "tables": tables,
#             "images": figures,
#             "raw_text": all_text,
#             "document_metadata": self.document_metadata,
#             "document_type": self.document_type,
#             "document_type_info": self.document_type_info,
#             "project_id": project_id,
#             "stats": {
#                 "text_count": len(self.text_chunks),
#                 "table_count": len(table_chunks),
#                 "image_count": len(image_chunks),
#                 "total_chunks": len(all_chunks)
#             }
#         }

#     def _create_rfi_metadata_document(self, metadata: Dict, base_filename: str, project_id: str) -> Dict:
#         """Create a single RFI metadata document for indexing (NO chunking) - NEW 8 FIELDS ONLY"""
#         import uuid
#         from datetime import datetime
        
#         # Create a single metadata document with ONLY the new 8 RFI fields + project_id
#         rfi_document = {
#             'chunk_id': str(uuid.uuid4())[:8],
#             'project_id': project_id,  # From filename (15 chars)
#             'file_name': base_filename,
#             'section_name': 'RFI_METADATA_DOCUMENT', 
#             'section_no': 'METADATA',
#             'domain': metadata.get('industry', 'Not Specified'),
#             'content_type': 'rfi_metadata',
#             'author': 'rfi_system',
#             'content': f"RFI: {metadata.get('project_name', 'Unknown')} - {metadata.get('scope_of_work', 'No scope')[:100]}",
#             'verbalized_content': f"RFI for {metadata.get('project_name', 'Unknown')} in {metadata.get('region', 'Unknown')}. Scope: {metadata.get('scope_of_work', 'Not specified')[:200]}. Activities: {metadata.get('required_activities', 'Not specified')[:200]}.",
#             'metadata': {
#                 'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#                 'chunk_index': 0,
#                 'word_count': len(str(metadata.get('scope_of_work', '') + ' ' + metadata.get('required_activities', '')).split()),
#                 'char_count': len(str(metadata)),
#                 # ONLY the 8 new RFI fields in metadata
#                 'llm_extracted_metadata': {
#                     'project_name': metadata.get('project_name', 'Not Specified'),
#                     'client': metadata.get('client', 'Not Specified'),
#                     'region': metadata.get('region', 'Not Specified'),
#                     'industry': metadata.get('industry', 'Not Specified'),
#                     'prepared_date': metadata.get('prepared_date', 'Not Specified'),
#                     'station_discipline': metadata.get('station_discipline', 'Not Specified'),
#                     'scope_of_work': metadata.get('scope_of_work', 'Not Specified'),
#                     'required_activities': metadata.get('required_activities', 'Not Specified')
#                 }
#             }
#         }
        
#         return rfi_document

#     def _print_rfi_debug(self, all_text: str, tables: List[Dict], figures: List[Dict]):
#         """Print RFI processing debug info (NO chunking)"""
#         print(f"\n{'='*80}")
#         print(f"🚫 RFI PROCESSING RESULTS - NO CHUNKING")
#         print(f"{'='*80}")
#         print(f"🎯 Document Type: {self.document_type}")
#         print(f"📄 Processing Mode: METADATA ONLY - NO CHUNKING")
#         print(f"📊 Confidence: {self.document_type_info.get('confidence', 0):.1%}")
        
#         print(f"\n🤖 RFI METADATA EXTRACTED (NEW FIELDS - NO DOC_ID):")
#         print(f"   📝 Project Name: {self.document_metadata.get('project_name', 'N/A')}")
#         print(f"   🔑 Project ID: {project_id} (from filename)")
#         print(f"   🏢 Client: {self.document_metadata.get('client', 'N/A')}")
#         print(f"   🌍 Region: {self.document_metadata.get('region', 'N/A')}")
#         print(f"   🏭 Industry: {self.document_metadata.get('industry', 'N/A')}")
#         print(f"   📅 Prepared Date: {self.document_metadata.get('prepared_date', 'N/A')}")
#         print(f"   ⚡ Station Discipline: {self.document_metadata.get('station_discipline', 'N/A')}")
#         print(f"   📋 Scope of Work: {len(str(self.document_metadata.get('scope_of_work', '')))} characters")
#         print(f"   🎯 Required Activities: {len(str(self.document_metadata.get('required_activities', '')))} characters")
        
#         print(f"\n📊 EXTRACTION SUMMARY:")
#         print(f"   🚫 Text chunks: 0 (NO CHUNKING for RFI)")
#         print(f"   📋 Tables extracted: {len(tables)}")
#         print(f"   🖼️ Images extracted: {len(figures)}")
#         print(f"   📤 Metadata documents for indexing: 1")
#         print(f"   💾 Local storage: Single metadata document saved")
#         print(f"   🔍 Raw text length: {len(all_text)} characters")
        
#         print(f"\n📋 SINGLE RFI METADATA DOCUMENT STRUCTURE:")
#         print(f"   🔑 chunk_id: Generated UUID")
#         print(f"   🔑 project_id: {project_id} (from filename)")
#         print(f"   📝 content_type: rfi_metadata")
#         print(f"   📄 metadata.llm_extracted_metadata: 8 fields only")
#         print(f"   🚫 NO: document_id, submission_date, duration, rfi_description")
#         print(f"   ✅ ONLY: project_name, client, region, industry, prepared_date, station_discipline, scope_of_work, required_activities")
        
#         print(f"✅ RFI metadata-only processing complete!")
#         print(f"{'='*80}")

#     def _print_rfp_debug(self, all_text: str, text_chunks: List[Dict], tables: List[Dict], 
#                         figures: List[Dict], table_chunks: List[Dict], image_chunks: List[Dict]):
#         """Print RFP processing debug info (normal chunking)"""
#         print(f"\n{'='*80}")
#         print(f"✅ RFP PROCESSING RESULTS - FULL CHUNKING")
#         print(f"{'='*80}")
#         print(f"🎯 Document Type: {self.document_type}")
#         print(f"📄 Processing Mode: FULL CHUNKING ENABLED")
#         print(f"📊 Confidence: {self.document_type_info.get('confidence', 0):.1%}")
        
#         # Print RFP metadata (existing fields)
#         print(f"\n🤖 RFP METADATA EXTRACTED:")
#         print(f"   📝 Project Title: {self.document_metadata.get('project_title', 'N/A')}")
#         print(f"   🏢 Client Name: {self.document_metadata.get('client_name', 'N/A')}")
#         print(f"   🏭 Vendor Name: {self.document_metadata.get('vendor_name', 'N/A')}")
#         print(f"   📅 Submission Date: {self.document_metadata.get('submission_date', 'N/A')}")
#         print(f"   🏷️ Domain Category: {self.document_metadata.get('domain_category', 'N/A')}")
#         print(f"   ⚙️ Service Category: {self.document_metadata.get('service_category', 'N/A')}")
#         print(f"   💰 Revenue Range: {self.document_metadata.get('revenue_range', 'N/A')}")
#         print(f"   🌍 Region: {self.document_metadata.get('region', 'N/A')}")
#         print(f"   💵 Project Value: {self.document_metadata.get('project_value', 'N/A')}")
#         print(f"   📜 Compliance Standard: {self.document_metadata.get('compliance_standard', 'N/A')}")
#         print(f"   🔧 Equipments Used: {self.document_metadata.get('equipments_used', 'N/A')}")
        
#         print(f"\n📊 CHUNKING SUMMARY:")
#         print(f"   📝 Text chunks: {len(text_chunks)}")
#         print(f"   📊 Table chunks: {len(table_chunks)}")
#         print(f"   🖼️ Image chunks: {len(image_chunks)}")
#         print(f"   📋 Tables extracted: {len(tables)}")
#         print(f"   🖼️ Images extracted: {len(figures)}")
#         print(f"   📤 Total chunks for indexing: {len(text_chunks) + len(table_chunks) + len(image_chunks)}")
#         print(f"✅ RFP full chunking processing complete!")
#         print(f"{'='*80}")

#     # Additional debugging method
#     def _print_extraction_debug(self, all_text: str, text_chunks: List[Dict], tables: List[Dict], 
#                                figures: List[Dict], table_chunks: List[Dict], image_chunks: List[Dict]):
#         """Legacy debug method - redirects to appropriate debug method"""
#         if self.document_type == "RFI":
#             self._print_rfi_debug(all_text, tables, figures)
#         else:
#             self._print_rfp_debug(all_text, text_chunks, tables, figures, table_chunks, image_chunks)


import os
from typing import Dict, List
from storage.storage_factory import get_storage_instance
from llm_metadata import RFIExtractor, RFPExtractor
from llm_metadata.document_type_detector import DocumentTypeDetector
from .text_extractor import TextExtractor
from .table_extractor import TableExtractor
from .image_extractor import ImageExtractor
from .section_mapper import SectionMapper
from data_indexing.data_to_rfp_indexer import AzureSearchRFPResponseUploader
from data_indexing.data_to_rfi_indexer import AzureSearchRFPRequestUploader
from config import (AZURE_AI_SEARCH_ENDPOINT, AZURE_AI_SEARCH_KEY, AZURE_AI_SEARCH_RFI_INDEX_NAME,
    AZURE_AI_SEARCH_RFP_INDEX_NAME, ENABLE_DOCUMENT_TYPE_DETECTION, DEFAULT_DOCUMENT_TYPE)


class ContentExtractor:
    """Extract and process content with RFI NO-CHUNKING flow and RFP normal chunking flow"""
    
    def __init__(self):
        self.storage = get_storage_instance()
        self.text_elements = []
        self.text_chunks = []
        self.document_metadata = {}
        self.document_type = "RFI"  # Default document type
        self.document_type_info = {}
        
        # Initialize components
        self.type_detector = DocumentTypeDetector()
        self.data_indexing_RFP_request = AzureSearchRFPRequestUploader()
        self.data_indexing_RFP_response = AzureSearchRFPResponseUploader()
        self.text_extractor = TextExtractor()
        self.table_extractor = TableExtractor()
        self.image_extractor = ImageExtractor()
        self.section_mapper = SectionMapper()

    def _extract_project_id_from_filename(self, filename: str) -> str:
        """Extract project ID (first 15 characters) from filename"""
        if not filename:
            return "unknown_project"
        
        base_name = os.path.splitext(filename)[0]
        project_id = base_name[:15] if len(base_name) >= 15 else base_name
        print(f"🔑 Extracted Project ID: {project_id}")
        return project_id
    
    async def extract_all_content(self, result, filename: str, client=None, operation_id=None) -> Dict:
        """Extract content with RFI NO-CHUNKING flow or RFP normal chunking flow"""
        base_filename = os.path.splitext(filename)[0]
        
        print(f"🔍 Extracting content from {filename}...")
        print(f"📋 Debug: client={client is not None}, operation_id={operation_id}")
        
        # Step 1: Extract text elements using Azure DI
        print(f"📋 Step 1: Extracting text elements...")
        self.text_elements = self.text_extractor.extract_text(result)
        print(f"📋 Text elements extracted: {len(self.text_elements)}")

        # Extract project ID from filename
        project_id = self._extract_project_id_from_filename(filename)
        
        # Step 2: Document type selection (Auto-detect or Hardcoded)
        if ENABLE_DOCUMENT_TYPE_DETECTION:
            print(f"📄 Step 1.2: Auto-detecting document type (RFI vs RFP)...")
            self.document_type_info = self.type_detector.detect_document_type(self.text_elements)
            self.document_type = self.document_type_info.get('document_type', 'RFP')
            self.type_detector.print_detection_summary(self.document_type_info)
        else:
            self.document_type = DEFAULT_DOCUMENT_TYPE
            print(f"🔒 HARDCODED: Using {self.document_type} extractor (detection disabled)")
            self.document_type_info = {
                'document_type': self.document_type,
                'confidence': 1.0,
                'reasoning': 'Hardcoded configuration setting'
            }
        
        document_type_folder = "rfp_request" if self.document_type == "RFI" else "rfp_response"
        self.storage.set_project_context(filename, document_type_folder)    

        # Step 3: Branch based on document type
        if self.document_type == "RFI":
            return await self._process_rfi_no_chunking(base_filename, filename, project_id, result, client, operation_id)
        else:
            return await self._process_rfp_with_chunking(base_filename, filename, project_id, result, client, operation_id)

    async def _process_rfi_no_chunking(self, base_filename: str, filename: str, project_id: str, result, client=None, operation_id=None) -> Dict:
        """Process RFI documents - NO CHUNKING, NO VERBALIZATION, only metadata extraction and basic storage"""
        print(f"🚫 RFI PROCESSING: NO CHUNKING, NO VERBALIZATION - Metadata extraction only")
        
        # Step 1: Extract RFI metadata using 8 fields (NO chunking)
        print(f"🤖 Step 1: Extracting RFI metadata using LLM (8 FIELDS - NO CHUNKING)...")
        rfi_extractor = RFIExtractor()
        self.document_metadata = await rfi_extractor.extract_metadata_only(self.text_elements)
        print(f"📋 RFI metadata extracted: {len(self.document_metadata)} fields")
        
        # Step 2: Extract tables and images WITHOUT verbalization
        print(f"📋 Step 2: Extracting tables WITHOUT verbalization...")
        tables = self.table_extractor.extract_tables(result, base_filename, self.section_mapper, self.storage)

        print(f"📋 Step 3: Extracting figures WITHOUT verbalization...")
        figures = self.image_extractor.extract_figures(result, base_filename, client, operation_id, self.section_mapper, self.text_elements, self.storage)
        
        # Step 3: Create single metadata document for indexing (NO text chunks)
        print(f"📤 Step 3: Creating single metadata document for RFI indexing...")
        rfi_metadata_document = self._create_rfi_metadata_document(self.document_metadata, base_filename, project_id)
        
        # Step 4: Index only the metadata document (NO chunks)
        print(f"📤 Step 4: Indexing RFI metadata document (NO CHUNKS)...")
        metadata_list = [rfi_metadata_document]  # Single document in list format
        chunk_data_for_indexing = {
            "filename": filename,
            "total_chunks": 1,  # Only one metadata document
            "processing_method": "rfi_metadata_only_no_chunking",
            "chunks": metadata_list
        }
        
        # Upload to RFI index
        try:
            self.data_indexing_RFP_request.upload_chunks_from_dict(chunk_data_for_indexing)
            print(f"✅ RFI metadata uploaded to Azure AI Search (NO CHUNKS)")
        except Exception as e:
            print(f"❌ Error uploading RFI metadata: {e}")
        
        # Step 5: Save ONLY the single RFI metadata document locally (NO chunking files)
        if rfi_metadata_document:
            print(f"💾 Saving single RFI metadata document locally...")
            single_document_list = [rfi_metadata_document]
            chunk_data, json_path = self.storage.save_text_chunks(single_document_list, base_filename)
            print(f"✅ Single RFI metadata document saved locally: {json_path}")
        else:
            print(f"⚠️ No RFI metadata document to save")
        
        # Step 6: Save raw text separately
        all_text = "\n\n".join([f"[{elem.get('role', 'unknown')}] {elem['content']}" for elem in self.text_elements])
        if all_text.strip():
            self.storage.save_raw_text(all_text, base_filename)
        
        print(f"✅ RFI processing complete - NO CHUNKING, NO VERBALIZATION!")
        self._print_rfi_debug(all_text, tables, figures, project_id)
        
        return {
            "text": all_text,
            "text_chunks": [],  # NO chunks for RFI
            "tables": tables,
            "images": figures,
            "raw_text": all_text,
            "document_metadata": self.document_metadata,
            "document_type": self.document_type,
            "document_type_info": self.document_type_info,
            "project_id": project_id,
            "rfi_processing_mode": "metadata_only_no_chunking",
            "stats": {
                "text_count": 0,  # NO text chunks for RFI
                "table_count": len(tables),
                "image_count": len(figures),
                "total_chunks": 0,  # NO chunks for RFI
                "metadata_documents": 1  # Only metadata document
            }
        }

    async def _process_rfp_with_chunking(self, base_filename: str, filename: str, project_id: str, result, client=None, operation_id=None) -> Dict:
        """Process RFP documents - NORMAL CHUNKING flow (existing code)"""
        print(f"✅ RFP PROCESSING: NORMAL CHUNKING - Full chunking flow")
        
        # Extract RFP ID for chunks
        all_text = "\n\n".join([f"[{elem.get('role', 'unknown')}] {elem['content']}" for elem in self.text_elements])
        rfp_id = self.text_extractor.extract_rfp_id_from_text(all_text)
        print(f"🔑 Extracted RFP ID for all chunks: {rfp_id}")
        
        # Step 1: Extract RFP metadata using existing fields
        print(f"🤖 Step 1: Extracting RFP metadata using LLM from complete document...")
        rfp_extractor = RFPExtractor()
        self.document_metadata = await rfp_extractor.extract_metadata(self.text_elements)
        print(f"📋 RFP metadata extracted: {len(self.document_metadata)} fields")
                
        # Step 2: Create text chunks with LLM metadata using SimpleChunker
        print(f"📋 Step 2: Creating text chunks with LLM metadata using SimpleChunker...")
        self.text_chunks = self.text_extractor.create_text_chunks_with_simple_chunker(
            self.text_elements, 
            self.document_metadata, 
            project_id
        )
        print(f"📋 Text chunks created: {len(self.text_chunks)}")
        
        # Step 3: Extract tables and images WITH verbalization (existing flow)
        print(f"📋 Step 3: Extracting tables with section association...")
        tables = self.table_extractor.extract_tables(result, base_filename, self.section_mapper, self.storage)

        print(f"📋 Step 4: Extracting figures with section association...")
        figures = self.image_extractor.extract_figures(result, base_filename, client, operation_id, self.section_mapper, self.text_elements, self.storage)
        
        # Step 4: Create table and image chunks with verbalization
        print(f"🤖 Creating table chunks with verbalization, section mapping, and LLM metadata...")
        table_chunks = await self.table_extractor.create_table_chunks(
            tables, 
            base_filename, 
            self.document_metadata, 
            self.section_mapper, 
            self.text_elements, 
            rfp_id=rfp_id, 
            project_id=project_id
        )

        print(f"🤖 Creating image chunks with verbalization, section mapping, and LLM metadata...")
        image_chunks = await self.image_extractor.create_image_chunks(
            figures, 
            base_filename, 
            self.document_metadata, 
            self.section_mapper, 
            self.text_elements, 
            rfp_id=rfp_id, 
            project_id=project_id
        )

        # Step 5: Combine all chunks and save
        all_chunks = self.text_chunks + table_chunks + image_chunks
        
        if all_chunks:
            print(f"📋 Saving enhanced text chunks to local storage...")
            chunk_data, json_path = self.storage.save_text_chunks(all_chunks, base_filename)
            
            if chunk_data:
                self.data_indexing_RFP_response.upload_chunks_from_dict(chunk_data)
                print(f"✅ RFP chunks uploaded to Azure AI Search")

        # Save text content to local storage
        if all_text.strip():
            self.storage.save_raw_text(all_text, base_filename)
        
        print(f"✅ RFP processing complete with full chunking!")
        self._print_rfp_debug(all_text, self.text_chunks, tables, figures, table_chunks, image_chunks)
        
        return {
            "text": all_text,
            "text_chunks": all_chunks,
            "tables": tables,
            "images": figures,
            "raw_text": all_text,
            "document_metadata": self.document_metadata,
            "document_type": self.document_type,
            "document_type_info": self.document_type_info,
            "project_id": project_id,
            "stats": {
                "text_count": len(self.text_chunks),
                "table_count": len(table_chunks),
                "image_count": len(image_chunks),
                "total_chunks": len(all_chunks)
            }
        }

    def _create_rfi_metadata_document(self, metadata: Dict, base_filename: str, project_id: str) -> Dict:
        """Create a single RFI metadata document for indexing (NO chunking) - 8 FIELDS ONLY"""
        import uuid
        from datetime import datetime
        
        # Create a single metadata document with ONLY the 8 RFI fields + project_id
        rfi_document = {
            'chunk_id': str(uuid.uuid4())[:8],
            'project_id': project_id,  # From filename (15 chars)
            'file_name': base_filename,
            'section_name': 'RFI_METADATA_DOCUMENT', 
            'section_no': 'METADATA',
            'domain': metadata.get('industry', 'Not Specified'),
            'content_type': 'rfi_metadata',
            'author': 'rfi_system',
            'content': f"RFI: {metadata.get('project_name', 'Unknown')} - {metadata.get('scope_of_work', 'No scope')[:100]}",
            'verbalized_content': f"RFI for {metadata.get('project_name', 'Unknown')} in {metadata.get('region', 'Unknown')}. Scope: {metadata.get('scope_of_work', 'Not specified')[:200]}. Activities: {metadata.get('required_activities', 'Not specified')[:200]}.",
            'metadata': {
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'chunk_index': 0,
                'word_count': len(str(metadata.get('scope_of_work', '') + ' ' + metadata.get('required_activities', '')).split()),
                'char_count': len(str(metadata)),
                # ONLY the 8 RFI fields in metadata
                'llm_extracted_metadata': {
                    'project_name': metadata.get('project_name', 'Not Specified'),
                    'client': metadata.get('client', 'Not Specified'),
                    'region': metadata.get('region', 'Not Specified'),
                    'industry': metadata.get('industry', 'Not Specified'),
                    'prepared_date': metadata.get('prepared_date', 'Not Specified'),
                    'station_discipline': metadata.get('station_discipline', 'Not Specified'),
                    'scope_of_work': metadata.get('scope_of_work', 'Not Specified'),
                    'required_activities': metadata.get('required_activities', 'Not Specified')
                }
            }
        }
        
        return rfi_document

    def _print_rfi_debug(self, all_text: str, tables: List[Dict], figures: List[Dict], project_id: str):
        """Print RFI processing debug info (NO chunking, NO verbalization)"""
        print(f"\n{'='*80}")
        print(f"🚫 RFI PROCESSING RESULTS - NO CHUNKING, NO VERBALIZATION")
        print(f"{'='*80}")
        print(f"🎯 Document Type: {self.document_type}")
        print(f"📄 Processing Mode: METADATA ONLY - NO CHUNKING, NO VERBALIZATION")
        print(f"📊 Confidence: {self.document_type_info.get('confidence', 0):.1%}")
        
        print(f"\n🤖 RFI METADATA EXTRACTED (8 FIELDS):")
        print(f"   📝 Project Name: {self.document_metadata.get('project_name', 'N/A')}")
        print(f"   🔑 Project ID: {project_id} (from filename)")
        print(f"   🏢 Client: {self.document_metadata.get('client', 'N/A')}")
        print(f"   🌍 Region: {self.document_metadata.get('region', 'N/A')}")
        print(f"   🏭 Industry: {self.document_metadata.get('industry', 'N/A')}")
        print(f"   📅 Prepared Date: {self.document_metadata.get('prepared_date', 'N/A')}")
        print(f"   ⚡ Station Discipline: {self.document_metadata.get('station_discipline', 'N/A')}")
        print(f"   📋 Scope of Work: {len(str(self.document_metadata.get('scope_of_work', '')))} characters")
        print(f"   🎯 Required Activities: {len(str(self.document_metadata.get('required_activities', '')))} characters")
        
        print(f"\n📊 EXTRACTION SUMMARY:")
        print(f"   🚫 Text chunks: 0 (NO CHUNKING for RFI)")
        print(f"   📋 Tables extracted: {len(tables)} (NO VERBALIZATION)")
        print(f"   🖼️ Images extracted: {len(figures)} (NO VERBALIZATION)")
        print(f"   📤 Metadata documents for indexing: 1")
        print(f"   💾 Local storage: Single metadata document saved")
        print(f"   🔍 Raw text length: {len(all_text)} characters")
        
        print(f"\n📋 SINGLE RFI METADATA DOCUMENT STRUCTURE:")
        print(f"   🔑 chunk_id: Generated UUID")
        print(f"   🔑 project_id: {project_id} (from filename)")
        print(f"   📝 content_type: rfi_metadata")
        print(f"   📄 metadata.llm_extracted_metadata: 8 fields only")
        print(f"   🚫 NO: chunking, verbalization, table/image chunks")
        print(f"   ✅ ONLY: project_name, client, region, industry, prepared_date, station_discipline, scope_of_work, required_activities")
        
        print(f"✅ RFI metadata-only processing complete!")
        print(f"{'='*80}")

    def _print_rfp_debug(self, all_text: str, text_chunks: List[Dict], tables: List[Dict], 
                        figures: List[Dict], table_chunks: List[Dict], image_chunks: List[Dict]):
        """Print RFP processing debug info (normal chunking)"""
        print(f"\n{'='*80}")
        print(f"✅ RFP PROCESSING RESULTS - FULL CHUNKING")
        print(f"{'='*80}")
        print(f"🎯 Document Type: {self.document_type}")
        print(f"📄 Processing Mode: FULL CHUNKING ENABLED")
        print(f"📊 Confidence: {self.document_type_info.get('confidence', 0):.1%}")
        
        # Print RFP metadata (existing fields)
        print(f"\n🤖 RFP METADATA EXTRACTED:")
        print(f"   📝 Project Title: {self.document_metadata.get('project_title', 'N/A')}")
        print(f"   🏢 Client Name: {self.document_metadata.get('client_name', 'N/A')}")
        print(f"   🏭 Vendor Name: {self.document_metadata.get('vendor_name', 'N/A')}")
        print(f"   📅 Submission Date: {self.document_metadata.get('submission_date', 'N/A')}")
        print(f"   🏷️ Domain Category: {self.document_metadata.get('domain_category', 'N/A')}")
        print(f"   ⚙️ Service Category: {self.document_metadata.get('service_category', 'N/A')}")
        print(f"   💰 Revenue Range: {self.document_metadata.get('revenue_range', 'N/A')}")
        print(f"   🌍 Region: {self.document_metadata.get('region', 'N/A')}")
        print(f"   💵 Project Value: {self.document_metadata.get('project_value', 'N/A')}")
        print(f"   📜 Compliance Standard: {self.document_metadata.get('compliance_standard', 'N/A')}")
        print(f"   🔧 Equipments Used: {self.document_metadata.get('equipments_used', 'N/A')}")
        
        print(f"\n📊 CHUNKING SUMMARY:")
        print(f"   📝 Text chunks: {len(text_chunks)}")
        print(f"   📊 Table chunks: {len(table_chunks)}")
        print(f"   🖼️ Image chunks: {len(image_chunks)}")
        print(f"   📋 Tables extracted: {len(tables)}")
        print(f"   🖼️ Images extracted: {len(figures)}")
        print(f"   📤 Total chunks for indexing: {len(text_chunks) + len(table_chunks) + len(image_chunks)}")
        print(f"✅ RFP full chunking processing complete!")
        print(f"{'='*80}")

    # Additional debugging method
    def _print_extraction_debug(self, all_text: str, text_chunks: List[Dict], tables: List[Dict], 
                               figures: List[Dict], table_chunks: List[Dict], image_chunks: List[Dict]):
        """Legacy debug method - redirects to appropriate debug method"""
        if self.document_type == "RFI":
            # For RFI, we don't have table_chunks or image_chunks, so we pass empty lists
            project_id = self._extract_project_id_from_filename(self.storage.project_id if hasattr(self.storage, 'project_id') else "unknown")
            self._print_rfi_debug(all_text, tables, figures, project_id)
        else:
            self._print_rfp_debug(all_text, text_chunks, tables, figures, table_chunks, image_chunks)