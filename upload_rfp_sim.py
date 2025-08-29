from processors.extraction.text_extractor import TextExtractor
from processors.azure_processor import AzureDocumentProcessor
from processors.file_handler import FileHandler
from config import AZURE_OPENAI_DEPLOYMENT_NAME, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_ENDPOINT

def get_file_bytes(file_path: str) -> bytes:
    with open(file_path, "rb") as f:
        return FileHandler.process_file(f)

from openai import AzureOpenAI

# Initialize the Azure OpenAI client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,  # Adjust if your deployment uses another version
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# Your model deployment name (check Azure portal)
DEPLOYMENT_NAME = AZURE_OPENAI_DEPLOYMENT_NAME

def find_section(input_text: str, custom_prompt: str) -> str:
    """
    Summarizes input_text based on a custom_prompt using Azure GPT-4o.
    """
    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that finds the section."},
            {"role": "user", "content": f"{custom_prompt}\n\nText:\n{input_text}"}
        ],
        temperature=0.5,
        max_tokens=500
    )
    return response.choices[0].message.content.strip()



async def extract_rfi_metadata_from_file(file_path: str, file_name: str) -> tuple[dict, list]:
    """
    Extract RFI metadata from a file using the enhanced RFI extractor.
    """
    # Import inside function to avoid circular import
    from llm_metadata.rfi_extractor import RFIExtractor

    file_bytes = get_file_bytes(file_path)

    # Get Document Intelligence result
    azure_processor = AzureDocumentProcessor()
    result, client, operation_id = azure_processor.analyze_document(file_bytes, file_name)  # This returns the DI result object
    #print(result)
    text_extractor = TextExtractor()
    text_elements = text_extractor.extract_text(result)
    #print(text_elements)
    rfi_extractor = RFIExtractor()
    metadata = await rfi_extractor.extract_metadata_only(text_elements, azure_di_result=result)
    return metadata, text_elements


def search_query(user_question, query, scope_of_work, required_activities):
    from azure.core.credentials import AzureKeyCredential
    from azure.search.documents import SearchClient
    from config import AZURE_AI_SEARCH_ENDPOINT,AZURE_AI_SEARCH_KEY,AZURE_AI_SEARCH_RFI_INDEX_NAME,AZURE_AI_SEARCH_RFP_INDEX_NAME,AZURE_EMBEDDING_MODEL,AZURE_EMBEDDING_ENDPOINT,AZURE_EMBEDDING_API_KEY
    from azure.search.documents.models import VectorizableTextQuery, QueryType, QueryCaptionType, QueryAnswerType
    endpoint = AZURE_AI_SEARCH_ENDPOINT
    index_name = AZURE_AI_SEARCH_RFI_INDEX_NAME
    credential = AzureKeyCredential(AZURE_AI_SEARCH_KEY)

    search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)

    client_b = SearchClient(endpoint=AZURE_AI_SEARCH_ENDPOINT, index_name=AZURE_AI_SEARCH_RFP_INDEX_NAME, credential=credential)

    vector_query_1 = VectorizableTextQuery(
        text=scope_of_work,
        k_nearest_neighbors=50,
        fields="scope_of_work_vectorized",  
        exhaustive=True,  
        weight=2
    )
 
    vector_query_2 = VectorizableTextQuery(
            text=required_activities,
            k_nearest_neighbors=50,
            fields="required_activities_vectorized",  
            exhaustive=True,  
            weight=0.5
        )

    field_name = "project_id"
 
    response_a = search_client.search(
        search_text=query,
        vector_queries=[vector_query_1, vector_query_2],  
        search_fields=["client", "region","industry"],  # Boost these fields
        query_type=QueryType.SEMANTIC,
        semantic_configuration_name='my-semantic-config',
        query_language="en",
        query_caption=QueryCaptionType.EXTRACTIVE,
        vector_filter_mode="postFilter",
        scoring_profile="weightedProfile",            
        top=45,
        select="project_id",            
        include_total_count=False
    )

    values = set()
    for doc in response_a:
        if field_name in doc:
            values.add(doc[field_name])
        # print(doc)

    if not values:
        print(f"No values found for field '{field_name}' in index A results.")
    else:
        import json
        safe_values = [v.replace("'", "''") for v in values]  
        # values_list = ",".join(f"'{v}'" for v in safe_values)
        values_list = f"'{','.join(safe_values)}'"
        # print(values_list)
        filter_expr = f"search.in({field_name} , {values_list},  ',')"
        # print(filter_expr)
    
        vector_query_3 = VectorizableTextQuery(
            text=query,
            k_nearest_neighbors=50,
            fields="content_vector",  
            query_rewrites="generative|count-5" ,  
            exhaustive=True,
        )
    
        # 2. Query Index B using the filter to get top 15 chunks
        response_b = client_b.search(
            search_text=user_question,
            filter=filter_expr,
            search_fields=["content", "section_name","domain"],
            query_type=QueryType.SEMANTIC,
            semantic_configuration_name='my-semantic-config',
            query_language="en",
            query_caption=QueryCaptionType.EXTRACTIVE,
            vector_queries=[vector_query_3],
            vector_filter_mode="postFilter",
            top=15,
            # select=["chunk_id", "domain", "content_type", "content",'file_name',"section_name"]
            select=["domain", "content","section_name"]
        )
    
        # print(response_b)
        # print(f"Top 15 chunks from index B where {field_name} matches values from A:")
        chunk_texts = []
        for doc in response_b:
            # print(doc)
            content = doc.get('content', '')
            if content:
                chunk_texts.append(content)
        
        return chunk_texts

