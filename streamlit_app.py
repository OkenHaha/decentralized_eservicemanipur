import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Gemma 4 Reasoning Arena", layout="centered")
st.title("🧠 Gemma 4 12B (QAT) Reasoning Chat")

# Point to your local Ollama server
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # Required by the library, but ignored by Ollama
)
#MODEL_NAME = "gemma3:4b"
MODEL_NAME = "hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL"

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful AI assistant with advanced reasoning capabilities. Think step-by-step before answering. Your response should no exceed more than 50 words"}
    ]

# Display past messages
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# User input
if user_prompt := st.chat_input("Ask Gemma 4 a complex logic or coding question..."):
    st.chat_message("user").markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    # Stream the response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Google's recommended sampling parameters for Gemma 4
        response_stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=st.session_state.messages,
            temperature=1.0,
            top_p=0.95,
            stream=True,
        )
        
        for chunk in response_stream:
            full_response += (chunk.choices[0].delta.content or "")
            message_placeholder.markdown(full_response + "▌")
            
        message_placeholder.markdown(full_response)
        
    st.session_state.messages.append({"role": "assistant", "content": full_response})
