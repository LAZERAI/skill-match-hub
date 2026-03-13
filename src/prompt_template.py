from langchain.prompts import PromptTemplate


def get_prompt():
    template = """
    You are an expert technical recruiter.

    Based on the resume context below, extract:
    - Technical Skills
    - Years of Experience
    - Education

    Return output strictly in JSON format.

    Resume Context:
    {context}

    Job Description:
    {question}
    """

    return PromptTemplate(
        input_variables=["context", "question"],
        template=template
    )
