import os
import openai
import pinecone
import streamlit as st
from pinecone import Pinecone
from openai import OpenAIError
from dotenv import load_dotenv
from prompt import purpose, get_started
from langchain.prompts import PromptTemplate

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="EarthBot - Your Eco Guide",
    page_icon="🌍",
    layout="wide"
)

# Custom CSS to enhance the UI
st.markdown("""
    <style>
        /* Vibrant Gradient Background */
        body {
            background: linear-gradient(135deg, #E3F2FD, #A5D6A7);
            font-family: 'Poppins', sans-serif;
        }

        /* Animated Title */
        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(-20px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        
        .stTitle {
            color: #1B5E20;
            font-size: 2.8rem !important;
            text-align: center;
            font-weight: 600;
            padding-bottom: 2rem;
            animation: fadeIn 1.5s ease-in-out;
            text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.2);
        }

        /* Chat Container */
        .stChatMessage {
            background-color: #F1F8E9;
            border-radius: 20px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease-in-out;
        }

        .stChatMessage:hover {
            transform: scale(1.02);
        }

        /* User Message */
        .stChatMessage[data-testid="user"] {
            background-color: #C8E6C9;
            border: 2px solid #2E7D32;
        }

        /* Assistant Message */
        .stChatMessage[data-testid="assistant"] {
            background-color: #FFFFFF;
            border: 2px solid #BDBDBD;
        }

        /* Enhanced Input Box */
        .stTextInput {
            border-radius: 25px;
            border: 2px solid #1B5E20;
            padding: 0.6rem 1.2rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            transition: all 0.3s ease-in-out;
        }

        .stTextInput:focus {
            border: 2px solid #388E3C;
            box-shadow: 0 4px 12px rgba(0, 128, 0, 0.2);
        }


        /* Footer */
        @keyframes fadeInUp {
            0% { opacity: 0; transform: translateY(20px); }
            100% { opacity: 1; transform: translateY(0); }
        }

        footer {
            position: fixed;
            bottom: 0;
            width: 100%;
            text-align: center;
            padding: 10px;
            background-color: rgba(255,255,255,0.95);
            font-weight: 500;
            animation: fadeInUp 1s ease-in-out;
            box-shadow: 0 -4px 6px rgba(0, 0, 0, 0.1);
        }

        /* Hide Streamlit Branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .viewerBadge_container__1QSob {display: none;}
        .stDeployButton {display: none;}
    </style>

    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

hide_streamlit_style = """
    <style>
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "openai_key" not in st.session_state:
    st.session_state["openai_key"] = None
if "pinecone_key" not in st.session_state:
    st.session_state["pinecone_key"] = None
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def validate_openai_key(api_key):
    """Validate OpenAI API Key"""
    openai.api_key = api_key  # Set key
    try:
        # Test request with a simple chat completion
        openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "Say 'Hello'"}]
        )
        return True
    except OpenAIError as e:
        st.error(f"OpenAI API Error: {e}")  # Show detailed error
        return False
    except Exception as e:
        st.error(f"Unexpected Error: {e}")  # Debugging info
        return False


def validate_pinecone_key(api_key):
    """Validate Pinecone API Key"""
    try:
        pc = Pinecone(api_key=api_key)
        indexes = pc.list_indexes()
        if indexes:
            return True
        else:
            st.warning("Pinecone API key is valid but no indexes found.")
            return True
    except Exception as e:
        st.error(f"Pinecone Error: {e}")  # Debugging
        return False

    
def show_api_form():
    """Display the API keys input form"""
    st.title("Welcome to EarthBot 🌍")
    
    st.markdown("""
        <div style='text-align: center; padding: 1rem; background-color: #E8F5E9; border-radius: 10px; margin-bottom: 2rem;'>
            <h3>Enter Your API Keys to Start</h3>
            <p>Your API keys will be used only for this session and won't be stored permanently.</p>
        </div>
    """, unsafe_allow_html=True)

    # Create two columns for API key inputs
    col1, col2 = st.columns(2)
    
    with col1:
        openai_key = st.text_input("OpenAI API Key", type="password", key="openai_key_input")

    with col2:
        pinecone_key = st.text_input("Pinecone API Key", type="password", key="pinecone_key_input")
    
    if st.button("Start Chat", key="start_chat"):
        if openai_key and pinecone_key:
            openai_valid = validate_openai_key(openai_key)
            pinecone_valid = validate_pinecone_key(pinecone_key)
            
            if openai_key:
                if validate_openai_key(openai_key):
                    st.session_state["openai_key"] = openai_key
                else:
                    st.error("Invalid OpenAI API Key.")

            if pinecone_key:
                if validate_pinecone_key(pinecone_key):
                    st.session_state["pinecone_key"] = pinecone_key
                else:
                    st.error("Invalid Pinecone API Key.")

            if st.session_state["openai_key"] and st.session_state["pinecone_key"]:
                st.session_state["authenticated"] = True
                st.rerun()

            else:
                if not openai_valid:
                    st.error("Invalid OpenAI API key. Please check and try again.")
                if not pinecone_valid:
                    st.error("Invalid Pinecone API key. Please check and try again.")
        else:
            st.warning("Please enter both API keys.")
            
