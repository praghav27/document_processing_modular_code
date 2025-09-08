


"""
Tetra Tech RFP/RFI Processing Pipeline
--------------------------------------
Enhanced version with separate metadata display for each file processed.
"""
 
# =========================
# 📦 IMPORTS
# =========================
import os
import asyncio
import concurrent.futures
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
from azure.data.tables import TableServiceClient

# =========================
# 🔍 METADATA DISPLAY UTILITIES
# =========================
def truncate_to_words(text: str, word_limit: int = 100) -> str:
    """
    Truncate text to specified number of words.
    
    Args:
        text (str): Text to truncate
        word_limit (int): Maximum number of words
        
    Returns:
        str: Truncated text
    """
    if not text:
        return ""
    
    words = text.split()
    if len(words) <= word_limit:
        return text
    
    return " ".join(words[:word_limit]) + "..."


def print_component_metadata_json(metadata: Dict, file_name: str = ""):
    """
    Print the component-based RFI metadata in exact JSON format with truncated content.
    
    Args:
        metadata (Dict): The metadata dictionary with new component format
        file_name (str): Name of the file for display
    """
    import json
    
    # Create a copy for display with truncated content
    display_metadata = {
        "project_name": metadata.get('project_name', ''),
        "client": metadata.get('client', ''),
        "industry": metadata.get('industry', ''),
        "region": metadata.get('region', ''),
        "prepared_date": metadata.get('prepared_date', ''),
        "components": {}
    }
    
    # Process components with truncation
    components = metadata.get('components', {})
    for comp_code, comp_data in components.items():
        if isinstance(comp_data, dict):
            scope = comp_data.get('scope_of_work', '')
            activities = comp_data.get('required_activities', '')
            
            display_metadata["components"][comp_code] = {
                "scope_of_work": truncate_to_words(scope, 100),
                "required_activities": truncate_to_words(activities, 100)
            }
    
    # Print as formatted JSON
    if file_name:
        print(f"\nMETADATA FOR FILE: {file_name}")
    print("="*80)
    print(json.dumps(display_metadata, indent=2, ensure_ascii=False))
    print("="*80)


def print_all_files_metadata(all_metadata: List[Tuple[Dict, str]]):
    """
    Print metadata for all files separately.
    
    Args:
        all_metadata: List of (metadata, file_name) tuples
    """
    print("\n" + "="*100)
    print("ALL FILES METADATA - SEPARATE DISPLAY")
    print("="*100)
    
    for i, (metadata, file_name) in enumerate(all_metadata, 1):
        print(f"\n📄 FILE {i}: {file_name}")
        print_component_metadata_json(metadata, file_name)
    
    print("\n" + "="*100)
    print(f"PROCESSING SUMMARY: {len(all_metadata)} files processed successfully")
    print("="*100)
 
# =========================
# 🔍 QUERY AZURE TABLE STORAGE
# =========================
async def query_azure_table(client_name: str, region: str, industry: str) -> list:
    """
    Query Azure Table Storage for matching rows based on client, region, and industry.
   
    Args:
        client_name (str): The client name to search for.
        region (str): The region to search for.
        industry (str): The industry to search for.
   
    Returns:
        list: A list of PartitionKeys for the matched rows.
    """
    print("Querying Azure Table Storage...")
 
    connection_string = "DefaultEndpointsProtocol=https;AccountName=ttdvcacdevstrfprfi;AccountKey=/wrMwjWw/9F21KFmZ+GcwvjemM6YvtNcvk0V5ZjOTk0AuNHCbkk62ku5EHw70Ofx3k+W2aW8FJcQ+AStT6033w==;EndpointSuffix=core.windows.net"
    table_name = "RFPFields"
    # --------------------------
    # 2. Connect to the service
    # --------------------------
    table_service = TableServiceClient.from_connection_string(conn_str=connection_string)
    table_client = table_service.get_table_client(table_name=table_name)
    # Build the filter query
    filter_query = f"client eq '{client_name}' or region eq '{region}' or industry eq '{industry}'"
 
    # Query the table
 
    matched_partition_keys = set()
    try:
        entities = table_client.query_entities(query_filter=filter_query)
        for entity in entities:
            partition_key = entity.get("PartitionKey")
            if partition_key:
                matched_partition_keys.add(partition_key)
                print(f"✅ Matched PartitionKey: {partition_key}")
    except Exception as e:
        print(f"❌ Error querying Azure Table Storage: {str(e)}")
 
    return matched_partition_keys
 
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
# 📂 FILE HANDLING
# =========================
def get_file_bytes(file_path: str) -> bytes:
    with open(file_path, "rb") as f:
        return FileHandler.process_file(f)
 
 
