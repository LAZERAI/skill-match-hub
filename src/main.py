from ingestion.pdf_loader import load_resume
from ingestion.text_cleaner import clean_text
from embeddings.embedding_model import get_embedding_model
from vectorstore.faiss_store import create_vector_store
from rag.retrieval_pipeline import build_rag_chain
from extraction.skill_extractor import extract_skills


def run_pipeline(pdf_path, job_description):
    # 1. Load & Clean
    raw_text = load_resume(pdf_path)
    cleaned_text = clean_text(raw_text)

    # 2. Create Vector Store
    embedding_model = get_embedding_model()
    vector_store = create_vector_store(cleaned_text, embedding_model)

    # 3. Build RAG Chain
    rag_chain = build_rag_chain(vector_store)

    # 4. Extract Skills
    result = extract_skills(rag_chain, job_description)

    return result


if __name__ == "__main__":
    pdf_path = "data/resumes/sample_resume.pdf"
    jd = "Looking for a Python developer with experience in LLM, LangChain, and AWS."

    output = run_pipeline(pdf_path, jd)
    print(output)
