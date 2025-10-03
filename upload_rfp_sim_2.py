# =========================
#  IMPORTS
# =========================
import os
import asyncio
import concurrent.futures
import json
import uuid
from datetime import datetime
from typing import Tuple, List, Dict, Any
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery, QueryType, QueryCaptionType

# Project imports (keep as provided)
from processors.extraction.text_extractor import TextExtractor
from processors.azure_processor import AzureDocumentProcessor
from processors.file_handler import FileHandler
import time
from config import (
    AZURE_OPENAI_DEPLOYMENT_NAME,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_ENDPOINT,
    AZURE_AI_SEARCH_ENDPOINT,
    AZURE_AI_SEARCH_KEY,
    AZURE_AI_SEARCH_RFI_INDEX_NAME,
    AZURE_AI_SEARCH_RFP_INDEX_NAME,
)
from llm_metadata.rfi_extractor import RFIExtractor
from azure.data.tables import TableServiceClient, TableClient
from azure.core.exceptions import ResourceNotFoundError
# =========================
#  QUERY AZURE TABLE STORAGE
# =========================
from azure.data.tables.aio import TableServiceClient
from azure.core.exceptions import ResourceNotFoundError

async def get_azure_table_client(connection_string, table_name):
    try:
        service_client = TableServiceClient.from_connection_string(connection_string)
        return service_client.get_table_client(table_name)
    except ResourceNotFoundError:
        print(f"Error: Table '{table_name}' not found.")
        return None

async def query_azure_table_async(connection_string, table_name, filters):
    table_client = await get_azure_table_client(connection_string, table_name)
    if not table_client:
        return []

    filter_clauses = []

    async def apply_filter(field_name: str, label: str):
        nonlocal filter_clauses
        if filters.get(field_name):
            # Check if the value is "Not mentioned in the document" or similar variations
            value = filters[field_name]
            if value.lower() in ["not mentioned in the document", "not mentioned in document", "not mentioned", ""]:
                print(f"Skipping {label} filter: value is '{value}' (not mentioned)")
                return
            
            value = value.replace("'", "''")
            test_clauses = filter_clauses + [f"{field_name} eq '{value}'"]
            query_str = " and ".join(test_clauses)

            results = []
            async for entity in table_client.query_entities(query_filter=query_str):
                results.append(entity)

            if not results:
                print(f"No results for {label}={filters[field_name]} with current filters → ignoring {label}")
            else:
                filter_clauses.append(f"{field_name} eq '{value}'")
                print(f"{label} found: {filters[field_name]}")

    # Progressive filtering
    await apply_filter("Client", "Client")
    await apply_filter("Industry", "Industry")
    await apply_filter("Region", "Region")
    await apply_filter("ComponentName", "ComponentName")
    await apply_filter("FieldType", "FieldType")
    await apply_filter("VoltageClass", "VoltageClass")
    await apply_filter("ContractTypes", "ContractTypes")

    final_query = " and ".join(filter_clauses) if filter_clauses else ""
    print(f"\nFinal Query Filter: {final_query if final_query else 'No filters applied'}")

    chunk_ids = []
    async for entity in table_client.query_entities(query_filter=final_query):
        if "ChunkId" in entity:
            chunk_ids.append(entity["ChunkId"])

    return chunk_ids

# =========================
# 🔌 OPENAI CLIENT
# =========================
def get_openai_client():
    return AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
    )


# =========================
#  FILE HANDLING
# =========================
def get_file_bytes(file_path: str) -> bytes:
    with open(file_path, "rb") as f:
        return FileHandler.process_file(f)


# =========================
#  SECTION IDENTIFIER
# =========================
def find_section(client, model: str, input_text: str, custom_prompt: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that finds the section."},
            {"role": "user", "content": f"{custom_prompt}\n\nText:\n{input_text}"},
        ],
        # temperature=0.5,
        max_completion_tokens=5000,
    )
    return response.choices[0].message.content.strip()


