from pydantic import BaseModel,ConfigDict,Field

class UserCreate(BaseModel):
    username: str
    password : str= Field(..., max_length=64) 

# sending the necessary response
# -----------------------------

class UserResponse(BaseModel):
    id:int
    username:str

    # this makes this class response return as aa dictionary
    model_config = ConfigDict(from_attributes=True)

class RegistrationSuccess(BaseModel): 
    message: str
    user: UserResponse

# ----------------------------

class UserLogin(BaseModel):
    username: str
    password : str = Field(..., max_length=64) 