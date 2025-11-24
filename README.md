# Interview Practice Partner (AI Interviewer)

**Interview Practice Partner** is an AI-powered mock interview app built with Streamlit.  
It uses your **resume + job description** to generate tailored interview questions, run **text or voice interviews**, and give you **structured feedback** on your performance.

This project is designed as a practical, portfolio-ready AI app that shows real-world use of LLMs, vector search, and speech interfaces.

---

## 🚀 Features

- **Resume-aware interviews**  
  Upload a PDF resume and optionally paste a job description. Questions are generated from *your* skills, tools, and experience.

- **Two modes: Text & Voice**
  - 💬 Text interview with chat-style UI  
  - 🎙️ Voice interview using microphone input + speech-to-text + text-to-speech

- **Role-specific interview styles**
  Built-in prompt templates for:
  - Software Engineer  
  - Data Analyst  
  - Marketing  
  - JD-based technical interviews  
  - Behavioral interviews

- **Smart follow-up questions**  
  The interviewer asks one question at a time, uses conversation history, and avoids repeating questions.

- **End-of-interview feedback**  
  Generates a summary, strengths, areas for improvement, score, and actionable tips.

---

## 🧱 Tech Stack

- **Frontend / UI:** Streamlit
- **LLM Orchestration:** LangChain
- **LLMs:** OpenAI GPT-4o-mini via **GitHub Models API**
- **Embeddings / Retrieval:** `text-embedding-3-small` + FAISS
- **PDF Parsing:** PyPDF2
- **Voice Input:** `audio_recorder_streamlit` + Whisper-based transcription
- **TTS:** gTTS (Google Text-to-Speech)

---

## ⚙️ Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Zulfi2003/Interview-Practice-Partner.git
cd Interview-Practice-Partner
```

### 2. Create and activate a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate    # macOS / Linux
# .venv\Scripts\activate     # Windows (PowerShell)
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

---

### 🔐 Configure API Secrets (secrets.toml)

This app uses **GitHub Models** as an OpenAI-compatible endpoint. You need a GitHub Personal Access Token (PAT) with permissions to call models.

1. **Create `.streamlit/secrets.toml`**

   In the project root, make sure this file exists:

   ```bash
   mkdir -p .streamlit
   nano .streamlit/secrets.toml
   ```

   Add:

   ```toml
   GITHUB_TOKEN = "YOUR_GITHUB_MODELS_PAT"
   ```

   > ⚠️ **Note:** Never commit this file — it’s already in `.gitignore`.

2. **How to get the GitHub Models token**
   1. Log in to GitHub.
   2. Go to: **Settings** → **Developer settings** → **Personal access tokens**. or visit (https://github.com/marketplace/models/azure-openai/gpt-4o-mini)
   3. Create a new **classic Personal Access Token (PAT)**.
   4. Make sure it has `models:read` (or `models` scope, depending on UI).
   5. Copy the token and paste it into `.streamlit/secrets.toml` as `GITHUB_TOKEN`.

   You can also refer to the official GitHub Models quickstart and PAT docs for details.

---

## ▶️ Run the App

From the project root:

```bash
streamlit run Homepage.py
```

Or, if you want to use the provided script:

```bash
chmod +x start.sh
./start.sh
```

Then open the URL shown in the terminal (usually `http://localhost:8501`).

---

## 🧩 How to Use

1. **Open the app** in the **Chrome** browser.
2. **On the homepage:**
   - Select interview type (Technical / HR / etc.).
   - Choose the role (e.g., Software Engineer, Data Analyst, Marketing).
   - Paste a job description or keywords (optional).
   - Upload your resume as a PDF.
3. **Choose:**
   - 💬 **Text Interview** → Chat-style Q&A
   - 🎙️ **Voice Interview** → Use your microphone; allow browser mic access.
4. **Answer questions** one by one.
5. **Click End Interview** to generate feedback and download it if needed.

---

## 📁 Project Structure (High-Level)

```
.
├── Homepage.py                 # Main Streamlit entry point
├── pages/
│   ├── Resume Screen.py        # Setup screen (resume + options)
│   ├── Resume Text Interview.py
│   └── Resume Voice Interview.py
├── prompts/                    # Prompt templates & selectors
├── audio_transcription/        # Whisper-based transcription helpers
├── static/                     # CSS + UI images
├── images/                     # Lottie / JSON animations
├── tts_utils.py                # Text-to-speech helper
├── app_utils.py
├── requirements.txt
├── packages.txt
└── .streamlit/
    ├── config.toml
    └── secrets.toml            # <-- your GITHUB_TOKEN (not committed)
```

---

## 🙋‍♂️ Author

- **GitHub:** [Zulfi2003](https://github.com/Zulfi2003)

---

*Interview Practice Partner is a learning + portfolio project focused on realistic AI interviews, not just simple chat completions. Contributions, issues, and suggestions are always welcome!*