# =========================
#  PARALLEL AZURE DOCUMENT PROCESSING
# =========================
async def process_document_async(file_path: str, file_name: str) -> Tuple[Any, str, str]:
    """
    Process a single document through Azure Document Intelligence asynchronously.
    
    Args:
        file_path (str): Path to the file
        file_name (str): Name of the file
    
    Returns:
        Tuple[Any, str, str]: (azure_result, file_path, file_name)
    """
    try:
        file_bytes = get_file_bytes(file_path)
        
        # Run Azure Document Intelligence in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        
        def process_doc():
            azure_processor = AzureDocumentProcessor()
            result, client, operation_id = azure_processor.analyze_document(file_bytes, file_name)
            return result
        
        # Use ThreadPoolExecutor for CPU-bound/IO-bound operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            azure_result = await loop.run_in_executor(executor, process_doc)
        
        print(f"Document processing completed for: {file_name}")
        return azure_result, file_path, file_name
    
    except Exception as e:
        print(f" Error processing {file_name}: {str(e)}")
        return None, file_path, file_name


async def extract_text_and_metadata_async(azure_result: Any, file_path: str, file_name: str) -> Tuple[Dict, List, str]:
    """
    Extract text and metadata from processed Azure result asynchronously.
    
    Args:
        azure_result: Result from Azure Document Intelligence
        file_path (str): Original file path
        file_name (str): Original file name
    
    Returns:
        Tuple[Dict, List, str]: (metadata, text_elements, file_name)
    """
    try:
        if azure_result is None:
            print(f" Skipping text extraction for {file_name} due to processing error")
            return {}, [], file_name
        
        # Run text extraction and metadata extraction in parallel
        loop = asyncio.get_event_loop()
        
        def extract_text():
            text_extractor = TextExtractor()
            return text_extractor.extract_text(azure_result)
        
        # Extract text in thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            text_elements = await loop.run_in_executor(executor, extract_text)
        
        # Extract metadata (this is already async)
        rfi_extractor = RFIExtractor()
        metadata = await rfi_extractor.extract_metadata_only(text_elements, azure_di_result=azure_result)
        
        print(f" Text and metadata extraction completed for: {file_name}")
        return metadata, text_elements, file_name
    
    except Exception as e:
        print(f" Error extracting data from {file_name}: {str(e)}")
        return {}, [], file_name


# =========================
#  ENHANCED PARALLEL RFI METADATA EXTRACTION WITH CHUNK CREATION
# =========================
async def extract_rfi_chunk_from_file_parallel(file_path: str, file_name: str, project_id: str = None) -> Dict:
    """
    Extract RFI metadata from a single file and create a complete chunk with enhanced component format.
    
    Args:
        file_path (str): Path to the file
        file_name (str): Name of the file
        project_id (str): Optional project ID
    
    Returns:
        Dict: Complete chunk with enhanced component format
    """
    # Step 1: Process document through Azure Document Intelligence
    azure_result, _, _ = await process_document_async(file_path, file_name)
    
    # Step 2: Extract text and metadata in parallel
    metadata, text_elements, _ = await extract_text_and_metadata_async(azure_result, file_path, file_name)
    
    # Step 3: Create enhanced chunk structure
    chunk = create_enhanced_chunk(metadata, text_elements, file_name, project_id)
    
    return chunk


def create_enhanced_chunk(metadata: Dict, text_elements: List, file_name: str, project_id: str = None) -> Dict:
    """
    Create enhanced chunk structure with component-specific fields.
    
    Args:
        metadata (Dict): Extracted metadata with enhanced component format
        text_elements (List): Extracted text elements
        file_name (str): Name of the file
        project_id (str): Optional project ID
    
    Returns:
        Dict: Enhanced chunk with component-specific fields
    """
    # Generate unique chunk ID
    chunk_id = str(uuid.uuid4())[:8]
    
    # Use project_id or generate from file name
    if not project_id:
        project_id = f"proj_{file_name.replace('.', '_').replace(' ', '_')}"
    
    # Create enhanced chunk structure
    chunk = {
        "chunk_id": chunk_id,
        "project_id": project_id,
        "file_name": file_name,
        "content_type": "document",
        "created_at": datetime.now().isoformat(),
        
        # Basic metadata fields
        "project_name": metadata.get("project_name", ""),
        "client": metadata.get("client", ""),
        "industry": metadata.get("industry", ""),
        "region": metadata.get("region", ""),
        "prepared_date": metadata.get("prepared_date", ""),
        "field_type": metadata.get("field_type", ""),
        "voltage_class": metadata.get("voltage_class", ""),
        "contract_types": metadata.get("contract_types", ""),
        "pricing": metadata.get("pricing", ""),

        # Enhanced components with specific fields
        "components": metadata.get("components", {}),
        
        # Additional chunk information
        "text_elements_count": len(text_elements),
        "total_content_length": sum(len(elem.get('content', '')) for elem in text_elements),
        "processing_timestamp": datetime.now().isoformat()
    }
    
    return chunk

