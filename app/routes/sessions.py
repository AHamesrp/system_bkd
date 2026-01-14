# app/routes/sessions.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete
from datetime import datetime, timedelta, timezone
from jose import jwt

from app.services.db import get_conn
from app.security.jwt import require_admin, SECRET_KEY, ALGORITHM
from app.schemas.session import active_sessions_table, token_denylist_table

router = APIRouter(prefix="/sessions", dependencies=[Depends(require_admin)])

@router.get("/active")
async def get_active_sessions(conn: AsyncSession = Depends(get_conn)):
    five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
    stmt = select(active_sessions_table).where(active_sessions_table.c.last_seen_at >= five_minutes_ago)
    result = await conn.execute(stmt)
    return result.mappings().all()

@router.delete("/{jti}")
async def force_logout(jti: str, token_data: dict = Depends(require_admin), conn: AsyncSession = Depends(get_conn)):
    # Adiciona o JTI à denylist para invalidá-lo
    # Para pegar a expiração, precisamos decodificar o token novamente (ou passar o token inteiro)
    # Aqui, vamos assumir que o token que está sendo invalidado é o mesmo que fez a requisição
    # Em um sistema real, o JTI seria de outro usuário
    
    # Simplesmente adicionamos à denylist, a expiração pode ser um valor futuro fixo para cleanup
    expire = datetime.now(timezone.utc) + timedelta(days=1)
    
    denylist_stmt = insert(token_denylist_table).values(jti=jti, expires_at=expire)
    await conn.execute(denylist_stmt)

    # Remove da lista de sessões ativas
    delete_stmt = delete(active_sessions_table).where(active_sessions_table.c.token_jti == jti)
    await conn.execute(delete_stmt)
    
    await conn.commit()
    return {"message": "Sessão invalidada com sucesso."}