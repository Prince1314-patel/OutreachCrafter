# OutReachCrafter: Phase 2 - Core Functionality Development

OutReachCrafter is an AI-powered tool that helps job seekers generate customized job application messages.
// ... existing content ...

## Features (Phase 1)
- Upload your resume (PDF, DOCX, or TXT)
- Extract and view resume text
- Manually enter target company information
- Placeholder for email message generation
- Simple, session-based Streamlit UI (no login, no persistence)

## Setup
1. Clone this repository.
2. Create a Python virtual environment:
   ```
   python -m venv venv
   ```
3. Install dependencies:
   ```
   venv\Scripts\python -m pip install --upgrade pip
   venv\Scripts\python -m pip install -r requirements.txt
   ```
4. Run the app:
   ```
   venv\Scripts\python -m streamlit run app.py
   ```

## Usage
1. Open the Streamlit app in your browser (usually at http://localhost:8501).
2. Upload your resume file.
3. Enter the target company information.
4. Click "Generate Message" (functionality coming in later phases).

## Next Steps
- Automated company info gathering
- LLM-powered message generation
- Multi-platform support

---
This is a Phase 1 MVP. All data is session-based and not stored persistently. 