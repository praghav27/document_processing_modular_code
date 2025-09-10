# import os
# import json
# from typing import List, Dict, Any
# from dotenv import load_dotenv
# from azure.core.credentials import AzureKeyCredential
# from azure.search.documents import SearchClient
# from openai import AzureOpenAI

# from config import (
#     AZURE_AI_SEARCH_ENDPOINT,
#     AZURE_AI_SEARCH_KEY,
#     AZURE_AI_SEARCH_RFI_INDEX_NAME,
#     AZURE_EMBEDDING_MODEL,
#     AZURE_EMBEDDING_API_KEY,
#     AZURE_EMBEDDING_ENDPOINT
# )

# class AzureSearchRFPRequestUploader:
#     def __init__(self):
#         load_dotenv()

#         # Initialize Azure clients
#         self.search_client = SearchClient(
#             endpoint=AZURE_AI_SEARCH_ENDPOINT,
#             index_name=AZURE_AI_SEARCH_RFI_INDEX_NAME,
#             credential=AzureKeyCredential(AZURE_AI_SEARCH_KEY)
#         )

#         self.openai_client = AzureOpenAI(
#             api_key=AZURE_EMBEDDING_API_KEY,
#             api_version="2023-05-15",
#             azure_endpoint=AZURE_EMBEDDING_ENDPOINT
#         )

#     def get_embedding(self, text: str, model: str = None) -> List[float]:
#         """Generate embeddings for the given text."""
#         if model is None:
#             model = AZURE_EMBEDDING_MODEL
#         try:
#             response = self.openai_client.embeddings.create(input=text, model=model)
#             return response.data[0].embedding
#         except Exception as e:
#             print(f"Error generating embedding: {e}")
#             return [0.0] * 3072  # Default vector size for the model

#     # def transform_chunk_to_document(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
#     #     """Transform chunk data to match the Azure Search index schema."""
        
#     #     # Create the document structure based on your index schema
#     #     document = {
#     #         "chunk_id": chunk.get("chunk_id"),
#     #         "project_id": chunk.get("project_id"),
#     #         "project_name": chunk.get("project_name"),
#     #         "client": chunk.get("client"),
#     #         "region": chunk.get("region"),
#     #         "industry": chunk.get("industry"),
#     #         "prepared_date": chunk.get("prepared_date"),
#     #         "station_discipline": chunk.get("station_discipline"),
#     #         "scope_of_work": chunk.get("scope_of_work"),  # This is the text field
#     #         "required_activities": chunk.get("required_activities")
#     #     }

#     #     # Generate embedding for scope_of_work and assign to scope_of_work_vectorized
#     #     scope_of_work_text = chunk.get("scope_of_work", "")
#     #     required_activities_text= chunk.get("required_activities")
#     #     if scope_of_work_text:
#     #         print(f"Generating embedding for scope of work: {scope_of_work_text[:100]}...")
#     #         document["scope_of_work_vectorized"] = self.get_embedding(scope_of_work_text)
#     #     else:
#     #         print(f"Warning: No scope_of_work found for chunk {chunk.get('chunk_id', 'Unknown')}")
#     #         document["scope_of_work_vectorized"] = [0.0] * 3072  # Default zero vector
#     #     if required_activities_text:
#     #         print(f"Generating embedding for required activities: {required_activities_text[:100]}...")
#     #         document["required_activities_vectorized"] = self.get_embedding(required_activities_text)
#     #     else:
#     #         print(f"Warning: No scope_of_work found for chunk {chunk.get('chunk_id', 'Unknown')}")
#     #         document["required_activities_vectorized"] = [0.0] * 3072  # Default zero vector
#     #     return document

#     def transform_chunk_to_document(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
#         """Transform chunk data to match the Azure Search index schema."""
 
#             # Helper function to determine a valid date
#         def get_prepared_date(chunk: Dict[str, Any]) -> str:
#             date_str = chunk.get("prepared_date", "").strip().lower()
#             invalid_values = {"", "none", "null", "na", "n/a","Not mentioned in document"}
 