# # Print results
# def print_results(results):
#     for result in results:
#         print(f"File: {result['file_name']}")
#         print(f"Section: {result['section_name']}")
#         print(f"Chunk ID: {result['chunk_id']}")
#         print(f"Score: {result['@search.score']}")
#         print(f"Content: {result['content']}")
#         print(f"Section No: {result['section_no']}")
#         print("-" * 40)
 
 
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
import os
 
# Replace these with your Azure OpenAI details
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
 
 
client_openai = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,  
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

def final_response(user_qn, detailed_rfp_request, context_chunks):
    combined_text = "\n\n".join(context_chunks)
    
    if combined_text.strip(): #engineering proposal writer
        prompt = f""" ROLE: You are a precise, expert-level assistant specializing in answering the user question {user_qn} 
        
        and summarizing the results from the contexts {detailed_rfp_request} and {combined_text}.
    
        CONTEXT: You’ll receive several extracted chunks of technical documents. These may contain overlapping information, 
        
        but your goal is to deliver a cohesive summary.
        
        OBJECTIVE: Generate a **concise, actionable, and insightful summary** of the provided content.
        
        AUDIENCE: A technical manager who needs key insights quickly.
        
        STYLE & TONE: Use professional language. Present the information in **bullet-point format**, prioritized by importance.
        
        LENGTH CONSTRAINT: Limit the summary to **5–7 bullets**, each no more than 30 words.


        
        OUTPUT FORMAT:
        - **Summary (5–7 bullets)**: highlight the core insights, grouped logically.
        - **Recommendations (optional)**: if actionable items emerge, list 2–3 clearly.
        - **Knowledge Gaps (optional)**: mention any missing or ambiguous information.
        
        INPUT:
        {user_qn}
        {combined_text}
        {detailed_rfp_request}
        
        """
        response = client_openai.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes technical documents."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000  
        )
   
        summary = response.choices[0].message.content
        print("\n🔍 Summary of the retrieved chunks:\n")
        print(summary)
    else:
        print("No content found to summarize.")     
 
 
 

async def main():
    # Initialize the Azure OpenAI client
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,  # Adjust if your deployment uses another version
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )

    # Your model deployment name (check Azure portal)
    DEPLOYMENT_NAME = AZURE_OPENAI_DEPLOYMENT_NAME
#what is the scope of work of this document?
    input_qn = """
                What is the risks involved in Cabling and Wiring?
                """
    #file_path = r"C:\Users\jhagan.a\Documents\Tetratech\RPFRFIs\five_splitted\705-22295407.00-B&M_HONI RFP-Chatham SS-Chatham_Lakeshore App AI Elect Install Works 1\705-22295407.00-B&M_HONI RFP-Chatham SS-Chatham_Lakeshore App AI Elect Install Works.pdf"
    file_path = r"C:\Users\jhagan.a\Documents\Tetratech\RPFRFIs\five_splitted\705-22295407.00-B&M_HONI RFP-Chatham SS-Chatham_Lakeshore App AI Elect Install Works 1\705-22295407.00-B&M_HONI RFP-Chatham SS-Chatham_Lakeshore Instruct for Const.pdf"
    file_name = "705-22295407.00-B&M_HONI RFP-Chatham SS-Chatham_Lakeshore Instruct for Const"
    custom_prompt = """You are an expert section identifier for the question input provided. 
    The solution should be present in only one of the below sections :

    Section list
    [Introduction, Scope of work, Required Activities, Risk and Assumptions, Checklist, References]

    Instructions : 
    
    
    **If no clear information is found, use "Not mentioned clearly" **
    
    The output should be only one from the section list or "not mentioned clearly"
    """


    import asyncio

    section_name = find_section(input_qn, custom_prompt)

    # print(section_name)

    metadata, text_elements = await extract_rfi_metadata_from_file(file_path, file_name)
    # print(metadata)

    exclude_keys = {"scope_of_work", "required_activities"}
 
    # Convert JSON key-value pairs into a sentence excluding chosen keys
    metadata_str = "; ".join([f"{k} is {v}" for k, v in metadata.items() if k not in exclude_keys])

    scope_of_work = metadata['scope_of_work']
    required_activities = metadata['required_activities']
    
    # Combine with base string
    final_sentence = f"{section_name} Metadata -> {metadata_str}."

    # print(final_sentence)

    index_response = search_query(input_qn, final_sentence, scope_of_work, required_activities)

    # print(index_response)

    all_text = "\n\n".join([f"[{elem.get('role', 'unknown')}] {elem['content']}" for elem in text_elements])

    print("\n\nFinal Response:\n")
    final_response(input_qn, all_text, index_response)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

    