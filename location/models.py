from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
import uuid
from database import Base




class Location(Base):
    __tablename__ = "locations"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(length=250), nullable=False)
    created_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_by = relationship("Users", backref="locations")





