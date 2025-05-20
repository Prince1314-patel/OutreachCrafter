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
    if 'resume_structured' not in st.session_state:
        st.session_state['resume_structured'] = None

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
                        st.session_state['resume_structured'] = structured_info
                        st.success("Structured information extracted and ready for editing.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
    else:
        st.info("Click the button above to extract structured information from your resume using AI.")

    # Editable view for structured info
    if st.session_state['resume_structured']:
        st.markdown("---")
        st.subheader("Edit Structured Resume Information")
        with st.form("edit_structured_info_form"):
            data = st.session_state['resume_structured']
            # Skills, Achievements, Projects as comma-separated
            skills = st.text_area("Skills (comma-separated)", ", ".join(data.get("skills", [])) if isinstance(data.get("skills", []), list) else str(data.get("skills", "")))
            achievements = st.text_area("Achievements (comma-separated)", ", ".join(data.get("achievements", [])) if isinstance(data.get("achievements", []), list) else str(data.get("achievements", "")))
            projects = st.text_area("Projects (comma-separated)", ", ".join(data.get("projects", [])) if isinstance(data.get("projects", []), list) else str(data.get("projects", "")))
            # Experience and Education as JSON
            exp_example = '[{"company": "Acme Corp", "title": "Engineer", "dates": "2020-2022", "description": "Did X"}]'
            experience = st.text_area("Experience (JSON list)", json.dumps(data.get("experience", []), indent=2) if isinstance(data.get("experience"), list) else str(data.get("experience", "")), help=f"Example: {exp_example}")
            edu_example = '[{"degree": "BSc", "institution": "Uni", "dates": "2016-2020"}]'
            education = st.text_area("Education (JSON list)", json.dumps(data.get("education", []), indent=2) if isinstance(data.get("education"), list) else str(data.get("education", "")), help=f"Example: {edu_example}")
            submitted = st.form_submit_button("Save Changes")
        if submitted:
            try:
                # Parse comma-separated fields
                new_skills = [s.strip() for s in skills.split(",") if s.strip()]
                new_achievements = [a.strip() for a in achievements.split(",") if a.strip()]
                new_projects = [p.strip() for p in projects.split(",") if p.strip()]
                # Parse and validate experience JSON
                import json
                from json import JSONDecodeError
                try:
                    exp_data = json.loads(experience) if experience.strip() else []
                except JSONDecodeError as e:
                    st.error(f"Malformed JSON in Experience: {e}. Please check your formatting. Example: {exp_example}")
                    exp_data = None
                if exp_data is not None:
                    if not isinstance(exp_data, list) or not all(isinstance(item, dict) for item in exp_data):
                        st.error("Experience must be a JSON list of objects. Example: {exp_example}")
                        exp_data = None
                    else:
                        required_exp_keys = {"company", "title", "dates", "description"}
                        for idx, item in enumerate(exp_data):
                            if not required_exp_keys.issubset(item.keys()):
                                st.error(f"Experience entry {idx+1} is missing required keys: {required_exp_keys - set(item.keys())}. Example: {exp_example}")
                                exp_data = None
                                break
                # Parse and validate education JSON
                try:
                    edu_data = json.loads(education) if education.strip() else []
                except JSONDecodeError as e:
                    st.error(f"Malformed JSON in Education: {e}. Please check your formatting. Example: {edu_example}")
                    edu_data = None
                if edu_data is not None:
                    if not isinstance(edu_data, list) or not all(isinstance(item, dict) for item in edu_data):
                        st.error("Education must be a JSON list of objects. Example: {edu_example}")
                        edu_data = None
                    else:
                        required_edu_keys = {"degree", "institution", "dates"}
                        for idx, item in enumerate(edu_data):
                            if not required_edu_keys.issubset(item.keys()):
                                st.error(f"Education entry {idx+1} is missing required keys: {required_edu_keys - set(item.keys())}. Example: {edu_example}")
                                edu_data = None
                                break
                # Only update if all validations pass
                if exp_data is not None and edu_data is not None:
                    new_structured = {
                        "skills": new_skills,
                        "achievements": new_achievements,
                        "projects": new_projects,
                        "experience": exp_data,
                        "education": edu_data
                    }
                    st.session_state['resume_structured'] = new_structured
                    st.success("Structured resume information updated successfully!")
            except Exception as e:
                st.error(f"Unexpected error updating structured info: {e}. Please check your input formatting.")
        st.markdown("#### Current Structured Resume Data:")
        st.json(st.session_state['resume_structured'])

st.header("2. Enter Target Company Information")
company_name = st.text_input("Company Name")
company_website = st.text_input("Company Website (optional)")
company_description = st.text_area("Company Description / Mission / Culture (paste or write)")

st.header("3. Generate Application Message (Email)")
if st.button("Generate Message"):
    st.info("Message generation coming soon! This is a placeholder for Phase 1.")

st.markdown("---")
st.caption("Phase 2: Core Functionality - LLM resume extraction, structured data validation, and editing. Company info automation coming next.") 