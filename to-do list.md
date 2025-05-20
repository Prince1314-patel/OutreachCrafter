# OutReachCrafter: Project To-Do List
> This document outlines the phases and tasks for developing the OutReachCrafter application.

**Legend:**
- [x]: Completed tasks
- [ ]: Pending tasks

## Phase 1: MVP
- [x] Set up project repository and environment
- [x] Install essential packages (Streamlit, LangChain, etc.)
- [x] Set up basic Streamlit UI shell
- [x] Implement resume upload (PDF, DOCX, TXT)
- [x] Extract text from uploaded resume
- [x] Manual input for company name, website, and description
- [x] Implement basic email message generation (placeholder exists)
- [x] Session-based data management (in-memory)
- [x] Display extracted resume text in UI
- [x] Error handling for file upload and parsing

### Phase 1 Complete
Now moving to **Phase 2: Core Functionality Development**

## Phase 2: Core Functionality Development

### Resume Extraction
- [x] Implement LLM-based resume information extraction
- [x] Create structured representation of resume data

### Data Validation & Editing
- [x] Build resume data validation and editable view

### Company Information Gathering (Web Scraping & APIs)
- [x] Integrate official APIs for company data (e.g., LinkedIn API, Glassdoor API, Google Custom Search API, Tavily API)
- [x] Implement fallback web scraping for company websites (ensure compliance with terms of service and robots.txt)
- [x] Process and display company data from APIs or scraping
- [x] Manual override/edit for company info

> **Now moving to Message Generation**

### Message Generation
- [ ] Develop prompt engineering for different platforms
- [ ] Implement LLM-based message generation (email)
- [ ] Add message customization options (tone, length, focus)

## Phase 3: UI Enhancement & Integration
- [ ] Create multi-step workflow UI
- [ ] Implement progress indicators
- [ ] Add help tooltips and guidance
- [ ] Design responsive layouts
- [ ] Connect resume parsing to company research
- [ ] Link company research to message generation
- [ ] Implement message preview
- [ ] Add copy-to-clipboard and download options
- [ ] Add message history within session

## Phase 4: Platform Expansion & Refinement
- [ ] Extend message generation to LinkedIn
- [ ] Implement WhatsApp message formatting
- [ ] Platform-specific customization options
- [ ] Implement message variants generation
- [ ] Add tone and style adjustments
- [ ] Create focus area selectors (skills, experience, culture)
- [ ] Comprehensive error handling and user feedback

## Phase 5: Testing & Optimization
- [ ] Unit testing for core components
- [ ] Integration testing for full workflow
- [ ] User testing with various resumes/companies
- [ ] Performance and load testing to ensure scalability
- [ ] Accessibility testing for WCAG compliance
- [ ] Optimize LLM prompt efficiency
- [ ] Improve web scraping/API reliability
- [ ] Enhance UI responsiveness
- [ ] Create user and technical documentation
- [ ] Prepare deployment guide 