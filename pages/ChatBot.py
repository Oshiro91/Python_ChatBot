import streamlit as st
import requests
import json
import os
from pathlib import Path

# Configure the page
st.set_page_config(page_title="Ollama Chatbot", page_icon="🤖", layout="wide")

st.title("🤖 Ollama AI Chatbot")

# Sidebar for model configuration
st.sidebar.header("Configuration")

# Ollama server configuration
ollama_url = st.sidebar.text_input("Ollama Server URL", value="http://localhost:11434")

# Function to get available models
@st.cache_data
def get_available_models(url):
    try:
        response = requests.get(f"{url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [model["name"] for model in models]
        else:
            return []
    except Exception as e:
        st.sidebar.error(f"Error connecting to Ollama: {str(e)}")
        return []

# Get and display available models
available_models = get_available_models(ollama_url)

if available_models:
    selected_model = st.sidebar.selectbox("Select Model", available_models)
else:
    st.sidebar.error("No models found. Make sure Ollama is running and has models installed.")
    selected_model = st.sidebar.text_input("Model Name", value="llama2")

# Chat parameters
temperature = st.sidebar.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
max_tokens = st.sidebar.slider("Max Tokens", 100, 4000, 150, 50)

# File upload section
st.sidebar.markdown("---")
st.sidebar.header("📁 File Upload")

# Initialize uploaded files in session state
if "uploaded_files_content" not in st.session_state:
    st.session_state.uploaded_files_content = {}

# File uploader
uploaded_files = st.sidebar.file_uploader(
    "Upload files to guide chatbot responses",
    type=['txt', 'md', 'py', 'js', 'html', 'css', 'json', 'csv'],
    accept_multiple_files=True,
    help="Upload text files that the chatbot can reference for context"
)

# Process uploaded files
def process_uploaded_files(files):
    """Process uploaded files and extract text content"""
    files_content = {}
    
    for file in files:
        try:
            # Read file content
            content = file.read()
            
            # Decode based on file type
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            
            files_content[file.name] = {
                'content': content,
                'size': len(content),
                'type': file.type or 'text/plain'
            }
            
        except Exception as e:
            st.sidebar.error(f"Error reading {file.name}: {str(e)}")
    
    return files_content

# Update session state with uploaded files
if uploaded_files:
    st.session_state.uploaded_files_content = process_uploaded_files(uploaded_files)
    
    # Display uploaded files info
    st.sidebar.success(f"✅ {len(uploaded_files)} file(s) uploaded")
    
    with st.sidebar.expander("📋 Uploaded Files"):
        for filename, file_info in st.session_state.uploaded_files_content.items():
            st.write(f"**{filename}**")
            st.write(f"Size: {file_info['size']} characters")
            st.write(f"Type: {file_info['type']}")
            st.write("---")

# Clear uploaded files button
if st.sidebar.button("🗑️ Clear Uploaded Files"):
    st.session_state.uploaded_files_content = {}
    st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Function to create context from uploaded files
def create_file_context():
    """Create context string from uploaded files"""
    if not st.session_state.uploaded_files_content:
        return ""
    
    context = "\n=== UPLOADED FILES CONTEXT ===\n"
    
    for filename, file_info in st.session_state.uploaded_files_content.items():
        context += f"\n--- File: {filename} ---\n"
        context += file_info['content']
        context += f"\n--- End of {filename} ---\n"
    
    context += "\n=== END OF UPLOADED FILES CONTEXT ===\n\n"
    context += "Please use the above files as reference when answering questions. "
    context += "If the user asks about something related to the uploaded files, "
    context += "provide specific information from those files.\n\n"
    
    return context

# Function to call Ollama API
def call_ollama(prompt, model, temp=0.7):
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temp,
                "num_predict": max_tokens
            }
        }
        
        response = requests.post(
            f"{ollama_url}/api/generate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json().get("response", "No response received")
        else:
            return f"Error: {response.status_code} - {response.text}"
    
    except requests.exceptions.RequestException as e:
        return f"Connection error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("O que você gostaria de saber?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Create file context
            file_context = create_file_context()
            
            # Build context from chat history
            chat_context = ""
            for msg in st.session_state.messages[-5:]:  # Last 5 messages for context
                if msg["role"] == "user":
                    chat_context += f"Human: {msg['content']}\n"
                else:
                    chat_context += f"Assistant: {msg['content']}\n"
            
            # Combine file context, chat context, and current prompt
            full_prompt = f"{file_context}{chat_context}Human: {prompt}\nAssistant:"
            
            # Get response from Ollama
            response = call_ollama(full_prompt, selected_model, temperature)
            
            # Display response
            st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar controls
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.messages = []
    st.rerun()

# Display connection status
st.sidebar.markdown("---")
st.sidebar.markdown("### Status")
try:
    response = requests.get(f"{ollama_url}/api/tags", timeout=2)
    if response.status_code == 200:
        st.sidebar.success("✅ Connected to Ollama")
    else:
        st.sidebar.error("❌ Ollama connection failed")
except:
    st.sidebar.error("❌ Cannot reach Ollama server")

# # Display file context info in main area
# if st.session_state.uploaded_files_content:
#     with st.expander("📁 Current File Context", expanded=False):
#         st.info(f"The chatbot has access to {len(st.session_state.uploaded_files_content)} uploaded file(s) and will use them to provide more accurate answers.")
        
#         for filename, file_info in st.session_state.uploaded_files_content.items():
#             st.write(f"**{filename}** ({file_info['size']} chars)")
