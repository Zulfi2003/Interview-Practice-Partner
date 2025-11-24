import streamlit as st
from streamlit_option_menu import option_menu
from app_utils import switch_page
from PIL import Image

im = Image.open("icon.png")
st.set_page_config(page_title="AI Interviewer", layout="centered", page_icon=im)

home_title = "AI Interviewer"
home_introduction = "Welcome to AI Interviewer, empowering your interview preparation with generative AI."

st.image(im, width=100)
st.markdown(f"# {home_title}")

st.markdown("""\n""")
st.markdown(
    "Welcome to AI Interviewer! 👏 AI Interviewer is your personal interviewer powered by generative AI that conducts mock interviews."
    "You can upload your resume and enter job descriptions, and AI Interviewer will ask you customized questions. Additionally, you can configure your own Interviewer!"
)
st.markdown("""\n""")
st.markdown("#### Get started!")
st.markdown("Start your AI-powered interview preparation!")

selected = option_menu(
        menu_title=None,
        options=["Resume Interview"],
        icons=["cloud-upload"],
        default_index=0,
        orientation="horizontal",
    )

st.info("""
📚In this session, the AI Interviewer will conduct a personalized interview based on your resume and job description.
- Choose between Technical or HR/Behavioral interview type
- Select your target role
- Provide job description or keywords
- Upload your resume
- Each Interview will take 10 to 15 mins
- Choose your favorite interaction style (text/voice)
- Start and enjoy！ """)

if st.button("Start Interview!"):
    switch_page("Resume Screen")