# =========================
# 📍 SECTION IDENTIFIER
# =========================
def find_section(client, model: str, input_text: str, custom_prompt: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that finds the section."},
            {"role": "user", "content": f"{custom_prompt}\n\nText:\n{input_text}"},
        ],
        temperature=0.5,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()
 
 
# =========================
# 🚀 PARALLEL AZURE DOCUMENT PROCESSING
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
       
        print(f"✅ Document processing completed for: {file_name}")
        return azure_result, file_path, file_name
   
    except Exception as e:
        print(f"❌ Error processing {file_name}: {str(e)}")
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
            print(f"⚠️ Skipping text extraction for {file_name} due to processing error")
            return {}, [], file_name
       
        # Run text extraction and metadata extraction in parallel
        loop = asyncio.get_event_loop()
       
        def extract_text():
            text_extractor = TextExtractor()
            return text_extractor.extract_text(azure_result)
       
        # Extract text in thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            text_elements = await loop.run_in_executor(executor, extract_text)
       
        # Extract metadata (this is already async) - NOW USES NEW COMPONENT FORMAT
        rfi_extractor = RFIExtractor()
        metadata = await rfi_extractor.extract_metadata_only(text_elements, azure_di_result=azure_result)
       
        print(f"✅ Text and metadata extraction completed for: {file_name}")
        return metadata, text_elements, file_name
   
    except Exception as e:
        print(f"❌ Error extracting data from {file_name}: {str(e)}")
        return {}, [], file_name
 
 
# =========================
# 📂 ENHANCED PARALLEL RFI METADATA EXTRACTION
# =========================
async def extract_rfi_metadata_from_file_parallel(file_path: str, file_name: str) -> Tuple[Dict, List]:
    """
    Extract RFI metadata from a single file with full parallel processing.
   
    Args:
        file_path (str): Path to the file
        file_name (str): Name of the file
   
    Returns:
        Tuple[Dict, List]: (metadata, text_elements)
    """
    # Step 1: Process document through Azure Document Intelligence
    azure_result, _, _ = await process_document_async(file_path, file_name)
   
    # Step 2: Extract text and metadata in parallel
    metadata, text_elements, _ = await extract_text_and_metadata_async(azure_result, file_path, file_name)
   
    return metadata, text_elements


# =========================
# 🔄 METADATA MERGING FOR SEARCH
# =========================
def merge_metadata_for_search(all_metadata: List[Tuple[Dict, str]]) -> Dict:
    """
    Merge metadata from multiple files for search purposes only.
    Combines all components from all files for comprehensive search.
    
    Args:
        all_metadata: List of (metadata, file_name) tuples
        
    Returns:
        Dict: Merged metadata for search
    """
    if not all_metadata:
        return {}
    
    # Collect all metadata
    metadata_list = [metadata for metadata, _ in all_metadata]
    
    if len(metadata_list) == 1:
        return metadata_list[0]
    
    merged = {}
    
    # Handle basic fields - take first non-empty value
    basic_fields = ['project_name', 'client', 'industry', 'region', 'prepared_date']
    
    for field in basic_fields:
        for metadata in metadata_list:
            value = metadata.get(field, '')
            if value and value.strip():
                merged[field] = value
                break
        else:
            merged[field] = ''
    
    # Merge all components from all files
    all_components = {}
    for metadata in metadata_list:
        components = metadata.get('components', {})
        for comp_code, comp_data in components.items():
            if comp_code not in all_components:
                all_components[comp_code] = comp_data
            else:
                # Combine component data if same component appears in multiple files
                existing_comp = all_components[comp_code]
                existing_scope = existing_comp.get('scope_of_work', '')
                existing_activities = existing_comp.get('required_activities', '')
                
                new_scope = comp_data.get('scope_of_work', '')
                new_activities = comp_data.get('required_activities', '')
                
                # Combine scopes and activities
                combined_scope = existing_scope
                if new_scope and new_scope not in existing_scope:
                    combined_scope = f"{existing_scope}. {new_scope}" if existing_scope else new_scope
                
                combined_activities = existing_activities
                if new_activities and new_activities not in existing_activities:
                    combined_activities = f"{existing_activities}. {new_activities}" if existing_activities else new_activities
                
                all_components[comp_code] = {
                    'scope_of_work': combined_scope,
                    'required_activities': combined_activities
                }
    
    merged['components'] = all_components
    return merged
 
 
