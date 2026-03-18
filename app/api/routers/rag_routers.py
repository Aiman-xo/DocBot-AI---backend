from fastapi import APIRouter,Depends
from app.database.connection import get_db
from sqlalchemy.orm import Session
from app.schemas.rag_schema import RagResponse,RagRequest
from app.core.dependencies import get_current_user
from app.services.rag_service import ask_question
from fastapi import HTTPException,status

router = APIRouter(prefix='/rag')

@router.post('/',response_model=RagResponse)
def ask_question_to_rag(request:RagRequest,db:Session=Depends(get_db),user=Depends(get_current_user)):
    answer = ask_question(request,db,user)

    if not answer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='Couldnt retrieve answer')
    
    return answer