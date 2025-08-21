#!/usr/bin/env python3
"""
Setup script to create the TIP document index in Azure AI Search
Run this once before processing TIP documents
"""

from data_indexing.tip_indexer import TIPIndexer

def main():
    """Create TIP document index"""
    print("🚀 Setting up TIP Document Index...")
    print("=" * 60)
    
    try:
        # Initialize indexer
        indexer = TIPIndexer()
        
        # Create the index
        success = indexer.create_tip_index()
        
        if success:
            print("\n🎉 TIP Index Setup Complete!")
            print("=" * 60)
            print("✅ Index created successfully")
            print("🔍 Ready to process TIP documents")
            print("\nNext steps:")
            print("1. Run: streamlit run app.py")
            print("2. Select 'TIP Document Processing' mode")
            print("3. Upload TIP documents to extract metadata")
            print("4. Search the index manually using Azure portal")
        else:
            print("\n❌ TIP Index Setup Failed!")
            print("Check your Azure AI Search credentials and try again.")
            
    except Exception as e:
        print(f"\n❌ Error setting up TIP index: {e}")
        print("Please check your environment variables and Azure credentials.")

if __name__ == "__main__":
    main()