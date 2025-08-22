# import streamlit as st
# import os
# import pandas as pd
# import asyncio
# from main import document_processor
# from simple_tip_processor import SimpleTIPProcessor  # Import simple TIP processor
# from config import AZURE_DOC_INTELLIGENCE_ENDPOINT, AZURE_DOC_INTELLIGENCE_KEY

# # Page configuration
# st.set_page_config(
#     page_title="Enhanced Document Processor",
#     page_icon="📄",
#     layout="wide"
# )

# # Custom CSS
# st.markdown("""
# <style>
#     .main-header {
#         text-align: center;
#         color: #1f77b4;
#         margin-bottom: 30px;
#     }
#     .content-box {
#         background-color: #f8f9fa;
#         padding: 15px;
#         border-radius: 10px;
#         margin: 10px 0;
#         border-left: 4px solid #1976d2;
#     }
#     .enhanced-chunk-box {
#         background-color: #f0f8ff;
#         padding: 15px;
#         border-radius: 10px;
#         margin: 10px 0;
#         border-left: 4px solid #4169e1;
#     }
#     .table-box {
#         background-color: #e8f5e8;
#         padding: 15px;
#         border-radius: 10px;
#         margin: 10px 0;
#         border-left: 4px solid #4caf50;
#     }
#     .image-box {
#         background-color: #fff3e0;
#         padding: 15px;
#         border-radius: 10px;
#         margin: 10px 0;
#         border-left: 4px solid #ff9800;
#     }
#     .tip-metadata-box {
#         background-color: #e8f5e8;
#         padding: 15px;
#         border-radius: 10px;
#         margin: 10px 0;
#         border-left: 4px solid #4caf50;
#     }
#     .section-context {
#         background-color: #f3e5f5;
#         padding: 10px;
#         border-radius: 5px;
#         margin: 5px 0;
#         border-left: 3px solid #9c27b0;
#         font-size: 0.9em;
#     }
#     .metadata-box {
#         background-color: #e8f5e8;
#         padding: 8px;
#         border-radius: 5px;
#         margin: 5px 0;
#         font-size: 0.85em;
#     }
#     .status-message {
#         background-color: #e3f2fd;
#         padding: 10px;
#         border-radius: 5px;
#         margin: 5px 0;
#         border: 1px solid #1976d2;
#     }
#     .storage-info {
#         background-color: #f3e5f5;
#         padding: 10px;
#         border-radius: 5px;
#         margin: 5px 0;
#         border-left: 4px solid #9c27b0;
#     }
# </style>
# """, unsafe_allow_html=True)

# # Initialize session state
# def initialize_session_state():
#     if 'processed_data' not in st.session_state:
#         st.session_state.processed_data = None
#     if 'processing_status' not in st.session_state:
#         st.session_state.processing_status = []
#     if 'current_file' not in st.session_state:
#         st.session_state.current_file = None
#     if 'processing_mode' not in st.session_state:
#         st.session_state.processing_mode = "Enhanced RFP/RFI"

# initialize_session_state()

# # Header
# st.markdown('<h1 class="main-header">📄 Enhanced Document Processor</h1>', unsafe_allow_html=True)

# # Processing mode selection
# st.markdown("### 🔧 Select Processing Mode")
# processing_mode = st.selectbox(
#     "Choose processing type:",
#     ["Enhanced RFP/RFI Processing", "Simple TIP Document Processing"],
#     index=0 if st.session_state.processing_mode == "Enhanced RFP/RFI" else 1
# )

# # Update session state if mode changed
# if processing_mode != st.session_state.processing_mode:
#     st.session_state.processing_mode = processing_mode
#     st.session_state.processed_data = None
#     st.session_state.processing_status = []
#     st.session_state.current_file = None

# # Display mode-specific description
# if processing_mode == "Enhanced RFP/RFI Processing":
#     st.markdown('<p style="text-align: center; color: #666;">Upload RFP/RFI documents and extract text, tables, and images with advanced chunking and section association</p>', unsafe_allow_html=True)
# else:
#     st.markdown('<p style="text-align: center; color: #666;">Upload TIP documents to extract metadata (doc_id, project_name, prepared_by, stations_tip, scope_of_work, qa_qc_info) and store in Azure AI Search</p>', unsafe_allow_html=True)

# # Sidebar configuration
# with st.sidebar:
#     st.header("⚙️ Configuration")
    
