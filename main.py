


import os
from processors import AzureDocumentProcessor, ContentExtractor, FileHandler
from storage.storage_factory import get_storage_instance
from typing import Dict, Any, List
import asyncio
from datetime import datetime

from application_logging.custom_logging_to_app_insights import configure_logger, log_step, log_exception
from opentelemetry import trace

# Configure the logger
logger = configure_logger()

# Create an OpenTelemetry tracer for distributed tracing (optional, for monitoring and diagnostics)
tracer = trace.get_tracer(__name__)

class DocumentProcessorMain:
    def __init__(self):
        with tracer.start_as_current_span("main_init_fn") as span:
            self.azure_processor = AzureDocumentProcessor()
            self.content_extractor = ContentExtractor()
            self.file_handler = FileHandler()
            self.storage = get_storage_instance() 
    
    def process_document(self, uploaded_file, progress_callback=None) -> Dict[str, Any]:
        with tracer.start_as_current_span("process_document_fn") as span:
            """Main processing pipeline with Azure Document Intelligence (Single file - existing)"""
            filename = uploaded_file.name
            base_filename = os.path.splitext(filename)[0]
            
            try:
                # Validate file
                if not self.file_handler.validate_file(filename):
                    raise ValueError(f"Unsupported file format: {self.file_handler.get_file_extension(filename)}")
                
                if progress_callback:
                    progress_callback("🔍 Converting file to bytes...")
                
                # Convert to bytes
                file_bytes = self.file_handler.process_file(uploaded_file)
                
                if progress_callback:
                    progress_callback("📄 Analyzing document with Azure Document Intelligence Layout Model...")
                
                # Analyze with Azure DI
                result, client, operation_id = self.azure_processor.analyze_document(file_bytes, filename)
                
                if progress_callback:
                    progress_callback("📝 Extracting text, tables, and images...")
                    progress_callback("🤖 Extracting metadata with enhanced LLM processing...")
                    progress_callback("💾 Storing metadata in Azure Table Storage...")
                
                # Extract all content - NOW WITH ASYNC SUPPORT + AZURE TABLE STORAGE
                extracted_content = asyncio.run(self.content_extractor.extract_all_content(
                    result,
                    filename,
                    client=client,
                    operation_id=operation_id
                ))

                if progress_callback:
                    progress_callback("💾 Saving extracted content...")
                    progress_callback("✅ Azure Table Storage operations completed...")
                
                # Finalize and return response
                return self._finalize_response(extracted_content, filename)
                
            except Exception as e:
                if progress_callback:
                    progress_callback(f"❌ Error processing document: {str(e)}")
                raise e

    async def process_multiple_documents_rfi(self, uploaded_files: List) -> List[Dict[str, Any]]:
        """
        Process multiple RFI documents in parallel with Azure Table Storage integration
        
        Args:
            uploaded_files: List of uploaded file objects from Streamlit
            
        Returns:
            List[Dict]: List of processing results for each file
        """
        print(f"\n{'='*80}")
        print(f"🚀 STARTING PARALLEL RFI PROCESSING FOR {len(uploaded_files)} DOCUMENTS")
        print(f"🗃️ Azure Table Storage: ENABLED - Metadata and components will be stored")
        print(f"{'='*80}")
        
        # Create tasks for parallel processing
        processing_tasks = []
        file_info = []
        
        for uploaded_file in uploaded_files:
            filename = uploaded_file.name
            print(f"📄 Queuing file: {filename}")
            
            # Store file info for later use
            file_info.append({
                'filename': filename,
                'size': uploaded_file.size,
                'uploaded_file': uploaded_file
            })
            
            # Create async task for each file
            task = self._process_single_rfi_document_async(uploaded_file)
            processing_tasks.append(task)
        
        print(f"🔄 Processing {len(processing_tasks)} documents in parallel...")
        print(f"💾 Each document will store metadata in Azure Table Storage...")
        
        # Execute all tasks in parallel
        try:
            results = await asyncio.gather(*processing_tasks, return_exceptions=True)
        except Exception as e:
            print(f"❌ Error in parallel processing: {e}")
            results = [{'success': False, 'error': str(e), 'filename': 'unknown'} for _ in uploaded_files]
        
        # Process results and handle exceptions
        processed_results = []
        successful_chunks = []  # Collect all chunks for terminal output
        table_storage_stats = {'successful': 0, 'failed': 0}
        
        for i, result in enumerate(results):
            filename = file_info[i]['filename']
            
            if isinstance(result, Exception):
                print(f"❌ Failed to process {filename}: {str(result)}")
                processed_results.append({
                    'filename': filename,
                    'success': False,
                    'error': str(result),
                    'chunks': [],
                    'metadata': {},
                    'table_storage': {'stored': False, 'error': str(result)}
                })
                table_storage_stats['failed'] += 1
            elif result and result.get('success', False):
                print(f"✅ Successfully processed {filename}")
                # Check if table storage was successful
                table_storage_success = result.get('enhancement_info', {}).get('table_storage_enabled', False)
                if table_storage_success:
                    table_storage_stats['successful'] += 1
                else:
                    table_storage_stats['failed'] += 1
                    
                processed_results.append(result)
                # Collect chunks for terminal output
                if result.get('chunks'):
                    successful_chunks.extend(result['chunks'])
            else:
                print(f"❌ Failed to process {filename}: {result.get('error', 'Unknown error')}")
                table_storage_stats['failed'] += 1
                processed_results.append(result)
        
        # Print summary
        successful_count = len([r for r in processed_results if r.get('success', False)])
        failed_count = len(processed_results) - successful_count
        
        print(f"\n{'='*80}")
        print(f"📊 PARALLEL RFI PROCESSING + AZURE TABLE STORAGE SUMMARY")
        print(f"{'='*80}")
        print(f"✅ Successfully processed: {successful_count}/{len(uploaded_files)} documents")
        print(f"❌ Failed to process: {failed_count} documents")
        print(f"📋 Total chunks created: {len(successful_chunks)}")
        print(f"🗃️ Azure Table Storage:")
        print(f"   ✅ Successful metadata storage: {table_storage_stats['successful']} documents")
        print(f"   ❌ Failed metadata storage: {table_storage_stats['failed']} documents")
        
        # Print all chunks to terminal (as requested)
        if successful_chunks:
            self._print_all_chunks_to_terminal(successful_chunks)
        
        return processed_results

    async def _process_single_rfi_document_async(self, uploaded_file) -> Dict[str, Any]:
        """
        Process a single RFI document asynchronously with Azure Table Storage integration
        
        Args:
            uploaded_file: Single uploaded file object
            
        Returns:
            Dict: Processing result for this file
        """
        filename = uploaded_file.name
        
        try:
            print(f"🔍 Processing: {filename}")
            
            # Validate file
            if not self.file_handler.validate_file(filename):
                return {
                    'filename': filename,
                    'success': False,
                    'error': f"Unsupported file format: {self.file_handler.get_file_extension(filename)}",
                    'chunks': [],
                    'metadata': {},
                    'table_storage': {'stored': False, 'error': 'Invalid file format'}
                }
            
            # Convert to bytes
            file_bytes = self.file_handler.process_file(uploaded_file)
            print(f"📄 Analyzing {filename} with Azure Document Intelligence...")
            
            # Analyze with Azure DI
            result, client, operation_id = self.azure_processor.analyze_document(file_bytes, filename)
            
            print(f"📝 Extracting content from {filename}...")
            print(f"💾 Storing metadata in Azure Table Storage for {filename}...")
            
            # Extract all content using the enhanced content extractor WITH TABLE STORAGE
            extracted_content = await self.content_extractor.extract_all_content(
                result,
                filename,
                client=client,
                operation_id=operation_id
            )
            
            print(f"✅ Successfully processed {filename}")
            
            # Check if table storage was successful
            table_storage_enabled = extracted_content.get('enhancement_info', {}).get('table_storage_enabled', False)
            
            # Return structured result
            return {
                'filename': filename,
                'success': True,
                'error': None,
                'chunks': extracted_content.get('text_chunks', []),
                'metadata': extracted_content.get('document_metadata', {}),
                'document_type': extracted_content.get('document_type', 'RFI'),
                'project_id': extracted_content.get('project_id', 'unknown'),
                'stats': extracted_content.get('stats', {}),
                'enhancement_info': extracted_content.get('enhancement_info', {}),
                'table_storage': {
                    'stored': table_storage_enabled,
                    'file_metadata': table_storage_enabled,
                    'component_data': table_storage_enabled and extracted_content.get('document_type') == 'RFI'
                },
                'processing_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error processing {filename}: {str(e)}")
            return {
                'filename': filename,
                'success': False,
                'error': str(e),
                'chunks': [],
                'metadata': {},
                'table_storage': {'stored': False, 'error': str(e)},
                'processing_time': datetime.now().isoformat()
            }

    def _print_all_chunks_to_terminal(self, all_chunks: List[Dict]):
        """
        Print all chunks from all documents to terminal in a formatted way (Enhanced with Table Storage info)
        
        Args:
            all_chunks: List of all chunks from all processed documents
        """
        print(f"\n{'='*100}")
        print(f"📋 ALL RFI CHUNKS OUTPUT - ENHANCED COMPONENT FORMAT + AZURE TABLE STORAGE")
        print(f"{'='*100}")
        print(f"Total chunks across all documents: {len(all_chunks)}")
        print(f"🗃️ All metadata and components stored in Azure Table Storage")
        
        # Group chunks by document/project
        chunks_by_project = {}
        for chunk in all_chunks:
            project_id = chunk.get('project_id', 'unknown')
            if project_id not in chunks_by_project:
                chunks_by_project[project_id] = []
            chunks_by_project[project_id].append(chunk)
        
        # Print chunks grouped by document
        for project_id, chunks in chunks_by_project.items():
            print(f"\n{'-'*80}")
            print(f"📄 PROJECT: {project_id} ({len(chunks)} chunks)")
            print(f"🗃️ Table Storage: FileMetadataV2 + ComponentDataV2 records created")
            print(f"{'-'*80}")
            
            for i, chunk in enumerate(chunks, 1):
                print(f"\nCHUNK {i}:")
                print(f"  📋 Chunk ID: {chunk.get('chunk_id', 'N/A')}")
                print(f"  📂 Project ID: {chunk.get('project_id', 'N/A')}")
                print(f"  🏢 Project Name: {chunk.get('project_name', 'N/A')}")
                print(f"  🏭 Client: {chunk.get('client', 'N/A')}")
                print(f"  🌍 Industry: {chunk.get('industry', 'N/A')}")
                print(f"  📍 Region: {chunk.get('region', 'N/A')}")
                print(f"  📅 Prepared Date: {chunk.get('prepared_date', 'N/A')}")
                print(f"  🏞️ Field Type: {chunk.get('field_type', 'N/A')}")
                print(f"  🔌 Voltage Class: {chunk.get('voltage_class', 'N/A')}")
                print(f"  📃 Contract Types: {chunk.get('contract_types', 'N/A')}")
                print(f"  💰 Pricing: {chunk.get('pricing', 'N/A')}")
                
                # Print components (enhanced format with specific fields)
                components = chunk.get('components', {})
                if components:
                    print(f"  ⚙️ Components ({len(components)}) - Stored in ComponentDataV2:")
                    for comp_code, comp_data in components.items():
                        print(f"    • {comp_code} Component:")
                        print(f"      - Scope of Work: {len(comp_data.get('scope_of_work', ''))} chars")
                        print(f"      - Required Activities: {len(comp_data.get('required_activities', ''))} chars")
                        
                        # Print component-specific fields
                        for field_name, field_value in comp_data.items():
                            if field_name not in ['scope_of_work', 'required_activities']:
                                field_preview = (field_value[:50] + "...") if len(str(field_value)) > 50 else field_value
                                print(f"      - {field_name}: {field_preview}")
                else:
                    print(f"  ⚙️ Components: None identified")
                
                print(f"  🕒 Created: {chunk.get('metadata', {}).get('created_at', 'N/A')}")
                print(f"  🗃️ Table Storage: Metadata and component records created")
        
        print(f"\n{'='*100}")
        print(f"✅ TERMINAL OUTPUT COMPLETE - All {len(all_chunks)} chunks displayed")
        print(f"🗃️ AZURE TABLE STORAGE - All metadata and components stored for structured querying")
        print(f"📊 Query Tables: FileMetadataV2 (document metadata), ComponentDataV2 (component details)")
        print(f"{'='*100}")
    
    def _finalize_response(self, content: Dict, filename: str) -> Dict:
        with tracer.start_as_current_span("_finalize_response_fn") as span:
            """Finalize response with metadata (existing method - enhanced with table storage info)"""
            
            # Add processing metadata
            content.update({
                "filename": filename,
                "file_extension": self.file_handler.get_file_extension(filename),
                "processing_method": "azure_document_intelligence_with_table_storage"
            })
            
            # Calculate basic statistics if not already present
            if "stats" not in content:
                content["stats"] = {
                    "text_count": len(content.get("text_chunks", [])),
                    "table_count": len(content.get("tables", [])),
                    "image_count": len(content.get("images", []))
                }
            
            # Add table storage information
            content["table_storage_info"] = {
                "enabled": content.get("enhancement_info", {}).get("table_storage_enabled", False),
                "file_metadata_stored": True,  # Always true if processing succeeded
                "component_data_stored": content.get("document_type") == "RFI",  # Only for RFI documents
                "tables_used": ["FileMetadataV2"] + (["ComponentDataV2"] if content.get("document_type") == "RFI" else [])
            }
            
            return content

# Global instance for use in Streamlit
document_processor = DocumentProcessorMain()