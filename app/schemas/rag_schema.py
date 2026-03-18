from pydantic import BaseModel

class RagRequest(BaseModel):
    question:str
    document_id:int

class RagResponse(BaseModel):
    answer:str