#             if date_str in invalid_values:
#                 # Extract year from project_idS
#                 project_id = chunk.get("project_id", "")
#                 # Example project_id: "705-25318708.00"
#                 # Extract the part after the first dash
#                 try:
#                     part_after_dash = project_id.split("-")[1]
#                     # Extract the first two digits to get the year part
#                     year_prefix = part_after_dash[:2]
 
#                     # Convert to int and form year as 20xx
#                     year = int(year_prefix)
#                     if year < 66:  # Assuming 2000-2049 range
#                         year += 2000
#                     else:
#                         year += 1900  # For safety if needed

#                     # Return date as YYYY-01-01
#                     return f"{year}-01-01"
#                 except Exception as e:
#                     print(f"⚠️ Warning: Failed to parse year from project_id '{project_id}': {e}")
#                     return None  # or some fallback date
#             else:
#                 # Assume the date is valid and return as is
#                 return chunk.get("prepared_date")
 
#         # Use the helper to get a proper prepared_date value
#         prepared_date_value = get_prepared_date(chunk)

#         # Create the document structure based on your index schema
#         document = {
#             "chunk_id": chunk.get("chunk_id"),
#             "project_id": chunk.get("project_id"),
#             "project_name": chunk.get("project_name"),
#             "client": chunk.get("client"),
#             "region": chunk.get("region"),
#             "industry": chunk.get("industry"),
#             "prepared_date": prepared_date_value,
#             "station_discipline": chunk.get("station_discipline"),
#             "scope_of_work": chunk.get("scope_of_work"),  # This is the text field
#             "required_activities": chunk.get("required_activities")
#         }
 
#         # Generate embedding for scope_of_work and assign to scope_of_work_vectorized
#         scope_of_work_text = chunk.get("scope_of_work", "")
#         if scope_of_work_text:
#             print(f"Generating embedding for scope of work: {scope_of_work_text[:100]}...")
#             document["scope_of_work_vectorized"] = self.get_embedding(scope_of_work_text)
#         else:
#             print(f"Warning: No scope_of_work found for chunk {chunk.get('chunk_id', 'Unknown')}")
#             document["scope_of_work_vectorized"] = [0.0] * 3072  # Default zero vector
 
#         return document

#     def generate_documents_for_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#         """Generate documents with embeddings for all chunks."""
#         documents = []

#         for i, chunk in enumerate(chunks):
#             print(f"Processing chunk {i + 1}/{len(chunks)}: {chunk.get('chunk_id', 'Unknown')}")
#             document = self.transform_chunk_to_document(chunk)
#             documents.append(document)

#         return documents

#     def upload_documents_in_batches(self, documents: List[Dict[str, Any]], batch_size: int = 50):
#         """Upload documents to Azure Search in batches."""
#         total_docs = len(documents)
#         successful_uploads = 0
#         failed_uploads = 0

#         for i in range(0, total_docs, batch_size):
#             batch = documents[i:i + batch_size]
#             batch_num = (i // batch_size) + 1
#             total_batches = (total_docs + batch_size - 1) // batch_size

#             print(f"Uploading batch {batch_num}/{total_batches} ({len(batch)} documents)...")
#             try:
#                 result = self.search_client.upload_documents(documents=batch)
#                 batch_successful = sum(1 for r in result if r.succeeded)
#                 batch_failed = len(batch) - batch_successful

#                 for r in result:
#                     if not r.succeeded:
#                         print(f"Failed to upload document {r.key}: {r.error_message}")

#                 successful_uploads += batch_successful
#                 failed_uploads += batch_failed
#                 print(f"Batch {batch_num} completed: {batch_successful} successful, {batch_failed} failed")

#             except Exception as e:
#                 print(f"Error uploading batch {batch_num}: {e}")
#                 failed_uploads += len(batch)

#         print(f"\n✅ Upload completed!")
#         print(f"📊 Total documents: {total_docs}")
#         print(f"✅ Successful uploads: {successful_uploads}")
#         print(f"❌ Failed uploads: {failed_uploads}")

#         return successful_uploads, failed_uploads

#     def upload_chunks_from_dict(self, chunk_data: Dict[str, Any]):
#         """Upload chunks from dictionary data."""
#         chunks = chunk_data.get("chunks", [])
#         if not chunks:
#             print("❌ No chunks found in the input data")
#             return

