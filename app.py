import streamlit as st
import json
import traceback
from pathlib import Path
import os
import base64

# --- LangGraph Agent Imports ---
try:
    from agents.process_input import parse_user_input
    from nodes.next_tool_router import route_to_next_tool
    from nodes.tool_executor_node import execute_tools
    from states.overall_state import OverallState
    from langgraph.graph import StateGraph, START, END
except ImportError as e:
    st.error(f"Failed to import agent modules: {e}. Make sure all agent files are in the correct directories.")
    st.stop() # Stop the app if core components are missing

# --- 1. Define and Compile the LangGraph "Brain" ---
@st.cache_resource
def compile_graph():
    """Compile the LangGraph and cache it."""
    try:
        overallGraph = StateGraph(OverallState)
        overallGraph.add_node("parse_user_input", parse_user_input)
        overallGraph.add_node("tool_executor", execute_tools)
        overallGraph.add_edge(START, "parse_user_input")
        overallGraph.add_edge("parse_user_input", "tool_executor")
        overallGraph.add_conditional_edges("tool_executor", route_to_next_tool, ["tool_executor", END])
        graph = overallGraph.compile()
        return graph
    except Exception as e:
        st.error(f"Failed to compile LangGraph: {e}")
        traceback.print_exc()
        st.stop()

try:
    graph = compile_graph()
except Exception as e:
    st.error(f"Failed to compile LangGraph: {e}")
    st.stop()

# --- 2. Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_profile" not in st.session_state:
    st.session_state.user_profile = None
if "user_profile_created" not in st.session_state:
    st.session_state.user_profile_created = False
if "thread_id" not in st.session_state:
    st.session_state.thread_id = 1 # Use a consistent thread_id for the session

# --- 3. Settings File Handling ---
# This path now matches your project structure
SETTINGS_FILE_PATH = Path("Database/settings.json")

def load_settings():
    """Load settings from JSON file into session state."""
    try:
        if SETTINGS_FILE_PATH.exists():
            with open(SETTINGS_FILE_PATH, "r") as f:
                settings = json.load(f)
                st.session_state.user_profile_created = settings.get("user_profile_created", False)
                st.session_state.user_profile = settings.get("user_profile", None)
        else:
            # Create default settings if file doesn't exist
            st.warning(f"Settings file not found at {SETTINGS_FILE_PATH}. Creating a new one.")
            default_settings = {"user_profile_created": False, "user_profile": None}
            # Ensure the Database directory exists
            SETTINGS_FILE_PATH.parent.mkdir(exist_ok=True)
            with open(SETTINGS_FILE_PATH, "w") as f:
                json.dump(default_settings, f, indent=4)
            st.session_state.user_profile_created = False
            st.session_state.user_profile = None
            
    except Exception as e:
        st.error(f"Error loading settings: {e}")
        traceback.print_exc()

def save_settings():
    """Save current session state to JSON file."""
    try:
        settings = {
            "user_profile_created": st.session_state.user_profile_created,
            "user_profile": st.session_state.user_profile
        }
        # Ensure the Database directory exists
        SETTINGS_FILE_PATH.parent.mkdir(exist_ok=True)
        with open(SETTINGS_FILE_PATH, "w") as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error saving settings: {e}")
        traceback.print_exc()
        return False

# --- 4. Helper Function for PDF Download ---
def get_binary_file_downloader_html(bin_file, file_label='File'):
    """Generate a link to download the given binary file."""
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href

# --- 5. Main App Logic ---

# Load settings once at the start
if st.session_state.user_profile is None:
    load_settings()

