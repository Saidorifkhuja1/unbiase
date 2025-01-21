from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from database import Base

class Cart(Base):
    __tablename__ = 'carts'

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    university_id = Column(PGUUID(as_uuid=True), ForeignKey('universities.id'), nullable=False)

    user = relationship("Users", backref="carts")
    university = relationship("University", backref="carts")

