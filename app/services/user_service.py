from app.models.users import User
from app.core.security import hash_password,verify_password,create_refresh_token,create_access_token
from fastapi import HTTPException,status
from app.core.config import settings
from datetime import timedelta

# the job of the service is to contain only the buisiness logic the communication with the client is done by the routers.

def create_user(user,db):
    password = user.password
    hashed_password = hash_password(password)

    new_user = User(
        username = user.username,
        hashed_password = hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def login_user(user_credentials,db):
    user = db.query(User).filter(User.username == user_credentials.username).first()

    if not user:
        return None
    
    if not verify_password(user_credentials.password,user.hashed_password):
        return None
    
    refresh_token = create_refresh_token({"sub":user.username},timedelta(days=int(settings.REFRESH_TOKEN_EXPIRE_DAYS)))
    access_token = create_access_token({"sub":user.username},timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES)))

    return access_token,refresh_token

def retrieve_users(db):
   return db.query(User).all()

def refresh_access_token(refresh_token: str, db):
    try:
        from jose import jwt, JWTError
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid Refresh Token")
        
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
            
        new_access_token = create_access_token(
            {"sub": user.username}, 
            timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        )
        return new_access_token
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Refresh Token")
