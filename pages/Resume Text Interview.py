# langchain: https://python.langchain.com/
import os
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'

from dataclasses import dataclass
import streamlit as st
from langchain_community.callbacks.manager import get_openai_callback
from langchain_community.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import RetrievalQA, ConversationChain
from langchain.prompts.prompt import PromptTemplate
from prompts.prompts import templates
from typing import Literal
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import NLTKTextSplitter
from PyPDF2 import PdfReader
from prompts.prompt_selector import prompt_sector
from langchain_community.embeddings import OpenAIEmbeddings
import logging
import warnings
import nltk
import html

# Recreate variables from session state
interview_type = st.session_state.get("interview_type_value")
role = st.session_state.get("role_value")
job_description = st.session_state.get("job_description_value")
resume = st.session_state.get("resume_value")
position = role
warnings.filterwarnings("ignore", message=".*model not found.*")
nltk.download('punkt', quiet=True)

@dataclass
class Message:
    """Class for keeping track of interview history."""
    origin: Literal["human", "ai"]
    message: str

def save_vector(resume, job_desc=""):
    """embeddings"""
    pdf_reader = PdfReader(resume)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    
    # Combine resume text with job description
    if job_desc:
        text += f"\n\nJob Description:\n{job_desc}"
    
    # Create embeddings using GitHub Models
    embeddings = OpenAIEmbeddings(
        model="openai/text-embedding-3-small",
        base_url="https://models.github.ai/inference",
        api_key=st.secrets["GITHUB_TOKEN"]
    )
    text_splitter = NLTKTextSplitter()
    texts = text_splitter.split_text(text)
    
    # Create FAISS vector store
    docsearch = FAISS.from_texts(texts, embeddings)
    return docsearch

def initialize_session_state_resume():
    """Initialize session state for resume interview"""
    if 'jd' not in st.session_state:
        st.session_state.jd = None
    if 'resume' not in st.session_state:
        st.session_state.resume = None
    if "resume_history" not in st.session_state:
        st.session_state.resume_history = []
    if "resume_guideline" not in st.session_state:
        llm = ChatOpenAI(
            model_name="openai/gpt-4o-mini",
            temperature=0.8,
            base_url="https://models.github.ai/inference",
            api_key=st.secrets["GITHUB_TOKEN"]
        )
        st.session_state.resume_guideline = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type_kwargs=st.session_state.chain_type_kwargs,
            chain_type='stuff',
            retriever=st.session_state.retriever,
            memory=st.session_state.resume_memory
        ).run("Create an interview guideline and prepare only two questions for each topic. Make sure the questions tests the knowledge")
    if "resume_screen" not in st.session_state:
        llm = ChatOpenAI(
            model_name="openai/gpt-4o-mini",
            temperature=0.8,
            base_url="https://models.github.ai/inference",
            api_key=st.secrets["GITHUB_TOKEN"]
        )
        PROMPT = PromptTemplate(
            input_variables=["history", "input"],
            template="""I want you to act as an interviewer strictly following the guideline in the current conversation.
            
            Ask me questions and wait for my answers like a human. Do not write explanations.
            Candidate has no assess to the guideline.
            Only ask one question at a time. 
            Do ask follow-up questions if necessary. 
            Do not ask the same question.
            Do not repeat the question. 
            Candidate has no assess to the guideline.
            You name is GPTInterviewer.
            I want you to only reply as an interviewer.
            Do not write all the conversation at once.
            If there is an error, point it out.

            Current Conversation:
            {history}
            
            Candidate: {input}
            AI: """
        )
        st.session_state.resume_screen = ConversationChain(
            prompt=PROMPT,
            llm=llm,
            memory=st.session_state.resume_memory
        )
    if 'resume_feedback' not in st.session_state:
        llm = ChatOpenAI(
            model_name="openai/gpt-4o-mini",
            temperature=0.8,
            base_url="https://models.github.ai/inference",
            api_key=st.secrets["GITHUB_TOKEN"]
        )
        st.session_state.resume_feedback = ConversationChain(
            prompt=PromptTemplate(input_variables=["history", "input"], template=templates.feedback_template),
            llm=llm,
            memory=st.session_state.resume_memory,
        )
    
    # Initialize greeting with a simple message
    interview_greeting = f"Hello, I am your interviewer today. I will conduct a {interview_type.lower()} interview for the {position} position based on your resume"
    if job_description:
        interview_greeting += " and the job description you provided"
    interview_greeting += ". Please start by saying hello or introducing yourself."
    
    st.session_state.resume_history.append(
        Message("ai", interview_greeting)
    )

def answer_call_back():
    """Process user's answer and get AI response"""
    with get_openai_callback() as cb:
        if st.session_state.get('interview_mode') == 'voice':
            # Save audio and transcribe
            audio_bytes = st.session_state['answer']
            file_path = save_wav_file(audio_bytes)
            try:
                human_answer = transcribe(file_path)
                if not human_answer or human_answer.strip() == "":
                    st.warning("Sorry, I couldn't understand that. Please try again.")
                    return
            except Exception as e:
                st.error(f"Transcription error: {e}")
                return
        else:
            human_answer = st.session_state['answer']
        
        if not human_answer or str(human_answer).strip() == "":
            return
        
        # Normalize user input: remove all extra whitespace & newlines
        cleaned_input = " ".join(str(human_answer).split())

        st.session_state.resume_history.append(
            Message("human", cleaned_input)
        )
        # OpenAI answer and save to history
        llm_answer = st.session_state.resume_screen.run(cleaned_input)
        st.session_state.resume_history.append(Message("ai", llm_answer))
        st.session_state.token_count += cb.total_tokens

