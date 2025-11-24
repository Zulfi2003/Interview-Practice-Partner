# langchain: https://python.langchain.com/
import os
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'

from dataclasses import dataclass
import streamlit as st
from audio_transcription.openai_whisper import save_wav_file, transcribe
from audio_recorder_streamlit import audio_recorder
from langchain_community.callbacks.manager import get_openai_callback
from langchain_community.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import RetrievalQA, ConversationChain
from langchain.prompts.prompt import PromptTemplate
from prompts.prompts import templates
from typing import Literal
from tts_utils import synthesize_speech
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import NLTKTextSplitter
from PyPDF2 import PdfReader
from prompts.prompt_selector import prompt_sector
from langchain_community.embeddings import OpenAIEmbeddings
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
logging.getLogger("streamlit.runtime.media_file_storage").setLevel(logging.ERROR)

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
        openai_api_base="https://models.github.ai/inference",
        openai_api_key=st.secrets["GITHUB_TOKEN"]
    )
    text_splitter = NLTKTextSplitter()
    texts = text_splitter.split_text(text)

    # Create FAISS vector store
    docsearch = FAISS.from_texts(texts, embeddings)
    return docsearch

def initialize_session_state_resume():
    """Initialize session state for resume interview"""
    if 'docserch' not in st.session_state:
        st.session_state.docserch = save_vector(resume, job_description)
    if 'retriever' not in st.session_state:
        st.session_state.retriever = st.session_state.docserch.as_retriever(search_type="similarity")
    if 'chain_type_kwargs' not in st.session_state:
        st.session_state.chain_type_kwargs = prompt_sector(position, templates)
    if "resume_history" not in st.session_state:
        st.session_state.resume_history = []
        interview_greeting = f"Hello, I am your interviewer today. I will conduct a {interview_type.lower()} interview for the {role} position based on your resume"
        if job_description:
            interview_greeting += " and the job description you provided"
        interview_greeting += ". Please start by saying hello or introducing yourself."
        st.session_state.resume_history.append(Message(origin="ai", message=interview_greeting))
    if "token_count" not in st.session_state:
        st.session_state.token_count = 0
    if "resume_memory" not in st.session_state:
        st.session_state.resume_memory = ConversationBufferMemory(human_prefix="Candidate: ", ai_prefix="Interviewer")
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
            Do ask follow-up questions if you think it's necessary.
            Do not ask the same question.
            Do not repeat the question.
            Candidate has no assess to the guideline.
            You name is GPTInterviewer.
            I want you to only reply as an interviewer.
            Do not write all the conversation at once.
            Candiate has no assess to the guideline.
            
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

def answer_call_back():
    """Process user's answer and get AI response"""
    with get_openai_callback() as cb:
        human_answer = st.session_state.answer
        
        # Save the audio file
        if not save_wav_file("temp/audio.wav", human_answer):
            st.session_state.resume_history.append(
                Message("ai", "Sorry, I couldn't save the audio. Please try again.")
            )
            return
        
        # Transcribe the audio
        success, result = transcribe("temp/audio.wav")
        
        if not success:
            # Transcription failed - ask the user to try again
            st.session_state.resume_history.append(
                Message("ai", f"{result} Please click the microphone and speak again.")
            )
            return
        
        # Normalize user input: remove all extra whitespace & newlines
        cleaned_input = " ".join(str(result).split())

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
        initialize_session_state_resume()
    else:
        st.info("👆 Please upload your resume to begin the interview preparation.")
        st.stop()

# Page config
st.markdown("# 🎙️ Voice Interview")
st.markdown("---")

# Show feedback button if requested
if st.session_state.get('show_feedback'):
    evaluation = st.session_state.resume_feedback.run("please give evalution regarding the interview")
    st.markdown(evaluation)
    st.download_button(label="Download Interview Feedback", data=evaluation, file_name="interview_feedback.txt")
    st.stop()

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

# ========== LAYOUT + CSS FOR VOICE UI (avatar LEFT, chat RIGHT) ==========

