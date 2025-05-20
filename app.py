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

def generate_platform_message(resume_structured, company_name, company_description, tone, length, job_title, platform):
    allowed_tones = ["formal", "enthusiastic", "conversational"]
    allowed_lengths = ["short", "medium", "long"]
    allowed_platforms = ["Email", "LinkedIn", "WhatsApp"]
    if tone not in allowed_tones:
        return {"error": f"Invalid tone: {tone}. Allowed values are: {', '.join(allowed_tones)}."}
    if length not in allowed_lengths:
        return {"error": f"Invalid length: {length}. Allowed values are: {', '.join(allowed_lengths)}."}
    if platform not in allowed_platforms:
        return {"error": f"Invalid platform: {platform}. Allowed values are: {', '.join(allowed_platforms)}."}
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
            input_variables=["resume", "company", "description", "tone", "length", "job_title", "platform"],
            template="""
You are an expert job application writer. Using the following information, generate a personalized outreach message for a job application. The message should be tailored to the company and role, reference the candidate's background, and match the specified tone and length.

Candidate Resume (JSON):
{resume}

Company Name:
{company}

Company Description:
{description}

Job Title / Role:
{job_title}

Platform: {platform}
Message Tone: {tone}
Message Length: {length}

Return only the message, no explanations or formatting. Make sure the message fits the style and constraints of the selected platform.
"""
        )
        serializable_resume = make_json_serializable(resume_structured)
        chain = prompt | llm
        result = chain.invoke({
            "resume": json.dumps(serializable_resume, indent=2),
            "company": company_name,
            "description": company_description,
            "tone": tone,
            "length": length,
            "job_title": job_title,
            "platform": platform
        })
        if isinstance(result, AIMessage):
            message_text = result.content.strip()
        else:
            message_text = str(result).strip()
        return {"message": message_text}
    except Exception as e:
        return {"error": str(e)}

# Multi-step workflow UI
st.title("OutReachCrafter: Multi-Platform Job Application Message Crafter")

# Define steps
steps = [
    "Upload Resume",
    "Company & Job Info",
    "Message Options",
    "Preview & Export"
]
if 'current_step' not in st.session_state:
    st.session_state['current_step'] = 0

# Progress indicator
st.progress((st.session_state['current_step'] + 1) / len(steps), text=f"Step {st.session_state['current_step'] + 1} of {len(steps)}: {steps[st.session_state['current_step']]}")

# Step navigation
def go_to_step(step_idx):
    st.session_state['current_step'] = step_idx

def next_step():
    if st.session_state['current_step'] < len(steps) - 1:
        st.session_state['current_step'] += 1

def prev_step():
    if st.session_state['current_step'] > 0:
        st.session_state['current_step'] -= 1

# Step 1: Upload Resume
if st.session_state['current_step'] == 0:
    st.header("1. Upload Your Resume")
    st.info("Upload your resume in PDF, DOCX, or TXT format. The AI will extract your skills, experience, and education.")
    resume_file = st.file_uploader("Upload Resume", type=["pdf", "docx", "txt"], help="Supported formats: PDF, DOCX, TXT")
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
        if st.button("Extract Structured Info with AI"):
            import requests
            try:
                with st.spinner("Extracting structured information from resume using LLM..."):
                    try:
                        structured_info = extract_resume_info_llm(resume_text)
                    except (requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
                        st.warning(f"API error: {e}. Retrying once...")
                        import time
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
    if st.session_state.get('resume_structured'):
        st.markdown("---")
        st.subheader("Structured Resume Data:")
        st.json(st.session_state['resume_structured'])
        st.button("Next: Company & Job Info", on_click=next_step, type="primary")

# Step 2: Company & Job Info
elif st.session_state['current_step'] == 1:
    st.header("2. Enter Target Company and Job Information")
    st.info("Provide the company name and the job title/role you are applying for. The app will fetch company info automatically.")
    company_name = st.text_input("Company Name", value=st.session_state.get('company_name', ""), help="e.g., Google, MindInventory")
    company_website = st.text_input("Company Website (optional)", value=st.session_state.get('company_website', ""))
    job_title = st.text_input("Job Title / Role", value=st.session_state.get('job_title', ""), help="e.g., Software Engineer, Product Manager")
    if company_name:
        st.session_state['company_name'] = company_name
    if company_website:
        st.session_state['company_website'] = company_website
    if job_title:
        st.session_state['job_title'] = job_title
    st.button("Back", on_click=prev_step)
    if company_name and job_title:
        st.button("Next: Message Options", on_click=next_step, type="primary")

# Step 3: Message Options
elif st.session_state['current_step'] == 2:
    st.header("3. Message Options")
    st.info("Choose the platform, tone, and length for your outreach message.")
    platform = st.selectbox("Select Platform", ["Email", "LinkedIn", "WhatsApp"], index=0, help="Choose where you want to send your message.")
    tone = st.selectbox("Select Message Tone", ["formal", "enthusiastic", "conversational"], index=0, help="Set the tone of your message.")
    length = st.selectbox("Select Message Length", ["short", "medium", "long"], index=1, help="Set the length of your message.")
    st.session_state['platform'] = platform
    st.session_state['tone'] = tone
    st.session_state['length'] = length
    st.button("Back", on_click=prev_step)
    st.button("Next: Preview & Export", on_click=next_step, type="primary")

# Step 4: Preview & Export
elif st.session_state['current_step'] == 3:
    st.header("4. Preview & Export Message")
    st.info("Preview your generated message, copy it, or download it as a text file.")
    # Fetch company info if needed
    company_info_cache = st.session_state.get('company_info_cache', {})
    company_name = st.session_state.get('company_name', "")
    company_description = company_info_cache.get(company_name, "")
    if not company_description and company_name:
        with st.spinner("Fetching company information..."):
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
    # Generate message if not already generated or if options changed
    regenerate = False
    if 'last_generation_params' not in st.session_state:
        st.session_state['last_generation_params'] = {}
    params = {
        'resume_structured': st.session_state.get('resume_structured'),
        'company_name': company_name,
        'company_description': company_description,
        'tone': st.session_state.get('tone'),
        'length': st.session_state.get('length'),
        'job_title': st.session_state.get('job_title'),
        'platform': st.session_state.get('platform')
    }
    if st.session_state['last_generation_params'] != params or 'generated_message' not in st.session_state:
        regenerate = True
    if regenerate:
        with st.spinner(f"Generating your {params['platform']} message..."):
            result = generate_platform_message(
                params['resume_structured'],
                params['company_name'],
                params['company_description'],
                params['tone'],
                params['length'],
                params['job_title'],
                params['platform']
            )
        if "error" in result:
            st.error(result["error"])
        else:
            st.session_state['generated_message'] = result["message"]
            st.session_state['last_generation_params'] = params
    if st.session_state.get('generated_message'):
        st.subheader(f"Generated {params['platform']} Message")
        st.code(st.session_state['generated_message'], language=None)
        st.download_button(f"Download {params['platform']} Message as .txt", st.session_state['generated_message'], file_name=f"outreach_{params['platform'].lower()}.txt")
    st.button("Back", on_click=prev_step)
    st.button("Start Over", on_click=lambda: go_to_step(0))