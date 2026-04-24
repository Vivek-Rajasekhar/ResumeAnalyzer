import hashlib
import io
import re
from typing import Set, Tuple

import nltk
import streamlit as st
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from nltk.tokenize import word_tokenize


SKILL_DICTIONARY = {
    # Programming Languages
    "python": "Python", "java": "Java", "c": "C", "c++": "C++", "csharp": "C#",
    "javascript": "JavaScript", "typescript": "TypeScript", "ruby": "Ruby",
    "php": "PHP", "swift": "Swift", "kotlin": "Kotlin", "go": "Go",
    "rust": "Rust", "scala": "Scala", "r": "R", "dart": "Dart", "bash": "Bash",

    # Web Development & Frameworks
    "html": "HTML", "css": "CSS", "react": "React.js", "angular": "Angular",
    "vue": "Vue.js", "node": "Node.js", "express": "Express.js", "django": "Django",
    "flask": "Flask", "fastapi": "FastAPI", "spring": "Spring Boot",
    "dotnet": ".NET", "rails": "Ruby on Rails", "nextjs": "Next.js",
    "bootstrap": "Bootstrap", "tailwindcss": "Tailwind CSS",

    # Databases & Vector Stores
    "sql": "SQL", "mysql": "MySQL", "postgresql": "PostgreSQL",
    "mongodb": "MongoDB", "sqlite": "SQLite", "redis": "Redis",
    "cassandra": "Cassandra", "oracle": "Oracle", "mariadb": "MariaDB",
    "elasticsearch": "Elasticsearch", "dynamodb": "DynamoDB", "firebase": "Firebase",
    "surrealdb": "SurrealDB", "faiss": "FAISS",

    # Cloud, DevOps & Automation
    "aws": "AWS", "azure": "Azure", "gcp": "Google Cloud",
    "docker": "Docker", "kubernetes": "Kubernetes", "terraform": "Terraform",
    "ansible": "Ansible", "jenkins": "Jenkins", "cicd": "CI/CD",
    "git": "Git", "github": "GitHub", "gitlab": "GitLab",
    "linux": "Linux", "nginx": "Nginx", "apache": "Apache", "ros": "ROS",

    # AI, ML & Data Science
    "artificial intelligence": "Artificial Intelligence", "machine learning": "Machine Learning",
    "deep learning": "Deep Learning", "nlp": "NLP", "computer vision": "Computer Vision",
    "tensorflow": "TensorFlow", "pytorch": "PyTorch", "scikitlearn": "Scikit-learn",
    "pandas": "Pandas", "numpy": "NumPy", "matplotlib": "Matplotlib",
    "langchain": "LangChain", "ollama": "Ollama", "huggingface": "Hugging Face",
    "llm": "LLMs", "rag": "RAG", "colbert": "ColBERT", "data analysis": "Data Analysis",
    "data science": "Data Science", "data engineering": "Data Engineering",

    # Mobile, Methodologies & Concepts
    "flutter": "Flutter", "react native": "React Native", "android": "Android", "ios": "iOS",
    "agile": "Agile", "scrum": "Scrum", "kanban": "Kanban",
    "rest api": "REST API", "graphql": "GraphQL", "microservices": "Microservices",
    "oop": "OOP", "tdd": "TDD", "system design": "System Design",
    "algorithms": "Algorithms", "data structures": "Data Structures",

    # Tools & Platforms
    "jira": "Jira", "confluence": "Confluence", "figma": "Figma",
    "postman": "Postman", "excel": "Excel", "kafka": "Apache Kafka",
    "spark": "Apache Spark", "hadoop": "Hadoop", "databricks": "Databricks",
    "snowflake": "Snowflake", "tableau": "Tableau", "powerbi": "Power BI"
}

SKILL_ALIASES = {
    # Language Variations
    "js": "javascript", "ts": "typescript", "c#": "csharp", "c plus plus": "c++",
    "golang": "go", "r language": "r",

    # Framework Variations
    "reactjs": "react", "react.js": "react",
    "vuejs": "vue", "vue.js": "vue",
    "nodejs": "node", "node.js": "node",
    "expressjs": "express", "express.js": "express",
    "springboot": "spring", "spring boot": "spring",
    ".net": "dotnet", "ruby on rails": "rails",

    # Database Variations
    "postgres": "postgresql", "postgre": "postgresql",
    "mongo": "mongodb", "elastic search": "elasticsearch",

    # Cloud & DevOps Variations
    "google cloud": "gcp", "google cloud platform": "gcp",
    "k8s": "kubernetes", "ci cd": "cicd", "ci/cd": "cicd",

    # AI/ML Variations
    "ai": "artificial intelligence", "ml": "machine learning",
    "dl": "deep learning", "natural language processing": "nlp",
    "cv": "computer vision", "sklearn": "scikitlearn", "scikit-learn": "scikitlearn",
    "llms": "llm", "large language models": "llm", "retrieval augmented generation": "rag",

    # API & Tools Variations
    "rest": "rest api", "restful api": "rest api", "restful apis": "rest api", "rest apis": "rest api",
    "power bi": "powerbi", "apache spark": "spark", "apache kafka": "kafka"
}


def ensure_nltk_data() -> Tuple[bool, str]:
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)

    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("stopwords", quiet=True)

    try:
        nltk.data.find("tokenizers/punkt")
        nltk.data.find("corpora/stopwords")
    except LookupError:
        return False, "Could not download required NLTK data (punkt, stopwords)."

    return True, ""


