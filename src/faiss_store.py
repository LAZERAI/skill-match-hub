from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document


def create_vector_store(text, embedding_model):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    docs = splitter.split_text(text)
    documents = [Document(page_content=chunk) for chunk in docs]

    vector_store = FAISS.from_documents(documents, embedding_model)
    return vector_store