def show_chat_interface():            
    # Initialize Pinecone
    openai_api_key = st.session_state["openai_key"]
    pc = Pinecone(api_key=st.session_state["pinecone_key"])
    index_name = "faqsembeddings"
    index = pc.Index(index_name)

    if st.sidebar.button("Logout"):
        st.session_state["authenticated"] = False
        st.session_state["openai_key"] = None
        st.session_state["pinecone_key"] = None
        st.session_state["messages"] = []
        st.rerun()
        
    def get_embedding(text):
        response = openai.Embedding.create(
            input=text, model="text-embedding-ada-002", api_key=openai_api_key
        )
        return response["data"][0]["embedding"]

    def generate_response(query_text, top_k=2):
        query_embedding = get_embedding(query_text)
        results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)

        faqs = "\n".join(
            [
                f"Q: {match['metadata']['question']}\nA: {match['metadata']['answer']}"
                for match in results["matches"]
            ]
        )

            prompt_template = PromptTemplate(
                input_variables=["question", "retrieved_faqs", "services", "get_started"],
                template="""
                    You're **Earthbot**, an AI assistant specializing in **sustainable practices, eco-friendly solutions, and green building materials**. I provide precise information about our **services, offerings, and product recommendations**. Feel free to ask any relevant questions!
    
                ---
                
                ## **Interaction Guidelines**
                
                ### **1. Handling Greetings & Closings**
                - **Professional & Warm Approach**  
                  - Greet users professionally while keeping responses aligned with our services.  
                  - Acknowledge gratitude and closing remarks courteously with a formal response.  
                
                ---
                
                ## **2. Persona & Boundaries**
                - **Clear Formatting:** Use structured headings where needed.  
                - **Purpose-Driven:** Reference `{purpose}` or `{get_started}` for service-related inquiries.  
                - **Precise & Professional:** Provide concise, relevant answers without unnecessary details.  
                - **Strict Data Reliance:** Respond only using the provided FAQ data without stating limitations.  
                - **No Off-Topic Responses:** If a query is unrelated, politely state that Earthbot only answers questions within its domain.  
                - **No Apologies:** Do not apologize for unavailable information; instead, offer alternative relevant insights.  
                
                ---
                
                ## **3. User Query Handling**
                - If the query is a **greeting or expression of gratitude**, respond warmly and professionally.  
                - Otherwise, provide an answer based on **retrieved FAQs**.  
                - If no relevant or less confident information or any other information like tech,medicle or any other is found, respond with:  
                  > *"I can only assist with questions related to our services and sustainable solutions. Please refer to our official sources for other inquiries."*  
                
                ---
                
                ## **4. Product Recommendations**
                - **Tailored Suggestions:** Recommend products based on sustainability and eco-friendliness.  
                - **Key Features:** Highlight benefits and eco-conscious attributes.  
                - **Comparison Assistance:** Offer insights to help users make informed choices.  
                - **Call to Action:** Direct users to our website, [earthbot.io](https://earthbot.io), for more details.  
                
                ---
                
                ### **User Query:** `{question}`  
                
                ### **Relevant FAQs:**  
                `{retrieved_faqs}`  
                
                Provide a **clear, professional, and informative** response, strictly staying within the provided FAQ data.  
            
              

                """,
        )

        formatted_prompt = prompt_template.format(
            question=query_text,
            retrieved_faqs=faqs,
            purpose=purpose,
            get_started=get_started,
        )

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": formatted_prompt}],
            api_key=openai_api_key,
            stream=True,
        )

        return response

    # Create a welcome container
    def show_welcome():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("EarthBot - Your Eco Guide 🌍")
            st.markdown("""
                <div style='text-align: center; padding: 1rem; background-color: #E8F5E9; border-radius: 10px;'>
                    <h3>Welcome to EarthBot! 👋</h3>
                    <p>Welcome to earthbot.io - your platform for a net-zero world.</p>
                </div>
            """, unsafe_allow_html=True)

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
        show_welcome()
    else:
        if not st.session_state["messages"]:
            show_welcome()

    # Custom message container
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"], avatar="🌍" if message["role"] == "assistant" else None):
            st.markdown(message["content"])

    # Enhanced chat input with placeholder
    user_query = st.chat_input("Ask me anything about sustainable practices...")

    if user_query:
        # Add user message
        st.session_state["messages"].append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Add assistant response with custom styling
        with st.chat_message("assistant", avatar="🌍"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Create a progress bar
            with st.spinner(""):
                for chunk in generate_response(user_query):
                    if "choices" in chunk:
                        content = chunk["choices"][0]["delta"].get("content", "")
                        full_response += content
                        message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
            
            # Add to chat history
            st.session_state["messages"].append({"role": "assistant", "content": full_response})

    # Add a subtle footer
    st.markdown("""
        <div style='position: fixed; bottom: 0; width: 100%; text-align: center; padding: 10px; background-color: rgba(255,255,255,0.9);'>
            <p style='color: #666; font-size: 0.8em;'>Powered by EarthBot 🌍 - Making sustainability accessible</p>
        </div>
    """, unsafe_allow_html=True)


# Main app logic
def main():
    if not st.session_state["authenticated"]:
        show_api_form()
    else:
        show_chat_interface()

if __name__ == "__main__":
    main()
