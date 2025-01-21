from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from database import Base

class Comment(Base):
    __tablename__ = 'comments'

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    body = Column(String, nullable=False)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    university_id = Column(PGUUID(as_uuid=True), ForeignKey('universities.id'), nullable=False)

    user = relationship("Users", backref="comments")
    university = relationship("University", backref="comments")

