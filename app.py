import streamlit as st
import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
import time
import requests
from tavily import TavilyClient
from langchain.schema import AIMessage

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

# Helper function for Google Custom Search API
def search_company_info(company_name):
    api_key = os.getenv("GOOGLE_CSE_API_KEY")
    cx = os.getenv("GOOGLE_CSE_CX")
    if not api_key or not cx:
        return {"error": "Google Custom Search API key or CX not set in environment."}
    params = {
        "key": api_key,
        "cx": cx,
        "q": company_name,
        "num": 5
    }
    try:
        resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for item in data.get("items", []):
            results.append({
                "title": item.get("title"),
                "snippet": item.get("snippet"),
                "link": item.get("link")
            })
        return {"results": results}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# Helper function for Tavily Search API
def search_company_info_tavily(company_name):
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {"error": "Tavily API key not set in environment."}
    try:
        client = TavilyClient(api_key)
        response = client.search(f"{company_name} company overview", max_results=5)
        results = []
        for item in response.get('results', []):
            results.append({
                "title": item.get("title"),
                "snippet": item.get("content"),
                "link": item.get("url")
            })
        return {"results": results}
    except (requests.exceptions.RequestException, Exception) as e:
        # If TavilyClient has a specific exception, add it here, e.g., TavilyClientException
        return {"error": str(e)}

def make_json_serializable(obj):
    import json
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]
    else:
        try:
            json.dumps(obj)
            return obj
        except TypeError:
            return str(obj)

def generate_email_message(resume_structured, company_name, company_description, tone, length):
    allowed_tones = ["formal", "enthusiastic", "conversational"]
    allowed_lengths = ["short", "medium", "long"]
    if tone not in allowed_tones:
        return {"error": f"Invalid tone: {tone}. Allowed values are: {', '.join(allowed_tones)}."}
    if length not in allowed_lengths:
        return {"error": f"Invalid length: {length}. Allowed values are: {', '.join(allowed_lengths)}."}
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"error": "Groq API key not found. Please set GROQ_API_KEY in your environment."}
    try:
        model_name = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        llm = ChatGroq(
            api_key=api_key,
            model=model_name,
            timeout=60
        )
        prompt = PromptTemplate(
            input_variables=["resume", "company", "description", "tone", "length"],
            template="""
You are an expert job application writer. Using the following information, generate a personalized outreach email for a job application. The email should be tailored to the company and role, reference the candidate's background, and match the specified tone and length.

Candidate Resume (JSON):
{resume}

Company Name:
{company}

Company Description:
{description}

Message Tone: {tone}
Message Length: {length}

Return only the email message, no explanations or formatting.
"""
        )
        serializable_resume = make_json_serializable(resume_structured)
        chain = prompt | llm
        result = chain.invoke({
            "resume": json.dumps(serializable_resume, indent=2),
            "company": company_name,
            "description": company_description,
            "tone": tone,
            "length": length
        })
        if isinstance(result, AIMessage):
            message_text = result.content.strip()
        else:
            message_text = str(result).strip()
        return {"message": message_text}
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
                        st.success("Structured information extracted.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
    else:
        st.info("Click the button above to extract structured information from your resume using AI.")

    # Only display the structured info, not an editable form
    if st.session_state['resume_structured']:
        st.markdown("---")
        st.subheader("Structured Resume Data:")
        st.json(st.session_state['resume_structured'])

st.header("2. Enter Target Company Information")
company_name = st.text_input("Company Name")
company_website = st.text_input("Company Website (optional)")

# Use session state for company_description cache by company name
if 'company_info_cache' not in st.session_state:
    st.session_state['company_info_cache'] = {}

st.header("3. Generate Application Message (Email)")
tone = st.selectbox("Select Message Tone", ["formal", "enthusiastic", "conversational"], index=0)
length = st.selectbox("Select Message Length", ["short", "medium", "long"], index=1)

if st.button("Generate Email Message"):
    if not st.session_state.get('resume_structured'):
        st.error("Please extract and validate your resume information first.")
    elif not company_name:
        st.error("Please provide the company name.")
    else:
        import time
        with st.spinner("Fetching company information and generating your personalized email message..."):
            # Use cached company description if available
            company_info_cache = st.session_state['company_info_cache']
            company_description = company_info_cache.get(company_name, "")
            if not company_description:
                tavily_result = search_company_info_tavily(company_name)
                if "error" in tavily_result:
                    st.error(f"Error fetching company info: {tavily_result['error']}")
                    company_description = ""
                elif tavily_result.get("results"):
                    company_description = tavily_result["results"][0]["snippet"]
                    company_info_cache[company_name] = company_description
                    st.session_state['company_info_cache'] = company_info_cache
                else:
                    st.error("No company information found. Please try a different company name.")
                    company_description = ""
            if company_description:
                st.session_state['company_description'] = company_description
                result = generate_email_message(
                    st.session_state['resume_structured'],
                    company_name,
                    company_description,
                    tone,
                    length
                )
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state['generated_email'] = result["message"]
                    st.success("Email message generated!")

if st.session_state.get('generated_email'):
    st.subheader("Generated Email Message")
    st.code(st.session_state['generated_email'], language=None)
    st.download_button("Download Email as .txt", st.session_state['generated_email'], file_name="outreach_email.txt")
    if st.button("Regenerate Email Message"):
        with st.spinner("Regenerating your email message..."):
            company_info_cache = st.session_state['company_info_cache']
            company_description = company_info_cache.get(company_name, "")
            if not company_description:
                tavily_result = search_company_info_tavily(company_name)
                if "error" in tavily_result:
                    st.error(f"Error fetching company info: {tavily_result['error']}")
                    company_description = ""
                elif tavily_result.get("results"):
                    company_description = tavily_result["results"][0]["snippet"]
                    company_info_cache[company_name] = company_description
                    st.session_state['company_info_cache'] = company_info_cache
                else:
                    st.error("No company information found. Please try a different company name.")
                    company_description = ""
            if company_description:
                st.session_state['company_description'] = company_description
                result = generate_email_message(
                    st.session_state['resume_structured'],
                    company_name,
                    company_description,
                    tone,
                    length
                )
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state['generated_email'] = result["message"]
                    st.success("Email message regenerated!")