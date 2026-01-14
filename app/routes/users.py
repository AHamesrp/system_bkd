from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.schemas.user import UserCreate, UserOut, AdminCreate, users_table  # <-- import correto da tabela
from app.services.db import get_conn
from app.services.users import create_or_get_user, create_admin_user

router = APIRouter()


# --- Cadastro de usuário normal/fotógrafo ---
@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, conn: AsyncSession = Depends(get_conn)):
    user = await create_or_get_user(conn, payload)
    
    user_data = dict(user)
    user_data['id'] = str(user_data['id'])  # converte UUID para string
    return UserOut(**user_data)


# --- Cadastro de admin ---
@router.post("/admin", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_admin(payload: AdminCreate, conn: AsyncSession = Depends(get_conn)):
    user = await create_admin_user(conn, payload)
    
    if not user:
        raise HTTPException(status_code=400, detail="Falha ao criar admin ou admin já existe.")
    
    user_data = dict(user)
    user_data['id'] = str(user_data['id'])
    return UserOut(**user_data)


# --- Buscar usuário por ID ---
@router.get("/{user_id}", response_model=UserOut)
async def get_user_by_id(user_id: str, conn: AsyncSession = Depends(get_conn)):
    try:
        uuid_obj = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de usuário inválido.")

    result = await conn.execute(
        select(
            users_table.c.id,
            users_table.c.name,
            users_table.c.last_name,
            users_table.c.email,
            users_table.c.whatsapp,
            users_table.c.instagram,
            users_table.c.accepted_lgpd,
            users_table.c.biometric_acceptance,
            users_table.c.international_transfer_data,
            users_table.c.image_usage_portifolio,
            users_table.c.marketing_communication_usage,
            users_table.c.age_declaration,
            users_table.c.responsible_consent,
            users_table.c.event_slug,
            users_table.c.role
        ).where(users_table.c.id == uuid_obj)
    )
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    user_data = dict(row)
    user_data['id'] = str(user_data['id'])  # converte UUID para string
    return UserOut(**user_data)
