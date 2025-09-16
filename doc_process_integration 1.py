import time
import asyncio
import logging

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery, QueryType, QueryCaptionType

from upload_rfp_sim_2 import (process_multiple_files_parallel_enhanced,
                             get_openai_client,
                             query_azure_table_async, COMPONENT_SEARCH_FIELDS)
from config import (AZURE_OPENAI_DEPLOYMENT_NAME, 
                    AZURE_STORAGE_CONNECTION_STRING, 
                    AZURE_AI_SEARCH_KEY,
                    AZURE_AI_SEARCH_ENDPOINT,
                    AZURE_AI_SEARCH_RFI_INDEX_NAME,
                    AZURE_AI_SEARCH_RFP_INDEX_NAME
                    )


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


connection_string = AZURE_STORAGE_CONNECTION_STRING
table_name = "ComponentData"
RFI_TOP_K=10


#Step 01
#Process Input Files

#Get File names and use doc intelligence to get the relevant information
class RFPDocProcess:
    client = get_openai_client()
    model = AZURE_OPENAI_DEPLOYMENT_NAME

    @staticmethod
    async def get_file_details(input_qn: str = "", file_list: list = []):
        loop = asyncio.get_running_loop()
 
        logger.info(" Phase 1: Starting ENHANCED PARALLEL document processing...")
        processing_start = loop.time()
 
        enhanced_chunks = await process_multiple_files_parallel_enhanced(file_list)
 
        processing_time = loop.time() - processing_start
        logger.info(f" Enhanced document processing completed in: {processing_time:.2f} seconds")
 
        return enhanced_chunks

    @staticmethod
    async def save_chunks_to_table(enhanced_chunks:list[dict]):
        if enhanced_chunks:
            print(f"Phase 2: Processing {len(enhanced_chunks)} chunks for Azure Search...")
            
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
                return component_to_chunks
        else:
            print(f"Empty Component to Chunks")
            return {}

    @staticmethod
    async def search_rfi_index(input_qn: str = "", file_list: list = []):
        # Step 1: Extract file details
        enhanced_chunks = await RFPDocProcess.get_file_details(file_list=file_list)

        print(f"Enhanced_Chunks:{enhanced_chunks}")
        # Step 2: Save chunks to table & get mapping of component -> chunk IDs
        component_to_chunks = await RFPDocProcess.save_chunks_to_table(enhanced_chunks=enhanced_chunks)
        print(f"Component Chunk Mapping: {component_to_chunks}")

        print("Starting async Azure Search (component-aware with field-specific vector queries)...")

        credential = AzureKeyCredential(AZURE_AI_SEARCH_KEY)

        # Create a mapping of component name to actual chunk data
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
                print(f"Skipping {comp_name}: no allowed fields or chunk IDs")
                return set()

            comp_data_list = component_to_chunk_data.get(comp_name, [])
            if not comp_data_list:
                print(f"No component data found for {comp_name}")
                return set()

            def run_request_search():
                try:
                    client = SearchClient(
                        endpoint=AZURE_AI_SEARCH_ENDPOINT,
                        index_name=AZURE_AI_SEARCH_RFI_INDEX_NAME,
                        credential=credential,
                    )
                    filter_expr = f"search.in(chunk_id, '{','.join(chunk_ids)}', ',')"

                    vector_queries = []
                    for field in allowed_fields:
                        field_texts = [
                            comp_data.get(field, "")
                            for comp_data in comp_data_list
                            if comp_data.get(field, "")
                               and comp_data.get(field, "").strip()
                               and comp_data.get(field) != "not mentioned in document"
                        ]

                        if field_texts:
                            combined_field_text = " ".join(field_texts)
                            vector_query = VectorizableTextQuery(
                                text=combined_field_text,
                                k_nearest_neighbors=30,
                                fields=f"{field}_vectorized",
                                exhaustive=True
                            )
                            vector_queries.append(vector_query)
                            print(f"Created vector query for {comp_name}.{field}: {combined_field_text[:100]}...")
                        else:
                            print(f"No valid text found for {comp_name}.{field}")

                    if not vector_queries:
                        print(f"No vector queries created for {comp_name}")
                        return []

                    response = client.search(
                        search_text="",
                        vector_queries=vector_queries,
                        filter=filter_expr,
                        query_type=QueryType.SEMANTIC,
                        semantic_configuration_name="my-semantic-config",
                        query_caption=QueryCaptionType.EXTRACTIVE,
                        vector_filter_mode="postFilter",
                        top=RFI_TOP_K,
                        select=["chunk_id", "project_id"]
                    )
                    return [doc for doc in response]

                except Exception as e:
                    print(f"Error during search for {comp_name}: {e}")
                    return []

            loop = asyncio.get_event_loop()
            request_results = await loop.run_in_executor(None, run_request_search)

            project_ids = {doc["project_id"] for doc in request_results if "project_id" in doc}
            print(f"Search results for {comp_name} -> Project IDs: {project_ids}")

            return project_ids

        # Step 3: Run searches concurrently for all components
        tasks = [search_component(comp, ids) for comp, ids in component_to_chunks.items()]
        results_project_ids = await asyncio.gather(*tasks)

        # Flatten results (list of sets -> single set)
        final_project_ids = set().union(*results_project_ids)

        if not final_project_ids:
            print("No project IDs found across any component")

        print(f"Final unique Project IDs: {final_project_ids}")
        return list(final_project_ids)

    @staticmethod
    async def search_rfp_index(project_ids:list, input_qn: str = ""):
        logger.info(f"Starting RFP index search with {len(project_ids)} project IDs")
        if not project_ids:
            logger.warning("No project IDs provided for RFP search")
            return []

        credential = AzureKeyCredential(AZURE_AI_SEARCH_KEY)

        
        
        def run_response_search():
            try:
                client = SearchClient(
                    endpoint=AZURE_AI_SEARCH_ENDPOINT,
                    index_name=AZURE_AI_SEARCH_RFP_INDEX_NAME,
                    credential=credential,
                )
                filter_expr = f"search.in(project_id, '{','.join(project_ids)}', ',')"
                response = client.search(
                    search_text=input_qn,  # Keep original user query for RFP search
                    filter=filter_expr,
                    vector_queries = [VectorizableTextQuery(
                            text=input_qn,  # Use component field text instead of user query
                            k_nearest_neighbors=30,
                            fields=f"content_vector",
                            exhaustive=True
                        )],
                    search_fields=["content", "section_name", "domain"],
                    query_type=QueryType.SEMANTIC,
                    semantic_configuration_name="my-semantic-config",
                    query_language="en",
                    query_caption=QueryCaptionType.EXTRACTIVE,
                    top=RFI_TOP_K,
                    select=["domain", "content", "section_name"]
                )
                return [doc for doc in response]
            except Exception as e:
                logger.error(f" Error in RFP Search: {e}")
                return []
            
        loop = asyncio.get_event_loop()
        

        response_results = await loop.run_in_executor(None, run_response_search)
        # return [
        #     {
        #         "domain": doc.get("domain", ""),
        #         "content": doc.get("content", ""),
        #         "section_name": doc.get("section_name", "")
        #     }
        #     for doc in response_results
        # ]
        print(f"RFP Search Results: {response_results}")
        return response_results




async def main():
   
    file_list = [
        r"C:Users/Sarthak.hardas/Downloads/Tetratech Five splitted document/705-22295407.00-B&M_HONI RFP-Chatham SS-Chatham_Lakeshore Appendix AJ Planning Specs.pdf"]
    # r"C:\Users\SowmyaDevaraj\Downloads\705-22295407.00-B&M_HONI RFP-Chatham SS-Chatham_Lakeshore Instruct for Const.docx"]

    
    project_ids = await RFPDocProcess.search_rfi_index(file_list=file_list)
    

    print(f"\nProject IDS:{project_ids}")

if __name__ == "__main__":
    asyncio.run(main())

        

