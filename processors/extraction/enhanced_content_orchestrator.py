import os
from typing import Dict, List
# from storage.local_storage import LocalStorage
from storage.analysis_storage import LocalStorage
# from llm_metadata.power_extractor import PowerMetadataExtractor
# from llm_metadata.rfi_extractor import RFIMetadataExtractor
from llm_metadata import RFIExtractor, RFPExtractor
from llm_metadata.document_type_detector import DocumentTypeDetector
from .text_extractor import TextExtractor  # Use existing file
from .table_extractor import TableExtractor  # Use existing file
from .image_extractor import ImageExtractor  # Use existing file
from .section_mapper import SectionMapper  # Use existing file


class ContentExtractor:
    """Extract and process content from Azure Document Intelligence results with verbalization and LLM metadata extraction"""
    
    def __init__(self):
        self.storage = LocalStorage()
        self.text_elements = []  # Store for section association
        self.text_chunks = []  # Store text chunks for section mapping
        self.document_metadata = {}  # Store LLM-extracted document metadata
        self.document_type = "RFP"  # Default document type
        self.document_type_info = {}  # Store document type detection results
        
        # Initialize document type detector
        self.type_detector = DocumentTypeDetector()
        
        # Initialize modular extractors (using existing files)
        self.text_extractor = TextExtractor()
        self.table_extractor = TableExtractor()
        self.image_extractor = ImageExtractor()
        self.section_mapper = SectionMapper()  # ✅ Keep section mapping separate
    
    def extract_all_content(self, result, filename: str, client=None, operation_id=None) -> Dict:
        """Extract text, tables, and images from Azure Document Intelligence result with verbalization and LLM metadata extraction"""
        base_filename = os.path.splitext(filename)[0]
        
        print(f"🔍 Extracting content from {filename}...")
        print(f"📋 Debug: client={client is not None}, operation_id={operation_id}")
        
        # Extract content using Azure DI
        print(f"📋 Step 1: Extracting text elements...")
        self.text_elements = self.text_extractor.extract_text(result)
        print(f"📋 Text elements extracted: {len(self.text_elements)}")
        
        # NEW: Step 1.2 - Detect document type (RFI vs RFP)
        print(f"📄 Step 1.2: Detecting document type (RFI vs RFP)...")
        self.document_type_info = self.type_detector.detect_document_type(self.text_elements)
        self.document_type = self.document_type_info.get('document_type', 'RFP')
        self.type_detector.print_detection_summary(self.document_type_info)
        
        # NEW: Step 1.5 - Extract document metadata using appropriate extractor
        if self.document_type == "RFI":
            print(f"🤖 Step 1.5: Extracting RFI metadata using LLM from complete document...")
            rfi_extractor = RFIExtractor()
            #  rfi_extractor = RFIMetadataExtractor()
            self.document_metadata = rfi_extractor.extract_metadata(self.text_elements)
            print(f"📋 RFI metadata extracted: {len(self.document_metadata)} fields")
        else:
            print(f"🤖 Step 1.5: Extracting RFP metadata using LLM from complete document...")
            rfp_extractor = RFPExtractor()
            # rfp_extractor = PowerMetadataExtractor()
            self.document_metadata = rfp_extractor.extract_metadata(self.text_elements)
            print(f"📋 RFP metadata extracted: {len(self.document_metadata)} fields")
        
        print(f"📋 Step 2: Creating text chunks with LLM metadata using SimpleChunker...")
        self.text_chunks = self.text_extractor.create_text_chunks_with_simple_chunker(self.text_elements, self.document_metadata)
        print(f"📋 Text chunks created: {len(self.text_chunks)}")
        
        print(f"📋 Step 3: Extracting tables with section association...")
        # ✅ Pass section_mapper to existing table_extractor
        tables = self.table_extractor.extract_tables(result, base_filename, self.section_mapper)
        print(f"📋 Tables extracted: {len(tables)}")
        
        print(f"📋 Step 4: Extracting figures with section association...")
        # ✅ Pass section_mapper to existing image_extractor  
        figures = self.image_extractor.extract_figures(result, base_filename, client, operation_id, self.section_mapper, self.text_elements)
        print(f"📋 Figures extracted: {len(figures)}")
        
        # Create table chunks with verbalization, section mapping, and LLM metadata
        print(f"🤖 Creating table chunks with verbalization, section mapping, and LLM metadata...")
        # ✅ Pass section_mapper to existing table_extractor
        table_chunks = self.table_extractor.create_table_chunks(tables, base_filename, self.document_metadata, self.section_mapper, self.text_elements)
        
        # Create image chunks with verbalization, section mapping, and LLM metadata
        print(f"🤖 Creating image chunks with verbalization, section mapping, and LLM metadata...")
        # ✅ Pass section_mapper to existing image_extractor
        image_chunks = self.image_extractor.create_image_chunks(figures, base_filename, self.document_metadata, self.section_mapper, self.text_elements)
        
        # Combine all chunks
        all_chunks = self.text_chunks + table_chunks + image_chunks
        
        # Create all text content for raw text storage
        all_text = "\n\n".join([f"[{elem.get('role', 'unknown')}] {elem['content']}" for elem in self.text_elements])
        
        # Save text content to local storage
        if all_text.strip():
            self.storage.save_raw_text(all_text, base_filename)
        
        # Save enhanced text chunks to local storage (now includes LLM metadata)
        if all_chunks:
            self.storage.save_text_chunks(all_chunks, base_filename)
        
        print(f"✅ Content extraction complete!")
        
        # Print debug information
        self._print_extraction_debug(all_text, self.text_chunks, tables, figures, table_chunks, image_chunks)
        
        return {
            "text": all_text,
            "text_chunks": all_chunks,
            "tables": tables,
            "images": figures,
            "raw_text": all_text,
            "document_metadata": self.document_metadata,  # Include LLM-extracted metadata in response
            "document_type": self.document_type,  # Include detected document type
            "document_type_info": self.document_type_info,  # Include detection details
            "stats": {
                "text_count": len(self.text_chunks),
                "table_count": len(table_chunks),
                "image_count": len(image_chunks),
                "total_chunks": len(all_chunks)
            }
        }
    
    def _print_extraction_debug(self, all_text, text_chunks, tables, figures, table_chunks, image_chunks):
        """Print comprehensive debug information with LLM metadata - FULL CONTENT DISPLAY INCLUDING RFI/RFP DETECTION"""
        
        # Print Document Type Detection Results FIRST
        print(f"\n{'='*80}")
        print(f"📄 DOCUMENT TYPE DETECTION RESULTS")
        print(f"{'='*80}")
        print(f"🎯 Detected Type: {self.document_type}")
        print(f"📊 Confidence: {self.document_type_info.get('confidence', 0):.1%}")
        print(f"🔍 RFP Score: {self.document_type_info.get('rfp_score', 0)}")
        print(f"🔍 RFI Score: {self.document_type_info.get('rfi_score', 0)}")
        print(f"💭 Reasoning: {self.document_type_info.get('reasoning', 'No reasoning available')}")
        
        # Print LLM-extracted metadata - WITH APPROPRIATE FIELD COUNT BASED ON DOCUMENT TYPE
        print(f"\n{'='*80}")
        if self.document_type == "RFI":
            print(f"🤖 LLM-EXTRACTED RFI DOCUMENT METADATA (8 FIELDS)")
            print(f"{'='*80}")
            print(f"🆔 Document ID: {self.document_metadata.get('document_id', 'N/A')}")
            print(f"🏢 Client Name: {self.document_metadata.get('client_name', 'N/A')}")
            print(f"🏷️ Domain Category: {self.document_metadata.get('domain_category', 'N/A')}")
            print(f"⚙️ Service Category: {self.document_metadata.get('service_category', 'N/A')}")
            print(f"📝 Project Title: {self.document_metadata.get('project_title', 'N/A')}")
            print(f"📄 RFI Description: {len(str(self.document_metadata.get('rfi_description', '')))} characters")
            print(f"📅 Submission Date: {self.document_metadata.get('submission_date', 'N/A')}")
            print(f"⏱️ Duration: {self.document_metadata.get('duration', 'N/A')}")
        else:
            print(f"🤖 LLM-EXTRACTED RFP DOCUMENT METADATA (11 FIELDS)")
            print(f"{'='*80}")
            print(f"📝 Project Title: {self.document_metadata.get('project_title', 'N/A')}")
            print(f"🏢 Client Name: {self.document_metadata.get('client_name', 'N/A')}")
            print(f"🏭 Vendor Name: {self.document_metadata.get('vendor_name', 'N/A')}")
            print(f"📅 Submission Date: {self.document_metadata.get('submission_date', 'N/A')}")
            print(f"🏷️ Domain Category: {self.document_metadata.get('domain_category', 'N/A')}")
            print(f"⚙️ Service Category: {self.document_metadata.get('service_category', 'N/A')}")
            print(f"💰 Revenue Range: {self.document_metadata.get('revenue_range', 'N/A')}")
            print(f"🌍 Region: {self.document_metadata.get('region', 'N/A')}")
            print(f"💵 Project Value: {self.document_metadata.get('project_value', 'N/A')}")
            print(f"📜 Compliance Standard: {self.document_metadata.get('compliance_standard', 'N/A')}")
            print(f"🔧 Equipments Used: {self.document_metadata.get('equipments_used', 'N/A')}")

        print(f"\n{'='*80}")
        field_count = 8 if self.document_type == "RFI" else 11
        print(f"🎯 ENHANCED SUMMARY WITH LLM INTEGRATION - {field_count} FIELDS ({self.document_type})")
        print(f"📄 Document Type: {self.document_type} (Confidence: {self.document_type_info.get('confidence', 0):.1%})")
        print(f"📝 Text chunks: {len(text_chunks)} (with LLM metadata)")
        print(f"📊 Table chunks: {len(table_chunks)} (with LLM metadata + verbalization)")
        print(f"🖼️ Image chunks: {len(image_chunks)} (with LLM metadata + verbalization)")
        print(f"🤖 LLM Metadata: ✅ Extracted {field_count} fields from complete document")
        print(f"🗂️ Section Mapping: ✅ Using separate SectionMapper for clean architecture")
        
        if self.document_type == "RFI":
            print(f"✅ RFI Fields: document_id, client_name, domain_category, service_category, project_title, rfi_description, submission_date, duration")
        else:
            print(f"✅ RFP Fields: project_title→file_name, vendor_name→author, domain_category→domain")
            print(f"✅ Financial Fields: revenue_range→💰, region→🌍, project_value→💵")
            print(f"✅ Technical Fields: compliance_standard→📜, equipments_used→🔧")
            
        print(f"✅ FULL CONTENT DISPLAY: No truncation - see complete text, tables, and verbalizations")
        print(f"{'='*80}")