#         print(f"📄 Found {len(chunks)} chunks to process")
#         print("🔄 Generating embeddings and transforming documents...")
#         documents = self.generate_documents_for_chunks(chunks)
#         print("🔄 Uploading documents to Azure AI Search...")
#         self.upload_documents_in_batches(documents)

#     def load_and_upload_chunks(self, json_file_path: str):
#         """Load JSON file and upload chunks to Azure Search."""
#         try:
#             with open(json_file_path, 'r', encoding='utf-8') as file:
#                 data = json.load(file)
#             print(f"✅ Loaded JSON data from {json_file_path}")
#         except FileNotFoundError:
#             print(f"❌ File not found: {json_file_path}")
#             return
#         except json.JSONDecodeError as e:
#             print(f"❌ Invalid JSON format: {e}")
#             return

#         self.upload_chunks_from_dict(data)

#     def upload_direct_data(self, data: Dict[str, Any]):
#         """Upload data directly from a dictionary (useful for the provided JSON data)."""
#         print("🔄 Processing provided data...")
#         self.upload_chunks_from_dict(data)

#     def test_single_document_upload(self, chunk: Dict[str, Any]):
#         """Test uploading a single document - useful for debugging."""
#         print("🔄 Testing single document upload...")
#         document = self.transform_chunk_to_document(chunk)
        
#         print(f"Document structure:")
#         for key, value in document.items():
#             if key == "scope_of_work_vectorized":
#                 print(f"  {key}: [vector of length {len(value)}]")
#             else:
#                 print(f"  {key}: {value}")
        
#         try:
#             result = self.search_client.upload_documents(documents=[document])
#             if result[0].succeeded:
#                 print(f"✅ Successfully uploaded document: {result[0].key}")
#             else:
#                 print(f"❌ Failed to upload document: {result[0].error_message}")
#         except Exception as e:
#             print(f"❌ Error during upload: {e}")


# if __name__ == "__main__":
#     uploader = AzureSearchRFPRequestUploader()
    
#     # Your provided JSON data
#     data = {
#         "filename": "705-25318708.00-RFP-Waubaushene TS-EN-ST-TEL-TIP",
#         "total_chunks": 1,
#         "processing_method": "enhanced_chunking_with_verbalization_and_llm_metadata",
#         "chunk_types": {
#             "text": 1,
#             "table": 0,
#             "image": 0
#         },
#         "created_at": "",
#         "chunks": [
#             {
#                 "chunk_id": "f7127442",
#                 "project_id": "705-25318708.00",
#                 "project_name": "TECHNICAL INFORMATION PACKAGE (TIP)",
#                 "client": "Hydro One Networks Inc.",
#                 "region": "Toronto, ON, Canada",
#                 "industry": "Telecommunications",
#                 "prepared_date": "none",
#                 "station_discipline": "Telecom",
#                 "scope_of_work": "The scope includes designing and implementing a new DESN LAN, decommissioning the existing LAN, reconfiguring routers for SCADA connectivity, installing inter-building fibre and metallic cables, relocating Rogers fibre cable, and ensuring compliance with Hydro One standards.",
#                 "required_activities": "Tasks include reviewing scope documents, collaborating with stakeholders, preparing design packages, updating drawings, ordering materials, configuring routers and switches, testing LAN systems, and submitting QA/QC forms."
#             }
#         ]
#     }
    
#     # Test single document first (recommended for debugging)
#     print("=== Testing Single Document Upload ===")
#     uploader.test_single_document_upload(data["chunks"][0])
    
#     # Upload all data
#     print("\n=== Uploading All Data ===")
#     uploader.upload_direct_data(data)
    
#     # Alternative: Load from a JSON file
#     # json_file_path = "path/to/your/json/file.json"
#     # uploader.load_and_upload_chunks(json_file_path)



import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI

from config import (
    AZURE_AI_SEARCH_ENDPOINT,
    AZURE_AI_SEARCH_KEY,
    AZURE_AI_SEARCH_RFI_INDEX_NAME,
    AZURE_EMBEDDING_MODEL,
    AZURE_EMBEDDING_API_KEY,
    AZURE_EMBEDDING_ENDPOINT
)