#     # Azure status
#     if AZURE_DOC_INTELLIGENCE_ENDPOINT and AZURE_DOC_INTELLIGENCE_KEY:
#         st.success("✅ Azure Document Intelligence configured")
#         if processing_mode == "Enhanced RFP/RFI Processing":
#             st.info("🎯 Using Enhanced Layout Model for extraction")
#         else:
#             st.info("🎯 Using TIP Metadata Extraction with Azure OpenAI")
#     else:
#         st.error("❌ Azure credentials not configured")
#         st.info("Please set your Azure credentials in config.py or environment variables")
    
#     # Mode-specific statistics
#     if st.session_state.processed_data:
#         if processing_mode == "Enhanced RFP/RFI Processing":
#             stats = st.session_state.processed_data.get("stats", {})
#             st.subheader("📊 Document Stats")
#             st.metric("Text Chunks", stats.get("text_count", 0))
#             st.metric("Tables", stats.get("table_count", 0))
#             st.metric("Images", stats.get("image_count", 0))
#         else:
#             # TIP mode statistics
#             tip_metadata = st.session_state.processed_data.get("tip_metadata", {})
#             content_extracted = st.session_state.processed_data.get("content_extracted", {})
#             st.subheader("📊 TIP Document Stats")
#             st.metric("Metadata Fields", len(tip_metadata))
#             st.metric("Document ID", tip_metadata.get("doc_id", "Not Found"))
#             st.metric("Text Elements", content_extracted.get("text_elements", 0))
#             st.metric("Tables Found", content_extracted.get("tables", 0))
#             st.metric("Images Found", content_extracted.get("images", 0))
#             if tip_metadata.get("scope_of_work"):
#                 scope_words = len(tip_metadata["scope_of_work"].split())
#                 st.metric("Scope Word Count", scope_words)

# # Main content
# col1, col2 = st.columns([1, 2])

# with col1:
#     st.subheader("📤 Upload Document")
    
#     uploaded_file = st.file_uploader(
#         "Choose a file",
#         type=['pdf', 'docx', 'xlsx'],
#         help="Supported formats: PDF, DOCX, XLSX"
#     )
    
#     # Check if file was removed
#     if uploaded_file is None and st.session_state.current_file is not None:
#         st.session_state.processed_data = None
#         st.session_state.processing_status = []
#         st.session_state.current_file = None
#         st.info("File removed. Upload a new document to process.")
    
#     if uploaded_file:
#         # Check if new file
#         if st.session_state.current_file != uploaded_file.name:
#             st.session_state.processed_data = None
#             st.session_state.processing_status = []
#             st.session_state.current_file = uploaded_file.name
        
#         st.success(f"📁 File loaded: {uploaded_file.name}")
#         st.info(f"📊 Size: {uploaded_file.size / 1024:.1f} KB")
        
#         # Process button - different based on mode
#         if processing_mode == "Enhanced RFP/RFI Processing":
#             button_label = "🚀 Process Document with Enhanced Chunking"
#             button_help = "Process with RFP/RFI detection and chunking"
#         else:
#             button_label = "🚀 Process TIP Document & Extract Metadata"
#             button_help = "Extract TIP metadata and upload to Azure AI Search"
        
#         if st.button(button_label, type="primary", help=button_help):
#             if not AZURE_DOC_INTELLIGENCE_ENDPOINT or not AZURE_DOC_INTELLIGENCE_KEY:
#                 st.error("Please configure Azure credentials")
#             else:
#                 # Progress tracking
#                 status_container = st.empty()
                
#                 def update_progress(message):
#                     st.session_state.processing_status.append(message)
#                     with status_container.container():
#                         for status in st.session_state.processing_status[-3:]:
#                             st.markdown(f'<div class="status-message">{status}</div>', unsafe_allow_html=True)
                
#                 try:
#                     if processing_mode == "Enhanced RFP/RFI Processing":
#                         # Original RFP/RFI processing
#                         with st.spinner("Processing document with Enhanced Azure Document Intelligence..."):
#                             result = document_processor.process_document(uploaded_file, update_progress)
                        
#                         st.session_state.processed_data = result
#                         st.success("✅ Document processed successfully with enhanced chunking!")
                        
#                     else:
#                         # TIP processing
#                         with st.spinner("Processing TIP document with metadata extraction..."):
#                             tip_processor = SimpleTIPProcessor()
#                             result = asyncio.run(tip_processor.process_document(uploaded_file, update_progress))
                        
#                         st.session_state.processed_data = result
#                         if result.get("azure_search_uploaded"):
#                             st.success("✅ TIP document processed and uploaded to Azure AI Search!")
#                         else:
#                             st.warning("⚠️ TIP document processed but search upload failed")
                    
