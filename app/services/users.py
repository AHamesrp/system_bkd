import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select
from passlib.hash import bcrypt
from fastapi import HTTPException, status
from app.schemas.user import users_table, UserCreate, AdminCreate, UserRole
from app.services.metrics import track

# -------------------------------
# Função auxiliar para validar role
# -------------------------------
def validate_role(role: str) -> UserRole:
    try:
        return UserRole(role)  # tenta converter direto para enum
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Role inválida: {role}")
# -------------------------------
# Criar ou obter usuário normal
# -------------------------------
async def create_or_get_user(conn: AsyncSession, data: UserCreate):
    email = data.email.lower().strip()
    stmt = select(users_table).where(users_table.c.email == email)
    result = await conn.execute(stmt)
    existing = result.mappings().first()
    
    if existing:
        return existing
    
    password_hash = bcrypt.hash(data.password)
    role_enum = validate_role(data.role.value)

    stmt = (
        insert(users_table)
        .values(
            name=data.name,
            email=email,
            last_name=data.last_name,
            password_hash=password_hash, 
            whatsapp=data.whatsapp,
            instagram=data.instagram,
            accepted_lgpd=data.accepted_lgpd,
            biometric_acceptance=data.biometric_acceptance,
            international_transfer_data=data.international_transfer_data,
            image_usage_portifolio=data.image_usage_portifolio,
            marketing_communication_usage=data.marketing_communication_usage,
            age_declaration=data.age_declaration,
            responsible_consent=data.responsible_consent,
            event_slug=data.event_slug,
            role=role_enum,
        )
        .returning(users_table)
    )
    result = await conn.execute(stmt)
    row = result.mappings().first()
    
    if row:
        await track(
            conn,
            action="register",
            user_id=str(row["id"]),
            event_slug=data.event_slug
        )
        await conn.commit()
        
    return row

# -------------------------------
# Criar usuário admin
# -------------------------------
async def create_admin_user(conn: AsyncSession, data: AdminCreate):
    email = data.email.lower().strip()
    stmt = select(users_table).where(users_table.c.email == email)
    result = await conn.execute(stmt)
    if result.mappings().first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Um usuário com este e-mail já existe.")

    password_hash = bcrypt.hash(data.password)
    role_enum = UserRole.ADMIN  # enum direto

    stmt = (
        insert(users_table)
        .values(
            name=data.name,
            last_name=data.last_name,
            email=email,
            whatsapp=data.whatsapp,
            instagram=data.instagram,
            accepted_lgpd=data.accepted_lgpd,
            biometric_acceptance=data.biometric_acceptance,
            international_transfer_data=data.international_transfer_data,
            image_usage_portifolio=data.image_usage_portifolio,
            marketing_communication_usage=data.marketing_communication_usage,
            age_declaration=data.age_declaration,
            responsible_consent=data.responsible_consent,
            password_hash=password_hash,
            role=role_enum,
            event_slug=data.event_slug,
        )
        .returning(users_table)
    )
    result = await conn.execute(stmt)
    row = result.mappings().first()


    return row

# -------------------------------
# Autenticação
# -------------------------------
async def authenticate_user(conn: AsyncSession, email: str, password: str):
    stmt = select(users_table).where(users_table.c.email == email.lower().strip())
    result = await conn.execute(stmt)
    user = result.mappings().first()
    if not user or not user["password_hash"]:
        return None
    if not bcrypt.verify(password, user["password_hash"]):
        return None
    return user