# =========================
# 🔍 ASYNC AZURE COGNITIVE SEARCH - UPDATED FOR COMPONENT FORMAT
# =========================
async def search_query_async(user_question, query, merged_metadata):
    """
    Perform Azure Cognitive Search asynchronously with the new component format.
    Extract scope and activities from components for search.
    """
    print("🔍 Starting async Azure Search with component format...")
    
    # Extract scope and activities from components
    components = merged_metadata.get('components', {})
    all_scopes = []
    all_activities = []
    
    for comp_code, comp_data in components.items():
        scope = comp_data.get('scope_of_work', '')
        activities = comp_data.get('required_activities', '')
        if scope:
            all_scopes.append(scope)
        if activities:
            all_activities.append(activities)
    
    # Combine all scopes and activities
    combined_scope = ". ".join(all_scopes)
    combined_activities = ". ".join(all_activities)
    
    print(f"📋 Combined scope from {len(all_scopes)} components: {len(combined_scope)} characters")
    print(f"📋 Combined activities from {len(all_activities)} components: {len(combined_activities)} characters")
 
    async def search_pipeline(s, a):
        """Run one full search pipeline for a single scope_of_work + required_activity"""
        loop = asyncio.get_event_loop()
 
        def rfi_search():
            credential = AzureKeyCredential(AZURE_AI_SEARCH_KEY)
            client_a = SearchClient(
                endpoint=AZURE_AI_SEARCH_ENDPOINT,
                index_name=AZURE_AI_SEARCH_RFI_INDEX_NAME,
                credential=credential,
            )
 
            vector_query_1 = VectorizableTextQuery(
                text=s,
                k_nearest_neighbors=50,
                fields="scope_of_work_vectorized",
                exhaustive=True,
                weight=2,
            )
            vector_query_2 = VectorizableTextQuery(
                text=a,
                k_nearest_neighbors=50,
                fields="required_activities_vectorized",
                exhaustive=True,
                weight=0.5,
            )
 
            response_a = client_a.search(
                search_text=query,
                vector_queries=[vector_query_1, vector_query_2],
                search_fields=["client", "region", "industry"],
                query_type=QueryType.SEMANTIC,
                semantic_configuration_name="my-semantic-config",
                query_language="en",
                query_caption=QueryCaptionType.EXTRACTIVE,
                vector_filter_mode="postFilter",
                scoring_profile="weightedProfile",
                select="project_id",
            )
 
            return {doc["project_id"] for doc in response_a if "project_id" in doc}
 
        project_ids = await loop.run_in_executor(None, rfi_search)
        print(f"✅ RFI search → {len(project_ids)} project IDs")
 
        if not project_ids:
            return []
 
        def rfp_search():
            credential = AzureKeyCredential(AZURE_AI_SEARCH_KEY)
            client_b = SearchClient(
                endpoint=AZURE_AI_SEARCH_ENDPOINT,
                index_name=AZURE_AI_SEARCH_RFP_INDEX_NAME,
                credential=credential,
            )
 
            filter_expr = f"search.in(project_id, '{','.join(project_ids)}', ',')"
            vector_query_3 = VectorizableTextQuery(
                text=query,
                k_nearest_neighbors=50,
                fields="content_vector",
                query_rewrites="generative|count-5",
                exhaustive=True,
            )
 
            response_b = client_b.search(
                search_text=user_question,
                filter=filter_expr,
                search_fields=["content", "section_name", "domain"],
                query_type=QueryType.SEMANTIC,
                semantic_configuration_name="my-semantic-config",
                query_language="en",
                query_caption=QueryCaptionType.EXTRACTIVE,
                vector_queries=[vector_query_3],
                vector_filter_mode="postFilter",
                top=5,
                select=["domain", "content", "section_name"],
            )
 
            return [doc.get("content", "") for doc in response_b if doc.get("content")]
 
        results = await loop.run_in_executor(None, rfp_search)
        print(f"✅ RFP search → {len(results)} results")
        return results
 
    # Run search pipeline
    results = await search_pipeline(combined_scope, combined_activities)
    
    print(f"🎯 Total results: {len(results)}")
    return results
 
 