#                     st.balloons()
#                     st.rerun()
                    
#                 except Exception as e:
#                     st.error(f"❌ Error: {str(e)}")
#     else:
#         mode_text = "enhanced RFP/RFI processing" if processing_mode == "Enhanced RFP/RFI Processing" else "TIP metadata extraction"
#         st.info(f"Upload a document to get started with {mode_text}")

# with col2:
#     st.subheader("📋 Processing Status")
    
#     if st.session_state.processing_status:
#         for status in st.session_state.processing_status[-5:]:
#             st.markdown(f'<div class="status-message">{status}</div>', unsafe_allow_html=True)
#     else:
#         st.info("Upload and process a document to see status updates")

# # Display results based on processing mode
# if st.session_state.processed_data:
#     st.markdown("---")
    
#     if processing_mode == "Enhanced RFP/RFI Processing":
#         # Original enhanced content display
#         st.header("📋 Enhanced Extracted Content")
        
#         # Create tabs for RFP/RFI mode
#         tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Enhanced Text Chunks", "📊 Tables with Context", "🖼️ Images with Context", "📋 Combined Analysis", "💾 Storage Info"])
        
#         with tab1:
#             st.subheader("📝 Enhanced Text Chunks")
#             text_chunks = st.session_state.processed_data.get("text_chunks", [])
#             raw_text = st.session_state.processed_data.get("raw_text", "")
            
#             if text_chunks:
#                 st.info(f"Found {len(text_chunks)} enhanced text chunks with section detection")
                
#                 # Show raw text option
#                 if st.checkbox("Show Raw Text"):
#                     with st.expander("Raw Extracted Text"):
#                         st.text_area("Raw Text", raw_text, height=300)
                
#                 # Enhanced filtering options
#                 col_filter1, col_filter2 = st.columns(2)
                
#                 with col_filter1:
#                     # Filter by section
#                     all_sections = set()
#                     for chunk in text_chunks:
#                         section_name = chunk.get("section_name", "Unknown")
#                         if section_name:
#                             all_sections.add(section_name)
                    
#                     selected_sections = st.multiselect(
#                         "Filter by Section",
#                         sorted(all_sections),
#                         help="Select sections to display"
#                     )
                
#                 with col_filter2:
#                     # Filter by content type or size
#                     min_word_count = st.slider(
#                         "Minimum Word Count",
#                         min_value=0,
#                         max_value=max([chunk.get("metadata", {}).get("word_count", 0) for chunk in text_chunks]) if text_chunks else 100,
#                         value=0,
#                         help="Filter chunks by minimum word count"
#                     )
                
#                 # Apply filters
#                 filtered_chunks = text_chunks
#                 if selected_sections:
#                     filtered_chunks = [chunk for chunk in filtered_chunks if chunk.get("section_name") in selected_sections]
                
#                 filtered_chunks = [chunk for chunk in filtered_chunks if chunk.get("metadata", {}).get("word_count", 0) >= min_word_count]
                
#                 # Pagination for chunks
#                 chunks_per_page = st.selectbox("Chunks per page", [5, 10, 20], index=1)
#                 total_pages = (len(filtered_chunks) - 1) // chunks_per_page + 1 if filtered_chunks else 1
                
#                 if total_pages > 1:
#                     page = st.selectbox("Page", range(1, total_pages + 1))
#                     start_idx = (page - 1) * chunks_per_page
#                     end_idx = min(start_idx + chunks_per_page, len(filtered_chunks))
#                     chunks_to_show = filtered_chunks[start_idx:end_idx]
#                 else:
#                     chunks_to_show = filtered_chunks
#                     start_idx = 0
                
#                 # Display enhanced chunks
#                 for i, chunk in enumerate(chunks_to_show):
#                     chunk_id = chunk.get("chunk_id", f"chunk_{start_idx + i + 1}")
#                     section_name = chunk.get("section_name", "Unknown Section")
#                     section_no = chunk.get("section_no", "N/A")
#                     content = chunk.get("content", "")
#                     metadata = chunk.get("metadata", {})
                    
