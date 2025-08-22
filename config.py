# import os
# from dotenv import load_dotenv

# load_dotenv()

# # Azure Document Intelligence (existing)
# AZURE_DOC_INTELLIGENCE_ENDPOINT = os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT")
# AZURE_DOC_INTELLIGENCE_KEY = os.getenv("AZURE_DOC_INTELLIGENCE_KEY")

# # Azure OpenAI for verbalization
# AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
# AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
# AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
# AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# # Azure OpenAI Embedding for semantic search (for future use)
# AZURE_EMBEDDING_ENDPOINT = os.getenv("AZURE_EMBEDDING_ENDPOINT")
# AZURE_EMBEDDING_API_KEY = os.getenv("AZURE_EMBEDDING_API_KEY")
# AZURE_EMBEDDING_MODEL = os.getenv("AZURE_EMBEDDING_MODEL")

# # Azure Blob Storage 
# USE_BLOB_STORAGE = os.getenv("USE_BLOB_STORAGE", "False").lower() == "true"
# AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
# INPUT_CONTAINER_NAME = "four-splitted-rfp-documents"
# OUTPUT_CONTAINER_NAME = "extracted-rfp-data"

# AZURE_AI_SEARCH_ENDPOINT=os.getenv("AZURE_AI_SEARCH_ENDPOINT")
# AZURE_AI_SEARCH_KEY = os.getenv("AZURE_AI_SEARCH_KEY")
# AZURE_AI_SEARCH_RFI_INDEX_NAME= os.getenv("AZURE_AI_SEARCH_RFI_INDEX_NAME")
# AZURE_AI_SEARCH_RFP_INDEX_NAME=os.getenv("AZURE_AI_SEARCH_RFP_INDEX_NAME")

# # Storage paths
# TABLES_DIR = "extracted_content/tables"
# IMAGES_DIR = "extracted_content/images"
# TEXT_DIR = "extracted_content/text"

# #Hardcode logic
# ENABLE_DOCUMENT_TYPE_DETECTION = os.getenv("ENABLE_DOCUMENT_TYPE_DETECTION", "True").lower() == "true"
# DEFAULT_DOCUMENT_TYPE = os.getenv("DEFAULT_DOCUMENT_TYPE", "RFP")  # RFP or RFI

# # Supported file types
# SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.xlsx']

# # Text chunking configuration (DEPRECATED - now using role-based chunking)
# MAX_CHUNK_SIZE = 2000  # Maximum characters per chunk
# CHUNK_OVERLAP = 200    # Overlap between chunks

# # Role-based chunking configuration
# ROLE_HIERARCHY = {
#     'section_roles': ['sectionHeading', 'title', 'subtitle'],
#     'content_roles': ['paragraph', 'listItem', 'text', 'unknown'],
#     'max_chunk_elements': 50,  # Maximum elements per chunk
#     'min_chunk_length': 100    # Minimum characters for a valid chunk
# }


# import os
# from dotenv import load_dotenv

# load_dotenv()

# # Azure Document Intelligence (existing)
# AZURE_DOC_INTELLIGENCE_ENDPOINT = os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT")
# AZURE_DOC_INTELLIGENCE_KEY = os.getenv("AZURE_DOC_INTELLIGENCE_KEY")

# # Azure OpenAI for verbalization
# AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
# AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
# AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
# AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# # Azure OpenAI Embedding for semantic search (for future use)
# AZURE_EMBEDDING_ENDPOINT = os.getenv("AZURE_EMBEDDING_ENDPOINT")
# AZURE_EMBEDDING_API_KEY = os.getenv("AZURE_EMBEDDING_API_KEY")
# AZURE_EMBEDDING_MODEL = os.getenv("AZURE_EMBEDDING_MODEL")

# # Azure Blob Storage 
# USE_BLOB_STORAGE = os.getenv("USE_BLOB_STORAGE", "False").lower() == "true"
# AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
# INPUT_CONTAINER_NAME = "four-splitted-rfp-documents"
# OUTPUT_CONTAINER_NAME = "extracted-rfp-data"

# AZURE_AI_SEARCH_ENDPOINT=os.getenv("AZURE_AI_SEARCH_ENDPOINT")
# AZURE_AI_SEARCH_KEY = os.getenv("AZURE_AI_SEARCH_KEY")
# AZURE_AI_SEARCH_RFI_INDEX_NAME= os.getenv("AZURE_AI_SEARCH_RFI_INDEX_NAME")
# AZURE_AI_SEARCH_RFP_INDEX_NAME=os.getenv("AZURE_AI_SEARCH_RFP_INDEX_NAME")