# =========================
#  ASYNC AZURE COGNITIVE SEARCH (UPDATED FOR COMPONENT FORMAT)
# =========================

def extract_scope_and_activities(data):
    """
    Extract the 'scope_of_work' and 'required_activities' from each component
    and store them in separate lists.
    """
    # Lists to store the extracted scope_of_work and required_activities
    scope_of_work_list = []
    required_activities_list = []

    # Iterate over the 'components' and extract values
    for component, details in data["components"].items():
        # Get the 'scope_of_work' and 'required_activities' values safely
        scope_of_work = details.get("scope_of_work", "")
        required_activities = details.get("required_activities", "")
        
        # Add to the lists if they are not empty
        if scope_of_work:
            scope_of_work_list.append(scope_of_work)
        if required_activities:
            required_activities_list.append(required_activities)
    
    return scope_of_work_list, required_activities_list

# =========================
#  COMPONENT-SPECIFIC AZURE COGNITIVE SEARCH
# =========================

COMPONENT_SEARCH_FIELDS = {
    "ELE": ["scope_of_work", "required_activities", "disconnect_switches", "transformer"],
    "FND": ["scope_of_work", "required_activities", "transformer_foundations", "equipment_support_foundations"],
    "AUX": ["scope_of_work", "required_activities", "HVAC_and_FAS", "HADs_arrangements"],
    "CNT": ["scope_of_work", "required_activities", "control_design_packages", "SCADA_infrastructure"],
    "EQP": ["scope_of_work", "required_activities", "bus_systems", "circuit_breakers_and_disconnects"],
    "TEL": ["scope_of_work", "required_activities", "station_lan_networks", "scada_and_transport_infrastructure"],
    "PRT": ["scope_of_work", "required_activities", "transformer_protection", "breaker_protection"],
    "STE": ["scope_of_work", "required_activities", "grading_and_roads", "drainage_and_water_management"],
    "STR": ["scope_of_work", "required_activities", "steel_and_station_structures", "transformer_and_equipment_structures"],
    "MET": ["scope_of_work", "required_activities", "new_metering_installations", "existing_metering_retain_or_update"],
    "LN":  ["scope_of_work", "required_activities", "line_relocations_and_bypasses", "line_rerouting_and_extensions"],
}


