import uuid
import enum
from sqlalchemy import Table, Column, String, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, EmailStr
from typing import Optional
from .base import metadata

# Enum para roles
class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    PHOTOGRAPHER = "PHOTOGRAPHER"

# Tabela SQLAlchemy
users_table = Table(
    "users",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("name", String, nullable=False),
    Column("last_name", String, nullable=True),
    Column("email", String(255), nullable=False, unique=True, index=True),
    Column("password_hash", String, nullable=False),
    Column("whatsapp", String, nullable=True),
    Column("instagram", String, nullable=True),
    Column("accepted_lgpd", Boolean, default=False, nullable=False),
    Column("biometric_acceptance", Boolean, default=False, nullable=False),
    Column("international_transfer_data", Boolean, default=False, nullable=False),
    Column("image_usage_portifolio", Boolean, default=False, nullable=False),
    Column("marketing_communication_usage", Boolean, default=False, nullable=False),
    Column("age_declaration", Boolean, default=False, nullable=False),
    Column("responsible_consent", Boolean, default=False, nullable=True),
    Column("event_slug", String, nullable=True),
    Column("role", Enum(UserRole, name="user_roles"), nullable=False, default=UserRole.USER),
)

# Schemas Pydantic
class UserBase(BaseModel):
    name: str
    last_name: Optional[str] = None
    email: EmailStr
    whatsapp: Optional[str] = None
    instagram: Optional[str] = None
    event_slug: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.USER
    accepted_lgpd: bool = True
    biometric_acceptance: bool = True
    international_transfer_data: bool = True
    image_usage_portifolio: bool = True
    marketing_communication_usage: bool = True
    age_declaration: bool = True
    responsible_consent: bool = True


# --- INÍCIO DA CORREÇÃO ---
class UserOut(BaseModel):
    """Este é o schema que a sua API RETORNA."""
    id: uuid.UUID
    name: str
    last_name: Optional[str] = None
    email: EmailStr
    whatsapp: Optional[str] = None
    instagram: Optional[str] = None
    event_slug: Optional[str] = None
    role: UserRole

    # ✅ Campos que estavam faltando foram adicionados
    accepted_lgpd: bool
    biometric_acceptance: bool
    international_transfer_data: bool
    image_usage_portifolio: bool
    marketing_communication_usage: bool
    age_declaration: bool
    responsible_consent: Optional[bool] = None  # É opcional, pois é nullable no DB

    class Config:
        from_attributes = True


# --- FIM DA CORREÇÃO ---

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class AdminCreate(UserBase):
    password: str
    role: UserRole = UserRole.ADMIN
    accepted_lgpd: bool = True
    biometric_acceptance: bool = True
    international_transfer_data: bool = True
    image_usage_portifolio: bool = True
    marketing_communication_usage: bool = True
    age_declaration: bool = True
    responsible_consent: bool = True