#                     with st.expander(f"Enhanced Chunk {start_idx + i + 1} - {section_name} ({len(content)} chars)"):
#                         # Main content
#                         st.markdown(f'''<div class="enhanced-chunk-box">
#                         <strong>📋 Chunk ID:</strong> {chunk_id}<br/>
#                         <strong>📁 File:</strong> {chunk.get("file_name", "N/A")}<br/>
#                         <strong>🎯 Section:</strong> {section_no} - {section_name}<br/>
#                         <strong>🏷️ Domain:</strong> {chunk.get("domain", "N/A")}<br/>
#                         <strong>📝 Content Type:</strong> {chunk.get("content_type", "text")}<br/>
#                         <strong>👤 Author:</strong> {chunk.get("author", "N/A")}<br/>
#                         <hr/>
#                         <strong>Content:</strong><br/>
#                         {content}
#                         </div>''', unsafe_allow_html=True)
                        
#                         # Metadata
#                         if metadata:
#                             st.markdown(f'''<div class="metadata-box">
#                             <strong>📊 Metadata:</strong><br/>
#                             • Word Count: {metadata.get('word_count', 0)}<br/>
#                             • Character Count: {metadata.get('char_count', 0)}<br/>
#                             • Created: {metadata.get('created_at', 'N/A')}<br/>
#                             • Chunk Index: {metadata.get('chunk_index', 'N/A')}
#                             </div>''', unsafe_allow_html=True)
#             else:
#                 st.warning("No enhanced text chunks created")
        
#         with tab2:
#             st.subheader("📊 Tables with Section Context")
#             tables = st.session_state.processed_data.get("tables", [])
            
#             if tables:
#                 st.info(f"Found {len(tables)} tables with section association")
                
#                 for i, table in enumerate(tables):
#                     with st.expander(f"Table {i + 1} - Page {table.get('page_number', 'Unknown')}"):
#                         # Section context
#                         section_info = table.get("section_info", {})
#                         if section_info:
#                             st.markdown(f'''<div class="section-context">
#                             <strong>🎯 Section Context:</strong><br/>
#                             • Role: {section_info.get('section_role', 'N/A')}<br/>
#                             • Content: {section_info.get('section_content', 'N/A')}<br/>
#                             • Page: {section_info.get('section_page', 'N/A')}<br/>
#                             • Distance: {section_info.get('distance_from_section', 'N/A')}
#                             </div>''', unsafe_allow_html=True)
                        
#                         col_a, col_b = st.columns([3, 1])
                        
#                         with col_a:
#                             if 'html' in table:
#                                 st.markdown("**Table Preview:**")
#                                 st.markdown(table['html'], unsafe_allow_html=True)
#                             else:
#                                 st.markdown("**Table Content:**")
#                                 st.text(table['content'])
                        
#                         with col_b:
#                             st.markdown("**Details:**")
#                             st.write(f"Page: {table.get('page_number', 'Unknown')}")
#                             st.write(f"Rows: {table.get('row_count', 'N/A')}")
#                             st.write(f"Columns: {table.get('column_count', 'N/A')}")
#                             st.write(f"Position: x={table.get('position', {}).get('x', 'N/A')}, y={table.get('position', {}).get('y', 'N/A')}")
                            
#                             # Download CSV
#                             if 'csv_path' in table and os.path.exists(table['csv_path']):
#                                 with open(table['csv_path'], 'rb') as f:
#                                     csv_data = f.read()
#                                 st.download_button(
#                                     label="📥 Download CSV",
#                                     data=csv_data,
#                                     file_name=os.path.basename(table['csv_path']),
#                                     mime="text/csv",
#                                     key=f"download_table_{i}"
#                                 )
#             else:
#                 st.warning("No tables extracted")
        
#         with tab3:
#             st.subheader("🖼️ Images with Section Context")
#             images = st.session_state.processed_data.get("images", [])
            
#             if images:
#                 st.info(f"Found {len(images)} images with section association")
                
#                 for i, image in enumerate(images):
#                     image_type = image.get('type', 'figure')
                    
#                     with st.expander(f"Image {i + 1} - Page {image.get('page_number', 'Unknown')} ({image_type})"):
#                         # Section context
#                         section_info = image.get("section_info", {})
#                         if section_info:
#                             st.markdown(f'''<div class="section-context">
#                             <strong>🎯 Section Context:</strong><br/>
#                             • Role: {section_info.get('section_role', 'N/A')}<br/>
#                             • Content: {section_info.get('section_content', 'N/A')}<br/>
#                             • Page: {section_info.get('section_page', 'N/A')}<br/>
#                             • Distance: {section_info.get('distance_from_section', 'N/A')}
#                             </div>''', unsafe_allow_html=True)
                        
#                         # Check if actual image is available
#                         if image.get('image_base64'):
#                             col_img, col_details = st.columns([2, 1])
                            
#                             with col_img:
#                                 # Display image
#                                 import base64
#                                 from PIL import Image as PILImage
#                                 import io
                                
