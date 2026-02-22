import json


def extract_skills(rag_chain, job_description):
    response = rag_chain.run(job_description)

    try:
        return json.loads(response)
    except:
        return {"error": "Invalid JSON response", "raw_output": response}
