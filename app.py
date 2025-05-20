import streamlit as st

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

st.header("2. Enter Target Company Information")
company_name = st.text_input("Company Name")
company_website = st.text_input("Company Website (optional)")
company_description = st.text_area("Company Description / Mission / Culture (paste or write)")

st.header("3. Generate Application Message (Email)")
if st.button("Generate Message"):
    st.info("Message generation coming soon! This is a placeholder for Phase 1.")

st.markdown("---")
st.caption("Phase 1 MVP: Basic resume upload, manual company info, and email message placeholder.") 