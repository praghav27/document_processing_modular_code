import os
import re
import asyncio
from typing import Dict, Any, List
from processors.azure_processor import AzureDocumentProcessor
from processors.file_handler import FileHandler
from processors.tip.tip_metadata_extractor import TIPMetadataExtractor
from storage.storage_factory import get_storage_instance
from data_indexing.tip_uploader import TIPUploader

class SimpleTIPProcessor:
    """Simple TIP document processing pipeline - No RFI/RFP detection, straight TIP processing"""
    
    def __init__(self):
        self.azure_processor = AzureDocumentProcessor()
        self.file_handler = FileHandler()
        self.tip_extractor = TIPMetadataExtractor()
        self.storage = get_storage_instance()
        self.tip_uploader = TIPUploader()
        
        print("🔵 Simple TIP Processor initialized")
        print("   📄 Azure Document Intelligence: Ready")
        print("   🤖 TIP Metadata Extractor: Ready")
        print("   💾 Storage: Ready")
        print("   🔍 Azure AI Search: Ready")
    
    async def process_document(self, uploaded_file, progress_callback=None) -> Dict[str, Any]:
        """Process TIP document - simple flow: File -> DI -> Text -> LLM -> Index"""
        filename = uploaded_file.name
        base_filename = os.path.splitext(filename)[0]
        
        try:
            # Step 1: Validate file
            if not self.file_handler.validate_file(filename):
                raise ValueError(f"Unsupported file format: {self.file_handler.get_file_extension(filename)}")
            
            if progress_callback:
                progress_callback("🔍 Converting file to bytes...")
            
            # Step 2: Convert to bytes
            file_bytes = self.file_handler.process_file(uploaded_file)
            
            if progress_callback:
                progress_callback("📄 Analyzing document with Azure Document Intelligence...")
            
            # Step 3: Analyze with Azure DI - extract text, tables, images
            result, client, operation_id = self.azure_processor.analyze_document(file_bytes, filename)
            
            if progress_callback:
                progress_callback("📝 Extracting all content from Document Intelligence...")
            
            # Step 4: Extract ALL content (text, tables, images) - but only use text for metadata
            text_elements = self._extract_text_elements(result)
            table_count = len(result.tables) if hasattr(result, 'tables') and result.tables else 0
            image_count = len(result.figures) if hasattr(result, 'figures') and result.figures else 0
            
            print(f"📋 Extracted from Document Intelligence:")
            print(f"   📝 Text elements: {len(text_elements)}")
            print(f"   📊 Tables: {table_count}")
            print(f"   🖼️ Images: {image_count}")
            
            if progress_callback:
                progress_callback("🔑 Extracting document ID from filename...")
            
            # Step 5: Extract document ID from filename (e.g., 705-25318708.00)
            doc_id_from_filename = self._extract_doc_id_from_filename(filename)
            print(f"🔑 Document ID from filename: {doc_id_from_filename}")
            
            if progress_callback:
                progress_callback("🤖 Extracting TIP metadata using Azure OpenAI...")
            
            # Step 6: Extract TIP metadata using LLM (6 fields)
            tip_metadata = await self.tip_extractor.extract_metadata(text_elements, doc_id_from_filename)
            print(f"📋 TIP metadata extracted: {len(tip_metadata)} fields")
            
            if progress_callback:
                progress_callback("💾 Saving TIP metadata locally...")
            
            # Step 7: Save metadata locally as JSON
            local_path = self._save_tip_metadata_locally(tip_metadata, base_filename)
            
            if progress_callback:
                progress_callback("🔍 Uploading TIP metadata to Azure AI Search...")
            
            # Step 8: Upload to Azure AI Search index
            upload_success = await self.tip_uploader.upload_tip_metadata(tip_metadata, base_filename)
            
            if progress_callback:
                if upload_success:
                    progress_callback("✅ TIP document processed successfully!")
                else:
                    progress_callback("⚠️ TIP metadata extracted but search upload failed")
            
            # Step 9: Return results
            return self._create_response(
                tip_metadata, 
                filename, 
                local_path, 
                upload_success, 
                len(text_elements),
                table_count,
                image_count
            )
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ Error processing TIP document: {str(e)}")
            raise e
    
    def _extract_text_elements(self, result) -> List[Dict]:
        """Extract text elements from Azure DI result"""
        text_elements = []
        
        if hasattr(result, 'paragraphs') and result.paragraphs:
            for para_idx, paragraph in enumerate(result.paragraphs):
                content = getattr(paragraph, 'content', '')
                if content and content.strip():
                    # Get page number safely
                    page_number = 1
                    try:
                        if hasattr(paragraph, 'bounding_regions') and paragraph.bounding_regions:
                            page_number = getattr(paragraph.bounding_regions[0], 'page_number', 1)
                    except:
                        pass
                    
                    text_elements.append({
                        "content": content,
                        "role": getattr(paragraph, "role", "unknown"),
                        "page_number": page_number,
                        "paragraph_index": para_idx + 1
                    })
        
        return text_elements
    
    def _extract_doc_id_from_filename(self, filename: str) -> str:
        """Extract document ID from filename (e.g., 705-25318708.00, 705-25318710.00)"""
        try:
            # Pattern to match doc IDs like 705-25318708.00, 705-25318710.00
            pattern = r'(\d{3}-\d{8}\.\d{2})'
            match = re.search(pattern, filename)
            
            if match:
                doc_id = match.group(1)
                print(f"✅ Found document ID in filename: {doc_id}")
                return doc_id
            else:
                # Fallback: try other patterns
                pattern2 = r'(\d{3}-\d+\.\d+)'
                match2 = re.search(pattern2, filename)
                if match2:
                    doc_id = match2.group(1)
                    print(f"✅ Found document ID (alternative pattern): {doc_id}")
                    return doc_id
                
                print(f"⚠️ No document ID pattern found in filename: {filename}")
                return "Not Found"
                
        except Exception as e:
            print(f"❌ Error extracting document ID from filename: {e}")
            return "Not Found"
    
    def _save_tip_metadata_locally(self, metadata: Dict, base_filename: str) -> str:
        """Save TIP metadata to local storage as JSON"""
        try:
            if hasattr(self.storage, 'save_tip_metadata'):
                return self.storage.save_tip_metadata(metadata, base_filename)
            else:
                # Fallback to basic JSON save
                import json
                from config import TEXT_DIR
                
                os.makedirs(TEXT_DIR, exist_ok=True)
                json_filename = f"{base_filename}_tip_metadata.json"
                json_path = os.path.join(TEXT_DIR, json_filename)
                
                tip_data = {
                    "filename": base_filename,
                    "extraction_method": "tip_azure_openai",
                    "tip_metadata": metadata,
                    "created_at": __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(tip_data, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Saved TIP metadata locally: {json_path}")
                return json_path
                
        except Exception as e:
            print(f"❌ Error saving TIP metadata locally: {e}")
            return None
    
    def _create_response(self, metadata: Dict, filename: str, local_path: str, upload_success: bool, 
                        text_elements_count: int, table_count: int, image_count: int) -> Dict:
        """Create response with TIP processing results"""
        return {
            "filename": filename,
            "file_extension": self.file_handler.get_file_extension(filename),
            "processing_method": "simple_tip_azure_document_intelligence",
            "tip_metadata": metadata,
            "local_storage_path": local_path,
            "azure_search_uploaded": upload_success,
            "content_extracted": {
                "text_elements": text_elements_count,
                "tables": table_count,
                "images": image_count
            },
            "stats": {
                "text_elements_extracted": text_elements_count,
                "metadata_fields_extracted": len(metadata),
                "doc_id": metadata.get('doc_id', 'Not Found'),
                "project_name": metadata.get('project_name', 'Not Specified'),
                "scope_word_count": len(metadata.get('scope_of_work', '').split()) if metadata.get('scope_of_work') else 0
            }
        }