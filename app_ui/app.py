"""
Ortho RAG Platform - UI Application
Streamlit-based user interface for the Ortho RAG Platform
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Ortho RAG Platform",
    page_icon="🧠",
    layout="wide"
)

# Main app
def main():
    st.title("🧠 Ortho RAG Platform")
    
    st.markdown("---")
    
    # Welcome section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Hello World! 👋")
        st.success("Streamlit UI container is running successfully!")
        
    with col2:
        st.markdown("""
        ### Status
        
        - ✅ **UI Service**: Active
        - 🚧 **Features**: Coming Soon
        """)
    
    st.markdown("---")
    
    # About section
    st.header("About This Platform")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        ### Discovery
        
        Search and discover YouTube videos based on your queries.
        """)
        
    with col2:
        st.warning("""
        ### Ingestion
        
        Process videos, extract transcripts, and generate embeddings.
        """)
        
    with col3:
        st.success("""
        ### RAG API
        
        Query your knowledge base with Retrieval Augmented Generation.
        """)
    
    st.markdown("---")
    
    # Footer
    st.footer("""
    ### Ortho RAG Platform UI
    
    Built with Streamlit | Version 0.1.0 (Hello World)
    """)

if __name__ == "__main__":
    main()
