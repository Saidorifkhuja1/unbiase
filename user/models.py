from sqlalchemy import Column, String, DateTime, func, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from passlib.context import CryptContext
import uuid
from database import Base
# Initialize password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define the base class for ORM models


# Define the Users model
class Users(Base):
    __tablename__ = 'users'

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)

    phone_number = Column(String(255), nullable=False)
    status = Column(Boolean, default=False, nullable=False)
    password = Column(String(60), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @staticmethod
    def verify_password(plain_password, hashed_password):
        """Verify if a plain password matches the hashed password."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password):
        """Hash the password using bcrypt."""
        return pwd_context.hash(password)