#                                 try:
#                                     img_data = base64.b64decode(image['image_base64'])
#                                     img = PILImage.open(io.BytesIO(img_data))
#                                     st.image(img, caption=f"Image from Page {image.get('page_number')}", use_column_width=True)
                                    
#                                     # Download button
#                                     st.download_button(
#                                         label="📥 Download Image",
#                                         data=img_data,
#                                         file_name=f"image_{i+1}_page_{image.get('page_number', 'unknown')}.png",
#                                         mime="image/png",
#                                         key=f"download_img_{i}"
#                                     )
#                                 except Exception as e:
#                                     st.error(f"Error displaying image: {e}")
                            
#                             with col_details:
#                                 st.markdown("**Image Details:**")
#                                 st.write(f"Page: {image.get('page_number', 'Unknown')}")
#                                 st.write(f"Type: {image_type}")
#                                 st.write(f"Position: x={image.get('position', {}).get('x', 'N/A')}, y={image.get('position', {}).get('y', 'N/A')}")
#                                 if image.get('width') and image.get('height'):
#                                     st.write(f"Size: {image.get('width')} × {image.get('height')}")
#                                 if image.get('image_path'):
#                                     st.write(f"Saved: {os.path.basename(image.get('image_path'))}")
                        
#                         # Show text content from image
#                         if image.get('content') and image.get('content') != f"Figure from page {image.get('page_number')}":
#                             st.markdown("**Text Content from Image:**")
#                             st.markdown(f'<div class="image-box">{image.get("content")}</div>', unsafe_allow_html=True)
                        
#                         # If no image but has text content
#                         if not image.get('image_base64') and image.get('content'):
#                             st.markdown("**Image Content (Text Only):**")
#                             content = image.get("content", "No text content")
#                             st.markdown(f'<div class="image-box">{content}</div>', unsafe_allow_html=True)
#                             st.info("💡 This is text content from a figure/diagram detected by Azure DI.")
#             else:
#                 st.warning("No images extracted")
        
#         with tab4:
#             st.subheader("📋 Combined Analysis")
            
#             # Enhanced statistics
#             text_chunks = st.session_state.processed_data.get("text_chunks", [])
#             tables = st.session_state.processed_data.get("tables", [])
#             images = st.session_state.processed_data.get("images", [])
            
#             # Overall statistics
#             col1, col2, col3, col4 = st.columns(4)
            
#             with col1:
#                 st.metric("📝 Text Chunks", len(text_chunks))
#             with col2:
#                 st.metric("📊 Tables", len(tables))
#             with col3:
#                 st.metric("🖼️ Images", len(images))
#             with col4:
#                 total_elements = len(text_chunks) + len(tables) + len(images)
#                 st.metric("📋 Total Elements", total_elements)
            
#             # Processing Summary
#             st.subheader("⚙️ Processing Summary")
            
#             processing_method = st.session_state.processed_data.get("processing_method", "enhanced_azure_document_intelligence")
#             file_extension = st.session_state.processed_data.get("file_extension", "unknown")
            
#             st.markdown(f'''<div class="content-box">
#             <strong>🔧 Processing Method:</strong> {processing_method}<br/>
#             <strong>📁 File Extension:</strong> {file_extension}<br/>
#             <strong>📝 Enhanced Text Chunks:</strong> {len(text_chunks)}<br/>
#             <strong>📊 Tables with Context:</strong> {len(tables)}<br/>
#             <strong>🖼️ Images with Context:</strong> {len(images)}<br/>
#             <strong>📋 Total Content Elements:</strong> {total_elements}
#             </div>''', unsafe_allow_html=True)
        
#         with tab5:
#             st.subheader("💾 Enhanced Storage Information")
            
#             # Display file paths and storage info
#             filename = st.session_state.processed_data.get("filename", "unknown")
#             base_filename = os.path.splitext(filename)[0]
            
#             st.markdown("**Files saved to enhanced local storage:**")
            
#             # Text files
#             st.markdown("**📝 Text Files:**")
#             text_chunks_path = f"extracted_content/text/{base_filename}_text_chunks.json"
#             raw_text_path = f"extracted_content/text/{base_filename}_raw_text.txt"
            
#             col1, col2 = st.columns(2)
#             with col1:
#                 if os.path.exists(text_chunks_path):
#                     st.success(f"✅ Enhanced text chunks: {text_chunks_path}")
#                     with open(text_chunks_path, 'rb') as f:
#                         st.download_button(
#                             "📥 Download Enhanced Text Chunks (JSON)",
#                             data=f.read(),
#                             file_name=f"{base_filename}_enhanced_text_chunks.json",
#                             mime="application/json"
#                         )
#                 else:
#                     st.info("No enhanced text chunks file")
            
