import uuid
from datetime import datetime
from typing import Dict
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from config import AZURE_AI_SEARCH_KEY, AZURE_AI_SEARCH_TIP_ENDPOINT, AZURE_AI_SEARCH_TIP_INDEX_NAME

class TIPUploader:
    """Upload TIP metadata to Azure AI Search index"""
    
    def __init__(self):
        print("📤 TIP Uploader initializing...")
        
        if not AZURE_AI_SEARCH_TIP_ENDPOINT or not AZURE_AI_SEARCH_KEY:
            raise ValueError("TIP Azure AI Search credentials not configured")
        
        self.search_client = SearchClient(
            endpoint=AZURE_AI_SEARCH_TIP_ENDPOINT,
            index_name=AZURE_AI_SEARCH_TIP_INDEX_NAME,
            credential=AzureKeyCredential(AZURE_AI_SEARCH_KEY)
        )
        
        print("✅ TIP Uploader initialized successfully")
        print(f"   📍 Endpoint: {AZURE_AI_SEARCH_TIP_ENDPOINT}")
        print(f"   📁 Index: {AZURE_AI_SEARCH_TIP_INDEX_NAME}")
    
    async def upload_tip_metadata(self, tip_metadata: Dict, filename: str) -> bool:
        """
        Upload TIP metadata to Azure AI Search index
        
        Args:
            tip_metadata: Dictionary containing 6 TIP metadata fields
            filename: Original filename (without extension)
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            print(f"📤 Uploading TIP metadata to Azure AI Search...")
            print(f"   📄 Document: {filename}")
            print(f"   🔑 Doc ID: {tip_metadata.get('doc_id', 'Not Found')}")
            
            # Create search document
            document = self._create_search_document(tip_metadata, filename)
            
            # Upload to search index
            result = self.search_client.upload_documents(documents=[document])
            
            # Check upload result
            upload_result = result[0]
            if upload_result.succeeded:
                print(f"✅ TIP metadata uploaded successfully")
                print(f"   🆔 Search ID: {document['id']}")
                print(f"   📋 Project: {tip_metadata.get('project_name', 'Not Specified')}")
                print(f"   🔧 Stations: {tip_metadata.get('stations_tip', 'Not Specified')[:50]}...")
                return True
            else:
                print(f"❌ Upload failed: {upload_result.error_message}")
                return False
                
        except Exception as e:
            print(f"❌ Error uploading TIP metadata: {e}")
            return False
    
    def _create_search_document(self, tip_metadata: Dict, filename: str) -> Dict:
        """Create search document from TIP metadata"""
        
        # Generate unique ID for the document
        doc_id = tip_metadata.get('doc_id', 'unknown')
        unique_id = f"{doc_id}_{uuid.uuid4().hex[:8]}"
        
        # Create search document
        document = {
            "id": unique_id,
            "doc_id": tip_metadata.get('doc_id', 'Not Found'),
            "project_name": tip_metadata.get('project_name', 'Not Specified'),
            "prepared_by": tip_metadata.get('prepared_by', 'Not Specified'),
            "stations_tip": tip_metadata.get('stations_tip', 'Not Specified'),
            "scope_of_work": tip_metadata.get('scope_of_work', 'Not Specified'),
            "qa_qc_info": tip_metadata.get('qa_qc_info', 'Not Specified'),
            "filename": filename,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "processing_method": "tip_azure_openai_extraction"
        }
        
        # Clean up any None values or very long content
        for key, value in document.items():
            if value is None:
                document[key] = 'Not Specified'
            elif isinstance(value, str) and len(value) > 10000:  # Prevent very large content
                document[key] = value[:10000] + "... [truncated]"
        
        return document
    
    def search_tip_documents(self, query: str, filters: str = None, top: int = 10) -> list:
        """
        Search TIP documents in the index
        
        Args:
            query: Search query string
            filters: OData filter string (optional)
            top: Number of results to return
            
        Returns:
            list: Search results
        """
        try:
            search_params = {
                "search_text": query,
                "top": top,
                "include_total_count": True
            }
            
            if filters:
                search_params["filter"] = filters
            
            results = self.search_client.search(**search_params)
            
            documents = []
            for result in results:
                documents.append(dict(result))
            
            print(f"🔍 Found {len(documents)} TIP documents for query: '{query}'")
            return documents
            
        except Exception as e:
            print(f"❌ Error searching TIP documents: {e}")
            return []
    
    def get_tip_document_by_doc_id(self, doc_id: str) -> Dict:
        """Get TIP document by document ID"""
        try:
            filter_query = f"doc_id eq '{doc_id}'"
            results = self.search_client.search(
                search_text="*",
                filter=filter_query,
                top=1
            )
            
            for result in results:
                print(f"✅ Found TIP document with doc_id: {doc_id}")
                return dict(result)
            
            print(f"❌ No TIP document found with doc_id: {doc_id}")
            return {}
            
        except Exception as e:
            print(f"❌ Error retrieving TIP document: {e}")
            return {}
    
    def get_all_tip_documents(self, top: int = 100) -> list:
        """Get all TIP documents in the index"""
        try:
            results = self.search_client.search(
                search_text="*",
                top=top,
                include_total_count=True
            )
            
            documents = []
            for result in results:
                documents.append(dict(result))
            
            print(f"📋 Retrieved {len(documents)} TIP documents from index")
            return documents
            
        except Exception as e:
            print(f"❌ Error retrieving all TIP documents: {e}")
            return []
    
    def delete_tip_document(self, doc_id: str) -> bool:
        """Delete TIP document by document ID"""
        try:
            # First find the document to get its search ID
            document = self.get_tip_document_by_doc_id(doc_id)
            
            if not document:
                print(f"❌ Cannot delete: TIP document with doc_id '{doc_id}' not found")
                return False
            
            search_id = document.get('id')
            if not search_id:
                print(f"❌ Cannot delete: No search ID found for doc_id '{doc_id}'")
                return False
            
            # Delete the document
            result = self.search_client.delete_documents(documents=[{"id": search_id}])
            
            delete_result = result[0]
            if delete_result.succeeded:
                print(f"✅ Deleted TIP document: {doc_id}")
                return True
            else:
                print(f"❌ Delete failed: {delete_result.error_message}")
                return False
                
        except Exception as e:
            print(f"❌ Error deleting TIP document: {e}")
            return False
    
    def get_upload_stats(self) -> Dict:
        """Get statistics about uploaded TIP documents"""
        try:
            # Get all documents to analyze
            all_docs = self.get_all_tip_documents()
            
            if not all_docs:
                return {"total_documents": 0}
            
            # Analyze statistics
            total_docs = len(all_docs)
            unique_projects = len(set(doc.get('project_name', '') for doc in all_docs))
            unique_preparers = len(set(doc.get('prepared_by', '') for doc in all_docs))
            docs_with_qa_qc = len([doc for doc in all_docs if doc.get('qa_qc_info', 'Not Specified') != 'Not Specified'])
            
            stats = {
                "total_documents": total_docs,
                "unique_projects": unique_projects,
                "unique_preparers": unique_preparers,
                "documents_with_qa_qc": docs_with_qa_qc,
                "qa_qc_percentage": round((docs_with_qa_qc / total_docs) * 100, 1) if total_docs > 0 else 0
            }
            
            print(f"📊 TIP Upload Statistics:")
            print(f"   📄 Total Documents: {stats['total_documents']}")
            print(f"   🏗️ Unique Projects: {stats['unique_projects']}")
            print(f"   👥 Unique Preparers: {stats['unique_preparers']}")
            print(f"   ✅ Documents with QA/QC: {stats['documents_with_qa_qc']} ({stats['qa_qc_percentage']}%)")
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting upload statistics: {e}")
            return {"error": str(e)}