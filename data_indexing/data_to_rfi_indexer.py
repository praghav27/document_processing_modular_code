import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI

from application_logging.custom_logging_to_app_insights import configure_logger, log_custom_event
from opentelemetry import trace

# Configure the logger
logger = configure_logger()

# Create an OpenTelemetry tracer for distributed tracing (optional, for monitoring and diagnostics)
tracer = trace.get_tracer(__name__)

from config import (
    AZURE_AI_SEARCH_ENDPOINT,
    AZURE_AI_SEARCH_KEY,
    AZURE_AI_SEARCH_RFI_INDEX_NAME,
    AZURE_EMBEDDING_MODEL,
    AZURE_EMBEDDING_API_KEY,
    AZURE_EMBEDDING_ENDPOINT
)

class AzureSearchRFPRequestUploader:
    @tracer.start_as_current_span("AzureSearchRFPRequestUploader_init_fn")
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
    @tracer.start_as_current_span("get_embedding_fn")
    def get_embedding(self, text: str, model: str = None) -> List[float]:
        """Generate embeddings for given text."""
        if model is None:
            model = AZURE_EMBEDDING_MODEL
        try:
            response = self.openai_client.embeddings.create(input=text, model=model)
            return response.data[0].embedding
        except Exception as e:
            #print(f" Error generating embedding: {e}")
            return [0.0] * 3072

    
    @tracer.start_as_current_span("expand_chunk_by_components_fn")
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
            "field_type": chunk.get("field_type"),
            "voltage_class": chunk.get("voltage_class"),
            "contract_types": chunk.get("contract_type"),  # schema expects contract_types
            "pricing": chunk.get("pricing"),
        }

        components = chunk.get("components", {})
        if not components:
            #print(f"⚠️ No components found in chunk {chunk.get('chunk_id')}")
            log_custom_event(
                 logger,
                 f"No components found in chunk {chunk.get('chunk_id')}",
                 level="warning",
                )
            return []

        for discipline, comp_data in components.items():
            doc = dict(base_fields)
            doc["ComponentName"] = discipline

            # core text fields
            text_fields = [
                "scope_of_work",
                "required_activities",
                "pricing",
                "disconnect_switches",
                "transformer",
                "transformer_foundations",
                "equipment_support_foundations",
                "HVAC_and_FAS",
                "HADs_arrangements",
                "control_design_packages",
                "SCADA_infrastructure",
                "bus_systems",
                "circuit_breakers_and_disconnects",
                "station_lan_networks",
                "scada_and_transport_infrastructure",
                "transformer_protection",
                "breaker_protection",
                "grading_and_roads",
                "drainage_and_water_management",
                "steel_and_station_structures",
                "transformer_and_equipment_structures",
                "new_metering_installations",
                "existing_metering_retain_or_update",
                "line_relocations_and_bypasses",
                "line_rerouting_and_extensions",
            ]

            for f in text_fields:
                val = comp_data.get(f, "")
                doc[f] = val
                vec_field = f"{f}_vectorized"
                if val:
                    doc[vec_field] = self.get_embedding(val)
                else:
                    doc[vec_field] = [0.0] * 3072

            # unique chunk_id per discipline
            doc["chunk_id"] = f"{chunk.get('chunk_id')}_{discipline}"
            documents.append(doc)

        return documents


    @tracer.start_as_current_span("upload_documents_in_batches_fn")
    def upload_documents_in_batches(self, documents: List[Dict[str, Any]], batch_size: int = 100):
        """Upload documents to Azure Search in LARGER batches for better performance"""
        total_docs = len(documents)
        successful, failed = 0, 0
        # Optimize batch size for parallel processing
        optimized_batch_size = min(batch_size, max(50, total_docs // 5)) if total_docs > 0 else batch_size

        #print(f"📤 Optimized batch upload: {total_docs} documents in batches of {optimized_batch_size}")
        log_custom_event(
                 logger,
                 f"Optimized batch upload: {total_docs} documents in batches of {optimized_batch_size}",
                 level="info",
                )

        for i in range(0, total_docs, optimized_batch_size):
            batch = documents[i:i+optimized_batch_size]
            batch_num = (i // optimized_batch_size) + 1
            total_batches = (total_docs + optimized_batch_size - 1) // optimized_batch_size

            #print(f"📤 Uploading batch {batch_num}/{total_batches} ({len(batch)} documents)...")
            
            try:
                result = self.search_client.upload_documents(documents=batch)
                batch_success = sum(1 for r in result if r.succeeded)
                batch_fail = len(batch) - batch_success
                successful += batch_success
                failed += batch_fail
                #print(f"✅ Batch {batch_num} completed: {batch_success} successful, {batch_fail} failed")
            except Exception as e:
                #print(f"❌ Error uploading batch {batch_num}: {e}")
                failed += len(batch)
        #print(f"\n📊 Upload summary: {successful} successful, {failed} failed (total {total_docs})")
        log_custom_event(
                 logger,
                 f"\n Upload summary: {successful} successful, {failed} failed (total {total_docs})",
                 level="info",
                )
        return successful, failed
    
    @tracer.start_as_current_span("upload_chunks_from_dict_fn")
    def upload_chunks_from_dict(self, chunk_data: Dict[str, Any]):
        """Enhanced batch upload with better performance"""
        chunks = chunk_data.get("chunks", [])
        if not chunks:
            #print("❌ No chunks found in input data")
            log_custom_event(
                 logger,
                 "No chunks found in input data",
                 level="warning",
                )
            return
        #print(f"📄 Processing {len(chunks)} chunks for batch upload...")
        log_custom_event(
                 logger,
                 f"📄 Processing {len(chunks)} chunks for batch upload...",
                 level="info",
                )
        documents = []
        # Process chunks in parallel batches
        for chunk in chunks:
            expanded_docs = self.expand_chunk_by_components(chunk)
            documents.extend(expanded_docs)
        #print(f"📊 Expanded {len(chunks)} chunks into {len(documents)} component documents")
        log_custom_event(
                 logger,
                 f"Expanded {len(chunks)} chunks into {len(documents)} component documents",
                 level="info",
                )
        # Upload with optimized batch processing
        if documents:
            self.upload_documents_in_batches(documents, batch_size=100)  # Larger batches
        else:
            #print("❌ No valid documents to upload")
            log_custom_event(
                 logger,
                 "No valid documents to upload",
                 level="warning",
                )
            
    @tracer.start_as_current_span("load_and_upload_chunks_fn")        
    def load_and_upload_chunks(self, json_file_path: str):
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                #print(f" Loaded {json_file_path}")
        except Exception as e:
            #print(f" Error loading JSON: {e}")
            return
        self.upload_chunks_from_dict(data)

    @tracer.start_as_current_span("upload_direct_data_fn")
    def upload_direct_data(self, data: Dict[str, Any]):
        #print(" Uploading direct data...")
        self.upload_chunks_from_dict(data)

    @tracer.start_as_current_span("test_single_document_upload_fn")
    def test_single_document_upload(self, chunk: Dict[str, Any]):
        doc = self.transform_chunk_to_document(chunk)
        #print(" Document preview:")
        for k, v in doc.items():
            if isinstance(v, list) and len(v) == 3072:
                #print(f"  {k}: [embedding length {len(v)}]")
                log_custom_event(
                 logger,
                 f"  {k}: [embedding length {len(v)}]",
                 level="info",
                )
            else:
                #print(f"  {k}: {v}")
                log_custom_event(
                 logger,
                 f"  {k}: {v}",
                 level="info",
                )
        try:
            res = self.search_client.upload_documents(documents=[doc])
            if res[0].succeeded:
                #print(f" Uploaded doc {res[0].key}")
                log_custom_event(
                 logger,
                 f" Uploaded doc {res[0].key}",
                 level="info",
                )
            else:
                #print(f" Upload failed: {res[0].error_message}")
                log_custom_event(
                 logger,
                 f" Uploaded doc {res[0].key}",
                 level="warning",
                )
        except Exception as e:
            #print(f" Error: {e}")
            print()


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
  "field_type": "Station",
  "voltage_class": "230kV",
  "contract_type": "T&M",
  "pricing": "3.5M",
  "components": {
    "ELE": {
      "scope_of_work": "The electrical scope involves the expansion of the 230kV yard at Chatham SS to include a new diameter, installation of three 3000A circuit breakers, six 230kV disconnect switches, two 2000A line disconnect switches, and six CVTs. A new 230kV relay building will be constructed, along with the installation of two 150kVA and two 75kVA pad-mounted transformers. Electrical arrangements also include modifications to existing diameters, installation of new cable trenches, and yard lighting upgrades.",
      "required_activities": "Activities include installing three 3000A SF6 circuit breakers, six 230kV disconnect switches, two 2000A line disconnect switches with grounding switches, and six CVTs. A new 230kV relay building will be constructed, and two 150kVA and two 75kVA pad-mounted transformers will be installed. Additional tasks involve extending the 230kV yard, modifying existing diameters, installing new cable trenches, and upgrading yard lighting.",
      "disconnect_switches": "230kV",
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
  "field_type": "Station",
  "voltage_class": "230kV",
  "contract_type": "T&M",
  "pricing": "3.5M",
  "components": {
    "ELE": {
      "scope_of_work": "The electrical scope involves the expansion of the 230kV yard at Chatham SS to include a new diameter, installation of three 3000A circuit breakers, six 230kV disconnect switches, two 2000A line disconnect switches, and six CVTs. A new 230kV relay building will be constructed, along with the installation of two 150kVA and two 75kVA pad-mounted transformers. Electrical arrangements also include modifications to existing diameters, installation of new cable trenches, and yard lighting upgrades.",
      "required_activities": "Activities include installing three 3000A SF6 circuit breakers, six 230kV disconnect switches, two 2000A line disconnect switches with grounding switches, and six CVTs. A new 230kV relay building will be constructed, and two 150kVA and two 75kVA pad-mounted transformers will be installed. Additional tasks involve extending the 230kV yard, modifying existing diameters, installing new cable trenches, and upgrading yard lighting.",
      "disconnect_switches": "230kV",
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
    #print("🚀 Starting test upload...")
    log_custom_event(
                 logger,
                 "Starting test upload...",
                 level="info",
                )
    uploader.upload_direct_data(sample_data)
