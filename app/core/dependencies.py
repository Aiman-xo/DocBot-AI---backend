from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends,HTTPException,status
from jose import jwt,JWTError
from app.models.users import User
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')

def get_current_user(token:str = Depends(oauth2_scheme),db:Session = Depends(get_db)):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token,settings.SECRET_KEY,algorithms=[settings.ALGORITHM])

        username = payload.get("sub")

        if not username :
            raise credentials_exception
        
        user = db.query(User).filter(User.username == username).first()

        
        return user
    except:
        raise HTTPException(status_code=401,detail='Invalid Token...') 
    



