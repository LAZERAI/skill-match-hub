from app.services.vector_service import search_vectors

def search_resumes(query):

    results = search_vectors(query)

    return results