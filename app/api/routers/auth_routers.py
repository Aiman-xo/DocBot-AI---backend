
from app.schemas.user_schema import UserCreate,RegistrationSuccess,UserResponse,UserLogin
from sqlalchemy.orm import Session
from app.database.connection import get_db
from fastapi import APIRouter,Depends,HTTPException,Response,Request
from app.services.user_service import create_user,retrieve_users,login_user,refresh_access_token
from app.models.users import User
from typing import List

router = APIRouter(
    prefix='/auth'
)

@router.post('/register',response_model=RegistrationSuccess)
def register(user:UserCreate,db:Session = Depends(get_db)):

    user_existed = db.query(User).filter(User.username == user.username).first()
    if user_existed:
        raise HTTPException(status_code=400,detail='User with same name already registered')
    
    registered_user = create_user(user,db)

    if not registered_user:
        raise HTTPException(status_code=400,detail='Invalid Request')
    
    return {
        'message':'User Registered Successfully',
        'user':registered_user
    }

@router.get('/',response_model=List[UserResponse])
def access_users(db:Session = Depends(get_db)):
    users = retrieve_users(db)
    return users

@router.post('/login')
def authenticate_user(user_credentials:UserLogin,response:Response,db:Session = Depends(get_db)):
    tokens = login_user(user_credentials,db)
    if not tokens:
        raise HTTPException(status_code=400,detail='Invalid Credentials')

    access_token,refresh_token = tokens

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,  # Changed to True for cross-domain support
        samesite="none" # Changed to "none" for cross-domain support
    )

    return {
        "message":"User Login Successful!",
        "access_token":access_token
    }

@router.post('/refresh')
def refresh_token(request: Request, db: Session = Depends(get_db)):
    refresh_token_cookie = request.cookies.get("refresh_token")
    
    if not refresh_token_cookie:
        raise HTTPException(status_code=401, detail="Refresh Token not found")

    new_access_token = refresh_access_token(refresh_token_cookie, db)
    
    return {
        "access_token": new_access_token
    }

@router.post('/logout')
def logout(response: Response):
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True, # Must match the original cookie settings
        samesite="none"
    )
    return {"message": "Logged out successfully"}

