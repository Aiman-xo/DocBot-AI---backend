from sqlalchemy import Column,Integer,String,ForeignKey,DateTime
from sqlalchemy.orm import relationship
from app.database.base import Base
from datetime import datetime,timezone

class DocumentModel(Base):
    __tablename__ = 'documents'
    id = Column(Integer,primary_key=True,index=True)
    file_name = Column(String,nullable=False)
    file_path = Column(String,nullable=False)
    user_id = Column(Integer,ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda:datetime.now(timezone.utc))

    user = relationship("User", back_populates="documents")