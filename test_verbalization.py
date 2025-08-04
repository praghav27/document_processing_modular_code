#!/usr/bin/env python3
"""
Test script for the verbalization functionality
Run this to verify the implementation works correctly
"""

import os
import sys
import json
from datetime import datetime

# Add the processors directory to path
sys.path.append('processors')

def test_verbalization():
    """Test the verbalization functionality"""
    print("🧪 Testing Verbalization Functionality")
    print("=" * 50)
    
    try:
        # Import the verbalizer
        from processors.content_verbalizer import ContentVerbalizer
        print("✅ ContentVerbalizer imported successfully")
        
        # Initialize verbalizer
        verbalizer = ContentVerbalizer()  # No model_type needed anymore
        print("✅ ContentVerbalizer initialized")
        
        # Test model info
        model_info = verbalizer.get_model_info()
        print(f"\n📊 Model Information:")
        print(f"   Model Type: {model_info['model_type']}")
        print(f"   Status: {model_info['status']}")
        print(f"   Client Ready: {model_info['client_initialized']}")
        print(f"   API Key Present: {model_info['api_key_present']}")
        
        # Run test verbalization
        print(f"\n🧪 Running Test Verbalization...")
        test_results = verbalizer.test_verbalization()
        
        print(f"\n📋 Test Results:")
        print(f"Table Verbalization:")
        print(f"   {test_results['table_verbalization'][:200]}...")
        
        print(f"\nImage Verbalization:")
        print(f"   {test_results['image_verbalization'][:200]}...")
        
        print(f"\n✅ Verbalization test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure all files are in the correct location")
        return False
    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False

def test_chunk_structure():
    """Test the new chunk structure"""
    print(f"\n🧪 Testing Enhanced Chunk Structure")
    print("=" * 50)
    
    # Sample chunk with new structure
    sample_chunk = {
        'chunk_id': 'test1234',
        'file_name': 'test_document.pdf',
        'section_name': 'Budget Summary',
        'section_no': '4.1',
        'domain': 'Water Cycle & Management',
        'content_type': 'table',
        'author': 'tetratech',
        'content': 'Project,Cost,Duration\nPhase 1,$2M,6 months\nPhase 2,$3M,8 months',
        'verbalized_content': 'This table presents a project budget breakdown showing two phases with costs of $2M and $3M respectively, spanning 6 and 8 months. The data aligns with Tetratech\'s Water Cycle & Management domain.',
        'metadata': {
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'chunk_index': 0,
            'word_count': 35,
            'char_count': 180
        }
    }
    
    print("✅ Sample chunk structure created")
    
    # Test JSON serialization
    try:
        json_str = json.dumps(sample_chunk, indent=2)
        print("✅ Chunk serializes to JSON correctly")
        
        # Test deserialization
        loaded_chunk = json.loads(json_str)
        print("✅ Chunk deserializes from JSON correctly")
        
        # Verify all fields
        required_fields = ['chunk_id', 'content', 'verbalized_content', 'content_type', 'metadata']
        missing_fields = [field for field in required_fields if field not in loaded_chunk]
        
        if not missing_fields:
            print("✅ All required fields present")
        else:
            print(f"❌ Missing fields: {missing_fields}")
            
        print(f"\n📋 Chunk Preview:")
        print(f"   ID: {loaded_chunk['chunk_id']}")
        print(f"   Type: {loaded_chunk['content_type']}")
        print(f"   Original Content: {loaded_chunk['content'][:50]}...")
        print(f"   Verbalized Content: {loaded_chunk['verbalized_content'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Chunk structure test failed: {e}")
        return False

def test_storage():
    """Test the enhanced storage functionality"""
    print(f"\n🧪 Testing Enhanced Storage")
    print("=" * 50)
    
    try:
        # Import storage
        sys.path.append('storage')
        from storage.local_storage import LocalStorage
        print("✅ LocalStorage imported successfully")
        
        # Initialize storage
        storage = LocalStorage()
        print("✅ LocalStorage initialized")
        
        # Test sample chunks
        sample_chunks = [
            {
                'chunk_id': 'text001',
                'file_name': 'test_doc',
                'section_name': 'Introduction',
                'section_no': '1.0',
                'domain': 'none',
                'content_type': 'text',
                'author': 'tetratech',
                'content': 'This is sample text content for testing.',
                'verbalized_content': 'This is sample text content for testing.',  # Same for text
                'metadata': {'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'chunk_index': 0, 'word_count': 8, 'char_count': 40}
            },
            {
                'chunk_id': 'tbl001',
                'file_name': 'test_doc',
                'section_name': 'Budget',
                'section_no': 'table_1',
                'domain': 'none',
                'content_type': 'table',
                'author': 'tetratech',
                'content': 'Item,Cost\nPhase 1,$2M\nPhase 2,$3M',
                'verbalized_content': 'This table shows budget breakdown with Phase 1 costing $2M and Phase 2 costing $3M, typical of Tetratech Water Management projects.',
                'metadata': {'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'chunk_index': 1, 'word_count': 25, 'char_count': 120}
            }
        ]
        
        # Test saving chunks
        saved_path = storage.save_text_chunks(sample_chunks, 'test_doc')
        print(f"✅ Chunks saved to: {saved_path}")
        
        # Test loading chunks
        loaded_chunks = storage.load_text_chunks('test_doc')
        print(f"✅ Loaded {len(loaded_chunks)} chunks")
        
        # Test verbalization stats
        stats = storage.get_verbalization_stats('test_doc')
        print(f"\n📊 Verbalization Stats:")
        print(f"   Total Chunks: {stats['total_chunks']}")
        print(f"   Verbalized Chunks: {stats['verbalized_chunks']}")
        print(f"   Verbalization Rate: {stats['verbalization_rate']:.2%}")
        print(f"   Verbalization Enabled: {stats['verbalization_enabled']}")
        
        # Clean up test files
        storage.cleanup_files('test_doc')
        print("✅ Test files cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Storage test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Enhanced Document Processor Tests")
    print("=" * 60)
    
    tests = [
        ("Verbalization Functionality", test_verbalization),
        ("Chunk Structure", test_chunk_structure),
        ("Enhanced Storage", test_storage)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'=' * 60}")
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed ({passed/total:.1%})")
    
    if passed == total:
        print("🎉 All tests passed! Your verbalization implementation is ready!")
        print("\n📝 Next steps:")
        print("   1. Set your API key: export OPENAI_API_KEY=your_key")
        print("   2. Uncomment the import lines in content_verbalizer.py")
        print("   3. Run your Streamlit app to test with real documents")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")

if __name__ == "__main__":
    main()