# =========================
# 📝 ASYNC FINAL RESPONSE (LLM)
# =========================
async def final_response_async(client, model: str, user_qn: str, detailed_rfp_request: str, context_chunks: list[str]) -> str:
    """
    Generate final response asynchronously using OpenAI API.
    """
    print("🤖 Starting async final response generation...")
   
    combined_text = "\n\n".join(context_chunks)
    if not combined_text.strip():
        return "No content found to summarize."
   
    print("The user question is:", user_qn)
 
    prompt = f"""
    ROLE: You are a precise assistant answering: {user_qn}.
    CONTEXT: Extracted chunks + RFP request.
    OBJECTIVE: Concise, actionable insights.
 
    FORMAT:
    - Give a detailed explanation of the answer.
    - Recommendations (optional).
    - Knowledge gaps (optional).
 
    INPUT:
    {user_qn}
    {combined_text}
    {detailed_rfp_request}
 
    TASK:
 
    1. Fully addresses the requirements stated in the uploaded documents \
    and answer for the specific question.
    2. Leverage the style, structure, and content patterns from previous \
        RFP responses when appropriate.
    3. Adhere to any sectional structure or formatting commonly expected in \
        architectural/engineering proposals (e.g., Executive Summary, Project Understanding, \
        Approach and Methodology, Team Qualifications, Past Experience, etc.)
    """
 
    # Run OpenAI API call in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
   
    def call_openai():
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system",
                "content": "You are a Proposal Engineer specializing in analyzing and summarizing RFP (Request for Proposal) documents. You create concise, structured summaries to support senior technical managers in decision-making."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
   
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        result = await loop.run_in_executor(executor, call_openai)
   
    print("✅ Final response generated successfully!")
    return result
 
 
# =========================
# 🚀 UPDATED PARALLEL MULTI-FILE PIPELINE
# =========================
async def process_multiple_files_parallel(file_list: List[str]) -> Tuple[List[Tuple[Dict, str]], List]:
    """
    Process multiple PDF files with FULL parallel processing.
    Returns separate metadata for each file instead of merged metadata.
   
    Args:
        file_list (List[str]): List of file paths to process.
   
    Returns:
        Tuple[List[Tuple[Dict, str]], List]: (list of (metadata, filename) tuples, merged_text_elements)
    """
    print(f"🚀 Starting parallel processing of {len(file_list)} files...")
   
    # Phase 1: Process all documents through Azure Document Intelligence in parallel
    print("📄 Phase 1: Processing documents through Azure Document Intelligence...")
    document_tasks = [
        process_document_async(file_path, os.path.basename(file_path))
        for file_path in file_list
    ]
   
    document_results = await asyncio.gather(*document_tasks, return_exceptions=True)
   
    # Filter successful results
    successful_results = [
        (result, path, name) for result, path, name in document_results
        if not isinstance(result, Exception) and result is not None
    ]
   
    print(f"✅ Document processing completed: {len(successful_results)}/{len(file_list)} successful")
   
    # Phase 2: Extract text and metadata in parallel
    print("🔍 Phase 2: Extracting text and metadata in parallel...")
    extraction_tasks = [
        extract_text_and_metadata_async(azure_result, file_path, file_name)
        for azure_result, file_path, file_name in successful_results
    ]
   
    extraction_results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
   
    # Phase 3: Collect results separately
    print("🔄 Phase 3: Collecting results separately for each file...")
    all_file_metadata = []  # List of (metadata, filename) tuples
    merged_text_elements = []
   
    successful_extractions = 0
    for result in extraction_results:
        if isinstance(result, Exception):
            print(f"⚠️ Extraction error: {result}")
            continue
           
        metadata, text_elements, file_name = result
        successful_extractions += 1
        
        # Store metadata separately for each file
        all_file_metadata.append((metadata, file_name))
        merged_text_elements.extend(text_elements)
        print(f"✅ Collected data from: {file_name}")
   
    print(f"🎉 Parallel processing completed: {successful_extractions}/{len(file_list)} files processed successfully")
    
    # Display all file metadata separately
    print_all_files_metadata(all_file_metadata)
    
    return all_file_metadata, merged_text_elements
 
 
