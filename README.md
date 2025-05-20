# OutReachCrafter: Multi-Platform Job Application Message Crafter

## Overview
OutReachCrafter is a production-ready, AI-powered tool that helps job seekers generate customized job application messages for multiple platforms (Email, LinkedIn, WhatsApp, Twitter DM, SMS). The app guides users through a multi-step workflow, from resume upload and parsing to company research and message generation, with robust customization and export options.

## Features
- Multi-step workflow UI with progress indicators
- Resume upload and LLM-powered structured extraction
- Automated company information gathering (Tavily API, with caching)
- Job title/role input
- Platform selection: Email, LinkedIn, WhatsApp, Twitter DM, SMS
- Platform-specific customization (e.g., max length, emojis)
- Tone, length, and focus area selection
- Generate multiple message variants per platform
- Secure prompt engineering and prompt injection mitigation
- Message preview, easy copy, and OS-friendly download options
- Responsive, user-friendly interface

## Requirements
- Python 3.9+
- See `requirements.txt` for all dependencies

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
4. Set up your `.env` file with the following keys:
   - `GROQ_API_KEY` (for LLM message generation)
   - `GOOGLE_CSE_API_KEY` and `GOOGLE_CSE_CX` (optional, for Google search)
   - `TAVILY_API_KEY` (for company info search)
5. Run the app:
   ```
   venv\Scripts\python -m streamlit run app.py
   ```

## Usage
1. Open the Streamlit app in your browser (usually at http://localhost:8501).
2. Follow the multi-step workflow:
   - **Step 1:** Upload your resume and extract structured info
   - **Step 2:** Enter company name and job title/role
   - **Step 3:** Choose platform, tone, length, focus areas, and platform-specific options
   - **Step 4:** Preview, copy, and download your generated message variants
3. Use the generated messages for your job applications across supported platforms.

## Project Status
**This project is complete and production-ready.**
- All planned features are implemented
- Robust error handling and user feedback
- Secure and efficient prompt engineering
- Modern, responsive UI

## License
MIT 