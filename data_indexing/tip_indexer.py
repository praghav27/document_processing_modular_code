import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchFieldDataType,
    SemanticSearch, SemanticField, SemanticPrioritizedFields,
    ScoringProfile, TextWeights, SemanticConfiguration
)
from config import AZURE_AI_SEARCH_KEY, AZURE_AI_SEARCH_TIP_ENDPOINT, AZURE_AI_SEARCH_TIP_INDEX_NAME

class TIPIndexer:
    """Create and manage Azure AI Search index for TIP documents"""
    
    def __init__(self):
        print("🔍 TIP Indexer initializing...")
        print(f"   📍 Endpoint: {AZURE_AI_SEARCH_TIP_ENDPOINT}")
        print(f"   📁 Index Name: {AZURE_AI_SEARCH_TIP_INDEX_NAME}")
        
        if not AZURE_AI_SEARCH_TIP_ENDPOINT or not AZURE_AI_SEARCH_KEY:
            raise ValueError("TIP Azure AI Search credentials not configured in environment variables")
        
        self.credential = AzureKeyCredential(AZURE_AI_SEARCH_KEY)
        self.index_client = SearchIndexClient(
            endpoint=AZURE_AI_SEARCH_TIP_ENDPOINT, 
            credential=self.credential
        )
        self.index_name = AZURE_AI_SEARCH_TIP_INDEX_NAME
        
        print("✅ TIP Indexer initialized successfully")
    
    def create_tip_index(self):
        """Create the TIP document index with proper field configurations"""
        print(f"🔨 Creating TIP index: {self.index_name}")
        
        # Define index fields with proper attributes for sorting, filtering, faceting
        fields = [
            # Primary key
            SimpleField(
                name="id", 
                type=SearchFieldDataType.String, 
                key=True, 
                retrievable=True
            ),
            
            # Document ID - Filterable, Sortable, Facetable
            SimpleField(
                name="doc_id", 
                type=SearchFieldDataType.String, 
                filterable=True, 
                sortable=True, 
                facetable=True, 
                retrievable=True
            ),
            
            # Project Name - Searchable, Filterable, Sortable, Facetable
            SearchableField(
                name="project_name", 
                type=SearchFieldDataType.String, 
                filterable=True, 
                sortable=True, 
                facetable=True, 
                retrievable=True
            ),
            
            # Prepared By - Searchable, Filterable, Facetable
            SearchableField(
                name="prepared_by", 
                type=SearchFieldDataType.String, 
                filterable=True, 
                facetable=True, 
                retrievable=True
            ),
            
            # Stations/TIP - Searchable, Filterable, Facetable
            SearchableField(
                name="stations_tip", 
                type=SearchFieldDataType.String, 
                filterable=True, 
                facetable=True, 
                retrievable=True
            ),
            
            # Scope of Work - Searchable (main content field)
            SearchableField(
                name="scope_of_work", 
                type=SearchFieldDataType.String, 
                retrievable=True
            ),
            
            # QA/QC Info - Searchable, Filterable
            SearchableField(
                name="qa_qc_info", 
                type=SearchFieldDataType.String, 
                filterable=True, 
                retrievable=True
            ),
            
            # System fields
            SimpleField(
                name="filename", 
                type=SearchFieldDataType.String, 
                filterable=True, 
                retrievable=True
            ),
            
            SimpleField(
                name="created_at", 
                type=SearchFieldDataType.DateTimeOffset, 
                filterable=True, 
                sortable=True, 
                retrievable=True
            ),
            
            SimpleField(
                name="processing_method", 
                type=SearchFieldDataType.String, 
                filterable=True, 
                facetable=True, 
                retrievable=True
            )
        ]
        
        # Create semantic configuration for better search
        semantic_config = SemanticConfiguration(
            name="tip-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="project_name"),
                keywords_fields=[
                    SemanticField(field_name="doc_id"),
                    SemanticField(field_name="prepared_by"),
                    SemanticField(field_name="stations_tip")
                ],
                content_fields=[
                    SemanticField(field_name="scope_of_work"),
                    SemanticField(field_name="qa_qc_info")
                ]
            )
        )
        
        # Create scoring profile for relevance boosting
        scoring_profiles = [
            ScoringProfile(
                name="tipRelevanceProfile",
                text_weights=TextWeights(weights={
                    "project_name": 3.0,
                    "doc_id": 2.5,
                    "stations_tip": 2.0,
                    "scope_of_work": 1.5,
                    "prepared_by": 1.0,
                    "qa_qc_info": 1.0
                })
            )
        ]
        
        # Create semantic search configuration
        semantic_search = SemanticSearch(
            configurations=[semantic_config]
        )
        
        # Create the index
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            scoring_profiles=scoring_profiles,
            semantic_search=semantic_search
        )
        
        try:
            # Delete existing index if it exists
            try:
                self.index_client.delete_index(self.index_name)
                print(f"🗑️ Deleted existing index: {self.index_name}")
            except Exception:
                print(f"ℹ️ No existing index to delete: {self.index_name}")
            
            # Create new index
            self.index_client.create_index(index)
            print(f"✅ TIP index created successfully: {self.index_name}")
            print(f"   📋 Fields: {len(fields)} fields configured")
            print(f"   🔍 Semantic search: Enabled")
            print(f"   📊 Scoring profiles: {len(scoring_profiles)} configured")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating TIP index: {e}")
            return False
    
    def index_exists(self) -> bool:
        """Check if the TIP index exists"""
        try:
            self.index_client.get_index(self.index_name)
            return True
        except Exception:
            return False
    
    def delete_index(self) -> bool:
        """Delete the TIP index"""
        try:
            self.index_client.delete_index(self.index_name)
            print(f"🗑️ Deleted TIP index: {self.index_name}")
            return True
        except Exception as e:
            print(f"❌ Error deleting TIP index: {e}")
            return False
    
    def get_index_info(self) -> dict:
        """Get information about the TIP index"""
        try:
            index = self.index_client.get_index(self.index_name)
            return {
                "name": index.name,
                "field_count": len(index.fields),
                "fields": [field.name for field in index.fields],
                "semantic_search_enabled": index.semantic_search is not None,
                "scoring_profiles": len(index.scoring_profiles) if index.scoring_profiles else 0
            }
        except Exception as e:
            print(f"❌ Error getting index info: {e}")
            return {}

# Main execution for creating index
if __name__ == "__main__":
    indexer = TIPIndexer()
    success = indexer.create_tip_index()
    
    if success:
        print(f"\n🎉 TIP Index Setup Complete!")
        print(f"   📍 Endpoint: {AZURE_AI_SEARCH_TIP_ENDPOINT}")
        print(f"   📁 Index: {AZURE_AI_SEARCH_TIP_INDEX_NAME}")
        print(f"   🔍 Ready for TIP document metadata storage and search")
    else:
        print(f"\n❌ TIP Index Setup Failed!")