# =========================
# 🚀 MAIN PIPELINE - UPDATED FOR SEPARATE FILE DISPLAY
# =========================
async def main():
    in_time = time.time()
    client = get_openai_client()
    model = AZURE_OPENAI_DEPLOYMENT_NAME
 
    input_qn = "what is tower type b2 and what is owner means in nalcor energy?"
   
    file_list = [
        r"C:/Users/Sarthak.hardas/Downloads/Tetratech Five splitted document/sample_1.pdf",
         r"C:Users/Sarthak.hardas/Downloads/Tetratech Five splitted document/sample_2.pdf",
         r"C:Users/Sarthak.hardas/Downloads/Tetratech Five splitted document/sample_3.pdf",
    ]
 
    # Phase 1: Extract metadata with FULL parallel processing - NOW KEEPS FILES SEPARATE
    print("🔥 Phase 1: Starting PARALLEL document processing with separate file tracking...")
    processing_start = time.time()
    all_file_metadata, text_elements = await process_multiple_files_parallel(file_list)
    processing_time = time.time() - processing_start
    print(f"⏱️ Document processing completed in: {processing_time:.2f} seconds")
   
    # Phase 2: Create merged metadata for search purposes only
    print("🔍 Phase 2: Creating merged metadata for search...")
    merged_metadata = merge_metadata_for_search(all_file_metadata)
    
    # Extract basic metadata for query construction
    exclude_keys = {"components"}
    metadata_str = "; ".join([f"{k} is {v}" for k, v in merged_metadata.items() if k not in exclude_keys])
 
    # Phase 3: Section detection
    print("🔍 Phase 3: Starting section detection...")
    custom_prompt = """
    You are an expert section identifier.
    Sections: [Introduction, Scope of work, Required Activities, Risk and Assumptions, Checklist, References]
    Output only one section or 'Not mentioned clearly'.
    """
   
    # Run section detection
    async def get_section_info():
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return await loop.run_in_executor(
                executor,
                find_section, client, model, input_qn, custom_prompt
            )
   
    section_task = asyncio.create_task(get_section_info())
   
    # Phase 4: Prepare text data
    all_text = "\n\n".join([f"[{el.get('role','unknown')}] {el['content']}" for el in text_elements])
   
    # Wait for section detection
    section_name = await section_task
    final_sentence = f"{section_name} Metadata -> {metadata_str}."
    print(f"✅ Section detected: {section_name}")
 
    # Phase 4.1: Query Azure Table Storage for PartitionKeys
    print("🔍 Querying Azure Table Storage for PartitionKeys...")
 
    # Function to manage queries based on merged metadata
    async def manage_queries(metadata):
        client_name = metadata.get("client", "")
        region = metadata.get("region", "")
        industry = metadata.get("industry", "")
 
        all_results = set()
 
        # Handle different data types
        if isinstance(client_name, list) and isinstance(region, list) and isinstance(industry, list):
            for client in client_name:
                for reg in region:
                    for ind in industry:
                        if client and reg and ind:
                            results = await query_azure_table(client, reg, ind)
                            all_results.update(results)
        else:
            # Single values
            if client_name and region and industry:
                results = await query_azure_table(client_name, region, industry)
                all_results.update(results)
           
        return list(all_results)
 
    partition_keys = await manage_queries(merged_metadata)
    print(f"✅ PartitionKeys found: {partition_keys}")
 
    # Phase 5: Run Azure Search with merged metadata
    print("🚀 Phase 5: Running Azure Search with combined component data...")
    search_start = time.time()
   
    # Start search with merged metadata
    search_task = asyncio.create_task(
        search_query_async(input_qn, final_sentence, merged_metadata)
    )
   
    # Azure search completes first, then we can start final response
    index_response = await search_task
    search_time = time.time() - search_start
    print(f"⏱️ Azure search completed in: {search_time:.2f} seconds")
   
    # Phase 6: Generate final response
    print("📝 Phase 6: Generating final response...")
    response_start = time.time()
    summary = await final_response_async(client, model, input_qn, all_text, index_response)
    response_time = time.time() - response_start
    print(f"⏱️ Final response generated in: {response_time:.2f} seconds")
   
    print("\n🔍 Final Summary:\n", summary)
   
    out_time = time.time()
    total_time = out_time - in_time
    print(f"\n⏱️ PERFORMANCE BREAKDOWN:")
    print(f"📄 Document Processing: {processing_time:.2f}s")
    print(f"🔍 Azure Search: {search_time:.2f}s")
    print(f"🤖 Final Response: {response_time:.2f}s")
    print(f"🎯 Total Pipeline Time: {total_time:.2f}s")
    
    # Final summary with separate file information
    print("\n" + "="*80)
    print("🎯 FINAL PROCESSING SUMMARY")
    print("="*80)
    print(f"📂 Files Processed: {len(all_file_metadata)}")
    for i, (metadata, file_name) in enumerate(all_file_metadata, 1):
        components_count = len(metadata.get('components', {}))
        print(f"   File {i}: {file_name} - {components_count} components")
    print("="*80)
 
 
if __name__ == "__main__":
    asyncio.run(main())