async def search_query_async(query: str, component_to_chunks: dict, enhanced_chunks: list, top_k: int = 10):
    print(" Starting async Azure Search (component-aware with field-specific vector queries)...")

    credential = AzureKeyCredential(AZURE_AI_SEARCH_KEY)

    # Create a mapping of component to chunk data for easy lookup
    component_to_chunk_data = {}
    for chunk in enhanced_chunks:
        components = chunk.get("components", {})
        for comp_name, comp_data in components.items():
            if comp_name not in component_to_chunk_data:
                component_to_chunk_data[comp_name] = []
            component_to_chunk_data[comp_name].append(comp_data)

    async def search_component(comp_name: str, chunk_ids: list):
        allowed_fields = COMPONENT_SEARCH_FIELDS.get(comp_name, [])
        if not allowed_fields or not chunk_ids:
            print(f" Skipping {comp_name}: no allowed fields or chunk IDs")
            return []

        # Get component data from chunks
        comp_data_list = component_to_chunk_data.get(comp_name, [])
        if not comp_data_list:
            print(f" No component data found for {comp_name}")
            return []

        def run_request_search():
            try:
                client = SearchClient(
                    endpoint=AZURE_AI_SEARCH_ENDPOINT,
                    index_name=AZURE_AI_SEARCH_RFI_INDEX_NAME,
                    credential=credential,
                )
                filter_expr = f"search.in(chunk_id, '{','.join(chunk_ids)}', ',')"
                
                # Create vector queries using component field values instead of user query
                vector_queries = []
                
                for field in allowed_fields:
                    # Extract text from component data for this field
                    field_texts = []
                    for comp_data in comp_data_list:
                        field_value = comp_data.get(field, "")
                        if field_value and field_value != "not mentioned in document" and field_value.strip():
                            field_texts.append(field_value)
                    
                    # If we have text for this field, create vector query
                    if field_texts:
                        # Combine all field texts for this component and field
                        combined_field_text = " ".join(field_texts)
                        
                        vector_query = VectorizableTextQuery(
                            text=combined_field_text,  # Use component field text instead of user query
                            k_nearest_neighbors=30,
                            fields=f"{field}_vectorized",
                            exhaustive=True
                        )
                        vector_queries.append(vector_query)
                        print(f"    Created vector query for {comp_name}.{field} with text: {combined_field_text[:100]}...")
                    else:
                        print(f"    No valid text found for {comp_name}.{field}")
                
                if not vector_queries:
                    print(f"    No vector queries created for {comp_name}")
                    return []
                
                response = client.search(
                    search_text="",
                    vector_queries=vector_queries,
                    filter=filter_expr,
                    query_type=QueryType.SEMANTIC,
                    semantic_configuration_name="my-semantic-config",
                    query_language="en",
                    query_caption=QueryCaptionType.EXTRACTIVE,
                    vector_filter_mode="postFilter",
                    top=top_k,
                    select=["chunk_id", "project_id"]
                )
                return [doc for doc in response]
            except Exception as e:
                print(f" Error in RFI Search for {comp_name}: {e}")
                return []

        loop = asyncio.get_event_loop()
        request_results = await loop.run_in_executor(None, run_request_search)

        project_ids = {doc["project_id"] for doc in request_results if "project_id" in doc}
        if not project_ids:
            print(f" No project IDs found for component {comp_name}")
            return []

        def run_response_search():
            try:
                client = SearchClient(
                    endpoint=AZURE_AI_SEARCH_ENDPOINT,
                    index_name=AZURE_AI_SEARCH_RFP_INDEX_NAME,
                    credential=credential,
                )
                filter_expr = f"search.in(project_id, '{','.join(project_ids)}', ',')"
                response = client.search(
                    search_text=query,  # Keep original user query for RFP search
                    filter=filter_expr,
                    vector_queries = [VectorizableTextQuery(
                            text=query,  # Use component field text instead of user query
                            k_nearest_neighbors=30,
                            fields=f"content_vector",
                            exhaustive=True
                        )],
                    search_fields=["content", "section_name", "domain"],
                    query_type=QueryType.SEMANTIC,
                    semantic_configuration_name="my-semantic-config",
                    query_language="en",
                    query_caption=QueryCaptionType.EXTRACTIVE,
                    top=top_k,
                    select=["domain", "content", "section_name"]
                )
                return [doc for doc in response]
            except Exception as e:
                print(f" Error in RFP Search for {comp_name}: {e}")
                return []

        response_results = await loop.run_in_executor(None, run_response_search)
        return [
            {
                "domain": doc.get("domain", ""),
                "content": doc.get("content", ""),
                "section_name": doc.get("section_name", "")
            }
            for doc in response_results
        ]

    tasks = [search_component(comp, ids) for comp, ids in component_to_chunks.items()]
    results = await asyncio.gather(*tasks)
    return {comp: res for comp, res in zip(component_to_chunks.keys(), results)}

