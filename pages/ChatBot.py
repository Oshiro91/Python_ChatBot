import streamlit as st
import requests
import json

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
max_tokens = st.sidebar.slider("Max Tokens", 100, 4000, 1000, 100)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

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
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Build context from chat history
            context = ""
            for msg in st.session_state.messages[-5:]:  # Last 5 messages for context
                if msg["role"] == "user":
                    context += f"Human: {msg['content']}\n"
                else:
                    context += f"Assistant: {msg['content']}\n"
            
            # Add current prompt
            full_prompt = f"{context}Human: {prompt}\nAssistant:"
            
            # Get response from Ollama
            response = call_ollama(full_prompt, selected_model, temperature)
            
            # Display response
            st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar controls
st.sidebar.markdown("---")
if st.sidebar.button("Clear Chat History"):
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