def extract_text_from_pdf(file_bytes: bytes) -> str:
    text_chunks = []
    reader = PdfReader(io.BytesIO(file_bytes))
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            text_chunks.append(page_text)
    return "\n".join(text_chunks).strip()


def extract_text_from_txt(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8").strip()
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1", errors="ignore").strip()


def extract_resume_text(file_name: str, file_bytes: bytes) -> Tuple[str, str]:
    name = file_name.lower()

    if name.endswith(".pdf"):
        try:
            return extract_text_from_pdf(file_bytes), ""
        except (PdfReadError, ValueError, TypeError, OSError) as err:
            return "", f"Failed to read PDF resume: {err}"

    if name.endswith(".txt"):
        return extract_text_from_txt(file_bytes), ""

    return "", "Unsupported file type. Please upload a PDF or TXT file."


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9+#./\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_skill_key(candidate: str) -> str:
    cleaned = candidate.strip()
    cleaned = cleaned.replace(".", "")
    cleaned = cleaned.replace("/", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if cleaned in SKILL_ALIASES:
        cleaned = SKILL_ALIASES[cleaned]
    return cleaned


def _generate_skill_candidates(tokens: list[str]) -> Set[str]:
    candidates: Set[str] = set()
    total = len(tokens)
    for idx in range(total):
        for size in (1, 2, 3):
            end = idx + size
            if end > total:
                continue
            cand = " ".join(tokens[idx:end])
            cand_key = _normalize_skill_key(cand)
            if cand_key:
                candidates.add(cand_key)
    return candidates


def extract_skills(text: str) -> Set[str]:
    norm = normalize_text(text)
    if not norm:
        return set()

    raw_tokens = word_tokenize(norm)
    tokens: list[str] = []
    for token in raw_tokens:
        tok = token.strip()
        if not tok or not re.match(r"^[a-z0-9+#./-]+$", tok):
            continue
        tok_key = _normalize_skill_key(tok)
        if tok_key:
            tokens.append(tok_key)

    candidates = _generate_skill_candidates(tokens)
    return {cand for cand in candidates if cand in SKILL_DICTIONARY}


def compute_match(resume_skills: Set[str], job_skills: Set[str]) -> Tuple[Set[str], Set[str], float]:
    matched_skills = resume_skills.intersection(job_skills)
    missing_skills = job_skills - resume_skills
    if not job_skills:
        return matched_skills, missing_skills, 0.0
    score = (len(matched_skills) / len(job_skills)) * 100
    return matched_skills, missing_skills, score


def render_skill_bullets(skills: list[str]) -> None:
    bullet_lines = "\n".join(f"- {skill}" for skill in skills)
    st.markdown(bullet_lines)


def render_results(score: float, matched_skills: Set[str], missing_skills: Set[str]) -> None:
    st.subheader("Match Results")
    st.metric(label="Match Score", value=f"{score:.1f}%")

    matched_labels = sorted({SKILL_DICTIONARY[skill] for skill in matched_skills})
    missing_labels = sorted({SKILL_DICTIONARY[skill] for skill in missing_skills})

    if matched_labels:
        st.success("Matching Skills")
        render_skill_bullets(matched_labels)
    else:
        st.info("No matching skills found between the resume and job description.")

    if missing_labels:
        st.warning("Missing Skills")
        render_skill_bullets(missing_labels)
    else:
        st.success("No missing skills. Great alignment with the required job skills.")


def get_resume_cache_key(file_name: str, file_bytes: bytes) -> str:
    digest = hashlib.sha256(file_bytes).hexdigest()
    return f"{file_name}:{digest}"


def main() -> None:
    st.title("AI Resume Analyzer & Job Matcher")
    st.subheader("Compare your resume with a job description to identify fit and skill gaps.")
    st.write("This tool helps tailor resumes to specific roles by surfacing matching and missing skills.")

    nltk_ok, nltk_err = ensure_nltk_data()
    if not nltk_ok:
        st.error(nltk_err)
        st.stop()

    if "resume_cache_key" not in st.session_state:
        st.session_state.resume_cache_key = ""
    if "resume_text" not in st.session_state:
        st.session_state.resume_text = ""
    if "resume_skills" not in st.session_state:
        st.session_state.resume_skills = set()

    col1, col2 = st.columns(2)
    with col1:
        resume_file = st.file_uploader("Upload Resume (PDF or TXT)", type=["pdf", "txt"])
    with col2:
        job_text = st.text_area("Paste Job Description Here")

    analyze_clicked = st.button("Analyze Match")

    if not analyze_clicked:
        return

    if resume_file is None:
        st.warning("Please upload a resume before analyzing.")
        st.stop()

    if not job_text.strip():
        st.warning("Please paste a job description before analyzing.")
        st.stop()

    resume_bytes = resume_file.getvalue()
    cache_key = get_resume_cache_key(resume_file.name, resume_bytes)

    if st.session_state.resume_cache_key != cache_key:
        resume_text, extract_err = extract_resume_text(resume_file.name, resume_bytes)
        if extract_err:
            st.error(extract_err)
            st.stop()
        if not resume_text.strip():
            st.error("No readable text could be extracted from the uploaded resume.")
            st.stop()
        st.session_state.resume_text = resume_text
        st.session_state.resume_skills = extract_skills(resume_text)
        st.session_state.resume_cache_key = cache_key

    job_skills = extract_skills(job_text)
    if not job_skills:
        st.warning("No recognized technical skills were found in the job description. Score set to 0.0%.")

    matched_skills, missing_skills, score = compute_match(
        st.session_state.resume_skills,
        job_skills,
    )
    render_results(score, matched_skills, missing_skills)


if __name__ == "__main__":
    main()
