import bcrypt
from app.core.config import settings
from jose import jwt
from datetime import timedelta,datetime,timezone

def hash_password(password:str):
    # Salt is generated automatically
    # Encodes password to bytes, hashes it, then decodes back to string for storage
    bytes_password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(bytes_password, salt)
    return hash.decode('utf-8')

def verify_password(plain_password:str, hashed_password:str):
    # Encodes both to bytes and uses bcrypt.checkpw to verify
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data:dict,expiry_time_limit:timedelta):
    to_encode_data = data.copy()
    expiry_time = datetime.now(timezone.utc) + expiry_time_limit
    to_encode_data.update({'exp':expiry_time})
    encoded_jwt = jwt.encode(to_encode_data,settings.SECRET_KEY,algorithm=settings.ALGORITHM)

    return encoded_jwt

def create_refresh_token(data:dict,expiry_time_limit:timedelta):
    to_encode_data = data.copy()
    expiry_time = datetime.now(timezone.utc) + expiry_time_limit
    to_encode_data.update({'exp':expiry_time})

    encoded_jwt = jwt.encode(to_encode_data,settings.SECRET_KEY,algorithm=settings.ALGORITHM)
    return encoded_jwt