st.markdown("""
<style>
.voice-page {
    margin-top: 1.5rem;
}

/* Chat panel */
.voice-chat-wrapper {
    width: 100%;
    max-height: 480px;
    overflow-y: auto;
    overflow-x: hidden;
    background-color: #0f172a;
    border-radius: 12px;
    padding: 16px 18px;
    border: 1px solid #1f2933;
}

/* Chat scrollbar */
.voice-chat-wrapper::-webkit-scrollbar {
    width: 8px;
}
.voice-chat-wrapper::-webkit-scrollbar-track {
    background: #1a1d24;
    border-radius: 10px;
}
.voice-chat-wrapper::-webkit-scrollbar-thumb {
    background: #4a5058;
    border-radius: 10px;
}
.voice-chat-wrapper::-webkit-scrollbar-thumb:hover {
    background: #5a6068;
}

/* Chat bubbles */
.voice-chat-row {
    display: flex;
    width: 100%;
    margin-bottom: 12px;
}
.voice-chat-row-ai {
    justify-content: flex-start;
}
.voice-chat-row-human {
    justify-content: flex-end;
}

.voice-chat-bubble-wrapper {
    display: flex;
    max-width: 70%;
}

.voice-chat-bubble {
    display: inline-block;
    max-width: 100%;
    padding: 10px 14px;
    border-radius: 18px;
    font-size: 0.95rem;
    line-height: 1.4;
    word-wrap: break-word;
}

.voice-chat-bubble-ai {
    background: #1e293b;
    color: #e5e7eb;
    border-bottom-left-radius: 4px;
}

.voice-chat-bubble-human {
    background: #22c55e;
    color: #0b1120;
    border-bottom-right-radius: 4px;
}

.voice-chat-avatar {
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

/* LEFT column: voice avatar + buttons */
.voice-avatar-container {
    position: relative;
    width: 150px;
    height: 150px;
    margin: 6px 0 24px 0;
}

.voice-pulse-circle {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    border-radius: 50%;
}

.voice-pulse-circle-1 {
    width: 150px;
    height: 150px;
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    animation: voice-pulse-1 2s ease-in-out infinite;
}

.voice-pulse-circle-2 {
    width: 120px;
    height: 120px;
    background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
    animation: voice-pulse-2 2s ease-in-out infinite;
    animation-delay: 0.3s;
}

.voice-pulse-circle-3 {
    width: 90px;
    height: 90px;
    background: linear-gradient(135deg, #93c5fd 0%, #c4b5fd 100%);
    animation: voice-pulse-3 2s ease-in-out infinite;
    animation-delay: 0.6s;
}

@keyframes voice-pulse-1 {
    0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.8; }
    50% { transform: translate(-50%, -50%) scale(1.1); opacity: 1; }
}

@keyframes voice-pulse-2 {
    0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.6; }
    50% { transform: translate(-50%, -50%) scale(1.15); opacity: 0.9; }
}

@keyframes voice-pulse-3 {
    0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.4; }
    50% { transform: translate(-50%, -50%) scale(1.2); opacity: 0.7; }
}

.voice-avatar-icon {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 48px;
    z-index: 10;
}

/* Hide Streamlit audio player (no visible "voice line") */
[data-testid="stAudio"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- TWO COLUMN LAYOUT (avatar left, chat right) ----------
st.markdown('<div class="voice-page">', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 2])

# LEFT: circular avatar + buttons
with col_left:
    st.markdown("""
    <div class="voice-avatar-container">
        <div class="voice-pulse-circle voice-pulse-circle-1"></div>
        <div class="voice-pulse-circle voice-pulse-circle-2"></div>
        <div class="voice-pulse-circle voice-pulse-circle-3"></div>
        <div class="voice-avatar-icon">🤖</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🎤 Press to Respond")
    st.caption("Click below and answer your interviewer using your voice.")

    recorder_key = f"voice_recorder_resume_{len(st.session_state.resume_history)}"
    answer = audio_recorder(
        pause_threshold=2.5,
        sample_rate=44100,
        key=recorder_key,
        text="Click to respond"
    )

# RIGHT: chat messages
with col_right:
    chat_html = ['<div class="voice-chat-wrapper">']

    for msg in st.session_state.resume_history:
        is_ai = (msg.origin == "ai")
        avatar = "🤖" if is_ai else "🧑"
        normalized_text = " ".join(str(msg.message).split())
        safe_text = html.escape(normalized_text)
        
        if is_ai:
            chat_html.append(
                '<div class="voice-chat-row voice-chat-row-ai">'
                f'<div class="voice-chat-avatar">{avatar}</div>'
                '<div class="voice-chat-bubble-wrapper">'
                f'<div class="voice-chat-bubble voice-chat-bubble-ai">{safe_text}</div>'
                '</div>'
                '</div>'
            )
        else:
            chat_html.append(
                '<div class="voice-chat-row voice-chat-row-human">'
                '<div class="voice-chat-bubble-wrapper">'
                f'<div class="voice-chat-bubble voice-chat-bubble-human">{safe_text}</div>'
                '</div>'
                f'<div class="voice-chat-avatar">{avatar}</div>'
                '</div>'
            )

    chat_html.append('</div>')
    st.markdown("".join(chat_html), unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # close .voice-page

# ===== Audio playback + recording handling =====
if st.session_state.resume_history:
    latest_ai = [m for m in st.session_state.resume_history if m.origin == 'ai']
    if latest_ai:
        audio_path = synthesize_speech(latest_ai[-1].message)
        if audio_path and os.path.exists(audio_path):
            st.audio(audio_path, format='audio/mp3', autoplay=True)

# Handle recording result
if 'answer' in locals() and answer:
    st.session_state['answer'] = answer
    answer_call_back()
    st.rerun()

# Bottom actions: End Interview (left) and Show Guideline (right)
st.markdown("---")
bottom_col1, bottom_col2 = st.columns(2)

with bottom_col1:
    end_clicked = st.button("⏹ End Interview", use_container_width=True, type="primary")

with bottom_col2:
    guideline_clicked = st.button("📝 Show Interview Guideline", use_container_width=True)

if guideline_clicked:
    st.markdown(st.session_state.resume_guideline)

if end_clicked:
    st.session_state['show_feedback'] = True
    st.rerun()