class AzureSearchRFPRequestUploader:
    def __init__(self):
        load_dotenv()

        # Azure clients
        self.search_client = SearchClient(
            endpoint=AZURE_AI_SEARCH_ENDPOINT,
            index_name=AZURE_AI_SEARCH_RFI_INDEX_NAME,
            credential=AzureKeyCredential(AZURE_AI_SEARCH_KEY)
        )

        self.openai_client = AzureOpenAI(
            api_key=AZURE_EMBEDDING_API_KEY,
            api_version="2023-05-15",
            azure_endpoint=AZURE_EMBEDDING_ENDPOINT
        )

    def get_embedding(self, text: str, model: str = None) -> List[float]:
        """Generate embeddings for given text."""
        if model is None:
            model = AZURE_EMBEDDING_MODEL
        try:
            response = self.openai_client.embeddings.create(input=text, model=model)
            return response.data[0].embedding
        except Exception as e:
            print(f" Error generating embedding: {e}")
            return [0.0] * 3072

    # def transform_chunk_to_document(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
    #     """Transform chunk data to match new Azure Search index schema."""

    #     # Helper: validate/normalize prepared_date
    #     def get_prepared_date(chunk: Dict[str, Any]) -> str:
    #         from datetime import datetime
    #         date_str = str(chunk.get("prepared_date", "")).strip()
    #         invalid_values = {"", "none", "null", "na", "n/a"}

    #         def is_valid_date_format(date: str) -> bool:
    #             try:
    #                 datetime.strptime(date, "%Y-%m-%d")
    #                 return True
    #             except ValueError:
    #                 return False

    #         if date_str.lower() in invalid_values or not is_valid_date_format(date_str):
    #             project_id = chunk.get("project_id", "")
    #             try:
    #                 part_after_dash = project_id.split("-")[1]
    #                 year_prefix = part_after_dash[:2]
    #                 year = int(year_prefix)
    #                 year = year + 2000 if year < 66 else year + 1900
    #                 return f"{year}-01-01"
    #             except Exception as e:
    #                 print(f" Warning: Failed to parse year from project_id '{project_id}': {e}")
    #                 return None
    #         return date_str

    #     prepared_date_value = get_prepared_date(chunk)

    #     # Base schema fields
    #     document = {
    #         "chunk_id": chunk.get("chunk_id"),
    #         "project_id": chunk.get("project_id"),
    #         "project_name": chunk.get("project_name"),
    #         "file_name": chunk.get("file_name"),
    #         "content_type": chunk.get("content_type"),
    #         "created_at": chunk.get("created_at"),
    #         "client": chunk.get("client"),
    #         "region": chunk.get("region"),
    #         "industry": chunk.get("industry"),
    #         "prepared_date": prepared_date_value,
    #         "discipline": chunk.get("discipline"),
    #         "scope_of_work": chunk.get("scope_of_work"),
    #         "required_activities": chunk.get("required_activities"),
    #         "voltage_class": chunk.get("voltage_class"),
    #         "transformer": chunk.get("transformer"),
    #         "transformer_foundations": chunk.get("transformer_foundations"),
    #         "equipment_support_foundations": chunk.get("equipment_support_foundations"),
    #         "HVAC_and_FAS": chunk.get("HVAC_and_FAS"),
    #         "HADs_arrangements": chunk.get("HADs_arrangements"),
    #         "control_design_packages": chunk.get("control_design_packages"),
    #         "SCADA_infrastructure": chunk.get("SCADA_infrastructure"),
    #         "bus_systems": chunk.get("bus_systems"),
    #         "circuit_breakers_and_disconnects": chunk.get("circuit_breakers_and_disconnects"),
    #         "station_lan_networks": chunk.get("station_lan_networks"),
    #         "scada_and_transport_infrastructure": chunk.get("scada_and_transport_infrastructure"),
    #         "transformer_protection": chunk.get("transformer_protection"),
    #         "breaker_protection": chunk.get("breaker_protection"),
    #         "grading_and_roads": chunk.get("grading_and_roads"),
    #         "drainage_and_water_management": chunk.get("drainage_and_water_management"),
    #         "steel_and_station_structures": chunk.get("steel_and_station_structures"),
    #         "transformer_and_equipment_structures": chunk.get("transformer_and_equipment_structures"),
    #         "new_metering_installations": chunk.get("new_metering_installations"),
    #         "existing_metering_retain_or_update": chunk.get("existing_metering_retain_or_update"),
    #         "line_relocations_and_bypasses": chunk.get("line_relocations_and_bypasses"),
    #         "line_rerouting_and_extensions": chunk.get("line_rerouting_and_extensions"),
    #     }

    #     # Embeddings
    #     scope_text = chunk.get("scope_of_work", "")
    #     req_text = chunk.get("required_activities", "")

    #     if scope_text:
    #         print(f" Generating embedding for scope_of_work: {scope_text[:100]}...")
    #         document["scope_of_work_vectorized"] = self.get_embedding(scope_text)
    #     else:
    #         document["scope_of_work_vectorized"] = [0.0] * 3072

    #     if req_text:
    #         print(f" Generating embedding for required_activities: {req_text[:100]}...")
    #         document["required_activities_vectorized"] = self.get_embedding(req_text)
    #     else:
    #         document["required_activities_vectorized"] = [0.0] * 3072

    #     return document

    def expand_chunk_by_components(self, chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Expand a single chunk into multiple documents, one per discipline inside 'components'.
        """
        documents = []
        base_fields = {
            "chunk_id": chunk.get("chunk_id"),
            "project_id": chunk.get("project_id"),
            "project_name": chunk.get("project_name"),
            "file_name": chunk.get("file_name"),
            "content_type": chunk.get("content_type"),
            "created_at": chunk.get("created_at"),
            "client": chunk.get("client"),
            "region": chunk.get("region"),
            "industry": chunk.get("industry"),
            "prepared_date": chunk.get("prepared_date"),
        }

        components = chunk.get("components", {})
        if not components:
            print(f"⚠️ No components found in chunk {chunk.get('chunk_id')}")
            return []

        for discipline, comp_data in components.items():
            doc = dict(base_fields)  # copy base fields
            doc["discipline"] = discipline

            # Discipline-specific fields from comp_data
            doc["scope_of_work"] = comp_data.get("scope_of_work", "")
            doc["required_activities"] = comp_data.get("required_activities", "")

            # Optional discipline-specific fields matching your index schema
            discipline_fields = [
                "bus_systems", "transformer", "transformer_foundations",
                "equipment_support_foundations", "HVAC_and_FAS", "HADs_arrangements",
                "control_design_packages", "SCADA_infrastructure", "bus_systems",
                "circuit_breakers_and_disconnects", "station_lan_networks",
                "scada_and_transport_infrastructure", "transformer_protection",
                "breaker_protection", "grading_and_roads", "drainage_and_water_management",
                "steel_and_station_structures", "transformer_and_equipment_structures",
                "new_metering_installations", "existing_metering_retain_or_update",
                "line_relocations_and_bypasses", "line_rerouting_and_extensions"
            ]
            for f in discipline_fields:
                doc[f] = comp_data.get(f, "")

            # Add embeddings
            if doc["scope_of_work"]:
                doc["scope_of_work_vectorized"] = self.get_embedding(doc["scope_of_work"])
            else:
                doc["scope_of_work_vectorized"] = [0.0] * 3072

            if doc["required_activities"]:
                doc["required_activities_vectorized"] = self.get_embedding(doc["required_activities"])
            else:
                doc["required_activities_vectorized"] = [0.0] * 3072

            # Make chunk_id unique per discipline
            doc["chunk_id"] = f"{chunk.get('chunk_id')}_{discipline}"

            documents.append(doc)

        return documents


    def upload_documents_in_batches(self, documents: List[Dict[str, Any]], batch_size: int = 50):
        """Upload documents to Azure Search in batches."""
        total_docs = len(documents)
        successful, failed = 0, 0

        for i in range(0, total_docs, batch_size):
            batch = documents[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            print(f" Uploading batch {batch_num}/{(total_docs+batch_size-1)//batch_size}...")

            try:
                result = self.search_client.upload_documents(documents=batch)
                batch_success = sum(1 for r in result if r.succeeded)
                batch_fail = len(batch) - batch_success

                for r in result:
                    if not r.succeeded:
                        print(f"Failed doc {r.key}: {r.error_message}")

                successful += batch_success
                failed += batch_fail
                print(f" Batch {batch_num} done: {batch_success} ok, {batch_fail} failed")
            except Exception as e:
                print(f" Error uploading batch {batch_num}: {e}")
                failed += len(batch)

        print(f"\n Upload finished → {successful} succeeded, {failed} failed (total {total_docs})")
        return successful, failed

    # def upload_chunks_from_dict(self, chunk_data: Dict[str, Any]):
    #     chunks = chunk_data.get("chunks", [])
    #     if not chunks:
    #         print(" No chunks found in input data")
    #         return
    #     print(f" Found {len(chunks)} chunks → processing...")
    #     docs = [self.transform_chunk_to_document(c) for c in chunks]
    #     self.upload_documents_in_batches(docs)

    def upload_chunks_from_dict(self, chunk_data: Dict[str, Any]):
        chunks = chunk_data.get("chunks", [])
        if not chunks:
            print("❌ No chunks found in input data")
            return

        print(f"📄 Found {len(chunks)} chunks → expanding by components...")
        documents = []
        for chunk in chunks:
            documents.extend(self.expand_chunk_by_components(chunk))

        print(f"📄 Expanded into {len(documents)} documents")
        self.upload_documents_in_batches(documents)


    def load_and_upload_chunks(self, json_file_path: str):
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f" Loaded {json_file_path}")
        except Exception as e:
            print(f" Error loading JSON: {e}")
            return
        self.upload_chunks_from_dict(data)

    def upload_direct_data(self, data: Dict[str, Any]):
        print(" Uploading direct data...")
        self.upload_chunks_from_dict(data)

    def test_single_document_upload(self, chunk: Dict[str, Any]):
        doc = self.transform_chunk_to_document(chunk)
        print(" Document preview:")
        for k, v in doc.items():
            if isinstance(v, list) and len(v) == 3072:
                print(f"  {k}: [embedding length {len(v)}]")
            else:
                print(f"  {k}: {v}")
        try:
            res = self.search_client.upload_documents(documents=[doc])
            if res[0].succeeded:
                print(f" Uploaded doc {res[0].key}")
            else:
                print(f" Upload failed: {res[0].error_message}")
        except Exception as e:
            print(f" Error: {e}")


if __name__ == "__main__":
    # Initialize uploader
    uploader = AzureSearchRFPRequestUploader()

    # -------- Sample test data --------
    sample_data = {
        "chunks": [
            {
  "chunk_id": "81699cf8",
  "project_id": "proj_705-22295407_00-B&M_HONI_RFP-Chatham_SS_docx",
  "project_name": "",
  "file_name": "705-22295407.00-B&M_HONI RFP-Chatham SS.docx",
  "content_type": "document",
  "created_at": "2025-09-09T13:04:57.068826",
  "client": "Hydro One Networks Inc.",
  "industry": "Power & Energy",
  "region": "Ontario, Canada",
  "prepared_date": "2021-10-06",
  "components": {
    "ELE": {
      "scope_of_work": "The electrical scope involves the expansion of the 230kV yard at Chatham SS to include a new diameter, installation of three 3000A circuit breakers, six 230kV disconnect switches, two 2000A line disconnect switches, and six CVTs. A new 230kV relay building will be constructed, along with the installation of two 150kVA and two 75kVA pad-mounted transformers. Electrical arrangements also include modifications to existing diameters, installation of new cable trenches, and yard lighting upgrades.",
      "required_activities": "Activities include installing three 3000A SF6 circuit breakers, six 230kV disconnect switches, two 2000A line disconnect switches with grounding switches, and six CVTs. A new 230kV relay building will be constructed, and two 150kVA and two 75kVA pad-mounted transformers will be installed. Additional tasks involve extending the 230kV yard, modifying existing diameters, installing new cable trenches, and upgrading yard lighting.",
      "voltage_class": "230kV",
      "transformer": "150kVA and 75kVA pad-mounted transformers"
    },
    "FND": {
      "scope_of_work": "The foundation scope includes constructing foundations for 230kV SF6 breakers, bus supports, disconnect switches, CVT supports, and ACSS transformers. Customized foundations for AC panels and road crossings with steel covers and guardrails are also part of the work.",
      "required_activities": "Activities involve installing three foundations for 230kV SF6 breakers, multiple augered or pile foundations for bus supports and disconnect switches, and precast vaults for ACSS transformers. Customized foundations for AC panels and road crossings with steel covers and guardrails are also included.",
      "transformer_foundations": "Precast vaults for ACSS transformers 533T13/533T14 and 533T15/533T16",
      "equipment_support_foundations": "Foundations for 230kV SF6 breakers, bus supports, and disconnect switches"
    },
    "CNT": {
      "scope_of_work": "The control scope involves designing and installing control systems for new and existing equipment, including SCADA/RTU interfaces, LAN expansions, and programmable synchrocheck relays. The work ensures redundancy and compliance with Hydro One and NERC standards.",
      "required_activities": "Activities include expanding the existing 230kV BES LAN, installing new LAN switches and RTUs, configuring SCADA/RTU interfaces, and integrating new protections with existing systems. Additional tasks involve updating NMS lists, ensuring compliance with Hydro One standards, and implementing redundancy measures.",
      "control_design_packages": "Design and installation of control systems for new and existing equipment",
      "SCADA_infrastructure": "Expansion of 230kV BES LAN and integration with SCADA/RTU systems"
    },
    "EQP": {
      "scope_of_work": "The equipment scope includes installing new bus systems, circuit breakers, disconnect switches, and CVTs in the 230kV yard. Modifications to existing bus systems and installation of rigid bus structures are also included.",
      "required_activities": "Activities involve installing new 2x2303kcmil ASC drops from high-level bus to breaker disconnect switches, new rigid bus structures, and 3000A SF6 circuit breakers. Additional tasks include modifying existing bus systems and installing CVTs with associated fuse boxes.",
      "bus_systems": "Installation of new 2x2303kcmil ASC drops and rigid bus structures",
      "circuit_breakers_and_disconnects": "Installation of 3000A SF6 circuit breakers and 230kV disconnect switches"
    },
    "TEL": {
      "scope_of_work": "The telecom scope involves designing and installing new OPGW fiber connections, inter-building fiber and copper cables, and BES LAN expansions. The work also includes relocating existing telecom infrastructure and ensuring compliance with NERC CIP-006 standards.",
      "required_activities": "Activities include installing new 96F OPGW fiber, inter-building 24F fiber cables, and 25PR copper cables. Additional tasks involve relocating existing Bell cables, configuring security networks, and integrating new telecom systems with existing infrastructure.",
      "station_lan_networks": "Design and installation of BES LAN expansions for 230kV systems",
      "scada_and_transport_infrastructure": "Installation of OPGW fiber and inter-building communication cables"
    },
    "PRT": {
      "scope_of_work": "The protection scope includes designing and installing new A and B line protections, breaker protections, and teleprotection systems for the 230kV yard. Modifications to existing protections and integration with SCADA/RTU systems are also included.",
      "required_activities": "Activities involve installing new A and B line protections, breaker protections, and teleprotection systems. Additional tasks include modifying existing protections, integrating new systems with SCADA/RTU, and performing functional testing.",
      "transformer_protection": "not mentioned in document",
      "breaker_protection": "Installation of A and B breaker protections for 3CB24, 3CB26, and 3CB28"
    },
    "STE": {
      "scope_of_work": "The site preparation scope includes grading, road construction, and drainage system installation for the 230kV yard expansion. Activities also involve removing organic material and preparing the site for construction.",
      "required_activities": "Activities include grading 15,600 square meters of the site, constructing 255 meters of service roads, and installing a drainage system. Additional tasks involve removing organic material and laying geotextile material.",
      "grading_and_roads": "Grading 15,600 square meters and constructing 255 meters of service roads",
      "drainage_and_water_management": "Installation of drainage systems as per Hydro One standards"
    },
    "STR": {
      "scope_of_work": "The structural scope includes fabricating and installing steel structures for bus supports, disconnect switches, and CVTs. Modifications to existing structures and preparation of design calculations are also included.",
      "required_activities": "Activities involve fabricating and installing steel structures for bus supports, disconnect switches, and CVTs. Additional tasks include preparing design calculations, galvanizing steel components, and coordinating tests for compliance.",
      "steel_and_station_structures": "Fabrication and installation of steel structures for bus supports and disconnect switches",
      "transformer_and_equipment_structures": "Design and installation of structures for CVTs and other equipment"
    },
    "AUX": {
      "scope_of_work": "The auxiliary systems scope includes providing necessary support systems such as backup power, fire protection, and lighting for the entire 230kV yard.",
      "required_activities": "Activities include installing backup diesel generators, fire alarm systems, fire extinguishers, and emergency lighting in compliance with safety codes.",
      "HVAC_and_FAS": "Installation of 200 kW backup diesel generators",
      "HADs_arrangements": "Installation of fire alarm systems and fire extinguishers"
    },
    "MET": {
      "scope_of_work": "The metering scope includes designing and installing metering systems to monitor voltage, current, and power usage at critical points in the 230kV yard.",
      "required_activities": "Activities involve installing metering transformers, current transformers (CTs), and potential transformers (PTs) for accurate measurement of electrical parameters. Data logging and monitoring systems are also part of the work.",
      "new_metering_installations": "Installation of 230kV metering transformers and CTs",
      "existing_metering_retain_or_update": "Implementation of data logging systems for real-time power monitoring"
    },
    "LN": {
      "scope_of_work": "The lighting scope involves designing and installing a lighting system for the 230kV yard to ensure visibility and safety during nighttime operations.",
      "required_activities": "Activities include installing high-efficiency LED floodlights, pole-mounted lights, and associated wiring to provide proper illumination across the yard.",
      "line_relocations_and_bypasses": "Installation of 100 LED floodlights and pole-mounted lights",
      "line_rerouting_and_extensions": "Design and installation of control panels for lighting system"
    }
  },
  "text_elements_count": 776,
  "total_content_length": 75098,
  "processing_timestamp": "2025-09-09T13:04:57.068826"
},{
  "chunk_id": "8169912cf8",
  "project_id": "proj_705-22295407_00-B&M_HONI_RFP-Chatham_SS_docx",
  "project_name": "",
  "file_name": "705-22295407.00-B&M_HONI RFP-Chatham SS.docx",
  "content_type": "document",
  "created_at": "2025-09-09T13:04:57.068826",
  "client": "Hydro One Networks Inc.",
  "industry": "Power & Energy",
  "region": "Ontario, Canada",
  "prepared_date": "2021-10-06",
  "components": {
    "ELE": {
      "scope_of_work": "The electrical scope involves the expansion of the 230kV yard at Chatham SS to include a new diameter, installation of three 3000A circuit breakers, six 230kV disconnect switches, two 2000A line disconnect switches, and six CVTs. A new 230kV relay building will be constructed, along with the installation of two 150kVA and two 75kVA pad-mounted transformers. Electrical arrangements also include modifications to existing diameters, installation of new cable trenches, and yard lighting upgrades.",
      "required_activities": "Activities include installing three 3000A SF6 circuit breakers, six 230kV disconnect switches, two 2000A line disconnect switches with grounding switches, and six CVTs. A new 230kV relay building will be constructed, and two 150kVA and two 75kVA pad-mounted transformers will be installed. Additional tasks involve extending the 230kV yard, modifying existing diameters, installing new cable trenches, and upgrading yard lighting.",
      "voltage_class": "230kV",
      "transformer": "150kVA and 75kVA pad-mounted transformers"
    }
  },
  "text_elements_count": 776,
  "total_content_length": 75098,
  "processing_timestamp": "2025-09-09T13:04:57.068826"
}

        ]
    }

    # -------- Upload workflow --------
    print("🚀 Starting test upload...")
    uploader.upload_direct_data(sample_data)
