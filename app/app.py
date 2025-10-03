import streamlit as st
import boto3
import os
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

# Page configuration
st.set_page_config(
    page_title="MIDAS Graph Explorer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with light color scheme
st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #F8F9FA 0%, #E8F4F8 100%);
    }
    
    /* Headers */
    h1 {
        color: #0E1B31;
        font-weight: 700;
    }
    
    h2, h3 {
        color: #0E1B31;
    }
    
    /* Welcome box */
    .welcome-box {
        background: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #7DD8D5;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    /* Style containers in the results section */
    section.main > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        background: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #67E5AD;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    /* Text elements */
    .highlight-text {
        color: #0E1B31;
        font-weight: 600;
        font-size: 18px;
    }
    
    .subtitle-text {
        color: #A8B2D1;
        font-size: 14px;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #7DD8D5 0%, #67E5AD 100%);
        color: #0E1B31;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: white;
    }
    
    /* Input fields */
    .stTextInput>div>div>input {
        border: 2px solid #7DD8D5;
        border-radius: 8px;
        background: white;
        color: #0E1B31;
        font-size: 16px;
        padding: 12px;
    }
    
    .stTextInput>label {
        color: #0E1B31 !important;
        font-weight: 600;
        font-size: 16px;
        margin-bottom: 8px;
    }
    
    .stButton>button:disabled {
        background: #cccccc;
        color: #666666;
        cursor: not-allowed;
    }
    
    /* Remove markdown formatting from output */
    .element-container {
        color: #0E1B31;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'mcp_client' not in st.session_state:
    st.session_state.mcp_client = None
if 'history' not in st.session_state:
    st.session_state.history = []
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False

def initialize_agent():
    """Initialize the Neptune MCP client and agent"""
    try:
        # Set AWS configuration
        profile_name = "default"
        os.environ["AWS_PROFILE"] = profile_name
        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
        boto3.setup_default_session(profile_name=profile_name)
        
        # Create MCP client
        mcp_client = MCPClient(lambda: stdio_client(StdioServerParameters(
            command="uvx",
            args=["awslabs.amazon-neptune-mcp-server@latest"],
            env={"NEPTUNE_ENDPOINT": "neptune-db://midas-dev-2510021802.cluster-c7j2zglv4rfb.us-east-1.neptune.amazonaws.com"},
        )))
        
        st.session_state.mcp_client = mcp_client
        return True
    except Exception as e:
        st.error(f"Failed to initialize: {str(e)}")
        return False

def query_agent(question):
    """Query the agent and return response"""
    try:
        with st.session_state.mcp_client:
            tools = st.session_state.mcp_client.list_tools_sync()
            agent = Agent(
                tools=tools,
                system_prompt="""You are a helpful assistant that explores biomedical knowledge graphs. 
                Always fetch the schema first to ensure correct labels and property names.
                Provide clear, concise answers without excessive markdown formatting."""
            )
            response = agent(question)
            return response
    except Exception as e:
        return f"Error: {str(e)}"

# Header
st.markdown('<h1 style="margin-bottom: 0px;">MIDAS</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-text" style="margin-top: 0px; font-size: 16px;">Ask questions about genes, diseases, and variants</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### About")
    st.markdown("**MIDAS** is Model Integration and Data Assembly System.")
    st.markdown("Biomedical knowledge graph with genes, diseases, and variants.")
    
    st.markdown("---")
    st.markdown("### Sample Questions")
    st.markdown("""
    - What's in the database?
    - Show me hub genes
    - Find cancer diseases
    - Node degree distribution
    - Tell me about gene BRCA1
    """)
    
    st.markdown("---")
    if st.button("Clear History", use_container_width=True):
        st.session_state.history = []
        st.rerun()

# Main content
st.markdown("")  # spacing

# Query input
question = st.text_input(
    "Your question:",
    placeholder="Ask anything about genes, diseases, or variants...",
    label_visibility="visible",
    key="question_input"
)

if st.button("Search", disabled=st.session_state.is_processing):
    if question:
        st.session_state.is_processing = True
        try:
            if st.session_state.mcp_client is None:
                with st.spinner("Initializing connection..."):
                    initialize_agent()
            
            with st.spinner("Analyzing..."):
                response = query_agent(question)
                st.session_state.history.append({
                    "question": question,
                    "response": response
                })
        finally:
            st.session_state.is_processing = False
            st.rerun()

# Display results
if st.session_state.history:
    st.markdown("---")
    st.markdown("### Results")
    
    # Show most recent result first
    for i, item in enumerate(reversed(st.session_state.history)):
        with st.container():
            # Question
            st.markdown(f'**Q: {item["question"]}**')
            st.markdown("")  # spacing
            
            # Response with markdown rendering
            response_text = str(item["response"])
            st.markdown(response_text)
        
        if i < len(st.session_state.history) - 1:
            st.markdown("")  # spacing between cards
else:
    st.markdown("""
    <div class="welcome-box">
        <h3 style="margin-top: 0;">Welcome!</h3>
        <p>Ask questions about the biomedical knowledge graph. Try "What's in the database?" or check sample questions in the sidebar.</p>
    </div>
    """, unsafe_allow_html=True)

