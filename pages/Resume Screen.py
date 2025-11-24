# langchain: https://python.langchain.com/
import os
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'

import streamlit as st
from streamlit_lottie import st_lottie
import json

# ---------- SESSION FLAGS ----------
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False

def load_lottiefile(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

# ---------- TOP HERO + HELP ----------
st_lottie(load_lottiefile("images/welcome.json"),
          speed=1, reverse=False, loop=True,
          quality="high", height=200)

st.markdown("# 🎯 AI Interview Assistant")
st.markdown("---")

# ============ INPUT WIDGETS ============
# Interview Type Dropdown
interview_type = st.selectbox(
    "📋 Interview Type",
    ["Technical", "HR / Behavioral"],
    help="Select the type of interview you want to practice",
    key="interview_type",
)

st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)

# Role Dropdown
role = st.selectbox(
    "👔 Role",
    ["Software Engineer", "Data Analyst", "Marketing"],
    help="Select the role you are interviewing for",
    key="role",
)

st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)

# Job Description Text Area
job_description = st.text_area(
    "💼 Job Description or Keywords",
    placeholder="Paste the job description here, or enter relevant keywords (e.g., Python, Leadership, Communication)...",
    height=150,
    help="Provide job description or keywords to tailor the interview questions",
    key="job_description",
)

st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)

# Resume Upload
resume = st.file_uploader(
    "📄 Upload Your Resume (PDF)",
    type=["pdf"],
    help="Upload your resume in PDF format",
    key="resume",
)

st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)

# ============ START INTERVIEW BUTTONS ============
if resume:
    st.markdown("## 🚀 Start Your Interview")
    st.markdown("Choose your preferred interview mode:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💬 Start Text Interview", use_container_width=True, type="primary"):
            # Store inputs in session state
            if "interview_type" in st.session_state:
                st.session_state.interview_type_value = st.session_state.interview_type
            if "role" in st.session_state:
                st.session_state.role_value = st.session_state.role
            if "job_description" in st.session_state:
                st.session_state.job_description_value = st.session_state.job_description
            if "resume" in st.session_state:
                st.session_state.resume_value = st.session_state.resume
            
            st.session_state.interview_mode = 'text'
            st.session_state.interview_started = True
            
            # Navigate to text interview page
            st.switch_page("pages/Resume Text Interview.py")
    
    with col2:
        if st.button("🎙️ Start Voice Interview", use_container_width=True, type="primary"):
            # Store inputs in session state
            if "interview_type" in st.session_state:
                st.session_state.interview_type_value = st.session_state.interview_type
            if "role" in st.session_state:
                st.session_state.role_value = st.session_state.role
            if "job_description" in st.session_state:
                st.session_state.job_description_value = st.session_state.job_description
            if "resume" in st.session_state:
                st.session_state.resume_value = st.session_state.resume
            
            st.session_state.interview_mode = 'voice'
            st.session_state.interview_started = True
            
            # Navigate to voice interview page
            st.switch_page("pages/Resume Voice Interview.py")
else:
    st.info("👆 Please upload your resume to begin the interview preparation.")