# =========================
#  ASYNC FINAL RESPONSE (LLM) - ENHANCED FOR COMPONENTS
# =========================
async def final_response_async_enhanced(client, model: str, user_qn: str, chunk_data: Dict, context_chunks: list[str]) -> str:
    """
    Generate final response asynchronously using OpenAI API with enhanced component data.
    """
    print(" Starting async final response generation with enhanced component format...")
    
    combined_text = "\n\n".join(context_chunks)
    if not combined_text.strip():
        return "No content found to summarize."
    
    print("The user question is:", user_qn)
    
    # Prepare component information for the prompt
    components_info = ""
    components = chunk_data.get("components", {})
    if components:
        components_info = "\n\nIDENTIFIED COMPONENTS:\n"
        for comp_code, comp_data in components.items():
            components_info += f"\n{comp_code} Component:\n"
            for field_name, field_value in comp_data.items():
                if field_value and field_value != "not mentioned in document":
                    components_info += f"- {field_name}: {field_value}\n"

    # Create detailed document context
    document_context = f"""
DOCUMENT METADATA:
- Project Name: {chunk_data.get('project_name', 'N/A')}
- Client: {chunk_data.get('client', 'N/A')}
- Industry: {chunk_data.get('industry', 'N/A')}
- Region: {chunk_data.get('region', 'N/A')}
- Prepared Date: {chunk_data.get('prepared_date', 'N/A')}
{components_info}
"""

    prompt = f"""
ROLE: You are a highly precise and thorough technical assistant answering: {user_qn}.  
CONTEXT: Enhanced RFI document with component-specific analysis + retrieved RFP content.  
OBJECTIVE: Provide a complete, component-aware, and engineering-standard explanation with no missing details.  

FORMAT & REQUIREMENTS:  
1. **Comprehensive Coverage**  
   - Fully address the input question and all requirements stated in the uploaded documents.  
   - Ensure no relevant technical, procedural, or contextual detail is omitted.  
   - If information is missing, explicitly state the gap and suggest assumptions or clarifications.  

2. **Component-Specific Analysis**  
   - Always evaluate and reference the following components when relevant:  
     - ELE (Electrical), FND (Foundations), AUX (Auxiliary Systems), CNT (Controls), EQP (Equipment), TEL (Telecommunications), PRT (Protection), STE (Steelwork), STR (Structures), MET (Metallurgy/Materials), LN (Lines).  
   - For each applicable component:  
     - Summarize scope, technical details, and activities.  
     - Highlight dependencies, constraints, and risks.  
     - Provide recommendations or optimizations.  

3. **Structured Response (Engineering Proposal Style)**  
   - **Introduction / Overview**: Restate the question and outline context.  
   - **Detailed Component-wise Analysis**: Break down findings and insights per component.  
   - **Cross-Component Integration**: Explain how components interact or depend on each other.  
   - **Recommendations**: Provide technical and procedural recommendations.  
   - **Knowledge Gaps & Assumptions**: Clearly highlight missing details, ambiguities, or assumptions needed.  
   - **Conclusion**: Summarize with a clear, actionable, and proposal-ready statement.  

4. **RFP Content Integration**  
   - Directly leverage and cite insights from retrieved RFP content ({combined_text}).  
   - Show how the RFP content supports or extends the RFI scope and requirements.  

DOCUMENT CONTEXT: {document_context}  
INPUT QUESTION: {user_qn}  
RETRIEVED RFP CONTENT: {combined_text}  

TASK:  
- Deliver a detailed, structured, and engineering-standard response that is **complete, component-aware, and proposal-ready**, leaving no gaps unaddressed.  
"""

    # Run OpenAI API call in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    
    def call_openai():
        response = client.chat.completions.create(
            model=model,
            messages=[ 
                {"role": "system", 
                "content": "You are an expert Proposal Engineer specializing in component-based RFI analysis. You understand electrical (ELE), foundations (FND), auxiliary (AUX), control (CNT), equipment (EQP), telecom (TEL), protection (PRT), site preparation (STE), structures (STR), metering (MET), and lines (LN) components in engineering projects."},
                {"role": "user", "content": prompt}
            ],
            # temperature=0.3,
            max_completion_tokens=1500,
        )
        return response.choices[0].message.content.strip()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        result = await loop.run_in_executor(executor, call_openai)
    
    print(" Enhanced final response generated successfully!")
    return result


# =========================
# 🚀 FULLY PARALLEL MULTI-FILE PIPELINE WITH ENHANCED CHUNKS
# =========================
async def process_multiple_files_parallel_enhanced(file_list: List[str]) -> List[Dict]:
    """
    Process multiple PDF files with FULL parallel processing and return individual enhanced chunks.
    
    Args:
        file_list (List[str]): List of file paths to process.
    
    Returns:
        List[Dict]: List of enhanced chunks (one per file)
    """
    print(f"🚀 Starting enhanced parallel processing of {len(file_list)} files...")
    
    # Process all files in parallel and create individual chunks
    chunk_tasks = [
        extract_rfi_chunk_from_file_parallel(file_path, os.path.basename(file_path)) 
        for file_path in file_list
    ]
    
    chunk_results = await asyncio.gather(*chunk_tasks, return_exceptions=True)
    
    # Filter successful results
    successful_chunks = [
        chunk for chunk in chunk_results
        if not isinstance(chunk, Exception) and chunk
    ]
    
    print(f" Enhanced chunk processing completed: {len(successful_chunks)}/{len(file_list)} successful")
    
    return successful_chunks


