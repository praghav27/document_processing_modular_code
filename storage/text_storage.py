import os
import json
import pandas as pd
from config import TEXT_DIR
from typing import List, Dict


class TextStorage:
    """Handle text-related storage operations"""
    
    def __init__(self):
        pass
    
    def save_text_chunks(self, text_chunks: List[Dict], filename: str) -> str:
        """Save enhanced text chunks with verbalization and LLM metadata as JSON file"""
        json_filename = f"{filename}_text_chunks.json"
        json_path = os.path.join(TEXT_DIR, json_filename)
        
        # Extract LLM metadata from chunks if available
        llm_metadata = {}
        if text_chunks and text_chunks[0].get('metadata', {}).get('llm_extracted_metadata'):
            llm_metadata = text_chunks[0]['metadata']['llm_extracted_metadata']
        
        # Convert chunks to serializable format with enhanced metadata including LLM data
        chunk_data = {
            "filename": filename,
            "total_chunks": len(text_chunks),
            "processing_method": "enhanced_chunking_with_verbalization_and_llm_metadata",
            "llm_extracted_metadata": llm_metadata,  # NEW: Store LLM metadata at document level
            "chunk_types": {
                "text": len([c for c in text_chunks if c['content_type'] == 'text']),
                "table": len([c for c in text_chunks if c['content_type'] == 'table']),
                "image": len([c for c in text_chunks if c['content_type'] == 'image'])
            },
            "created_at": text_chunks[0].get("metadata", {}).get("created_at", "") if text_chunks else "",
            "chunks": []
        }
        
        for chunk in text_chunks:
            chunk_info = {
                "chunk_id": chunk.get("chunk_id", ""),
                "file_name": chunk.get("file_name", ""),
                "section_name": chunk.get("section_name", ""),
                "section_no": chunk.get("section_no", ""),
                "domain": chunk.get("domain", ""),
                "content_type": chunk.get("content_type", "text"),
                "author": chunk.get("author", ""),  # Now includes LLM-extracted vendor_name
                "content": chunk.get("content", ""),
                "verbalized_content": chunk.get("verbalized_content", ""),
                "metadata": chunk.get("metadata", {})
            }
            chunk_data["chunks"].append(chunk_info)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved enhanced text chunks with LLM metadata: {json_path}")
        print(f"   📊 Chunk breakdown: {chunk_data['chunk_types']['text']} text, {chunk_data['chunk_types']['table']} table, {chunk_data['chunk_types']['image']} image")
        if llm_metadata:
            print(f"   🤖 LLM Metadata: Project='{llm_metadata.get('project_title', 'N/A')[:30]}...', Vendor='{llm_metadata.get('vendor_name', 'N/A')}', Domain='{llm_metadata.get('domain_category', 'N/A')}'")
        return json_path
    
    def save_raw_text(self, raw_text: str, filename: str) -> str:
        """Save raw extracted text"""
        txt_filename = f"{filename}_raw_text.txt"
        txt_path = os.path.join(TEXT_DIR, txt_filename)
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(raw_text)
        
        print(f"💾 Saved raw text: {txt_path}")
        return txt_path
    
    def save_document_metadata(self, metadata: Dict, filename: str) -> str:
        """Save LLM-extracted document metadata separately"""
        metadata_filename = f"{filename}_llm_metadata.json"
        metadata_path = os.path.join(TEXT_DIR, metadata_filename)
        
        metadata_data = {
            "filename": filename,
            "extraction_method": "llm_azure_openai",
            "extracted_metadata": metadata,
            "created_at": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved LLM-extracted document metadata: {metadata_path}")
        return metadata_path
    
    def load_text_chunks(self, filename: str) -> List[Dict]:
        """Load enhanced text chunks with verbalization and LLM metadata from JSON file"""
        json_filename = f"{filename}_text_chunks.json"
        json_path = os.path.join(TEXT_DIR, json_filename)
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            chunks = data.get("chunks", [])
            
            # Ensure backward compatibility - add missing fields if needed
            for chunk in chunks:
                if "verbalized_content" not in chunk:
                    chunk["verbalized_content"] = chunk.get("content", "")
                # Ensure LLM metadata is present in chunk metadata
                if "metadata" in chunk and "llm_extracted_metadata" not in chunk["metadata"]:
                    chunk["metadata"]["llm_extracted_metadata"] = data.get("llm_extracted_metadata", {})
            
            print(f"📂 Loaded {len(chunks)} chunks with LLM metadata and verbalization support")
            if data.get("llm_extracted_metadata"):
                print(f"   🤖 Document metadata: {data['llm_extracted_metadata'].get('project_title', 'N/A')}")
            return chunks
            
        except Exception as e:
            print(f"❌ Error loading text chunks: {e}")
            return []
    
    def load_document_metadata(self, filename: str) -> Dict:
        """Load LLM-extracted document metadata"""
        metadata_filename = f"{filename}_llm_metadata.json"
        metadata_path = os.path.join(TEXT_DIR, metadata_filename)
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("extracted_metadata", {})
        except Exception as e:
            print(f"❌ Error loading document metadata: {e}")
            return {}
    
    def load_raw_text(self, filename: str) -> str:
        """Load raw text from file"""
        txt_filename = f"{filename}_raw_text.txt"
        txt_path = os.path.join(TEXT_DIR, txt_filename)
        
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Error loading raw text: {e}")
            return ""