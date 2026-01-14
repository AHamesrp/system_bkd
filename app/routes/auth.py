# app/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException, Form, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from passlib.hash import bcrypt
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.services.db import get_conn
from app.schemas.user import users_table, UserOut, UserRole
from app.schemas.session import active_sessions_table
from app.security.jwt import create_access_token, require_any_user

router = APIRouter()

# Executor para operações bloqueantes de autenticação (bcrypt)
_auth_executor = ThreadPoolExecutor(
    max_workers=20,
    thread_name_prefix="auth_worker"
)


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
        conn: AsyncSession = Depends(get_conn),
):
    stmt = select(users_table).where(users_table.c.email == email)
    result = await conn.execute(stmt)
    user_from_db = result.mappings().first()

    # Verificação básica de existência do usuário
    if not user_from_db or not user_from_db["password_hash"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    # Mover bcrypt.verify para thread pool (operação bloqueante)
    loop = asyncio.get_running_loop()
    password_valid = await loop.run_in_executor(
        _auth_executor,
        bcrypt.verify,
        password,
        user_from_db["password_hash"]
    )

    if not password_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    jti = str(uuid.uuid4())
    user_id = str(user_from_db["id"])

    payload = {
        "sub": user_id,
        "role": user_from_db["role"],
    }

    token, _ = create_access_token(payload, jti=jti)

    session_stmt = insert(active_sessions_table).values(
        user_id=user_id,
        token_jti=jti,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", "N/A"),
    )
    await conn.execute(session_stmt)
    await conn.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "jti": jti,
        "user": {
            "id": user_id,
            "email": user_from_db["email"],
            "name": user_from_db["name"],
            "role": user_from_db["role"],
            "event_slug": user_from_db["event_slug"],
        }
    }

@router.post("/refresh")
async def refresh(payload=Depends(require_any_user)):
    jti = str(uuid.uuid4())
    token, exp = create_access_token({
        "sub": payload["user_id"],
        "role": payload["role"]
    }, jti=jti)

    return {"access_token": token, "expires_at": exp}


