from langchain.chains import RetrievalQA
from llm.llm_client import get_llm
from llm.prompt_template import get_prompt


def build_rag_chain(vector_store):
    llm = get_llm()
    prompt = get_prompt()

    retriever = vector_store.as_retriever()

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt}
    )

    return qa_chain