#             with col2:
#                 if os.path.exists(raw_text_path):
#                     st.success(f"✅ Raw text: {raw_text_path}")
#                     with open(raw_text_path, 'rb') as f:
#                         st.download_button(
#                             "📥 Download Raw Text",
#                             data=f.read(),
#                             file_name=f"{base_filename}_raw_text.txt",
#                             mime="text/plain"
#                         )
#                 else:
#                     st.info("No raw text file")
    
#     else:
#         # TIP MODE DISPLAY
#         st.header("📋 TIP Document Metadata")
        
#         # Create tabs for TIP mode
#         tab1, tab2, tab3 = st.tabs(["📝 Extracted Metadata", "🔍 Search Index Info", "💾 Storage Info"])
        
#         with tab1:
#             st.subheader("📝 TIP Metadata Fields")
#             tip_metadata = st.session_state.processed_data.get("tip_metadata", {})
            
#             if tip_metadata:
#                 st.info(f"Successfully extracted {len(tip_metadata)} metadata fields using TIP-specific prompts")
                
#                 # Display each field in a styled box
#                 for field, value in tip_metadata.items():
#                     if field == "scope_of_work":
#                         # Special handling for scope of work
#                         with st.expander(f"📋 {field.replace('_', ' ').title()} ({len(value.split())} words)"):
#                             st.markdown(f'''<div class="tip-metadata-box">
#                             <strong>Scope of Work (300 words technical summary):</strong><br/>
#                             {value}
#                             </div>''', unsafe_allow_html=True)
#                     elif field == "stations_tip":
#                         # Special handling for stations/TIP
#                         with st.expander(f"📋 {field.replace('_', ' ').title()}"):
#                             st.markdown(f'''<div class="tip-metadata-box">
#                             <strong>Stations/TIP (aux, ele, eqp, etc.):</strong><br/>
#                             {value}
#                             </div>''', unsafe_allow_html=True)
#                     else:
#                         st.markdown(f'''<div class="tip-metadata-box">
#                         <strong>📋 {field.replace('_', ' ').title()}:</strong> {value}
#                         </div>''', unsafe_allow_html=True)
                
#                 # Download metadata as JSON
#                 import json
#                 metadata_json = json.dumps(tip_metadata, indent=2, ensure_ascii=False)
#                 st.download_button(
#                     label="📥 Download TIP Metadata (JSON)",
#                     data=metadata_json,
#                     file_name=f"{os.path.splitext(st.session_state.current_file)[0]}_tip_metadata.json",
#                     mime="application/json"
#                 )
#             else:
#                 st.warning("No TIP metadata extracted")
        
#         with tab2:
#             st.subheader("🔍 Azure AI Search Index Status")
            
#             upload_success = st.session_state.processed_data.get("azure_search_uploaded", False)
#             tip_metadata = st.session_state.processed_data.get("tip_metadata", {})
            
#             if upload_success:
#                 st.success("✅ TIP metadata successfully uploaded to Azure AI Search")
                
#                 # Display search index information
#                 # st.markdown(f'''<div class="content-box">
#                 # <strong>📊 Search Index Details:</strong><br/>
#                 # • Index Name: tip_document_index<br/>
#                 # • Document ID: {tip_metadata.get('doc_id', 'Not Found')}<br/>
#                 # • Project Name: {tip_metadata.get('project_name', 'Not Specified')}<br/>
#                 # • Upload Status: ✅ Success<br/>
#                 # • Search Available: Yes<br/>
#                 # • Search Endpoint: https://ttdevopscacdevsrch-rfprfi.search.windows.net<br/>
#                 # • Fields: doc_id (filterable, searchable), project_name (searchable, filterable, facetable), prepared_by (searchable, filterable, facetable), stations_tip (searchable, filterable, facetable), scope_of_work (searchable), qa_qc_info (search


import streamlit as st
import os
import pandas as pd
import asyncio
from simple_tip_processor import SimpleTIPProcessor  # Import simple TIP processor
from config import AZURE_DOC_INTELLIGENCE_ENDPOINT, AZURE_DOC_INTELLIGENCE_KEY

