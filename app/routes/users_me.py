from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.db import get_conn
from app.schemas.user import users_table
from app.security.jwt import require_any_user

router = APIRouter()

@router.get("/me")
async def get_me(user=Depends(require_any_user), conn: AsyncSession = Depends(get_conn)):
    result = await conn.execute(
        select(
            users_table.c.id,
            users_table.c.name.label("user_name"),  # adiciona user_name
            users_table.c.email,
            users_table.c.role,
            users_table.c.event_slug,
        ).where(users_table.c.id == user["user_id"])
    )
    db_user = result.mappings().first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return dict(db_user)