# # Storage paths
# TABLES_DIR = "extracted_content/tables"
# IMAGES_DIR = "extracted_content/images"
# TEXT_DIR = "extracted_content/text"

# # Document type detection and processing configuration
# ENABLE_DOCUMENT_TYPE_DETECTION = os.getenv("ENABLE_DOCUMENT_TYPE_DETECTION", "True").lower() == "true"
# DEFAULT_DOCUMENT_TYPE = os.getenv("DEFAULT_DOCUMENT_TYPE", "RFP")  # RFP or RFI

# # RFI Processing Configuration - NEW
# RFI_CHUNKING_ENABLED = os.getenv("RFI_CHUNKING_ENABLED", "False").lower() == "true"  # NEW: Control RFI chunking
# RFI_METADATA_ONLY = os.getenv("RFI_METADATA_ONLY", "True").lower() == "true"  # NEW: RFI metadata-only mode

# # Supported file types
# SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.xlsx']

# # Text chunking configuration (DEPRECATED for RFI - now using role-based chunking for RFP only)
# MAX_CHUNK_SIZE = 2000  # Maximum characters per chunk
# CHUNK_OVERLAP = 200    # Overlap between chunks

# # Role-based chunking configuration (RFP ONLY)
# ROLE_HIERARCHY = {
#     'section_roles': ['sectionHeading', 'title', 'subtitle'],
#     'content_roles': ['paragraph', 'listItem', 'text', 'unknown'],
#     'max_chunk_elements': 50,  # Maximum elements per chunk
#     'min_chunk_length': 100    # Minimum characters for a valid chunk
# }

# # RFI New Metadata Fields Configuration - NEW (removed doc_id, using project_id from filename)
# RFI_METADATA_FIELDS = [
#     'project_name',
#     'client',
#     'region',
#     'industry',
#     'prepared_date',
#     'station_discipline',
#     'scope_of_work',
#     'required_activities'
# ]

# # Processing mode indicators
# def get_processing_mode(document_type: str) -> str:
#     """Get processing mode based on document type"""
#     if document_type == "RFI":
#         if RFI_METADATA_ONLY:
#             return "metadata_only_no_chunking"
#         elif RFI_CHUNKING_ENABLED:
#             return "full_chunking_enabled" 
#         else:
#             return "metadata_only_no_chunking"  # Default for RFI
#     else:  # RFP
#         return "full_chunking_enabled"  # Always full chunking for RFP

# def print_configuration_summary():
#     """Print current configuration summary"""
#     print(f"\n{'='*60}")
#     print(f"DOCUMENT PROCESSING CONFIGURATION")
#     print(f"{'='*60}")
#     print(f"🎯 Document Type Detection: {'ENABLED' if ENABLE_DOCUMENT_TYPE_DETECTION else 'DISABLED'}")
#     print(f"📄 Default Document Type: {DEFAULT_DOCUMENT_TYPE}")
#     print(f"🚫 RFI Chunking Enabled: {'YES' if RFI_CHUNKING_ENABLED else 'NO'}")
#     print(f"📋 RFI Metadata Only: {'YES' if RFI_METADATA_ONLY else 'NO'}")
#     print(f"✅ RFP Chunking: ALWAYS ENABLED")
#     print(f"💾 Blob Storage: {'ENABLED' if USE_BLOB_STORAGE else 'LOCAL'}")
#     print(f"🔍 Processing Modes:")
#     print(f"   RFI: {get_processing_mode('RFI')}")
#     print(f"   RFP: {get_processing_mode('RFP')}")
#     print(f"📊 RFI Metadata Fields: {len(RFI_METADATA_FIELDS)} fields")
#     print(f"{'='*60}")

# # Print configuration on import
# if __name__ == "__main__":
#     print_configuration_summary()


import os
from dotenv import load_dotenv

load_dotenv()

# Azure Document Intelligence (existing)
AZURE_DOC_INTELLIGENCE_ENDPOINT = os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT")
AZURE_DOC_INTELLIGENCE_KEY = os.getenv("AZURE_DOC_INTELLIGENCE_KEY")

# Azure OpenAI for verbalization
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# Azure OpenAI Embedding for semantic search (for future use)
AZURE_EMBEDDING_ENDPOINT = os.getenv("AZURE_EMBEDDING_ENDPOINT")
AZURE_EMBEDDING_API_KEY = os.getenv("AZURE_EMBEDDING_API_KEY")
AZURE_EMBEDDING_MODEL = os.getenv("AZURE_EMBEDDING_MODEL")