# =========================
#  MAIN PIPELINE - ENHANCED COMPONENT FORMAT FOR ALL CHUNKS
# =========================
async def main():
    in_time = time.time()
    client = get_openai_client()
    model = AZURE_OPENAI_DEPLOYMENT_NAME

    input_qn = "what is the scope of work for the following files ?"
    
    file_list = [
        r"C:\Users\jhagan.a\Downloads\705-22295407.00-B&M_HONI RFP-Chatham SS.docx"
         #r"C:\Users\jhagan.a\Documents\Tetratech\RPFRFIs\testing\sample_1.pdf",
         #r"C:\Users\jhagan.a\Documents\Tetratech\RPFRFIs\testing\sample_2.pdf"
         ]

    # Phase 1: Extract enhanced chunks with component-specific fields
    print(" Phase 1: Starting ENHANCED PARALLEL document processing...")
    processing_start = time.time()
    enhanced_chunks = await process_multiple_files_parallel_enhanced(file_list)
    processing_time = time.time() - processing_start
    print(f" Enhanced document processing completed in: {processing_time:.2f} seconds")
    
    # Display enhanced chunks
    print("\n" + "=" * 100)
    print("ENHANCED CHUNKS WITH COMPONENT-SPECIFIC FIELDS")
    print("=" * 100)
    for i, chunk in enumerate(enhanced_chunks, 1):
        print(f"\nCHUNK {i}:")
        print(json.dumps(chunk, indent=2, ensure_ascii=False))
        print("\n" + "-" * 100)
    
    # Phase 2: Process ALL chunks for search and response
    if enhanced_chunks:
        print(f"Phase 2: Processing {len(enhanced_chunks)} chunks for Azure Search...")
        
        # Connection string for Azure Table
        connection_string = "DefaultEndpointsProtocol=https;AccountName=ttdvcacdevstrfprfi;AccountKey=/wrMwjWw/9F21KFmZ+GcwvjemM6YvtNcvk0V5ZjOTk0AuNHCbkk62ku5EHw70Ofx3k+W2aW8FJcQ+AStT6033w==;EndpointSuffix=core.windows.net"
        table_name = "ComponentData"
        
        # Store all search results from all chunks
        all_search_results = []
        all_processed_chunks = []
        
        # Process each chunk individually
        for chunk_idx, chunk in enumerate(enhanced_chunks):
            print(f"\n Processing Chunk {chunk_idx + 1}/{len(enhanced_chunks)}...")
            print(f"   File: {chunk.get('file_name', 'Unknown')}")
            print(f"   Project: {chunk.get('project_name', 'Unknown')}")
            
            # Extract base filters from current chunk
            base_filters = {
                "Client": chunk.get("client", ""),
                "Industry": chunk.get("industry", ""),
                "Region": chunk.get("region", ""),
                "FieldType": chunk.get("field_type", ""),
                "VoltageClass": chunk.get("voltage_class", ""),
                "ContractTypes": chunk.get("contract_types", ""),
            }
            
            # Run queries for each component in this chunk
            async def query_for_component(component_name: str):
                comp_filters = base_filters.copy()
                comp_filters["ComponentName"] = component_name
                chunk_ids = await query_azure_table_async(connection_string, table_name, comp_filters)
                return {component_name: chunk_ids}
            
            # Get components for this chunk
            component_names = list(chunk.get("components", {}).keys())
            if not component_names:
                print(f"    No components found in chunk {chunk_idx + 1}, skipping...")
                continue
                
            print(f"    Found components: {component_names}")
            
            # Run parallel queries for all components in this chunk
            tasks = [query_for_component(comp) for comp in component_names]
            results = await asyncio.gather(*tasks)
            
            # Merge component results for this chunk
            component_to_chunks = {}
            for result in results:
                component_to_chunks.update(result)
            
            print(f"    Component to ChunkId mapping for chunk {chunk_idx + 1}:")
            for comp, chunk_ids in component_to_chunks.items():
                print(f"      {comp}: {len(chunk_ids)} chunk IDs")
            
            # Phase 3: Run Azure Search for this chunk
            if component_to_chunks:
                print(f"   🔍 Running Azure Search for chunk {chunk_idx + 1}...")
                search_results = await search_query_async(input_qn, component_to_chunks, enhanced_chunks)
                
                # Store results with chunk context
                chunk_results = {
                    "chunk_info": {
                        "chunk_id": chunk.get("chunk_id", f"chunk_{chunk_idx}"),
                        "file_name": chunk.get("file_name", ""),
                        "project_name": chunk.get("project_name", ""),
                        "client": chunk.get("client", ""),
                    },
                    "search_results": search_results,
                    "component_mapping": component_to_chunks
                }
                
                all_search_results.append(chunk_results)
                all_processed_chunks.append(chunk)
                
                # Count total results for this chunk
                total_docs = sum(len(docs) for docs in search_results.values())
                print(f"    Found {total_docs} relevant documents for chunk {chunk_idx + 1}")
            else:
                print(f"    No valid component mappings for chunk {chunk_idx + 1}")
        
        search_time = time.time() - processing_start - processing_time
        print(f"\n Enhanced Azure search for all chunks completed in: {search_time:.2f} seconds")
        
        # Phase 4: Aggregate all results for final response
        print(f"\n Phase 4: Aggregating results from {len(all_search_results)} processed chunks...")
        
        # Flatten all search results across all chunks
        aggregated_content = []
        chunk_summaries = []
        
        for chunk_result in all_search_results:
            chunk_info = chunk_result["chunk_info"]
            search_results = chunk_result["search_results"]
            
            # Create a summary for this chunk
            chunk_summary = f"""
CHUNK: {chunk_info['file_name']} (Project: {chunk_info['project_name']})
Client: {chunk_info['client']}
Components Found: {list(search_results.keys())}
"""
            chunk_summaries.append(chunk_summary)
            
            # Extract content from search results
            for component, docs in search_results.items():
                for doc in docs:
                    if "content" in doc and doc["content"].strip():
                        content_with_context = f"""
[Source: {chunk_info['file_name']} - {component} Component]
{doc.get('section_name', 'Unknown Section')}: {doc['content']}
"""
                        aggregated_content.append(content_with_context)
        
        print(f" Aggregated Content Statistics:")
        print(f"   Total Chunks Processed: {len(all_processed_chunks)}")
        print(f"   Total Content Pieces: {len(aggregated_content)}")
        print(f"   Average Content per Chunk: {len(aggregated_content)/len(all_processed_chunks):.1f}")
        
        # Phase 5: Generate enhanced final response with ALL chunk data
        print("\n🤖 Phase 5: Generating enhanced final response with aggregated data...")
        response_start = time.time()
        
        # Create combined chunk metadata for the LLM
        combined_metadata = {
            "processed_chunks": len(all_processed_chunks),
            "total_files": len(enhanced_chunks),
            "chunk_summaries": chunk_summaries,
            "all_components": list(set(
                comp for chunk in all_processed_chunks 
                for comp in chunk.get("components", {}).keys()
            )),
            "clients": list(set(chunk.get("client", "") for chunk in all_processed_chunks if chunk.get("client"))),
            "projects": list(set(chunk.get("project_name", "") for chunk in all_processed_chunks if chunk.get("project_name"))),
        }
        
        # Use the enhanced final response function with aggregated data
        summary = await final_response_async_enhanced_multi_chunk(
            client, model, input_qn, combined_metadata, all_processed_chunks, aggregated_content
        )
        
        response_time = time.time() - response_start
        print(f" Enhanced final response generated in: {response_time:.2f} seconds")
        
        print("\n ENHANCED FINAL SUMMARY (ALL CHUNKS):\n", summary)
    
    else:
        print(" No chunks were successfully processed!")
    
    # Phase 6: Save enhanced chunks to JSON file
    output_file = "enhanced_rfi_chunks.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enhanced_chunks, f, indent=2, ensure_ascii=False)
    print(f"\n Enhanced chunks saved to: {output_file}")
    
    # Save search results
    if 'all_search_results' in locals():
        search_output_file = "enhanced_search_results.json"
        with open(search_output_file, 'w', encoding='utf-8') as f:
            json.dump(all_search_results, f, indent=2, ensure_ascii=False)
        print(f" Search results saved to: {search_output_file}")
    
    out_time = time.time()
    total_time = out_time - in_time
    print(f"\n ENHANCED PERFORMANCE BREAKDOWN:")
    print(f" Enhanced Document Processing: {processing_time:.2f}s")
    if enhanced_chunks:
        print(f" Enhanced Azure Search (All Chunks): {search_time:.2f}s") 
        print(f" Enhanced Final Response: {response_time:.2f}s")
    print(f" Total Enhanced Pipeline Time: {total_time:.2f}s")