# Initialize if needed
if "resume_history" not in st.session_state:
    # First time - need to setup everything
    if resume:
        # Save resume data
        st.session_state.jd = job_description if job_description else ""
        st.session_state.resume = resume
        
        # Create vector store
        with st.spinner("Processing your resume..."):
            docsearch = save_vector(resume, st.session_state.jd)
            st.session_state.retriever = docsearch.as_retriever(search_type="similarity")
            st.session_state.chain_type_kwargs = prompt_sector(position, templates)
        
        # Initialize memory
        if "resume_memory" not in st.session_state:
            st.session_state.resume_memory = ConversationBufferMemory(human_prefix="Candidate: ", ai_prefix="Interviewer")
        
        if "token_count" not in st.session_state:
            st.session_state.token_count = 0
        
        # Initialize session state
        initialize_session_state_resume()
    else:
        st.info("👆 Please upload your resume to begin the interview preparation.")
        st.stop()

# Page config
st.markdown("# 💬 Text Interview")
st.markdown("---")

# Show feedback button if requested
if st.session_state.get('show_feedback'):
    evaluation = st.session_state.resume_feedback.run("please give evalution regarding the interview")
    st.markdown(evaluation)
    st.download_button(label="Download Interview Feedback", data=evaluation, file_name="interview_feedback.txt")
    st.stop()

# Top actions: End Interview (left) and Show Guideline (right)
top_col1, top_col2 = st.columns(2)

with top_col1:
    end_clicked = st.button("⏹ End Interview", use_container_width=True, type="primary")

with top_col2:
    guideline_clicked = st.button("📝 Show Interview Guideline", use_container_width=True)

if guideline_clicked:
    st.markdown(st.session_state.resume_guideline)

if end_clicked:
    st.session_state['show_feedback'] = True
    st.rerun()

# # Buttons
# col1, col2 = st.columns(2)
# with col1:
#     feedback = st.button("📊 Get Interview Feedback")
# with col2:
#     guideline = st.button("📝 Show Interview Guideline")

# if guideline:
#     st.markdown(st.session_state.resume_guideline)
# if feedback:
#     st.session_state['show_feedback'] = True
#     st.rerun()

# Text/Chat mode - WhatsApp-style left/right bubbles
st.markdown("""
<style>
.chat-wrapper {
    max-height: 500px;
    overflow-y: auto;
    overflow-x: hidden;
    background-color: #0f172a;
    border-radius: 12px;
    padding: 16px 16px 8px 16px;
    margin-bottom: 16px;
    border: 1px solid #1f2933;
}

.chat-row {
    display: flex;
    width: 100%;
    margin-bottom: 10px;
}

/* AI row (left side) */
.chat-row-ai {
    justify-content: flex-start;
}

/* Human row (right side) */
.chat-row-human {
    justify-content: flex-end;
}

.chat-bubble-wrapper {
    display: flex;
    max-width: 70%;
}

.chat-bubble {
    display: inline-block;
    max-width: 100%;
    padding: 10px 14px;
    border-radius: 18px;
    font-size: 0.95rem;
    line-height: 1.4;
    word-wrap: break-word;
    word-break: break-word;
    white-space: normal;
}

/* Interviewer (AI) bubble on the LEFT */
.chat-bubble-ai {
    background: #1e293b;
    color: #e5e7eb;
    border-bottom-left-radius: 4px;
}

/* Candidate (You) bubble on the RIGHT */
.chat-bubble-human {
    background: #22c55e;
    color: #0b1120;
    border-bottom-right-radius: 4px;
}

.chat-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    margin: 0 8px;
    background-color: #020617;
    flex-shrink: 0;
}

/* AI avatar on the left of bubble */
.chat-avatar-ai {
    order: 0;
}
.chat-bubble-wrapper-ai {
    order: 1;
}

/* Human avatar on the right of bubble */
.chat-avatar-human {
    order: 1;
}
.chat-bubble-wrapper-human {
    order: 0;
}
</style>
""", unsafe_allow_html=True)

# Render the conversation
chat_html = ['<div class="chat-wrapper">']

for msg in st.session_state.resume_history:
    is_ai = (msg.origin == "ai")
    avatar = "🤖" if is_ai else "🧑"

    # collapse whitespace just in case
    normalized_text = " ".join(str(msg.message).split())
    safe_text = html.escape(normalized_text)

    if is_ai:
        # Interviewer on the left
        chat_html.append(
            '<div class="chat-row chat-row-ai">'
            f'<div class="chat-avatar chat-avatar-ai">{avatar}</div>'
            '<div class="chat-bubble-wrapper chat-bubble-wrapper-ai">'
            f'<div class="chat-bubble chat-bubble-ai">{safe_text}</div>'
            '</div>'
            '</div>'
        )
    else:
        # Candidate on the right
        chat_html.append(
            '<div class="chat-row chat-row-human">'
            '<div class="chat-bubble-wrapper chat-bubble-wrapper-human">'
            f'<div class="chat-bubble chat-bubble-human">{safe_text}</div>'
            '</div>'
            f'<div class="chat-avatar chat-avatar-human">{avatar}</div>'
            '</div>'
        )

chat_html.append('</div>')
st.markdown("".join(chat_html), unsafe_allow_html=True)

# Input box
answer = st.chat_input("Type your answer here...")
if answer:
    st.session_state['answer'] = answer
    answer_call_back()
    st.rerun()