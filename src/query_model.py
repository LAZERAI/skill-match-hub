from pydantic import BaseModel

class QueryRequest(BaseModel):
    user_type: str
    query: str