# --- A: Profile Creation UI (if profile doesn't exist) ---
if not st.session_state.user_profile_created:
    
    st.title("Welcome to the Financial Advisor Bot! 📈")
    st.header("Create Your Profile")
    st.caption("We need some basic information to provide tailored advice.")

    with st.form(key="profile_form"):
        st.subheader("Personal Information")
        name = st.text_input("Enter your name", placeholder="e.g., Jane Doe")
        age = st.number_input("Enter your age", min_value=18, max_value=100, step=1, format="%d")
        
        st.subheader("Investment Profile")
        risk_tolerance = st.selectbox(
            "What is your risk tolerance?",
            ("low", "moderate", "high"),
            index=None,
            placeholder="Select a risk level"
        )
        
        investment_horizon = st.selectbox(
            "What is your investment horizon?",
            ("Short-term (1-3 years)", "Medium-term (3-7 years)", "Long-term (7+ years)"),
            index=None,
            placeholder="Select a time horizon"
        )
        
        submitted = st.form_submit_button("Save Profile")

    if submitted:
        if not all([name, age, risk_tolerance, investment_horizon]):
            st.error("Please fill out all fields.")
        else:
            st.session_state.user_profile = {
                "name": name,
                "age": str(age), 
                "risk_tolerance": risk_tolerance,
                "investment_horizon": investment_horizon
            }
            st.session_state.user_profile_created = True
            
            if save_settings():
                st.success("Profile created successfully! The chat will now load.")
                st.balloons()
                st.rerun() 
            else:
                st.session_state.user_profile = None
                st.session_state.user_profile_created = False
                st.error("Failed to save profile. Please try again.")

# --- B: Chat Interface (if profile exists) ---
else:
    st.title("Financial Advisor Chatbot 💬")
    st.caption(f"Hello, {st.session_state.user_profile.get('name', 'User')}! How can I help you today?")

    if "messages" not in st.session_state or not st.session_state.messages:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! How can I help you with your finances today?"}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message.get("is_download_link", False):
                st.markdown(message["content"], unsafe_allow_html=True)
            else:
                st.markdown(message["content"])

    if prompt := st.chat_input("What is your financial question?"):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # --- CHANGE 1: Define friendly names for your nodes ---
            NODE_FRIENDLY_NAMES = {
                "parse_user_input": "Parsing your request...",
                "tool_executor": "Running financial analysis...",
                "__end__": "Finalizing response..."
            }
            
            response = "" # Initialize response
            
            # --- CHANGE 2: Use st.status instead of st.spinner ---
            with st.status("Thinking...", expanded=False) as status:
                try:
                    # --- CHANGE 3: Use .stream() instead of .invoke() ---
                    events = graph.stream(
                        {"messages": [{"role": "user", "content": prompt}], "user_profile": st.session_state.user_profile},
                        config={"configurable": {"thread_id": st.session_state.thread_id}}
                    )
                    
                    final_result = None
                    for event in events:
                        # The event key is the name of the node that just ran
                        node_name = list(event.keys())[0] 
                        
                        # --- CHANGE 4: Update the status label ---
                        friendly_name = NODE_FRIENDLY_NAMES.get(node_name, f"Processing: {node_name}...")
                        status.update(label=friendly_name)
                        
                        # Store the state from the last node that ran
                        final_result = event.get(node_name) 

                    # --- Processing the final result (moved outside loop) ---
                    if final_result and "messages" in final_result and final_result["messages"]:
                        response = final_result["messages"][-1].content
                    else:
                        response = "I'm not sure how to respond to that."
                    
                    status.update(label="Done!", state="complete")

                except Exception as e:
                    status.update(label="An error occurred", state="error")
                    st.error(f"An error occurred: {e}") # This will show in the main app
                    traceback.print_exc()
                    response = "Sorry, an error occurred." # Set response to error
            
            # --- CHANGE 5: Render the final response *after* the status block ---
            if response.endswith(".pdf") and Path(response).exists():
                file_name = os.path.basename(response)
                download_link = get_binary_file_downloader_html(response, f"Your Report ({file_name})")
                response_content = f"I have generated your report. You can download it here:\n\n{download_link}"
                
                st.markdown(response_content, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": response_content, "is_download_link": True})
                    
                st.markdown(response_content, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": response_content, "is_download_link": True})
            
            else:
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

