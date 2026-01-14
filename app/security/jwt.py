import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.db import get_conn
from app.schemas.session import token_denylist_table
from app.schemas.user import UserRole

SECRET_KEY = os.getenv("SECRET_KEY", "seu-segredo-super-secreto")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(data: dict, jti: str):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "jti": jti})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expire



async def require_role(required_role: UserRole, token: str = Depends(oauth2_scheme), conn: AsyncSession = Depends(get_conn)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        role: str = payload.get("role")

        if user_id is None or jti is None or role is None:
            raise credentials_exception

        if role != required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão negada")

        # Verifica denylist
        stmt = select(token_denylist_table).where(token_denylist_table.c.jti == jti)
        result = await conn.execute(stmt)
        if result.first() is not None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    return {"user_id": user_id, "jti": jti, "role": role}


# atalhos
async def require_admin(token: str = Depends(oauth2_scheme), conn: AsyncSession = Depends(get_conn)):
    return await require_role(UserRole.ADMIN, token, conn)


async def require_photographer(token: str = Depends(oauth2_scheme), conn: AsyncSession = Depends(get_conn)):
    return await require_role(UserRole.PHOTOGRAPHER, token, conn)


async def require_user(token: str = Depends(oauth2_scheme), conn: AsyncSession = Depends(get_conn)):
    return await require_role(UserRole.USER, token, conn)


# aceita USER ou PHOTOGRAPHER
import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.db import get_conn
from app.schemas.session import token_denylist_table
from app.schemas.user import UserRole

SECRET_KEY = os.getenv("SECRET_KEY", "seu-segredo-super-secreto")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(data: dict, jti: str):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "jti": jti})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expire



async def require_role(required_role: UserRole, token: str = Depends(oauth2_scheme), conn: AsyncSession = Depends(get_conn)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        role: str = payload.get("role")

        if user_id is None or jti is None or role is None:
            raise credentials_exception

        if role != required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão negada")

        # Verifica denylist
        stmt = select(token_denylist_table).where(token_denylist_table.c.jti == jti)
        result = await conn.execute(stmt)
        if result.first() is not None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    return {"user_id": user_id, "jti": jti, "role": role}


# atalhos
async def require_admin(token: str = Depends(oauth2_scheme), conn: AsyncSession = Depends(get_conn)):
    return await require_role(UserRole.ADMIN, token, conn)


async def require_photographer(token: str = Depends(oauth2_scheme), conn: AsyncSession = Depends(get_conn)):
    return await require_role(UserRole.PHOTOGRAPHER, token, conn)


async def require_user(token: str = Depends(oauth2_scheme), conn: AsyncSession = Depends(get_conn)):
    return await require_role(UserRole.USER, token, conn)


# aceita USER ou PHOTOGRAPHER
async def require_any_user(token: str = Depends(oauth2_scheme), conn: AsyncSession = Depends(get_conn)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        role: str = payload.get("role")

        if user_id is None or jti is None or role is None:
            raise credentials_exception

        if role not in [UserRole.USER, UserRole.PHOTOGRAPHER, UserRole.ADMIN]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão negada")

        # Verifica denylist
        stmt = select(token_denylist_table).where(token_denylist_table.c.jti == jti)
        result = await conn.execute(stmt)
        if result.first() is not None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    return {"user_id": user_id, "jti": jti, "role": role}
