import streamlit as st
import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
import time

load_dotenv()


# Helper function for LLM-based resume information extraction
def extract_resume_info_llm(resume_text):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"error": "Groq API key not found. Please set GROQ_API_KEY in your environment."}
    try:
        model_name = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        llm = ChatGroq(
            api_key=api_key, 
            model=model_name,
            timeout=60  # Add timeout to prevent hanging on slow responses
        )
        prompt = PromptTemplate(
            input_variables=["resume_text"],
            template="""
You are an expert resume parser. Extract the following structured information from the resume text below:
- Professional skills
- Work experience (with company, title, dates, and description)
- Educational background (degree, institution, dates)
- Achievements and certifications
- Personal projects
Return the result as a JSON object with keys: skills, experience, education, achievements, projects.

Resume Text:
{resume_text}
"""
        )
        chain = prompt | llm
        result = chain.invoke({"resume_text": resume_text})
        import json
        try:
            structured = json.loads(result)
        except Exception:
            structured = {"raw_output": result}
        return structured
    except Exception as e:
        return {"error": str(e)}

st.set_page_config(page_title="OutReachCrafter - Phase 1 MVP", layout="centered")
st.title("OutReachCrafter: Job Application Message Creator")

st.header("1. Upload Your Resume")
resume_file = st.file_uploader("Upload your resume (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])

resume_text = ""
if resume_file is not None:
    try:
        if resume_file.type == "application/pdf":
            import PyPDF2
            reader = PyPDF2.PdfReader(resume_file)
            resume_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif resume_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            import docx2txt
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                tmp.write(resume_file.read())
                tmp_path = tmp.name
            resume_text = docx2txt.process(tmp_path)
        elif resume_file.type == "text/plain":
            resume_text = resume_file.read().decode("utf-8")
        else:
            st.warning("Unsupported file type.")
    except Exception as e:
        st.error(f"Failed to parse resume: {e}")

if resume_text:
    st.subheader("Extracted Resume Text")
    st.text_area("Resume Content", resume_text, height=300)

    st.subheader("Structured Resume Information (LLM Extracted)")
    if st.button("Extract Structured Info with AI"):
        import requests
        try:
            with st.spinner("Extracting structured information from resume using LLM..."):
                try:
                    structured_info = extract_resume_info_llm(resume_text)
                except (requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
                    st.warning(f"API error: {e}. Retrying once...")
                    time.sleep(2)
                    try:
                        structured_info = extract_resume_info_llm(resume_text)
                    except (requests.exceptions.Timeout, requests.exceptions.HTTPError) as e2:
                        st.error(f"API error after retry: {e2}. Please try again later or check your API usage.")
                        structured_info = None
                if structured_info:
                    if "error" in structured_info:
                        st.error(structured_info["error"])
                    else:
                        st.json(structured_info)
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
    else:
        st.info("Click the button above to extract structured information from your resume using AI.")

st.header("2. Enter Target Company Information")
company_name = st.text_input("Company Name")
company_website = st.text_input("Company Website (optional)")
company_description = st.text_area("Company Description / Mission / Culture (paste or write)")

st.header("3. Generate Application Message (Email)")
if st.button("Generate Message"):
    st.info("Message generation coming soon! This is a placeholder for Phase 1.")

st.markdown("---")
st.caption("Phase 1 MVP: Basic resume upload, manual company info, and email message placeholder.") 