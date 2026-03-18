from sqlalchemy import Column,Integer,String,Boolean
from sqlalchemy.orm import relationship
from app.database.base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer,primary_key=True,index=True)
    username = Column(String,index=True,unique=True)
    hashed_password = Column(String)

    documents = relationship("DocumentModel", back_populates="user")


