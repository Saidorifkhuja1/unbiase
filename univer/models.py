from sqlalchemy import Column, String, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
import uuid
from database import Base


class University(Base):
    __tablename__ = "universities"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(length=255), nullable=False,unique=True)
    photo = Column(String(length=255), nullable=True)
    location_id = Column(PGUUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    category_id = Column(PGUUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    description = Column(Text, nullable=False)
    video = Column(String(length=255), nullable=True)
    amount_of_students = Column(Integer, nullable=False)
    phone_number = Column(String(length=20), nullable=False, unique=True)
    email = Column(String(length=255), nullable=False, unique=True)
    webpage = Column(String(length=255), nullable=False)
    created_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    location = relationship("Location", backref="universities")
    category = relationship("Category", backref="universities")
    created_by = relationship("Users", backref="universities")


class Department(Base):
    __tablename__ = "departments"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(length=255), nullable=False, unique=True)
    photo = Column(String(length=255), nullable=True)
    description = Column(Text, nullable=False)
    university_id = Column(PGUUID(as_uuid=True), ForeignKey("universities.id"), nullable=False)
    university = relationship("University", backref="departments")




class Deterioration(Base):
    __tablename__ = "deteriorations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(length=255), nullable=False, unique=True)
    department_id = Column(PGUUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    photo = Column(String(length=255), nullable=True)
    description = Column(Text, nullable=False)
    number_of_students = Column(Integer, nullable=False)
    department = relationship("Department", backref="deteriorations")

