from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(length=100), nullable=False)
    lastname = Column(String(length=100), nullable=False)
    photo = Column(String, nullable=True)
    deterioration_id = Column(UUID(as_uuid=True), ForeignKey("deteriorations.id"), nullable=False)
    description = Column(String, nullable=True)
    working_place = Column(String(length=250), nullable=True)
    achievements = Column(String, nullable=True)
    deterioration = relationship("Deterioration", backref="students")
