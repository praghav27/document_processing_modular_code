import os
import json
import pandas as pd
from config import TABLES_DIR, IMAGES_DIR, TEXT_DIR
from typing import List, Dict
from .text_storage import TextStorage
from .table_storage import TableStorage
from .image_storage import ImageStorage


class LocalStorage:
    """Main coordinator for all storage operations with analysis and reporting capabilities"""
    
    def __init__(self):
        self._ensure_directories()
        self.text_storage = TextStorage()
        self.table_storage = TableStorage()
        self.image_storage = ImageStorage()
    
    def _ensure_directories(self):
        """Create storage directories if they don't exist"""
        os.makedirs(TABLES_DIR, exist_ok=True)
        os.makedirs(IMAGES_DIR, exist_ok=True)
        os.makedirs(TEXT_DIR, exist_ok=True)
    
    # Delegate text operations to TextStorage
    def save_text_chunks(self, text_chunks: List[Dict], filename: str) -> str:
        return self.text_storage.save_text_chunks(text_chunks, filename)
    
    def save_raw_text(self, raw_text: str, filename: str) -> str:
        return self.text_storage.save_raw_text(raw_text, filename)
    
    def save_document_metadata(self, metadata: Dict, filename: str) -> str:
        return self.text_storage.save_document_metadata(metadata, filename)
    
    def load_text_chunks(self, filename: str) -> List[Dict]:
        return self.text_storage.load_text_chunks(filename)
    
    def load_document_metadata(self, filename: str) -> Dict:
        return self.text_storage.load_document_metadata(filename)
    
    def load_raw_text(self, filename: str) -> str:
        return self.text_storage.load_raw_text(filename)
    
    # Delegate table operations to TableStorage
    def save_table(self, df: pd.DataFrame, filename: str, table_index: int) -> str:
        return self.table_storage.save_table(df, filename, table_index)
    
    # Delegate image operations to ImageStorage
    def save_figure_image_bytes(self, image_bytes: bytes, filename: str, figure_index: int) -> str:
        return self.image_storage.save_figure_image_bytes(image_bytes, filename, figure_index)
    
    def save_figure_text(self, text_content: str, filename: str, figure_index: int) -> str:
        return self.image_storage.save_figure_text(text_content, filename, figure_index)
    
    # Analysis and reporting methods
    def save_extraction_summary(self, filename: str, summary_data: Dict) -> str:
        """Save extraction summary with all content types, verbalization, and LLM metadata info"""
        summary_filename = f"{filename}_extraction_summary.json"
        summary_path = os.path.join(TEXT_DIR, summary_filename)
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved extraction summary: {summary_path}")
        return summary_path
    
    def save_section_analysis(self, filename: str, sections_data: List[Dict]) -> str:
        """Save section analysis data"""
        sections_filename = f"{filename}_sections_analysis.json"
        sections_path = os.path.join(TEXT_DIR, sections_filename)
        
        analysis_data = {
            "filename": filename,
            "total_sections": len(sections_data),
            "processing_method": "azure_document_intelligence_with_llm_metadata_and_verbalization",
            "sections": sections_data
        }
        
        with open(sections_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved section analysis: {sections_path}")
        return sections_path
    
    def load_extraction_summary(self, filename: str) -> Dict:
        """Load extraction summary"""
        summary_filename = f"{filename}_extraction_summary.json"
        summary_path = os.path.join(TEXT_DIR, summary_filename)
        
        try:
            with open(summary_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading extraction summary: {e}")
            return {}
    
    def get_storage_summary(self, filename: str) -> Dict:
        """Get comprehensive summary of all stored files for a document with LLM metadata and verbalization info"""
        base_filename = os.path.splitext(filename)[0]
        
        summary = {
            "base_filename": base_filename,
            "files": {
                "text": [],
                "tables": [],
                "images": [],
                "analysis": []
            },
            "storage_stats": {
                "total_files": 0,
                "total_size_mb": 0
            },
            "verbalization_info": {
                "chunks_with_verbalization": 0,
                "verbalization_enabled": False
            },
            "llm_metadata_info": {
                "metadata_extracted": False,
                "extraction_method": "none",
                "document_metadata": {}
            }
        }
        
        # Check each directory for files
        directories = {
            "text": TEXT_DIR,
            "tables": TABLES_DIR,
            "images": IMAGES_DIR
        }
        
        for category, directory in directories.items():
            if os.path.exists(directory):
                for file in os.listdir(directory):
                    if file.startswith(base_filename):
                        file_path = os.path.join(directory, file)
                        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                        
                        file_info = {
                            "filename": file,
                            "path": file_path,
                            "size_mb": round(file_size, 2),
                            "type": self._get_file_type(file)
                        }
                        
                        # Categorize analysis files
                        if file.endswith(('_summary.json', '_analysis.json', '_sections_analysis.json', '_llm_metadata.json')):
                            summary["files"]["analysis"].append(file_info)
                        else:
                            summary["files"][category].append(file_info)
                        
                        summary["storage_stats"]["total_files"] += 1
                        summary["storage_stats"]["total_size_mb"] += file_size
        
        # Check for verbalization info
        chunks_data = self.load_text_chunks(base_filename)
        if chunks_data:
            verbalized_chunks = [c for c in chunks_data if c.get('verbalized_content') and c.get('verbalized_content') != c.get('content', '')]
            summary["verbalization_info"]["chunks_with_verbalization"] = len(verbalized_chunks)
            summary["verbalization_info"]["verbalization_enabled"] = len(verbalized_chunks) > 0
        
        # Check for LLM metadata info
        llm_metadata = self.load_document_metadata(base_filename)
        if llm_metadata:
            summary["llm_metadata_info"]["metadata_extracted"] = True
            summary["llm_metadata_info"]["extraction_method"] = "llm_azure_openai"
            summary["llm_metadata_info"]["document_metadata"] = llm_metadata
        
        summary["storage_stats"]["total_size_mb"] = round(summary["storage_stats"]["total_size_mb"], 2)
        
        return summary
    
    def create_comprehensive_report(self, filename: str) -> Dict:
        """Create a comprehensive report of all extracted content with LLM metadata and verbalization"""
        base_filename = os.path.splitext(filename)[0]
        
        report = {
            "document_name": filename,
            "processing_timestamp": "",
            "content_summary": {
                "text_chunks": 0,
                "table_chunks": 0,
                "image_chunks": 0,
                "tables": 0,
                "figures": 0,
                "sections": 0
            },
            "verbalization_summary": {
                "total_verbalized_chunks": 0,
                "verbalized_tables": 0,
                "verbalized_images": 0,
                "verbalization_enabled": False
            },
            "llm_metadata_summary": {
                "metadata_extracted": False,
                "extraction_method": "none",
                "document_metadata": {},
                "chunks_with_llm_metadata": 0
            },
            "file_locations": {
                "text_files": [],
                "table_files": [],
                "image_files": [],
                "analysis_files": []
            },
            "storage_info": self.get_storage_summary(filename)
        }
        
        # Load text chunks info
        chunks_data = self.load_text_chunks(base_filename)
        if chunks_data:
            # Count chunks by type
            text_chunks = [c for c in chunks_data if c.get('content_type') == 'text']
            table_chunks = [c for c in chunks_data if c.get('content_type') == 'table']
            image_chunks = [c for c in chunks_data if c.get('content_type') == 'image']
            
            report["content_summary"]["text_chunks"] = len(text_chunks)
            report["content_summary"]["table_chunks"] = len(table_chunks)
            report["content_summary"]["image_chunks"] = len(image_chunks)
            
            # Count verbalized chunks
            verbalized_tables = [c for c in table_chunks if c.get('verbalized_content') and c.get('verbalized_content') != c.get('content', '')]
            verbalized_images = [c for c in image_chunks if c.get('verbalized_content') and c.get('verbalized_content') != c.get('content', '')]
            
            report["verbalization_summary"]["verbalized_tables"] = len(verbalized_tables)
            report["verbalization_summary"]["verbalized_images"] = len(verbalized_images)
            report["verbalization_summary"]["total_verbalized_chunks"] = len(verbalized_tables) + len(verbalized_images)
            report["verbalization_summary"]["verbalization_enabled"] = len(verbalized_tables) > 0 or len(verbalized_images) > 0
            
            # Count chunks with LLM metadata
            chunks_with_llm = [c for c in chunks_data if c.get('metadata', {}).get('llm_extracted_metadata')]
            report["llm_metadata_summary"]["chunks_with_llm_metadata"] = len(chunks_with_llm)
            
            # Extract sections info
            sections = set()
            for chunk in chunks_data:
                if chunk.get("section_name"):
                    sections.add(chunk["section_name"])
            report["content_summary"]["sections"] = len(sections)
        
        # Load LLM metadata
        llm_metadata = self.load_document_metadata(base_filename)
        if llm_metadata:
            report["llm_metadata_summary"]["metadata_extracted"] = True
            report["llm_metadata_summary"]["extraction_method"] = "llm_azure_openai"
            report["llm_metadata_summary"]["document_metadata"] = llm_metadata
        
        # Count tables and figures from files
        storage_summary = self.get_storage_summary(filename)
        report["content_summary"]["tables"] = len([f for f in storage_summary["files"]["tables"] if f["type"] == "table_data"])
        report["content_summary"]["figures"] = len([f for f in storage_summary["files"]["images"] if f["type"] == "figure_image"])
        
        # File locations
        report["file_locations"]["text_files"] = [f["path"] for f in storage_summary["files"]["text"]]
        report["file_locations"]["table_files"] = [f["path"] for f in storage_summary["files"]["tables"]]
        report["file_locations"]["image_files"] = [f["path"] for f in storage_summary["files"]["images"]]
        report["file_locations"]["analysis_files"] = [f["path"] for f in storage_summary["files"]["analysis"]]
        
        return report
    
    def cleanup_files(self, filename: str) -> bool:
        """Remove all files associated with a document"""
        base_filename = os.path.splitext(filename)[0]
        removed_files = []
        
        directories = [TEXT_DIR, TABLES_DIR, IMAGES_DIR]
        
        for directory in directories:
            if os.path.exists(directory):
                for file in os.listdir(directory):
                    if file.startswith(base_filename):
                        file_path = os.path.join(directory, file)
                        try:
                            os.remove(file_path)
                            removed_files.append(file_path)
                        except Exception as e:
                            print(f"❌ Error removing file {file_path}: {e}")
        
        print(f"🗑️ Removed {len(removed_files)} files for {filename}")
        return len(removed_files) > 0
    
    def get_verbalization_stats(self, filename: str) -> Dict:
        """Get detailed verbalization statistics for a document"""
        base_filename = os.path.splitext(filename)[0]
        chunks_data = self.load_text_chunks(base_filename)
        
        stats = {
            "total_chunks": 0,
            "verbalized_chunks": 0,
            "chunk_types": {
                "text": {"total": 0, "verbalized": 0},
                "table": {"total": 0, "verbalized": 0},
                "image": {"total": 0, "verbalized": 0}
            },
            "verbalization_rate": 0.0,
            "avg_verbalization_length": 0,
            "verbalization_enabled": False
        }
        
        if chunks_data:
            stats["total_chunks"] = len(chunks_data)
            
            verbalized_lengths = []
            
            for chunk in chunks_data:
                content_type = chunk.get('content_type', 'text')
                stats["chunk_types"][content_type]["total"] += 1
                
                # Check if chunk is verbalized (different from original content)
                original = chunk.get('content', '')
                verbalized = chunk.get('verbalized_content', '')
                
                if verbalized and verbalized != original:
                    stats["verbalized_chunks"] += 1
                    stats["chunk_types"][content_type]["verbalized"] += 1
                    verbalized_lengths.append(len(verbalized))
            
            if stats["total_chunks"] > 0:
                stats["verbalization_rate"] = stats["verbalized_chunks"] / stats["total_chunks"]
            
            if verbalized_lengths:
                stats["avg_verbalization_length"] = sum(verbalized_lengths) / len(verbalized_lengths)
                stats["verbalization_enabled"] = True
        
        return stats
    
    def get_llm_metadata_stats(self, filename: str) -> Dict:
        """Get detailed LLM metadata statistics for a document"""
        base_filename = os.path.splitext(filename)[0]
        chunks_data = self.load_text_chunks(base_filename)
        llm_metadata = self.load_document_metadata(base_filename)
        
        stats = {
            "metadata_extracted": False,
            "extraction_method": "none",
            "document_metadata": {},
            "chunks_with_metadata": 0,
            "metadata_fields_populated": 0,
            "metadata_completeness": 0.0,
            "chunk_integration": {
                "text": {"total": 0, "with_metadata": 0},
                "table": {"total": 0, "with_metadata": 0},
                "image": {"total": 0, "with_metadata": 0}
            }
        }
        
        # Check document-level metadata
        if llm_metadata:
            stats["metadata_extracted"] = True
            stats["extraction_method"] = "llm_azure_openai"
            stats["document_metadata"] = llm_metadata
            
            # Count populated fields
            required_fields = ['project_title', 'client_name', 'vendor_name', 'submission_date', 'domain_category', 'service_category']
            populated_fields = sum(1 for field in required_fields if llm_metadata.get(field) not in [None, '', 'Not Specified', 'Other'])
            stats["metadata_fields_populated"] = populated_fields
            stats["metadata_completeness"] = populated_fields / len(required_fields) if required_fields else 0
        
        # Check chunk-level integration
        if chunks_data:
            for chunk in chunks_data:
                content_type = chunk.get('content_type', 'text')
                stats["chunk_integration"][content_type]["total"] += 1
                
                # Check if chunk has LLM metadata integrated
                if chunk.get('metadata', {}).get('llm_extracted_metadata'):
                    stats["chunks_with_metadata"] += 1
                    stats["chunk_integration"][content_type]["with_metadata"] += 1
        
        return stats
    
    def _get_file_type(self, filename: str) -> str:
        """Determine file type from filename"""
        if filename.endswith('.json'):
            if 'chunks' in filename:
                return 'text_chunks_with_llm_metadata'
            elif 'llm_metadata' in filename:
                return 'llm_extracted_metadata'
            elif 'summary' in filename:
                return 'extraction_summary'
            elif 'analysis' in filename:
                return 'section_analysis'
            else:
                return 'json_data'
        elif filename.endswith('.txt'):
            if 'raw_text' in filename:
                return 'raw_text'
            elif 'figure' in filename:
                return 'figure_text'
            else:
                return 'text_file'
        elif filename.endswith('.csv'):
            return 'table_data'
        elif filename.endswith(('.png', '.jpg', '.jpeg')):
            return 'figure_image'
        else:
            return 'unknown'