# Page configuration
st.set_page_config(
    page_title="TIP Document Processor",
    page_icon="📄",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 30px;
    }
    .tip-metadata-box {
        background-color: #e8f5e8;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #4caf50;
    }
    .status-message {
        background-color: #e3f2fd;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border: 1px solid #1976d2;
    }
    .storage-info {
        background-color: #f3e5f5;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 4px solid #9c27b0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = []
    if 'current_file' not in st.session_state:
        st.session_state.current_file = None

initialize_session_state()

# Header
st.markdown('<h1 class="main-header">📄 TIP Document Processor</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666;">Upload TIP documents to extract metadata (doc_id, project_name, prepared_by, stations_tip, scope_of_work, qa_qc_info) and store in Azure AI Search</p>', unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Azure status
    if AZURE_DOC_INTELLIGENCE_ENDPOINT and AZURE_DOC_INTELLIGENCE_KEY:
        st.success("✅ Azure Document Intelligence configured")
        st.info("🎯 Using TIP Metadata Extraction with Azure OpenAI")
    else:
        st.error("❌ Azure credentials not configured")
        st.info("Please set your Azure credentials in config.py or environment variables")
    
    # TIP mode statistics
    if st.session_state.processed_data:
        tip_metadata = st.session_state.processed_data.get("tip_metadata", {})
        content_extracted = st.session_state.processed_data.get("content_extracted", {})
        st.subheader("📊 TIP Document Stats")
        st.metric("Metadata Fields", len(tip_metadata))
        st.metric("Document ID", tip_metadata.get("doc_id", "Not Found"))
        st.metric("Text Elements", content_extracted.get("text_elements", 0))
        st.metric("Tables Found", content_extracted.get("tables", 0))
        st.metric("Images Found", content_extracted.get("images", 0))
        if tip_metadata.get("scope_of_work"):
            scope_words = len(tip_metadata["scope_of_work"].split())
            st.metric("Scope Word Count", scope_words)

# Main content
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📤 Upload TIP Document")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'docx', 'xlsx'],
        help="Supported formats: PDF, DOCX, XLSX"
    )
    
    # Check if file was removed
    if uploaded_file is None and st.session_state.current_file is not None:
        st.session_state.processed_data = None
        st.session_state.processing_status = []
        st.session_state.current_file = None
        st.info("File removed. Upload a new document to process.")
    
    if uploaded_file:
        # Check if new file
        if st.session_state.current_file != uploaded_file.name:
            st.session_state.processed_data = None
            st.session_state.processing_status = []
            st.session_state.current_file = uploaded_file.name
        
        st.success(f"📁 File loaded: {uploaded_file.name}")
        st.info(f"📊 Size: {uploaded_file.size / 1024:.1f} KB")
        
        # Process button
        if st.button("🚀 Process TIP Document & Extract Metadata", type="primary", help="Extract TIP metadata and upload to Azure AI Search"):
            if not AZURE_DOC_INTELLIGENCE_ENDPOINT or not AZURE_DOC_INTELLIGENCE_KEY:
                st.error("Please configure Azure credentials")
            else:
                # Progress tracking
                status_container = st.empty()
                
                def update_progress(message):
                    st.session_state.processing_status.append(message)
                    with status_container.container():
                        for status in st.session_state.processing_status[-3:]:
                            st.markdown(f'<div class="status-message">{status}</div>', unsafe_allow_html=True)
                
                try:
                    # TIP processing
                    with st.spinner("Processing TIP document with metadata extraction..."):
                        tip_processor = SimpleTIPProcessor()
                        result = asyncio.run(tip_processor.process_document(uploaded_file, update_progress))
                    
                    st.session_state.processed_data = result
                    if result.get("azure_search_uploaded"):
                        st.success("✅ TIP document processed and uploaded to Azure AI Search!")
                    else:
                        st.warning("⚠️ TIP document processed but search upload failed")
                
                    st.balloons()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    else:
        st.info("Upload a TIP document to get started with metadata extraction")

with col2:
    st.subheader("📋 Processing Status")
    
    if st.session_state.processing_status:
        for status in st.session_state.processing_status[-5:]:
            st.markdown(f'<div class="status-message">{status}</div>', unsafe_allow_html=True)
    else:
        st.info("Upload and process a document to see status updates")

# Display results for TIP processing
if st.session_state.processed_data:
    st.markdown("---")
    
    st.header("📋 TIP Document Metadata")
    
    # Create tabs for TIP mode
    tab1, tab2, tab3 = st.tabs(["📝 Extracted Metadata", "🔍 Search Index Info", "💾 Storage Info"])
    
    with tab1:
        st.subheader("📝 TIP Metadata Fields")
        tip_metadata = st.session_state.processed_data.get("tip_metadata", {})
        
        if tip_metadata:
            st.info(f"Successfully extracted {len(tip_metadata)} metadata fields using TIP-specific prompts")
            
            # Display each field in a styled box
            for field, value in tip_metadata.items():
                if field == "scope_of_work":
                    # Special handling for scope of work
                    with st.expander(f"📋 {field.replace('_', ' ').title()} ({len(value.split())} words)"):
                        st.markdown(f'''<div class="tip-metadata-box">
                        <strong>Scope of Work (300 words technical summary):</strong><br/>
                        {value}
                        </div>''', unsafe_allow_html=True)
                elif field == "stations_tip":
                    # Special handling for stations/TIP
                    with st.expander(f"📋 {field.replace('_', ' ').title()}"):
                        st.markdown(f'''<div class="tip-metadata-box">
                        <strong>Stations/TIP (aux, ele, eqp, etc.):</strong><br/>
                        {value}
                        </div>''', unsafe_allow_html=True)
                else:
                    st.markdown(f'''<div class="tip-metadata-box">
                    <strong>📋 {field.replace('_', ' ').title()}:</strong> {value}
                    </div>''', unsafe_allow_html=True)
            
            # Download metadata as JSON
            import json
            metadata_json = json.dumps(tip_metadata, indent=2, ensure_ascii=False)
            st.download_button(
                label="📥 Download TIP Metadata (JSON)",
                data=metadata_json,
                file_name=f"{os.path.splitext(st.session_state.current_file)[0]}_tip_metadata.json",
                mime="application/json"
            )
        else:
            st.warning("No TIP metadata extracted")
    
    with tab2:
        st.subheader("🔍 Azure AI Search Index Status")
        
        upload_success = st.session_state.processed_data.get("azure_search_uploaded", False)
        tip_metadata = st.session_state.processed_data.get("tip_metadata", {})
        
        if upload_success:
            st.success("✅ TIP metadata successfully uploaded to Azure AI Search")
            
            # Display search index information
            st.markdown(f'''<div class="storage-info">
            <strong>📊 Search Index Details:</strong><br/>
            • Index Name: tip_document_index<br/>
            • Document ID: {tip_metadata.get('doc_id', 'Not Found')}<br/>
            • Project Name: {tip_metadata.get('project_name', 'Not Specified')}<br/>
            • Upload Status: ✅ Success<br/>
            • Search Available: Yes<br/>
            • Search Endpoint: https://ttdevopscacdevsrch-rfprfi.search.windows.net<br/>
            • Fields: doc_id (filterable, searchable), project_name (searchable, filterable, facetable), prepared_by (searchable, filterable, facetable), stations_tip (searchable, filterable, facetable), scope_of_work (searchable), qa_qc_info (searchable, filterable)
            </div>''', unsafe_allow_html=True)
        else:
            st.error("❌ TIP metadata upload to Azure AI Search failed")
            st.info("The metadata was extracted but could not be uploaded to the search index. Check your Azure AI Search configuration.")
    
    with tab3:
        st.subheader("💾 Local Storage Information")
        
        # Display file paths and storage info
        filename = st.session_state.processed_data.get("filename", "unknown")
        base_filename = os.path.splitext(filename)[0]
        local_path = st.session_state.processed_data.get("local_storage_path", "")
        
        st.markdown("**Files saved to local storage:**")
        
        if local_path and os.path.exists(local_path):
            st.success(f"✅ TIP metadata: {local_path}")
            with open(local_path, 'rb') as f:
                st.download_button(
                    "📥 Download Local TIP Metadata (JSON)",
                    data=f.read(),
                    file_name=f"{base_filename}_tip_metadata.json",
                    mime="application/json"
                )
        else:
            st.warning("❌ Local storage file not found")
        
        # Show extraction summary
        content_extracted = st.session_state.processed_data.get("content_extracted", {})
        st.markdown(f'''<div class="storage-info">
        <strong>📊 Content Extraction Summary:</strong><br/>
        • Text Elements: {content_extracted.get('text_elements', 0)}<br/>
        • Tables: {content_extracted.get('tables', 0)}<br/>
        • Images: {content_extracted.get('images', 0)}<br/>
        • Processing Method: {st.session_state.processed_data.get('processing_method', 'Unknown')}<br/>
        • Local Storage: ✅ JSON metadata saved<br/>
        • Azure Search: {'✅ Uploaded' if upload_success else '❌ Failed'}
        </div>''', unsafe_allow_html=True)