# =========================
#  ENHANCED FINAL RESPONSE FOR MULTIPLE CHUNKS
# =========================
async def final_response_async_enhanced_multi_chunk(
    client, model: str, user_qn: str, combined_metadata: Dict, 
    all_chunks: List[Dict], aggregated_content: List[str]
) -> str:
    """
    Generate final response asynchronously using OpenAI API with data from multiple chunks.
    """
    print(" Starting async final response generation with multi-chunk enhanced format...")
    
    if not aggregated_content:
        return "No relevant content found across all processed documents."
    
    # Combine all content
    combined_text = "\n\n".join(aggregated_content)
    
    print(f" Processing {len(all_chunks)} chunks with {len(aggregated_content)} content pieces")
    
    # Create comprehensive document context
    document_context = f"""
MULTI-DOCUMENT ANALYSIS SUMMARY:
- Total Documents Processed: {combined_metadata['processed_chunks']}
- Clients: {', '.join(combined_metadata['clients'])}
- Projects: {', '.join(combined_metadata['projects'])}
- All Components Found: {', '.join(combined_metadata['all_components'])}

DOCUMENT DETAILS:
{chr(10).join(combined_metadata['chunk_summaries'])}
"""

    prompt = f"""
ROLE: You are a highly precise and thorough technical assistant answering: {user_qn}.  
CONTEXT: Multi-document enhanced RFI analysis with component-specific data from {len(all_chunks)} documents + retrieved RFP content.  
OBJECTIVE: Provide a comprehensive, cross-document, component-aware engineering analysis with complete coverage.  

FORMAT & REQUIREMENTS:  
1. **Multi-Document Comprehensive Coverage**  
   - Synthesize information across ALL {len(all_chunks)} processed documents.
   - Address the input question using insights from all available sources.
   - Identify patterns, consistencies, and variations across documents.
   - Ensure no relevant technical, procedural, or contextual detail is omitted.

2. **Cross-Document Component Analysis**  
   - Analyze the following components across all documents: {', '.join(combined_metadata['all_components'])}
   - For each component, provide:
     - Scope variations across projects/documents
     - Common requirements and specifications
     - Document-specific details and constraints
     - Integration points and dependencies
   - Highlight component interactions across different projects.

3. **Structured Multi-Document Response**  
   - **Executive Summary**: Overall findings across all documents
   - **Document-by-Document Analysis**: Key insights from each source
   - **Component Synthesis**: Consolidated component analysis across all sources
   - **Cross-Project Patterns**: Common themes and variations
   - **Integrated Recommendations**: Recommendations considering all sources
   - **Knowledge Gaps**: Missing information across the document set
   - **Conclusion**: Comprehensive, actionable summary

4. **RFP Content Integration**  
   - Leverage retrieved content from: {len(aggregated_content)} sources
   - Show how RFP content supports or extends the multi-document RFI scope
   - Identify complementary and conflicting information

MULTI-DOCUMENT CONTEXT: {document_context}  
INPUT QUESTION: {user_qn}  
AGGREGATED RFP CONTENT: {combined_text}  

TASK:  
Deliver a detailed, multi-source, structured engineering response that synthesizes ALL available information into a **complete, cross-document, component-aware analysis** ready for engineering decision-making.
"""

    # Run OpenAI API call in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    
    def call_openai():
        response = client.chat.completions.create(
            model=model,
            messages=[ 
                {"role": "system", 
                "content": f"You are an expert Proposal Engineer specializing in multi-document component-based RFI analysis. You excel at synthesizing information across {len(all_chunks)} documents and understanding electrical (ELE), foundations (FND), auxiliary (AUX), control (CNT), equipment (EQP), telecom (TEL), protection (PRT), site preparation (STE), structures (STR), metering (MET), and lines (LN) components across multiple engineering projects."},
                {"role": "user", "content": prompt}
            ],
            # temperature=0.3,
            max_completion_tokens=2000,  # Increased for multi-document response
        )
        return response.choices[0].message.content.strip()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        result = await loop.run_in_executor(executor, call_openai)
    
    print(" Enhanced multi-chunk final response generated successfully!")
    return result


if __name__ == "__main__":
    asyncio.run(main())