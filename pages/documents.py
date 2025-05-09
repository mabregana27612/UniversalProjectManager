import streamlit as st
import datetime
import base64
import pandas as pd
from utils.data_management import get_project, get_project_documents, add_document

def show_documents():
    st.title("📄 Document Management")
    
    # Check if a project is selected
    if not st.session_state.current_project_id:
        st.warning("Please select a project from the sidebar first!")
        return
    
    # Get project and documents
    project_id = st.session_state.current_project_id
    project = get_project(project_id)
    documents = get_project_documents(project_id)
    
    if not project:
        st.error("Project not found!")
        return
    
    # Display documents image
    st.image("https://pixabay.com/get/g4f7346177f9b636f6f773478a715e351690a9bf2590e467dcdc6b21727d3f0e7330d2d66f00c6dad09df80f3879e6abf1d003a21f64a8d0b5cb3eb923c62ae73_1280.jpg", 
             caption="Project Documentation", use_container_width=True)
    
    # Project documents header
    st.subheader(f"Documents for: {project['name']}")
    
    # Create tabs for Document Library and Upload
    tab1, tab2 = st.tabs(["Document Library", "Upload Document"])
    
    with tab1:
        # Document library
        st.subheader("Document Library")
        
        if documents:
            # Document categories for filtering
            categories = sorted(list(set(doc.get('category', 'Uncategorized') for doc in documents)))
            selected_category = st.selectbox(
                "Filter by Category",
                ["All Categories"] + categories
            )
            
            # Filter documents by category
            filtered_docs = documents
            if selected_category != "All Categories":
                filtered_docs = [doc for doc in documents if doc.get('category', 'Uncategorized') == selected_category]
            
            # Create search box
            search_query = st.text_input("Search Documents", "")
            
            # Apply search filter if query exists
            if search_query:
                search_query = search_query.lower()
                filtered_docs = [
                    doc for doc in filtered_docs 
                    if search_query in doc['name'].lower() or 
                    search_query in doc.get('description', '').lower()
                ]
            
            # Display documents
            if filtered_docs:
                # Sort by upload date (newest first)
                sorted_docs = sorted(
                    filtered_docs,
                    key=lambda x: x.get('uploaded_at', ''),
                    reverse=True
                )
                
                # Display as cards
                for doc in sorted_docs:
                    with st.expander(f"{doc['name']} ({doc.get('category', 'Uncategorized')})"):
                        st.write(f"**Description:** {doc.get('description', 'N/A')}")
                        st.write(f"**Uploaded:** {doc.get('uploaded_at', 'N/A')}")
                        
                        # Display document content if available
                        if 'file_content' in doc and doc['file_content']:
                            # Create download link
                            file_content = base64.b64decode(doc['file_content'])
                            b64_content = base64.b64encode(file_content).decode()
                            
                            download_link = f'<a href="data:application/octet-stream;base64,{b64_content}" download="{doc["name"]}">Download File</a>'
                            st.markdown(download_link, unsafe_allow_html=True)
                            
                            # Preview for text files
                            try:
                                text_content = file_content.decode('utf-8')
                                with st.expander("Preview Content"):
                                    st.text(text_content)
                            except UnicodeDecodeError:
                                st.write("Binary file (preview not available)")
            else:
                st.info("No documents found with the current filter/search criteria.")
        else:
            st.info("No documents uploaded. Use the Upload Document tab to add documents.")
    
    with tab2:
        # Document upload form
        st.subheader("Upload New Document")
        
        doc_name = st.text_input("Document Name", "")
        doc_description = st.text_area("Document Description", "")
        
        # Document categories
        doc_categories = [
            "Requirements",
            "Design",
            "Plans",
            "Specifications",
            "Contracts",
            "Reports",
            "Meeting Minutes",
            "Change Requests",
            "Correspondence",
            "Tests & Quality",
            "User Documentation",
            "Other"
        ]
        
        doc_category = st.selectbox("Document Category", doc_categories)
        
        # File upload
        uploaded_file = st.file_uploader("Upload File", type=["txt", "pdf", "doc", "docx", "xls", "xlsx", "csv"])
        
        if st.button("Submit Document"):
            if not doc_name:
                st.error("Document name is required!")
            elif not uploaded_file:
                st.error("Please upload a file!")
            else:
                # Read file content
                file_content = uploaded_file.getvalue()
                # Convert to base64 for storage
                encoded_content = base64.b64encode(file_content).decode()
                
                document_data = {
                    'project_id': project_id,
                    'name': doc_name,
                    'description': doc_description,
                    'category': doc_category,
                    'file_path': uploaded_file.name,
                    'file_content': encoded_content
                }
                
                doc_id = add_document(document_data)
                if doc_id:
                    st.success(f"Document uploaded successfully with ID: {doc_id}")
                    # Clear form
                    st.rerun()
                else:
                    st.error("Failed to upload document!")
    
    # Document management best practices
    with st.expander("Document Management Best Practices"):
        st.markdown("""
        ### Document Management Guidelines
        
        1. **Clear Naming**: Use consistent and descriptive naming conventions.
        2. **Organized Categories**: Categorize documents appropriately for easy retrieval.
        3. **Detailed Descriptions**: Provide sufficient context in document descriptions.
        4. **Version Control**: Clearly indicate document versions when uploading updates.
        5. **Accessibility**: Ensure team members know where to find important documents.
        6. **Completeness**: Include all necessary documentation for each project phase.
        
        Good documentation practices improve project communication and provide valuable records for future reference.
        """)
