import streamlit as st
import os
from langchain_ollama import ChatOllama
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain.embeddings import OllamaEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain

# Streamlit page configuration
st.set_page_config(
    page_title="Airtel Kenya Assistant",
    page_icon="📞",
    layout="wide"
)

# Docker Ollama configuration
OLLAMA_BASE_URL = "http://frontline-ollama-container-1:11434"

@st.cache_resource
def initialize_rag_system():
    """Initialize the RAG system with caching to avoid reloading on every interaction"""
    
    # Initialize the LLM
    llm = ChatOllama(
        model="qwen3:0.6b",
        temperature=0.1,  # Reduced for more consistent responses
        num_thread=8,
        num_ctx=2048,
        verbose=True
    )
    
    # Load Data 
    loader = PDFPlumberLoader("/Users/danielwanganga/Documents/GitHub/PROJECT_FRONTLINE/INTERN_PROJECT/frontline/knowledge_base/Rudishiwa Troubleshooting Steps (6).pdf")
    docs = loader.load()
    
    # Define the text splitter
    text_splitter = SemanticChunker(OllamaEmbeddings(model="qwen3:0.6b"))
    documents = text_splitter.split_documents(docs)
    
    # Create embedder
    embedder = OllamaEmbeddings(model="qwen3:0.6b")
    
    # Create VectorDB 
    vector = FAISS.from_documents(documents=documents, embedding=embedder)
    
    # Create retriever
    retriever = vector.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5}  # Increased for better context
    )
    
    # Enhanced prompt for better AI assistant behavior
    prompt = """
    You are a knowledgeable and helpful AI Assistant for Airtel Kenya, specializing in customer service and technical support.
    
    INSTRUCTIONS:
    1. Provide accurate, professional, and comprehensive answers based on the provided context
    2. Use a friendly but professional tone - you are an expert helping valued customers
    3. If the information isn't in your knowledge base, politely say "I don't have that specific information in my current knowledge base, but I'd be happy to help you with related questions or direct you to the appropriate Airtel Kenya support channels."
    4. Structure your responses clearly with bullet points or numbered steps when appropriate
    5. Always acknowledge the customer's question and provide actionable guidance
    6. Be proactive - if you see potential follow-up questions, briefly address them
    7. End responses with an offer to help further: "Is there anything else about Airtel Kenya services I can help you with?"
    
    Context: {context}
    
    Question: {question}
    
    Professional Response: """
    
    QA_CHAIN_PROMPT = PromptTemplate.from_template(prompt)
    
    # Define the Chain
    llm_chain = LLMChain(
        llm=llm,
        prompt=QA_CHAIN_PROMPT,
        verbose=True
    )
    
    document_prompt = PromptTemplate(
        input_variables=['page_content', "source"],
        template="Context:\ncontent:{page_content}\nsource:{source}"
    )
    
    combine_documents_chain = StuffDocumentsChain(
        llm_chain=llm_chain,
        document_variable_name="context",
        document_prompt=document_prompt,
    )
    
    qa = RetrievalQA(
        combine_documents_chain=combine_documents_chain,
        verbose=True,
        retriever=retriever,
        return_source_documents=True
    )
    
    return qa

# Streamlit UI
def main():
    st.title("🏠 Airtel Kenya Intelligence Assistant")
    st.markdown("Your expert guide to Airtel Kenya's services and support. Ask me anything!")
    
    # Initialize the RAG system
    try:
        with st.spinner("Initializing your AI Assistant..."):
            qa_system = initialize_rag_system()
        st.success("✅ Your AI Assistant is ready to help!")
    except Exception as e:
        st.error(f"❌ Error initializing system: {str(e)}")
        st.stop()
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Hello! I'm your Airtel Kenya AI Assistant. I'm here to help you with questions about our services, customer registration, technical support, and more. How can I assist you today?"
        })
    
    # Create container for chat messages
    chat_container = st.container()
    
    # Display chat messages
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant" and "sources" in message:
                    with st.expander("📄 View Sources"):
                        for i, source in enumerate(message["sources"], 1):
                            st.write(f"**Source {i}:**")
                            st.write(f"Content: {source.page_content[:300]}...")
                            if hasattr(source, 'metadata') and source.metadata:
                                st.write(f"Metadata: {source.metadata}")
    
    # Add some spacing before the input
    st.markdown("---")
    
    # Chat input at the bottom
    st.markdown("### 💬 Ask Your Question")
    
    # Create columns for better layout
    input_col1, input_col2 = st.columns([4, 1])
    
    with input_col1:
        user_input = st.text_input(
            "Type your question here...", 
            key="user_question",
            placeholder="e.g., How do I register a new customer? What are the broadband packages available?",
            label_visibility="collapsed"
        )
    
    with input_col2:
        send_button = st.button("Send", type="primary", use_container_width=True)
    
    # Process user input
    if send_button and user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Get assistant response
        with st.spinner("Processing your question..."):
            try:
                result = qa_system({"query": user_input})
                answer = result["result"]
                sources = result.get("source_documents", [])
                
                # Add assistant message to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer,
                    "sources": sources
                })
                
            except Exception as e:
                error_msg = f"I apologize, but I encountered a technical issue while processing your question. Please try rephrasing your question or contact Airtel Kenya support directly. Error: {str(e)}"
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": error_msg
                })
        
        # Clear the input and rerun to show new messages
        st.rerun()
    
    # Alternative: Also support Enter key submission
    if user_input and not send_button:
        # This handles the case where user presses Enter in the text input
        if st.session_state.get("last_input") != user_input:
            st.session_state["last_input"] = user_input
            
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Get assistant response
            with st.spinner("Processing your question..."):
                try:
                    result = qa_system({"query": user_input})
                    answer = result["result"]
                    sources = result.get("source_documents", [])
                    
                    # Add assistant message to chat history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer,
                        "sources": sources
                    })
                    
                except Exception as e:
                    error_msg = f"I apologize, but I encountered a technical issue while processing your question. Please try rephrasing your question or contact Airtel Kenya support directly. Error: {str(e)}"
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_msg
                    })
            
            st.rerun()
            
    

if __name__ == "__main__":
    main()