# Azure Blob Storage 
USE_BLOB_STORAGE = os.getenv("USE_BLOB_STORAGE", "False").lower() == "true"
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
INPUT_CONTAINER_NAME = "four-splitted-rfp-documents"
OUTPUT_CONTAINER_NAME = "extracted-rfp-data"

AZURE_AI_SEARCH_ENDPOINT=os.getenv("AZURE_AI_SEARCH_ENDPOINT")
AZURE_AI_SEARCH_KEY = os.getenv("AZURE_AI_SEARCH_KEY")
AZURE_AI_SEARCH_RFI_INDEX_NAME= os.getenv("AZURE_AI_SEARCH_RFI_INDEX_NAME")
AZURE_AI_SEARCH_RFP_INDEX_NAME=os.getenv("AZURE_AI_SEARCH_RFP_INDEX_NAME")

# Storage paths
TABLES_DIR = "extracted_content/tables"
IMAGES_DIR = "extracted_content/images"
TEXT_DIR = "extracted_content/text"

# Document type detection and processing configuration
ENABLE_DOCUMENT_TYPE_DETECTION = os.getenv("ENABLE_DOCUMENT_TYPE_DETECTION", "True").lower() == "true"
DEFAULT_DOCUMENT_TYPE = os.getenv("DEFAULT_DOCUMENT_TYPE", "RFP")  # RFP or RFI

# RFI Processing Configuration - UPDATED
RFI_CHUNKING_ENABLED = False  # HARDCODED: RFI never uses chunking
RFI_VERBALIZATION_ENABLED = False  # HARDCODED: RFI never uses verbalization
RFI_METADATA_ONLY = True  # HARDCODED: RFI always metadata-only mode

# Supported file types
SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.xlsx']

# Text chunking configuration (RFP ONLY - RFI doesn't use chunking)
MAX_CHUNK_SIZE = 2000  # Maximum characters per chunk
CHUNK_OVERLAP = 200    # Overlap between chunks

# Role-based chunking configuration (RFP ONLY)
ROLE_HIERARCHY = {
    'section_roles': ['sectionHeading', 'title', 'subtitle'],
    'content_roles': ['paragraph', 'listItem', 'text', 'unknown'],
    'max_chunk_elements': 50,  # Maximum elements per chunk
    'min_chunk_length': 100    # Minimum characters for a valid chunk
}

# RFI Metadata Fields Configuration (8 fields only)
RFI_METADATA_FIELDS = [
    'project_name',
    'client',
    'region',
    'industry',
    'prepared_date',
    'station_discipline',
    'scope_of_work',
    'required_activities'
]

# Processing mode indicators
def get_processing_mode(document_type: str) -> str:
    """Get processing mode based on document type"""
    if document_type == "RFI":
        return "metadata_only_no_chunking_no_verbalization"  # Always for RFI
    else:  # RFP
        return "full_chunking_with_verbalization"  # Always for RFP

def print_configuration_summary():
    """Print current configuration summary"""
    print(f"\n{'='*60}")
    print(f"DOCUMENT PROCESSING CONFIGURATION")
    print(f"{'='*60}")
    print(f"🎯 Document Type Detection: {'ENABLED' if ENABLE_DOCUMENT_TYPE_DETECTION else 'DISABLED'}")
    print(f"📄 Default Document Type: {DEFAULT_DOCUMENT_TYPE}")
    print(f"🚫 RFI Chunking: {'YES' if RFI_CHUNKING_ENABLED else 'NO'} (HARDCODED: NO)")
    print(f"🚫 RFI Verbalization: {'YES' if RFI_VERBALIZATION_ENABLED else 'NO'} (HARDCODED: NO)")
    print(f"📋 RFI Metadata Only: {'YES' if RFI_METADATA_ONLY else 'NO'} (HARDCODED: YES)")
    print(f"✅ RFP Chunking: ALWAYS ENABLED")
    print(f"✅ RFP Verbalization: ALWAYS ENABLED")
    print(f"💾 Blob Storage: {'ENABLED' if USE_BLOB_STORAGE else 'LOCAL'}")
    print(f"🔍 Processing Modes:")
    print(f"   RFI: {get_processing_mode('RFI')}")
    print(f"   RFP: {get_processing_mode('RFP')}")
    print(f"📊 RFI Metadata Fields: {len(RFI_METADATA_FIELDS)} fields")
    print(f"   Fields: {', '.join(RFI_METADATA_FIELDS)}")
    print(f"{'='*60}")

# Print configuration on import
if __name__ == "__main__":
    print_configuration_summary()