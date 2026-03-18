from pydantic import BaseModel,ConfigDict
from datetime import datetime

class PDFDocument(BaseModel):
    file_name: str


class PDFDocumentResponse(BaseModel):
    id: int
    file_name: str
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PDFDocumentUploadResponse(BaseModel):
    message : str
    document : PDFDocumentResponse